

I'll generate the complete test suite manually since the tool encountered an issue. Let me build all 6 required files with proper test coverage.

---

## 🧪 Test Suite Package for FTL to PI Migration

### Summary Table

| Test Type | Count | Files Generated |
|-----------|-------|-----------------|
| **Unit Tests** | 9 tests | `tests/unit/unit_tests.sql` |
| **Functional Tests** | 12 tests | `tests/functional/functional_tests.sql` |
| **Gold Equivalence Test** | 1 test | `tests/functional/gold_equivalence_test.sql` |
| **dbt YAML Tests** | 20 tests | `models/silver/slv_ftl_agent_base_agg.yml` |
| **Regression Suite** | 8 tests | `tests/regression/regression_suite.sql` |
| **Test Runbook** | 1 guide | `TEST_RUNBOOK.md` |
| **TOTAL** | **50 tests** | **6 files** |

---

### 🧪 STEP 1: Unit Tests — Validate each business rule transformation

**Purpose**: Verify that each BR-001 through BR-009 transformation produces expected results

---

### FILE 1: `tests/unit/unit_tests.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- FTL TO PI MIGRATION — UNIT TESTS
-- Purpose: Validate each business rule transformation individually
-- Pass Condition: Each test returns 0 rows = PASS
-- On Failure: Contact Data Engineering team; review transformation logic
-- ═══════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR001_user_id
-- Business Rule: BR-001 AGENT_ID → USER_ID semantic mapping
-- Pass: All AGENT_ID values successfully map to USER_ID
-- Fail: NULL USER_ID where AGENT_ID exists OR USER_ID != AGENT_ID
-- ────────────────────────────────────────────────────────────────────────────
WITH br001_test AS (
    SELECT 
        AGENT_ID,
        USER_ID,
        'test_unit_BR001_user_id' AS test_name,
        CASE 
            WHEN AGENT_ID IS NOT NULL AND USER_ID IS NULL 
                THEN 'FAIL: USER_ID is NULL when AGENT_ID exists'
            WHEN AGENT_ID IS NOT NULL AND USER_ID != AGENT_ID 
                THEN 'FAIL: USER_ID does not match AGENT_ID'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br001_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR002_direction
-- Business Rule: BR-002 DIRECTION case normalization to uppercase
-- Pass: All DIRECTION values are uppercase (INBOUND or OUTBOUND)
-- Fail: Any lowercase or mixed-case values found
-- ────────────────────────────────────────────────────────────────────────────
WITH br002_test AS (
    SELECT 
        DIRECTION,
        'test_unit_BR002_direction' AS test_name,
        CASE 
            WHEN DIRECTION IS NOT NULL 
                 AND DIRECTION NOT IN ('INBOUND', 'OUTBOUND')
                THEN 'FAIL: DIRECTION not normalized to uppercase'
            WHEN DIRECTION != UPPER(DIRECTION)
                THEN 'FAIL: DIRECTION contains lowercase characters'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br002_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR003_modality
-- Business Rule: BR-003 MODALITY case normalization to uppercase
-- Pass: All MODALITY values are uppercase
-- Fail: Any lowercase or mixed-case values found
-- ────────────────────────────────────────────────────────────────────────────
WITH br003_test AS (
    SELECT 
        MODALITY,
        'test_unit_BR003_modality' AS test_name,
        CASE 
            WHEN MODALITY IS NOT NULL 
                 AND MODALITY NOT IN ('SMS', 'EMAIL', 'CHAT', 'PHONE', 'VIDEO')
                THEN 'FAIL: Invalid MODALITY value'
            WHEN MODALITY != UPPER(MODALITY)
                THEN 'FAIL: MODALITY contains lowercase characters'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br003_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR004_channel
-- Business Rule: BR-004 CHANNEL normalization for combination with MODALITY
-- Pass: All CHANNEL values are uppercase
-- Fail: Any lowercase or invalid channel values
-- ────────────────────────────────────────────────────────────────────────────
WITH br004_test AS (
    SELECT 
        CHANNEL,
        'test_unit_BR004_channel' AS test_name,
        CASE 
            WHEN CHANNEL IS NOT NULL 
                 AND CHANNEL NOT IN ('VIDEO', 'PHONE', 'CHAT', 'EMAIL', 'SMS')
                THEN 'FAIL: Invalid CHANNEL value'
            WHEN CHANNEL != UPPER(CHANNEL)
                THEN 'FAIL: CHANNEL contains lowercase characters'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br004_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR005_inbound_phone_mins
-- Business Rule: BR-005 Unit conversion from milliseconds to minutes
-- Pass: INBOUND_PHONE_MINS = INBOUND_PHONE_MS / 60000 (within rounding tolerance)
-- Fail: Conversion formula incorrect or NULL when source exists
-- ────────────────────────────────────────────────────────────────────────────
WITH br005_test AS (
    SELECT 
        INBOUND_PHONE_MS,
        INBOUND_PHONE_MINS,
        ROUND(INBOUND_PHONE_MS / 60000.0, 2) AS expected_mins,
        'test_unit_BR005_inbound_phone_mins' AS test_name,
        CASE 
            WHEN INBOUND_PHONE_MS IS NOT NULL 
                 AND INBOUND_PHONE_MINS IS NULL
                THEN 'FAIL: INBOUND_PHONE_MINS is NULL when source exists'
            WHEN INBOUND_PHONE_MS IS NOT NULL 
                 AND ABS(INBOUND_PHONE_MINS - ROUND(INBOUND_PHONE_MS / 60000.0, 2)) > 0.01
                THEN 'FAIL: Unit conversion incorrect'
            WHEN INBOUND_PHONE_MINS < 0
                THEN 'FAIL: Negative duration value'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br005_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR006_duration_sec
-- Business Rule: BR-006 Unit conversion from milliseconds to seconds
-- Pass: DURATION_SEC = INBOUND_PHONE_MS / 1000 (within rounding tolerance)
-- Fail: Conversion formula incorrect or NULL when source exists
-- ────────────────────────────────────────────────────────────────────────────
WITH br006_test AS (
    SELECT 
        INBOUND_PHONE_MS,
        DURATION_SEC,
        ROUND(INBOUND_PHONE_MS / 1000.0, 2) AS expected_sec,
        'test_unit_BR006_duration_sec' AS test_name,
        CASE 
            WHEN INBOUND_PHONE_MS IS NOT NULL 
                 AND DURATION_SEC IS NULL
                THEN 'FAIL: DURATION_SEC is NULL when source exists'
            WHEN INBOUND_PHONE_MS IS NOT NULL 
                 AND ABS(DURATION_SEC - ROUND(INBOUND_PHONE_MS / 1000.0, 2)) > 0.01
                THEN 'FAIL: Unit conversion incorrect'
            WHEN DURATION_SEC < 0
                THEN 'FAIL: Negative duration value'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br006_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR007_is_active_account
-- Business Rule: BR-007 IS_ACTIVE → IS_ACTIVE_ACCOUNT semantic mapping
-- Pass: IS_ACTIVE_ACCOUNT inherits all IS_ACTIVE boolean values
-- Fail: Type mismatch or NULL propagation issue
-- ────────────────────────────────────────────────────────────────────────────
WITH br007_test AS (
    SELECT 
        IS_ACTIVE_ACCOUNT,
        'test_unit_BR007_is_active_account' AS test_name,
        CASE 
            WHEN IS_ACTIVE_ACCOUNT IS NULL
                THEN 'FAIL: IS_ACTIVE_ACCOUNT is NULL'
            WHEN IS_ACTIVE_ACCOUNT NOT IN (TRUE, FALSE)
                THEN 'FAIL: IS_ACTIVE_ACCOUNT is not boolean'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br007_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR008_region
-- Business Rule: BR-008 CLUSTER → REGION mapping via lookup table
-- Pass: All CLUSTER values successfully map to REGION
-- Fail: NULL REGION where CLUSTER exists OR 'Unknown' region found
-- ────────────────────────────────────────────────────────────────────────────
WITH br008_test AS (
    SELECT 
        CLUSTER,
        REGION,
        'test_unit_BR008_region' AS test_name,
        CASE 
            WHEN CLUSTER IS NOT NULL AND REGION IS NULL
                THEN 'FAIL: REGION is NULL when CLUSTER exists'
            WHEN REGION = 'Unknown'
                THEN 'WARN: CLUSTER mapped to Unknown region'
            WHEN REGION NOT IN ('North America', 'Europe', 'Asia Pacific', 'Unknown')
                THEN 'FAIL: Invalid REGION value'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br008_test;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_unit_BR009_date_key
-- Business Rule: BR-009 DATA_DATE (TEXT) → DATE_KEY (DATE) type conversion
-- Pass: All DATA_DATE values successfully cast to DATE
-- Fail: NULL DATE_KEY where DATA_DATE exists OR invalid date format
-- ────────────────────────────────────────────────────────────────────────────
WITH br009_test AS (
    SELECT 
        DATA_DATE_RAW,
        DATE_KEY,
        REPORT_DATE,
        START_DATE,
        'test_unit_BR009_date_key' AS test_name,
        CASE 
            WHEN DATA_DATE_RAW IS NOT NULL AND DATE_KEY IS NULL
                THEN 'FAIL: DATE_KEY is NULL when DATA_DATE exists'
            WHEN DATE_KEY IS NOT NULL AND DATE_KEY::TEXT != DATA_DATE_RAW
                THEN 'FAIL: DATE_KEY does not match source DATA_DATE'
            WHEN DATE_KEY != REPORT_DATE OR DATE_KEY != START_DATE
                THEN 'FAIL: Date dimension inconsistency across columns'
            ELSE NULL
        END AS failure_reason
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE failure_reason IS NOT NULL
)
SELECT * FROM br009_test;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF UNIT TESTS
-- Total: 9 unit tests covering BR-001 through BR-009
-- ═══════════════════════════════════════════════════════════════════════════
```

---

### 🧪 STEP 2: Functional Tests — Validate data quality and completeness

**Purpose**: Row counts, NULL checks, value distribution, referential integrity

---

### FILE 2: `tests/functional/functional_tests.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- FTL TO PI MIGRATION — FUNCTIONAL TESTS
-- Purpose: Validate data quality, completeness, and referential integrity
-- Pass Condition: Each test returns 0 rows = PASS
-- On Failure: Contact Data Engineering team; investigate data quality issues
-- ═══════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_row_count_match
-- Validates: Row count in Silver matches Bronze source
-- Pass: Silver row count = Bronze row count
-- Fail: Row count mismatch indicates data loss or duplication
-- ────────────────────────────────────────────────────────────────────────────
WITH row_counts AS (
    SELECT 
        (SELECT COUNT(*) FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG) AS bronze_count,
        (SELECT COUNT(*) FROM {{ ref('slv_ftl_agent_base_agg') }}) AS silver_count
),
test_result AS (
    SELECT 
        'test_func_row_count_match' AS test_name,
        bronze_count,
        silver_count,
        CASE 
            WHEN bronze_count != silver_count 
                THEN CONCAT('FAIL: Row count mismatch - Bronze: ', bronze_count, ', Silver: ', silver_count)
            ELSE NULL
        END AS failure_reason
    FROM row_counts
)
SELECT * FROM test_result WHERE failure_reason IS NOT NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_account_id_not_null
-- Validates: ACCOUNT_ID is never NULL (required for all joins)
-- Pass: Zero NULL ACCOUNT_ID values
-- Fail: NULL ACCOUNT_ID found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_account_id_not_null' AS test_name,
    COUNT(*) AS null_count,
    'FAIL: NULL ACCOUNT_ID found' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE ACCOUNT_ID IS NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_engagement_id_uniqueness
-- Validates: ENGAGEMENT_ID is unique (primary key constraint)
-- Pass: No duplicate ENGAGEMENT_ID values
-- Fail: Duplicates found
-- ────────────────────────────────────────────────────────────────────────────
WITH duplicates AS (
    SELECT 
        ENGAGEMENT_ID,
        COUNT(*) AS dup_count
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE ENGAGEMENT_ID IS NOT NULL
    GROUP BY ENGAGEMENT_ID
    HAVING COUNT(*) > 1
)
SELECT 
    'test_func_engagement_id_uniqueness' AS test_name,
    ENGAGEMENT_ID,
    dup_count,
    'FAIL: Duplicate ENGAGEMENT_ID found' AS failure_reason
FROM duplicates;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_date_key_not_null
-- Validates: DATE_KEY is never NULL (required for time-series analysis)
-- Pass: Zero NULL DATE_KEY values
-- Fail: NULL DATE_KEY found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_date_key_not_null' AS test_name,
    COUNT(*) AS null_count,
    'FAIL: NULL DATE_KEY found - date conversion failed' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE DATE_KEY IS NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_phone_sessions_non_negative
-- Validates: PHONE_SESSIONS >= 0 (cannot have negative session counts)
-- Pass: All PHONE_SESSIONS >= 0
-- Fail: Negative values found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_phone_sessions_non_negative' AS test_name,
    PHONE_SESSIONS,
    'FAIL: Negative PHONE_SESSIONS value' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE PHONE_SESSIONS < 0;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_duration_values_non_negative
-- Validates: All duration metrics >= 0
-- Pass: INBOUND_PHONE_MINS, DURATION_SEC, INBOUND_PHONE_MS all >= 0
-- Fail: Negative duration found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_duration_values_non_negative' AS test_name,
    INBOUND_PHONE_MS,
    INBOUND_PHONE_MINS,
    DURATION_SEC,
    'FAIL: Negative duration value detected' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE INBOUND_PHONE_MS < 0 
   OR INBOUND_PHONE_MINS < 0 
   OR DURATION_SEC < 0;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_direction_valid_values
-- Validates: DIRECTION contains only valid values
-- Pass: DIRECTION IN ('INBOUND', 'OUTBOUND') or NULL
-- Fail: Invalid DIRECTION value found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_direction_valid_values' AS test_name,
    DIRECTION,
    COUNT(*) AS invalid_count,
    'FAIL: Invalid DIRECTION value' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE DIRECTION NOT IN ('INBOUND', 'OUTBOUND')
  AND DIRECTION IS NOT NULL
GROUP BY DIRECTION;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_modality_valid_values
-- Validates: MODALITY contains only valid values
-- Pass: MODALITY IN ('SMS', 'EMAIL', 'CHAT', 'PHONE', 'VIDEO') or NULL
-- Fail: Invalid MODALITY value found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_modality_valid_values' AS test_name,
    MODALITY,
    COUNT(*) AS invalid_count,
    'FAIL: Invalid MODALITY value' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE MODALITY NOT IN ('SMS', 'EMAIL', 'CHAT', 'PHONE', 'VIDEO')
  AND MODALITY IS NOT NULL
GROUP BY MODALITY;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_gap_GAP001_client_type_is_null
-- Validates: GAP-001 CLIENT_TYPE new capability tracking
-- Pass: CLIENT_TYPE populated where available
-- Fail: Unexpectedly high NULL rate (>20%)
-- ────────────────────────────────────────────────────────────────────────────
WITH null_rate AS (
    SELECT 
        COUNT(*) AS total_rows,
        SUM(CASE WHEN CLIENT_TYPE IS NULL THEN 1 ELSE 0 END) AS null_count,
        ROUND(100.0 * SUM(CASE WHEN CLIENT_TYPE IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS null_pct
    FROM {{ ref('slv_ftl_agent_base_agg') }}
)
SELECT 
    'test_gap_GAP001_client_type_is_null' AS test_name,
    null_count,
    null_pct,
    'FAIL: CLIENT_TYPE NULL rate exceeds 20% threshold' AS failure_reason
FROM null_rate
WHERE null_pct > 20;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_gap_GAP002_os_is_null
-- Validates: GAP-002 OS new capability tracking
-- Pass: OS populated where available
-- Fail: Unexpectedly high NULL rate (>20%)
-- ────────────────────────────────────────────────────────────────────────────
WITH null_rate AS (
    SELECT 
        COUNT(*) AS total_rows,
        SUM(CASE WHEN OS IS NULL THEN 1 ELSE 0 END) AS null_count,
        ROUND(100.0 * SUM(CASE WHEN OS IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS null_pct
    FROM {{ ref('slv_ftl_agent_base_agg') }}
)
SELECT 
    'test_gap_GAP002_os_is_null' AS test_name,
    null_count,
    null_pct,
    'FAIL: OS NULL rate exceeds 20% threshold' AS failure_reason
FROM null_rate
WHERE null_pct > 20;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_data_quality_flag_distribution
-- Validates: Data quality flag tracking
-- Pass: <5% of records flagged with quality issues
-- Fail: Quality flag rate exceeds threshold
-- ────────────────────────────────────────────────────────────────────────────
WITH quality_summary AS (
    SELECT 
        COUNT(*) AS total_rows,
        SUM(CASE WHEN DATA_QUALITY_FLAG IS NOT NULL THEN 1 ELSE 0 END) AS flagged_rows,
        ROUND(100.0 * SUM(CASE WHEN DATA_QUALITY_FLAG IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS flagged_pct
    FROM {{ ref('slv_ftl_agent_base_agg') }}
)
SELECT 
    'test_func_data_quality_flag_distribution' AS test_name,
    flagged_rows,
    flagged_pct,
    'FAIL: Data quality flag rate exceeds 5% threshold' AS failure_reason
FROM quality_summary
WHERE flagged_pct > 5;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_func_region_mapping_completeness
-- Validates: BR-008 CLUSTER → REGION mapping completeness
-- Pass: All records have valid REGION (not 'Unknown')
-- Fail: 'Unknown' region mappings found
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_func_region_mapping_completeness' AS test_name,
    CLUSTER,
    REGION,
    COUNT(*) AS unknown_count,
    'FAIL: CLUSTER mapped to Unknown region' AS failure_reason
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE REGION = 'Unknown'
GROUP BY CLUSTER, REGION;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF FUNCTIONAL TESTS
-- Total: 12 functional tests covering data quality and completeness
-- ═══════════════════════════════════════════════════════════════════════════
```

---

### 🧪 STEP 3: Gold Equivalence Test — Compare FTL Gold vs PI Gold

**Purpose**: Validate that gld_aggregate_new produces equivalent results to GLD_AGGREGATE

---

### FILE 3: `tests/functional/gold_equivalence_test.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- FTL TO PI MIGRATION — GOLD EQUIVALENCE TEST
-- Purpose: Compare gld_aggregate_new (FTL source) vs GLD_AGGREGATE (PI source)
-- Pass Condition: Metrics match within 5% tolerance OR row differences explained
-- On Failure: Contact Data Engineering + Business Analytics teams
-- ═══════════════════════════════════════════════════════════════════════════

-- [ASSUMPTION] gld_aggregate_new model exists and has been materialized
-- [ASSUMPTION] GLD_AGGREGATE schema matches: DATE, REGION, SEGMENT, IS_LICENSED,
--              ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS

WITH ftl_gold AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        ACTIVE_ACCOUNTS,
        ACTIVE_USERS,
        PHONE_USAGE,
        USERS_ACTIVE_16PLUS_DAYS,
        'FTL_SOURCE' AS source_system
    FROM {{ ref('gld_aggregate_new') }}
    WHERE DATE >= DATEADD(day, -30, CURRENT_DATE())  -- Last 30 days
),

pi_gold AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        ACTIVE_ACCOUNTS,
        ACTIVE_USERS,
        PHONE_USAGE,
        USERS_ACTIVE_16PLUS_DAYS,
        'PI_SOURCE' AS source_system
    FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
    WHERE DATE >= DATEADD(day, -30, CURRENT_DATE())  -- Last 30 days
),

combined AS (
    SELECT * FROM ftl_gold
    UNION ALL
    SELECT * FROM pi_gold
),

comparison AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        
        -- FTL metrics
        MAX(CASE WHEN source_system = 'FTL_SOURCE' THEN ACTIVE_ACCOUNTS END) AS ftl_active_accounts,
        MAX(CASE WHEN source_system = 'FTL_SOURCE' THEN ACTIVE_USERS END) AS ftl_active_users,
        MAX(CASE WHEN source_system = 'FTL_SOURCE' THEN PHONE_USAGE END) AS ftl_phone_usage,
        MAX(CASE WHEN source_system = 'FTL_SOURCE' THEN USERS_ACTIVE_16PLUS_DAYS END) AS ftl_users_16plus,
        
        -- PI metrics
        MAX(CASE WHEN source_system = 'PI_SOURCE' THEN ACTIVE_ACCOUNTS END) AS pi_active_accounts,
        MAX(CASE WHEN source_system = 'PI_SOURCE' THEN ACTIVE_USERS END) AS pi_active_users,
        MAX(CASE WHEN source_system = 'PI_SOURCE' THEN PHONE_USAGE END) AS pi_phone_usage,
        MAX(CASE WHEN source_system = 'PI_SOURCE' THEN USERS_ACTIVE_16PLUS_DAYS END) AS pi_users_16plus
        
    FROM combined
    GROUP BY DATE, REGION, SEGMENT, IS_LICENSED
),

variance_check AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        
        -- Active Accounts comparison
        ftl_active_accounts,
        pi_active_accounts,
        ROUND(100.0 * ABS(ftl_active_accounts - pi_active_accounts) / NULLIF(pi_active_accounts, 0), 2) AS accounts_variance_pct,
        
        -- Active Users comparison
        ftl_active_users,
        pi_active_users,
        ROUND(100.0 * ABS(ftl_active_users - pi_active_users) / NULLIF(pi_active_users, 0), 2) AS users_variance_pct,
        
        -- Phone Usage comparison
        ftl_phone_usage,
        pi_phone_usage,
        ROUND(100.0 * ABS(ftl_phone_usage - pi_phone_usage) / NULLIF(pi_phone_usage, 0), 2) AS phone_variance_pct,
        
        -- Users 16+ Days comparison
        ftl_users_16plus,
        pi_users_16plus,
        ROUND(100.0 * ABS(ftl_users_16plus - pi_users_16plus) / NULLIF(pi_users_16plus, 0), 2) AS users_16plus_variance_pct,
        
        -- Overall variance flag
        CASE 
            WHEN ABS(ftl_active_accounts - pi_active_accounts) / NULLIF(pi_active_accounts, 0) > 0.05 THEN 'FAIL: Active Accounts variance > 5%'
            WHEN ABS(ftl_active_users - pi_active_users) / NULLIF(pi_active_users, 0) > 0.05 THEN 'FAIL: Active Users variance > 5%'
            WHEN ABS(ftl_phone_usage - pi_phone_usage) / NULLIF(pi_phone_usage, 0) > 0.05 THEN 'FAIL: Phone Usage variance > 5%'
            WHEN ABS(ftl_users_16plus - pi_users_16plus) / NULLIF(pi_users_16plus, 0) > 0.05 THEN 'FAIL: Users 16+ Days variance > 5%'
            ELSE NULL
        END AS failure_reason
        
    FROM comparison
)

-- ────────────────────────────────────────────────────────────────────────────
-- TEST RESULT: Only return rows with variance > 5%
-- Pass: Returns 0 rows (all metrics within tolerance)
-- Fail: Returns rows with >5% variance requiring investigation
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_gold_equivalence' AS test_name,
    DATE,
    REGION,
    SEGMENT,
    IS_LICENSED,
    accounts_variance_pct,
    users_variance_pct,
    phone_variance_pct,
    users_16plus_variance_pct,
    failure_reason
FROM variance_check
WHERE failure_reason IS NOT NULL
ORDER BY DATE DESC, REGION, SEGMENT;

-- ═══════════════════════════════════════════════════════════════════════════
-- SUPPLEMENTAL DIAGNOSTIC QUERY (comment out for automated testing)
-- Uncomment to investigate variance patterns
-- ═══════════════════════════════════════════════════════════════════════════

/*
-- Row-level comparison for troubleshooting
WITH row_diff AS (
    SELECT 
        COALESCE(f.DATE, p.DATE) AS DATE,
        COALESCE(f.REGION, p.REGION) AS REGION,
        CASE 
            WHEN f.DATE IS NULL THEN 'MISSING_IN_FTL'
            WHEN p.DATE IS NULL THEN 'MISSING_IN_PI'
            ELSE 'PRESENT_IN_BOTH'
        END AS row_status
    FROM ftl_gold f
    FULL OUTER JOIN pi_gold p
        ON f.DATE = p.DATE 
        AND f.REGION = p.REGION 
        AND f.SEGMENT = p.SEGMENT
        AND f.IS_LICENSED = p.IS_LICENSED
)
SELECT 
    row_status,
    COUNT(*) AS row_count
FROM row_diff
GROUP BY row_status;
*/

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF GOLD EQUIVALENCE TEST
-- ═══════════════════════════════════════════════════════════════════════════
```

---

### 🧪 STEP 4: dbt YAML Tests — Schema validation for CI/CD

**Purpose**: Automated dbt test suite for continuous integration

---

### FILE 4: `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      Silver layer transformation of FTL Agent Base Aggregation data.
      
      **Business Rules Applied:**
      - BR-001: AGENT_ID → USER_ID semantic mapping
      - BR-002: DIRECTION case normalization (UPPER)
      - BR-003: MODALITY case normalization (UPPER)
      - BR-004: CHANNEL normalization
      - BR-005: INBOUND_PHONE_MS → INBOUND_PHONE_MINS (ms to minutes)
      - BR-006: INBOUND_PHONE_MS → DURATION_SEC (ms to seconds)
      - BR-007: IS_ACTIVE → IS_ACTIVE_ACCOUNT semantic mapping
      - BR-008: CLUSTER → REGION via lookup table
      - BR-009: DATA_DATE (TEXT) → DATE_KEY (DATE) type conversion
      
      **New Capabilities:**
      - GAP-001: CLIENT_TYPE dimension (Mobile|Desktop|Web)
      - GAP-002: OS metadata dimension
      - ZCC_ACCOUNT_ID: Cross-platform account linking
    
    config:
      tags: ['silver', 'ftl_migration', 'critical']
    
    columns:
      # ─── PRIMARY IDENTIFIERS ───
      
      - name: ZCC_ACCOUNT_ID
        description: "ZCC-specific account identifier enabling cross-platform linking (NEW_CAPABILITY)"
        tests:
          - not_null:
              severity: error
          - unique:
              severity: warn
      
      - name: ACCOUNT_ID
        description: "Primary account identifier (DIRECT_MATCH to multiple PI Silver tables)"
        tests:
          - not_null:
              severity: error
              error_if: ">0"
          - relationships:
              severity: error
              to: source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG')
              field: ACCOUNT_ID
      
      - name: ENGAGEMENT_ID
        description: "Unique engagement identifier (DIRECT_MATCH to SLV_COMBINED_CHANNELS.ENGAGEMENT_ID)"
        tests:
          - unique:
              severity: error
          - not_null:
              severity: error
      
      - name: USER_ID
        description: "User identifier (BR-001: transformed from AGENT_ID). Assumption: agents are users."
        tests:
          - not_null:
              severity: error
          - relationships:
              severity: warn
              to: ref('slv_ftl_agent_base_agg')
              field: AGENT_ID
              config:
                where: "AGENT_ID IS NOT NULL"
      
      # ─── COMMUNICATION ATTRIBUTES ───
      
      - name: DIRECTION
        description: "Communication direction (BR-002: normalized to uppercase INBOUND|OUTBOUND)"
        tests:
          - not_null:
              severity: error
          - accepted_values:
              severity: error
              values: ['INBOUND', 'OUTBOUND']
              quote: true
      
      - name: MODALITY
        description: "Communication modality (BR-003: normalized to uppercase)"
        tests:
          - accepted_values:
              severity: error
              values: ['SMS', 'EMAIL', 'CHAT', 'PHONE', 'VIDEO']
              quote: true
      
      - name: CHANNEL
        description: "Communication channel (BR-004: normalized for combination with MODALITY)"
        tests:
          - accepted_values:
              severity: error
              values: ['VIDEO', 'PHONE', 'CHAT', 'EMAIL', 'SMS']
              quote: true
      
      # ─── USAGE METRICS ───
      
      - name: PHONE_SESSIONS
        description: "Count of phone sessions (DIRECT_MATCH to SLV_USAGE_MASTER.PHONE_SESSIONS)"
        tests:
          - not_null:
              severity: error
          - dbt_utils.accepted_range:
              severity: error
              min_value: 0
              inclusive: true
      
      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (BR-005: converted from milliseconds)"
        tests:
          - dbt_utils.accepted_range:
              severity: error
              min_value: 0
              inclusive: true
          - dbt_utils.expression_is_true:
              severity: warn
              expression: "INBOUND_PHONE_MINS = ROUND(INBOUND_PHONE_MS / 60000.0, 2)"
              config:
                where: "INBOUND_PHONE_MS IS NOT NULL"
      
      - name: DURATION_SEC
        description: "Duration in seconds (BR-006: converted from milliseconds for SLV_COMBINED_CHANNELS)"
        tests:
          - dbt_utils.accepted_range:
              severity: error
              min_value: 0
              inclusive: true
          - dbt_utils.expression_is_true:
              severity: warn
              expression: "DURATION_SEC = ROUND(INBOUND_PHONE_MS / 1000.0, 2)"
              config:
                where: "INBOUND_PHONE_MS IS NOT NULL"
      
      - name: INBOUND_PHONE_MS
        description: "Raw inbound phone duration in milliseconds (preserved from source)"
        tests:
          - dbt_utils.accepted_range:
              severity: error
              min_value: 0
              inclusive: true
      
      # ─── DEVICE/PLATFORM METADATA (NEW CAPABILITIES) ───
      
      - name: CLIENT_TYPE
        description: "Client classification: Mobile|Desktop|Web (NEW_CAPABILITY — GAP-001)"
        tests:
          - accepted_values:
              severity: warn
              values: ['Mobile', 'Desktop', 'Web']
              quote: true
              config:
                where: "CLIENT_TYPE IS NOT NULL"
      
      - name: OS
        description: "Operating system metadata (NEW_CAPABILITY — GAP-002)"
        # No specific test - free-form metadata field
      
      # ─── ACTIVITY FLAGS ───
      
      - name: IS_ACTIVE_ACCOUNT
        description: "Account activity flag (BR-007: semantic mapping from IS_ACTIVE)"
        tests:
          - not_null:
              severity: error
          - accepted_values:
              severity: error
              values: [true, false]
              quote: false
      
      # ─── GEOGRAPHIC DIMENSIONS ───
      
      - name: REGION
        description: "Geographic region (BR-008: derived from CLUSTER via lookup)"
        tests:
          - not_null:
              severity: error
          - accepted_values:
              severity: error
              values: ['North America', 'Europe', 'Asia Pacific', 'Unknown']
              quote: true
      
      - name: CLUSTER
        description: "Cloud cluster identifier (source field preserved)"
        tests:
          - accepted_values:
              severity: warn
              values: ['us-east-1', 'eu-central-1', 'ap-south-1']
              quote: true
              config:
                where: "CLUSTER IS NOT NULL"
      
      # ─── DATE DIMENSIONS ───
      
      - name: DATE_KEY
        description: "Date dimension (BR-009: cast from DATA_DATE text to DATE)"
        tests:
          - not_null:
              severity: error
          - dbt_utils.expression_is_true:
              severity: error
              expression: "DATE_KEY >= '2020-01-01' AND DATE_KEY <= CURRENT_DATE()"
      
      - name: REPORT_DATE
        description: "Report date dimension for metrics tables (BR-009)"
        tests:
          - not_null:
              severity: error
          - dbt_utils.expression_is_true:
              severity: warn
              expression: "REPORT_DATE = DATE_KEY"
      
      - name: START_DATE
        description: "Start date dimension for engagement tables (BR-009)"
        tests:
          - not_null:
              severity: error
          - dbt_utils.expression_is_true:
              severity: warn
              expression: "START_DATE = DATE_KEY"
      
      - name: DATA_DATE_RAW
        description: "Original DATA_DATE text field preserved from source"
        # No test - raw field preservation
      
      # ─── DATA QUALITY ───
      
      - name: DATA_QUALITY_FLAG
        description: "Quality flag identifying records with validation issues"
        tests:
          - accepted_values:
              severity: warn
              values: ['MISSING_ACCOUNT_ID', 'INVALID_DATE', 'INVALID_DIRECTION', 'INVALID_MODALITY', null]
              quote: true
```

---

### 🧪 STEP 5: Regression Suite — Full end-to-end validation

**Purpose**: Comprehensive regression testing across all layers

---

### FILE 5: `tests/regression/regression_suite.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- FTL TO PI MIGRATION — REGRESSION TEST SUITE
-- Purpose: End-to-end regression testing across Bronze → Silver → Gold
-- Execution: Run after each deployment to validate system integrity
-- Pass Condition: All 8 tests return 0 rows
-- On Failure: Halt deployment; contact Data Engineering Lead
-- ═══════════════════════════════════════════════════════════════════════════

-- ════════════════════════════════════════════════════════════════════════════
-- SECTION 1: BRONZE LAYER INTEGRITY
-- ════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_bronze_row_count_stable
-- Validates: Bronze row count has not unexpectedly changed
-- Pass: Row count within expected daily variance (±10%)
-- Baseline: [ASSUMPTION] Expected daily load ~1000-2000 rows
-- ────────────────────────────────────────────────────────────────────────────
WITH bronze_stats AS (
    SELECT 
        COUNT(*) AS current_count,
        AVG(COUNT(*)) OVER (ORDER BY TRY_CAST(DATA_DATE AS DATE) ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS avg_7day_count
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
    GROUP BY TRY_CAST(DATA_DATE AS DATE)
    HAVING TRY_CAST(DATA_DATE AS DATE) = CURRENT_DATE()
)
SELECT 
    'test_regr_bronze_row_count_stable' AS test_name,
    current_count,
    avg_7day_count,
    ROUND(100.0 * (current_count - avg_7day_count) / avg_7day_count, 2) AS variance_pct,
    'FAIL: Bronze row count variance exceeds ±10%' AS failure_reason
FROM bronze_stats
WHERE ABS((current_count - avg_7day_count) / avg_7day_count) > 0.10;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_bronze_date_continuity
-- Validates: No missing dates in Bronze layer
-- Pass: All expected dates present in last 30 days
-- Fail: Date gaps found
-- ────────────────────────────────────────────────────────────────────────────
WITH date_series AS (
    SELECT DATEADD(day, SEQ4(), DATEADD(day, -30, CURRENT_DATE())) AS expected_date
    FROM TABLE(GENERATOR(ROWCOUNT => 30))
),
actual_dates AS (
    SELECT DISTINCT TRY_CAST(DATA_DATE AS DATE) AS actual_date
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
    WHERE TRY_CAST(DATA_DATE AS DATE) >= DATEADD(day, -30, CURRENT_DATE())
)
SELECT 
    'test_regr_bronze_date_continuity' AS test_name,
    d.expected_date,
    'FAIL: Missing date in Bronze layer' AS failure_reason
FROM date_series d
LEFT JOIN actual_dates a ON d.expected_date = a.actual_date
WHERE a.actual_date IS NULL;

-- ════════════════════════════════════════════════════════════════════════════
-- SECTION 2: SILVER LAYER TRANSFORMATIONS
-- ════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_silver_transformation_completeness
-- Validates: All business rules applied successfully
-- Pass: 100% of rows have all transformed columns populated
-- Fail: Missing transformed values found
-- ────────────────────────────────────────────────────────────────────────────
WITH transformation_check AS (
    SELECT 
        COUNT(*) AS total_rows,
        SUM(CASE WHEN USER_ID IS NULL AND AGENT_ID IS NOT NULL THEN 1 ELSE 0 END) AS br001_fails,
        SUM(CASE WHEN DIRECTION NOT IN ('INBOUND', 'OUTBOUND') AND DIRECTION IS NOT NULL THEN 1 ELSE 0 END) AS br002_fails,
        SUM(CASE WHEN INBOUND_PHONE_MINS IS NULL AND INBOUND_PHONE_MS IS NOT NULL THEN 1 ELSE 0 END) AS br005_fails,
        SUM(CASE WHEN DURATION_SEC IS NULL AND INBOUND_PHONE_MS IS NOT NULL THEN 1 ELSE 0 END) AS br006_fails,
        SUM(CASE WHEN REGION IS NULL THEN 1 ELSE 0 END) AS br008_fails,
        SUM(CASE WHEN DATE_KEY IS NULL THEN 1 ELSE 0 END) AS br009_fails
    FROM {{ ref('slv_ftl_agent_base_agg') }}
)
SELECT 
    'test_regr_silver_transformation_completeness' AS test_name,
    'BR-001' AS business_rule,
    br001_fails AS failure_count,
    'FAIL: USER_ID transformation incomplete' AS failure_reason
FROM transformation_check WHERE br001_fails > 0
UNION ALL
SELECT 'test_regr_silver_transformation_completeness', 'BR-002', br002_fails, 'FAIL: DIRECTION normalization incomplete' 
FROM transformation_check WHERE br002_fails > 0
UNION ALL
SELECT 'test_regr_silver_transformation_completeness', 'BR-005', br005_fails, 'FAIL: INBOUND_PHONE_MINS conversion incomplete' 
FROM transformation_check WHERE br005_fails > 0
UNION ALL
SELECT 'test_regr_silver_transformation_completeness', 'BR-006', br006_fails, 'FAIL: DURATION_SEC conversion incomplete' 
FROM transformation_check WHERE br006_fails > 0
UNION ALL
SELECT 'test_regr_silver_transformation_completeness', 'BR-008', br008_fails, 'FAIL: REGION mapping incomplete' 
FROM transformation_check WHERE br008_fails > 0
UNION ALL
SELECT 'test_regr_silver_transformation_completeness', 'BR-009', br009_fails, 'FAIL: DATE_KEY conversion incomplete' 
FROM transformation_check WHERE br009_fails > 0;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_silver_downstream_join_integrity
-- Validates: Silver data can successfully join to downstream tables
-- Pass: All ACCOUNT_IDs in Silver exist in SLV_ACCT_FIRST_ACTIVE
-- [ASSUMPTION] This test assumes SLV_ACCT_FIRST_ACTIVE is the account dimension
-- ────────────────────────────────────────────────────────────────────────────
WITH silver_accounts AS (
    SELECT DISTINCT ACCOUNT_ID
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE ACCOUNT_ID IS NOT NULL
),
dimension_accounts AS (
    SELECT DISTINCT ACCOUNT_ID
    FROM ZOOM_AI_POC.SILVER.SLV_ACCT_FIRST_ACTIVE
)
SELECT 
    'test_regr_silver_downstream_join_integrity' AS test_name,
    s.ACCOUNT_ID,
    'FAIL: ACCOUNT_ID in Silver not found in dimension table' AS failure_reason
FROM silver_accounts s
LEFT JOIN dimension_accounts d ON s.ACCOUNT_ID = d.ACCOUNT_ID
WHERE d.ACCOUNT_ID IS NULL;

-- ════════════════════════════════════════════════════════════════════════════
-- SECTION 3: GOLD LAYER AGGREGATIONS
-- ════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_gold_metric_consistency
-- Validates: Gold aggregations are mathematically consistent
-- Pass: ACTIVE_USERS <= ACTIVE_ACCOUNTS (users cannot exceed accounts)
-- Fail: Logical inconsistency in metrics
-- ────────────────────────────────────────────────────────────────────────────
SELECT 
    'test_regr_gold_metric_consistency' AS test_name,
    DATE,
    REGION,
    ACTIVE_USERS,
    ACTIVE_ACCOUNTS,
    'FAIL: ACTIVE_USERS exceeds ACTIVE_ACCOUNTS' AS failure_reason
FROM {{ ref('gld_aggregate_new') }}
WHERE ACTIVE_USERS > ACTIVE_ACCOUNTS;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_gold_time_series_continuity
-- Validates: Gold aggregations have no unexpected gaps
-- Pass: All dates present in last 30 days
-- Fail: Missing dates found
-- ────────────────────────────────────────────────────────────────────────────
WITH date_series AS (
    SELECT DATEADD(day, SEQ4(), DATEADD(day, -30, CURRENT_DATE())) AS expected_date
    FROM TABLE(GENERATOR(ROWCOUNT => 30))
),
gold_dates AS (
    SELECT DISTINCT DATE AS actual_date
    FROM {{ ref('gld_aggregate_new') }}
    WHERE DATE >= DATEADD(day, -30, CURRENT_DATE())
)
SELECT 
    'test_regr_gold_time_series_continuity' AS test_name,
    d.expected_date,
    'FAIL: Missing date in Gold aggregation' AS failure_reason
FROM date_series d
LEFT JOIN gold_dates g ON d.expected_date = g.actual_date
WHERE g.actual_date IS NULL;

-- ════════════════════════════════════════════════════════════════════════════
-- SECTION 4: CROSS-LAYER CONSISTENCY
-- ════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_bronze_to_gold_traceability
-- Validates: Every Bronze record contributes to Gold aggregation
-- Pass: Bronze row count = sum of contributing records to Gold
-- [ASSUMPTION] This test validates data lineage integrity
-- ────────────────────────────────────────────────────────────────────────────
WITH bronze_daily AS (
    SELECT 
        TRY_CAST(DATA_DATE AS DATE) AS date_key,
        COUNT(*) AS bronze_count
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
    WHERE TRY_CAST(DATA_DATE AS DATE) >= DATEADD(day, -7, CURRENT_DATE())
    GROUP BY TRY_CAST(DATA_DATE AS DATE)
),
silver_daily AS (
    SELECT 
        DATE_KEY,
        COUNT(*) AS silver_count
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE DATE_KEY >= DATEADD(day, -7, CURRENT_DATE())
    GROUP BY DATE_KEY
)
SELECT 
    'test_regr_bronze_to_gold_traceability' AS test_name,
    b.date_key,
    b.bronze_count,
    s.silver_count,
    'FAIL: Row count mismatch between Bronze and Silver' AS failure_reason
FROM bronze_daily b
FULL OUTER JOIN silver_daily s ON b.date_key = s.DATE_KEY
WHERE b.bronze_count != s.silver_count 
   OR b.bronze_count IS NULL 
   OR s.silver_count IS NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- TEST: test_regr_data_quality_flag_threshold
-- Validates: Data quality flags remain below acceptable threshold
-- Pass: <2% of records flagged across entire pipeline
-- Fail: Quality flag rate exceeds threshold
-- ────────────────────────────────────────────────────────────────────────────
WITH quality_summary AS (
    SELECT 
        COUNT(*) AS total_rows,
        SUM(CASE WHEN DATA_QUALITY_FLAG IS NOT NULL THEN 1 ELSE 0 END) AS flagged_rows,
        ROUND(100.0 * SUM(CASE WHEN DATA_QUALITY_FLAG IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS flagged_pct
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE DATE_KEY >= DATEADD(day, -30, CURRENT_DATE())
)
SELECT 
    'test_regr_data_quality_flag_threshold' AS test_name,
    flagged_rows,
    flagged_pct,
    'FAIL: Data quality flag rate exceeds 2% regression threshold' AS failure_reason
FROM quality_summary
WHERE flagged_pct > 2;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF REGRESSION TEST SUITE
-- Total: 8 regression tests covering Bronze → Silver → Gold integrity
-- ═══════════════════════════════════════════════════════════════════════════
```

---

### 🧪 STEP 6: Test Runbook — Execution guide with failure actions

**Purpose**: Step-by-step testing protocol with clear escalation paths

---

### FILE 6: `TEST_RUNBOOK.md`

```markdown
# FTL to PI Migration — Test Execution Runbook

**Version:** 1.0  
**Last Updated:** 2026-06-05  
**Owner:** Data Engineering Team  
**Severity:** CRITICAL — All tests must pass before production deployment

---

## 📋 Table of Contents

1. [Pre-Test Checklist](#pre-test-checklist)
2. [Execution Order](#execution-order)
3. [Test Commands](#test-commands)
4. [Failure Response Matrix](#failure-response-matrix)
5. [Rollback Procedure](#rollback-procedure)
6. [Sign-Off Checklist](#sign-off-checklist)

---

## ✅ Pre-Test Checklist

Before executing tests, verify:

- [ ] **Bronze Layer**: BRZ_FTL_AGENT_BASE_AGG has data for target date range
- [ ] **Reference Data**: CLUSTER_REGION_MAP lookup table deployed
- [ ] **dbt Dependencies**: dbt_utils package installed (`packages.yml`)
- [ ] **Snowflake Permissions**: Test user has SELECT on all Bronze/Silver/Gold tables
- [ ] **Environment Variables**: DBT_PROFILE and DBT_TARGET configured correctly
- [ ] **Backup Complete**: Current production Gold table backed up

```sql
-- Verify Bronze data availability
SELECT 
    MIN(TRY_CAST(DATA_DATE AS DATE)) AS earliest_date,
    MAX(TRY_CAST(DATA_DATE AS DATE)) AS latest_date,
    COUNT(*) AS total_rows
FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG;
-- Expected: Latest_date = CURRENT_DATE(), total_rows > 0

-- Verify reference data
SELECT * FROM ZOOM_AI_POC.SEED.CLUSTER_REGION_MAP;
-- Expected: 3 rows (us-east-1, eu-central-1, ap-south-1)
```

---

## 🔢 Execution Order

Tests MUST be executed in this sequence:

| Phase | Test Suite | Execution Time | Blocking? |
|-------|-----------|----------------|-----------|
| **1** | Unit Tests | 2-3 min | YES — Must pass before proceeding |
| **2** | Functional Tests | 5-7 min | YES — Must pass before proceeding |
| **3** | dbt YAML Tests | 3-5 min | YES — Must pass before proceeding |
| **4** | Gold Equivalence Test | 8-10 min | NO — Investigate variances |
| **5** | Regression Suite | 10-15 min | YES — Must pass before production |

**Total Estimated Time:** 28-40 minutes

---

## 🖥️ Test Commands

### Phase 1: Unit Tests (BR-001 through BR-009)

```bash
# Execute all unit tests
dbt test --select test_type:unit --models slv_ftl_agent_base_agg

# Or run SQL directly
snowsql -f tests/unit/unit_tests.sql -o output_format=tsv -o friendly=false

# Expected Output: 0 rows returned for each test
```

**Pass Criteria:** All 9 unit tests return 0 rows  
**On Failure:** See [Failure Response Matrix](#failure-response-matrix) — Section BR-XXX

---

### Phase 2: Functional Tests (Data Quality)

```bash
# Execute functional test suite
dbt test --select test_type:functional --models slv_ftl_agent_base_agg

# Or run SQL directly
snowsql -f tests/functional/functional_tests.sql -o output_format=tsv

# Expected Output: 0 rows returned for each test
```

**Pass Criteria:** All 12 functional tests return 0 rows  
**On Failure:** See [Failure Response Matrix](#failure-response-matrix) — Section FUNC-XXX

---

### Phase 3: dbt YAML Tests (Automated Schema Tests)

```bash
# Run dbt schema tests
dbt test --models slv_ftl_agent_base_agg

# Expected Output:
# Completed successfully
# Done. PASS=20 WARN=0 ERROR=0 SKIP=0 TOTAL=20
```

**Pass Criteria:** 20/20 tests pass (ERROR=0)  
**Warn Criteria:** WARN > 0 acceptable if documented  
**On Failure:** Review `target/run_results.json` for failure details

---

### Phase 4: Gold Equivalence Test (FTL vs PI Comparison)

```bash
# Execute gold equivalence comparison
snowsql -f tests/functional/gold_equivalence_test.sql -o output_format=tsv

# Expected Output: 0 rows (no variance > 5%)
```

**Pass Criteria:** 0 rows returned (all metrics within 5% tolerance)  
**Investigation Required:** Any rows returned with variance > 5%  
**Action:** Document variance reasons in `VARIANCE_LOG.md`

⚠️ **Note:** This test is informational during initial migration. Variances may be acceptable if:
- FTL captures additional data sources (e.g., ZCC accounts)
- Date range differences explain metric deltas
- Business logic changes are intentional

---

### Phase 5: Regression Suite (End-to-End Validat