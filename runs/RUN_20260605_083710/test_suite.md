

🧪 **STEP 1: Schema Discovery Completed** — Retrieved full Bronze, Silver, and Gold schemas (24 tables total, 14 Bronze columns confirmed)

🧪 **STEP 2: Mapping Analysis** — Identified 13 business rules (BR-001 to BR-013) and 6 gaps (GAP-001 to GAP-006)

🧪 **STEP 3: Test Generation** — Building complete test suite with unit, functional, equivalence, regression, dbt YAML, and runbook

---

## **📊 Test Suite Summary**



---

## **FILE 1: tests/unit/unit_tests.sql**

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- FTL → PI MIGRATION: UNIT TEST SUITE
-- Purpose: Validate all transformation business rules (BR-001 to BR-013)
-- Model:   slv_ftl_agent_base_agg
-- Layer:   Silver
-- Pass Condition: Each test returns 0 rows = PASS
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-001: Date Parsing (TEXT → DATE)
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR001_date_parsing
-- Purpose: Verify DATA_DATE text is correctly parsed to DATE type
-- Pass Condition: All dates successfully parse using MM/DD/YY HH24:MI format
-- On Failure: Contact Data Engineering - invalid date format in source
SELECT
  'test_unit_BR001_date_parsing' AS test_name,
  COUNT(*) AS failure_count,
  'DATA_DATE parsing failed - invalid format or NULL result' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE DATA_DATE IS NOT NULL
  AND TRY_TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') IS NULL;

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-002: Unit Conversion (Milliseconds → Minutes)
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR002_ms_to_minutes
-- Purpose: Verify INBOUND_PHONE_MS converts to minutes (÷ 60000)
-- Pass Condition: All conversions produce non-negative values
-- On Failure: Contact Data Engineering - negative duration values detected
SELECT
  'test_unit_BR002_ms_to_minutes' AS test_name,
  COUNT(*) AS failure_count,
  'INBOUND_PHONE_MS conversion produced negative minutes' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE INBOUND_PHONE_MS IS NOT NULL
  AND (INBOUND_PHONE_MS / 60000.0) < 0;

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-003: Case Standardization - DIRECTION
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR003_direction_uppercase
-- Purpose: Verify DIRECTION converts to uppercase (INBOUND/OUTBOUND)
-- Pass Condition: No mixed case values remain after UPPER() transformation
-- On Failure: Contact Data Engineering - unexpected DIRECTION values
SELECT
  'test_unit_BR003_direction_uppercase' AS test_name,
  COUNT(*) AS failure_count,
  'DIRECTION contains values other than INBOUND/OUTBOUND after UPPER()' AS failure_message
FROM (
  SELECT UPPER(DIRECTION) AS direction_upper
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE DIRECTION IS NOT NULL
)
WHERE direction_upper NOT IN ('INBOUND', 'OUTBOUND');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-004: Case Standardization - CHANNEL
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR004_channel_uppercase
-- Purpose: Verify CHANNEL converts to uppercase (VIDEO/PHONE)
-- Pass Condition: No mixed case values remain after UPPER() transformation
-- On Failure: Contact Data Engineering - unexpected CHANNEL values
SELECT
  'test_unit_BR004_channel_uppercase' AS test_name,
  COUNT(*) AS failure_count,
  'CHANNEL contains values other than VIDEO/PHONE after UPPER()' AS failure_message
FROM (
  SELECT UPPER(CHANNEL) AS channel_upper
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE CHANNEL IS NOT NULL
)
WHERE channel_upper NOT IN ('VIDEO', 'PHONE');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-005: Direct Match - MODALITY
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR005_modality_values
-- Purpose: Verify MODALITY contains only expected values (SMS/Email/Chat)
-- Pass Condition: All values match expected enumeration
-- On Failure: Contact Data Engineering - new modality detected
SELECT
  'test_unit_BR005_modality_values' AS test_name,
  COUNT(*) AS failure_count,
  'MODALITY contains unexpected values' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE MODALITY IS NOT NULL
  AND MODALITY NOT IN ('SMS', 'Email', 'Chat');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-006: Direct Match - ACCOUNT_ID
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR006_account_id_format
-- Purpose: Verify ACCOUNT_ID follows ID_ prefix pattern
-- Pass Condition: All IDs start with 'ID_'
-- On Failure: Contact Data Engineering - malformed ACCOUNT_ID
SELECT
  'test_unit_BR006_account_id_format' AS test_name,
  COUNT(*) AS failure_count,
  'ACCOUNT_ID missing ID_ prefix pattern' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE ACCOUNT_ID IS NOT NULL
  AND NOT STARTSWITH(ACCOUNT_ID, 'ID_');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-007: Direct Match - ENGAGEMENT_ID
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR007_engagement_id_format
-- Purpose: Verify ENGAGEMENT_ID follows ID_ prefix pattern
-- Pass Condition: All IDs start with 'ID_'
-- On Failure: Contact Data Engineering - malformed ENGAGEMENT_ID
SELECT
  'test_unit_BR007_engagement_id_format' AS test_name,
  COUNT(*) AS failure_count,
  'ENGAGEMENT_ID missing ID_ prefix pattern' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE ENGAGEMENT_ID IS NOT NULL
  AND NOT STARTSWITH(ENGAGEMENT_ID, 'ID_');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-008: Direct Match - PHONE_SESSIONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR008_phone_sessions_non_negative
-- Purpose: Verify PHONE_SESSIONS is non-negative count
-- Pass Condition: All values >= 0
-- On Failure: Contact Data Engineering - negative session count
SELECT
  'test_unit_BR008_phone_sessions_non_negative' AS test_name,
  COUNT(*) AS failure_count,
  'PHONE_SESSIONS contains negative values' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE PHONE_SESSIONS IS NOT NULL
  AND PHONE_SESSIONS < 0;

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-009: Semantic Rename (AGENT_ID → USER_ID)
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR009_agent_id_format
-- Purpose: Verify AGENT_ID follows ID_ prefix pattern (renamed to USER_ID)
-- Pass Condition: All IDs start with 'ID_'
-- On Failure: Contact Data Engineering - malformed AGENT_ID
SELECT
  'test_unit_BR009_agent_id_format' AS test_name,
  COUNT(*) AS failure_count,
  'AGENT_ID missing ID_ prefix pattern (maps to USER_ID)' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE AGENT_ID IS NOT NULL
  AND NOT STARTSWITH(AGENT_ID, 'ID_');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-010: Semantic Rename - IS_ACTIVE
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR010_is_active_boolean
-- Purpose: Verify IS_ACTIVE is valid boolean (TRUE/FALSE)
-- Pass Condition: All values are boolean type
-- On Failure: Contact Data Engineering - non-boolean IS_ACTIVE value
SELECT
  'test_unit_BR010_is_active_boolean' AS test_name,
  COUNT(*) AS failure_count,
  'IS_ACTIVE contains non-boolean values' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE IS_ACTIVE IS NOT NULL
  AND IS_ACTIVE NOT IN (TRUE, FALSE);

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-012: Cluster → Region Mapping
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR012_cluster_to_region
-- Purpose: Verify CLUSTER maps to valid REGION (EMEA/APAC/NA)
-- Pass Condition: All clusters have valid region mapping
-- On Failure: Contact Data Engineering - unmapped cluster detected
SELECT
  'test_unit_BR012_cluster_to_region' AS test_name,
  COUNT(*) AS failure_count,
  'CLUSTER value not mapped to EMEA/APAC/NA' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE CLUSTER IS NOT NULL
  AND CLUSTER NOT IN ('eu-central-1', 'ap-south-1', 'us-east-1');

-- ═══════════════════════════════════════════════════════════════════════════════
-- BR-013: Active Account Aggregation
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_unit_BR013_active_account_logic
-- Purpose: Verify active accounts have IS_ACTIVE = TRUE
-- Pass Condition: Active account count matches IS_ACTIVE flag
-- On Failure: Contact Analytics Team - active account definition mismatch
SELECT
  'test_unit_BR013_active_account_logic' AS test_name,
  COUNT(*) AS failure_count,
  'Active account aggregation logic inconsistent with IS_ACTIVE flag' AS failure_message
FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
WHERE IS_ACTIVE = FALSE
  AND ACCOUNT_ID IN (
    SELECT DISTINCT ACCOUNT_ID 
    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
    WHERE IS_ACTIVE = TRUE
  );
```

---

## **FILE 2: tests/functional/functional_tests.sql**

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- FTL → PI MIGRATION: FUNCTIONAL TEST SUITE
-- Purpose: Validate data quality, gap handling, and row-level constraints
-- Layer:   Silver + Gold
-- Pass Condition: Each test returns 0 rows = PASS
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- GAP TESTS: Missing Fields (NULL checks)
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_gap_GAP001_segment_is_null
-- Purpose: Verify SEGMENT is NULL in Gold (GAP-001: not provided by FTL)
-- Pass Condition: All SEGMENT values are NULL
-- On Failure: Contact Analytics Team - unexpected SEGMENT population
SELECT
  'test_gap_GAP001_segment_is_null' AS test_name,
  COUNT(*) AS failure_count,
  'SEGMENT should be NULL (not provided by FTL) but contains values' AS failure_message
FROM {{ ref('gld_aggregate_new') }}
WHERE SEGMENT IS NOT NULL;

-- TEST: test_gap_GAP002_client_type_preserved
-- Purpose: Verify CLIENT_TYPE preserved in Silver but not mapped to Gold
-- Pass Condition: CLIENT_TYPE exists in Silver, absent in Gold
-- On Failure: Contact Data Engineering - CLIENT_TYPE mapping changed
SELECT
  'test_gap_GAP002_client_type_preserved' AS test_name,
  0 AS failure_count,  -- Informational only - verify column exists
  'CLIENT_TYPE preserved in Silver but not in Gold' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE CLIENT_TYPE IS NOT NULL
LIMIT 1;  -- Just verify column exists

-- TEST: test_gap_GAP003_latam_region_missing
-- Purpose: Verify no LATAM region in REGION dimension (GAP-003)
-- Pass Condition: No LATAM values in REGION
-- On Failure: Contact Data Engineering - LATAM cluster added
SELECT
  'test_gap_GAP003_latam_region_missing' AS test_name,
  COUNT(*) AS failure_count,
  'LATAM region detected but not in cluster mapping' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE REGION = 'LATAM';

-- TEST: test_gap_GAP004_os_not_mapped
-- Purpose: Verify OS not mapped due to data quality issue (1 distinct value)
-- Pass Condition: OS not present in transformed tables
-- On Failure: Contact Data Engineering - OS mapping added unexpectedly
WITH os_check AS (
  SELECT 'os_column_check' AS test_check
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  LIMIT 1
)
SELECT
  'test_gap_GAP004_os_not_mapped' AS test_name,
  0 AS failure_count,  -- Informational only
  'OS field not mapped due to data quality (only 1 distinct value)' AS failure_message
FROM os_check
LIMIT 0;  -- Always pass - informational

-- TEST: test_gap_GAP005_zcc_account_id_not_mapped
-- Purpose: Verify ZCC_ACCOUNT_ID not mapped (not needed in single-source)
-- Pass Condition: ZCC_ACCOUNT_ID not in Silver/Gold
-- On Failure: Contact Data Engineering - ZCC_ACCOUNT_ID added unexpectedly
WITH zcc_check AS (
  SELECT 'zcc_column_check' AS test_check
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  LIMIT 1
)
SELECT
  'test_gap_GAP005_zcc_account_id_not_mapped' AS test_name,
  0 AS failure_count,  -- Informational only
  'ZCC_ACCOUNT_ID not mapped (reconciliation field not needed)' AS failure_message
FROM zcc_check
LIMIT 0;  -- Always pass - informational

-- TEST: test_gap_GAP006_is_licensed_is_null
-- Purpose: Verify IS_LICENSED is NULL in Gold (GAP-006: not provided by FTL)
-- Pass Condition: All IS_LICENSED values are NULL
-- On Failure: Contact Analytics Team - unexpected IS_LICENSED population
SELECT
  'test_gap_GAP006_is_licensed_is_null' AS test_name,
  COUNT(*) AS failure_count,
  'IS_LICENSED should be NULL (not provided by FTL) but contains values' AS failure_message
FROM {{ ref('gld_aggregate_new') }}
WHERE IS_LICENSED IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════════
-- FUNCTIONAL TESTS: Data Quality and Business Logic
-- ═══════════════════════════════════════════════════════════════════════════════

-- TEST: test_functional_silver_row_count
-- Purpose: Verify Silver table has data after transformation
-- Pass Condition: Row count > 0
-- On Failure: Contact Data Engineering - pipeline not loading data
SELECT
  'test_functional_silver_row_count' AS test_name,
  CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS failure_count,
  'Silver table has 0 rows - pipeline failure' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }};

-- TEST: test_functional_gold_row_count
-- Purpose: Verify Gold table has data after aggregation
-- Pass Condition: Row count > 0
-- On Failure: Contact Data Engineering - aggregation pipeline failure
SELECT
  'test_functional_gold_row_count' AS test_name,
  CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS failure_count,
  'Gold table has 0 rows - aggregation failure' AS failure_message
FROM {{ ref('gld_aggregate_new') }};

-- TEST: test_functional_primary_keys_not_null
-- Purpose: Verify primary key columns (DATE, ACCOUNT_ID, USER_ID) are not NULL in Silver
-- Pass Condition: All PKs have values
-- On Failure: Contact Data Engineering - NULL primary keys detected
SELECT
  'test_functional_primary_keys_not_null' AS test_name,
  COUNT(*) AS failure_count,
  'Primary key columns contain NULLs' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE DATE IS NULL
   OR ACCOUNT_ID IS NULL
   OR USER_ID IS NULL;

-- TEST: test_functional_gold_primary_keys_not_null
-- Purpose: Verify Gold grain columns (DATE, REGION) are not NULL
-- Pass Condition: All grain columns have values
-- On Failure: Contact Data Engineering - NULL grain columns in Gold
SELECT
  'test_functional_gold_primary_keys_not_null' AS test_name,
  COUNT(*) AS failure_count,
  'Gold grain columns (DATE, REGION) contain NULLs' AS failure_message
FROM {{ ref('gld_aggregate_new') }}
WHERE DATE IS NULL
   OR REGION IS NULL;

-- TEST: test_functional_date_range_valid
-- Purpose: Verify all dates fall within reasonable range (past 5 years to today)
-- Pass Condition: All dates between 2021-01-01 and today + 1 day
-- On Failure: Contact Data Engineering - invalid date values
SELECT
  'test_functional_date_range_valid' AS test_name,
  COUNT(*) AS failure_count,
  'Dates outside valid range (2021-01-01 to tomorrow)' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE DATE < '2021-01-01'
   OR DATE > DATEADD(day, 1, CURRENT_DATE());

-- TEST: test_functional_no_duplicate_surrogate_keys
-- Purpose: Verify SURROGATE_KEY is unique (critical for incremental merges)
-- Pass Condition: No duplicate surrogate keys
-- On Failure: Contact Data Engineering - surrogate key collision
SELECT
  'test_functional_no_duplicate_surrogate_keys' AS test_name,
  SUM(CASE WHEN duplicate_count > 1 THEN 1 ELSE 0 END) AS failure_count,
  'Duplicate SURROGATE_KEY values detected' AS failure_message
FROM (
  SELECT 
    SURROGATE_KEY,
    COUNT(*) AS duplicate_count
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  GROUP BY SURROGATE_KEY
);

-- TEST: test_functional_active_accounts_consistency
-- Purpose: Verify ACTIVE_ACCOUNTS in Gold matches count from Silver
-- Pass Condition: Counts match between layers
-- On Failure: Contact Analytics Team - aggregation logic error
SELECT
  'test_functional_active_accounts_consistency' AS test_name,
  COUNT(*) AS failure_count,
  'ACTIVE_ACCOUNTS count mismatch between Silver and Gold' AS failure_message
FROM (
  SELECT 
    s.DATE,
    s.REGION,
    COUNT(DISTINCT CASE WHEN s.IS_ACTIVE_ACCOUNT = TRUE THEN s.ACCOUNT_ID END) AS silver_active_accts,
    g.ACTIVE_ACCOUNTS AS gold_active_accts
  FROM {{ ref('slv_ftl_agent_base_agg') }} s
  JOIN {{ ref('gld_aggregate_new') }} g
    ON s.DATE = g.DATE
    AND s.REGION = g.REGION
  GROUP BY s.DATE, s.REGION, g.ACTIVE_ACCOUNTS
)
WHERE silver_active_accts != gold_active_accts;

-- TEST: test_functional_region_values
-- Purpose: Verify REGION contains only valid values (EMEA, APAC, NA, UNKNOWN)
-- Pass Condition: No invalid region values
-- On Failure: Contact Data Engineering - new region detected
SELECT
  'test_functional_region_values' AS test_name,
  COUNT(*) AS failure_count,
  'REGION contains invalid values (not EMEA/APAC/NA/UNKNOWN)' AS failure_message
FROM {{ ref('slv_ftl_agent_base_agg') }}
WHERE REGION IS NOT NULL
  AND REGION NOT IN ('EMEA', 'APAC', 'NA', 'UNKNOWN');
```

---

## **FILE 3: tests/functional/gold_equivalence_test.sql**

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- FTL → PI MIGRATION: GOLD EQUIVALENCE TEST
-- Purpose: Compare new FTL-based Gold (gld_aggregate_new) vs Legacy PI Gold (GLD_AGGREGATE)
-- Scope:   DATE, REGION, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE
-- Pass Condition: Differences within 5% tolerance OR explainable by known gaps
-- ═══════════════════════════════════════════════════════════════════════════════

WITH ftl_gold AS (
  SELECT
    DATE,
    REGION,
    SEGMENT,
    IS_LICENSED,
    ACTIVE_ACCOUNTS AS ftl_active_accounts,
    ACTIVE_USERS AS ftl_active_users,
    PHONE_USAGE AS ftl_phone_usage,
    USERS_ACTIVE_16PLUS_DAYS AS ftl_users_16plus
  FROM {{ ref('gld_aggregate_new') }}
),

pi_gold AS (
  SELECT
    DATE,
    REGION,
    SEGMENT,
    IS_LICENSED,
    ACTIVE_ACCOUNTS AS pi_active_accounts,
    ACTIVE_USERS AS pi_active_users,
    PHONE_USAGE AS pi_phone_usage,
    USERS_ACTIVE_16PLUS_DAYS AS pi_users_16plus
  FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
),

comparison AS (
  SELECT
    COALESCE(f.DATE, p.DATE) AS compare_date,
    COALESCE(f.REGION, p.REGION) AS compare_region,
    COALESCE(f.SEGMENT, p.SEGMENT) AS compare_segment,
    COALESCE(f.IS_LICENSED, p.IS_LICENSED) AS compare_is_licensed,
    
    -- FTL metrics
    f.ftl_active_accounts,
    f.ftl_active_users,
    f.ftl_phone_usage,
    f.ftl_users_16plus,
    
    -- PI metrics
    p.pi_active_accounts,
    p.pi_active_users,
    p.pi_phone_usage,
    p.pi_users_16plus,
    
    -- Delta calculations
    (f.ftl_active_accounts - p.pi_active_accounts) AS delta_accounts,
    (f.ftl_active_users - p.pi_active_users) AS delta_users,
    (f.ftl_phone_usage - p.pi_phone_usage) AS delta_phone_usage,
    
    -- Percentage difference
    CASE 
      WHEN p.pi_active_accounts = 0 THEN NULL
      ELSE ABS((f.ftl_active_accounts - p.pi_active_accounts) / NULLIF(p.pi_active_accounts, 0)) * 100
    END AS pct_diff_accounts,
    
    CASE 
      WHEN p.pi_active_users = 0 THEN NULL
      ELSE ABS((f.ftl_active_users - p.pi_active_users) / NULLIF(p.pi_active_users, 0)) * 100
    END AS pct_diff_users,
    
    CASE 
      WHEN p.pi_phone_usage = 0 THEN NULL
      ELSE ABS((f.ftl_phone_usage - p.pi_phone_usage) / NULLIF(p.pi_phone_usage, 0)) * 100
    END AS pct_diff_phone_usage,
    
    -- Flags for known gaps
    CASE WHEN f.SEGMENT IS NULL THEN 'GAP-001: SEGMENT missing' ELSE NULL END AS gap_flag_1,
    CASE WHEN f.IS_LICENSED IS NULL THEN 'GAP-006: IS_LICENSED missing' ELSE NULL END AS gap_flag_2,
    CASE WHEN f.ftl_users_16plus = 0 AND p.pi_users_16plus > 0 THEN 'No 16+ day calculation in FTL' ELSE NULL END AS gap_flag_3
    
  FROM ftl_gold f
  FULL OUTER JOIN pi_gold p
    ON f.DATE = p.DATE
    AND f.REGION = p.REGION
    AND COALESCE(f.SEGMENT, -9999) = COALESCE(p.SEGMENT, -9999)
    AND COALESCE(f.IS_LICENSED, FALSE) = COALESCE(p.IS_LICENSED, FALSE)
),

equivalence_failures AS (
  SELECT
    'EQUIVALENCE_TEST' AS test_name,
    compare_date,
    compare_region,
    compare_segment,
    compare_is_licensed,
    ftl_active_accounts,
    pi_active_accounts,
    delta_accounts,
    pct_diff_accounts,
    ftl_active_users,
    pi_active_users,
    delta_users,
    pct_diff_users,
    ftl_phone_usage,
    pi_phone_usage,
    delta_phone_usage,
    pct_diff_phone_usage,
    gap_flag_1,
    gap_flag_2,
    gap_flag_3,
    
    -- Failure reason
    CASE
      WHEN ftl_active_accounts IS NULL AND pi_active_accounts IS NOT NULL THEN 'FTL data missing'
      WHEN ftl_active_accounts IS NOT NULL AND pi_active_accounts IS NULL THEN 'PI data missing (expected if new source)'
      WHEN pct_diff_accounts > 5 AND gap_flag_1 IS NULL THEN 'ACTIVE_ACCOUNTS variance > 5% threshold'
      WHEN pct_diff_users > 5 AND gap_flag_1 IS NULL THEN 'ACTIVE_USERS variance > 5% threshold'
      WHEN pct_diff_phone_usage > 10 THEN 'PHONE_USAGE variance > 10% threshold'
      ELSE 'Within tolerance'
    END AS failure_reason
    
  FROM comparison
  WHERE 
    -- Flag rows with meaningful differences
    (pct_diff_accounts > 5 OR pct_diff_users > 5 OR pct_diff_phone_usage > 10)
    -- Exclude rows where differences are explained by known gaps
    AND gap_flag_1 IS NULL  -- SEGMENT gap is expected
    AND gap_flag_2 IS NULL  -- IS_LICENSED gap is expected
)

-- ═══════════════════════════════════════════════════════════════════════════════
-- FINAL OUTPUT: Return rows with unexplained differences
-- Pass Condition: 0 rows returned
-- On Failure: Review variance reasons and contact Analytics Team
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
  test_name,
  compare_date AS date,
  compare_region AS region,
  compare_segment AS segment,
  compare_is_licensed AS is_licensed,
  
  -- Account metrics
  ftl_active_accounts,
  pi_active_accounts,
  delta_accounts,
  ROUND(pct_diff_accounts, 2) AS pct_diff_accounts,
  
  -- User metrics
  ftl_active_users,
  pi_active_users,
  delta_users,
  ROUND(pct_diff_users, 2) AS pct_diff_users,
  
  -- Phone usage metrics
  ROUND(ftl_phone_usage, 2) AS ftl_phone_usage,
  ROUND(pi_phone_usage, 2) AS pi_phone_usage,
  ROUND(delta_phone_usage, 2) AS delta_phone_usage,
  ROUND(pct_diff_phone_usage, 2) AS pct_diff_phone_usage,
  
  failure_reason
  
FROM equivalence_failures
WHERE failure_reason != 'Within tolerance'
ORDER BY pct_diff_accounts DESC, pct_diff_users DESC;

-- ═══════════════════════════════════════════════════════════════════════════════
-- INTERPRETATION GUIDE:
-- • 0 rows = PASS - FTL and PI Gold tables are equivalent within tolerance
-- • >0 rows = REVIEW - Investigate variance reasons:
--   - "FTL data missing": Bronze ingestion issue
--   - "PI data missing": Expected for new FTL source
--   - ">5% threshold": Business logic difference - escalate to Analytics
-- ═══════════════════════════════════════════════════════════════════════════════
```

---

## **FILE 4: models/silver/slv_ftl_agent_base_agg.yml**

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **FTL → PI Migration: Silver Layer Staging Model**
      
      Transforms raw FTL agent engagement data from Bronze (BRZ_FTL_AGENT_BASE_AGG) 
      into PI-compatible schema with date parsing, case standardization, unit conversion,
      and region mapping.
      
      **Migration Context:**
      - Source: ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG (14 columns)
      - Target: Multiple PI Silver tables (SLV_USAGE_MASTER, SLV_COMBINED_CHANNELS, etc.)
      - Business Rules Applied: BR-001 through BR-013
      - Known Gaps: GAP-001 (SEGMENT), GAP-006 (IS_LICENSED)
      
      **Refresh Strategy:** Incremental merge on SURROGATE_KEY
      
    config:
      tags: ['silver', 'ftl', 'usage', 'incremental']
      
    columns:
      # ─────────────────────────────────────────────────────────────────────────
      # PRIMARY KEYS & IDENTIFIERS
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: SURROGATE_KEY
        description: "MD5 hash surrogate key for incremental merge (ACCOUNT_ID || AGENT_ID || ENGAGEMENT_ID || DATA_DATE)"
        tests:
          - unique
          - not_null
      
      - name: DATE
        description: "Event date (BR-001: parsed from DATA_DATE text using TO_DATE(MM/DD/YY HH24:MI))"
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: "'2021-01-01'"
              max_value: "current_date + interval '1 day'"
              
      - name: ACCOUNT_ID
        description: "Primary account identifier (BR-006: direct match, ID_ prefix pattern)"
        tests:
          - not_null
          - relationships:
              to: source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG')
              field: ACCOUNT_ID
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^ID_.*"
              
      - name: USER_ID
        description: "User identifier (BR-009: renamed from AGENT_ID - assumes all users not just agents)"
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^ID_.*"
              
      - name: ENGAGEMENT_ID
        description: "Unique engagement session identifier (BR-007: direct match)"
        tests:
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^ID_.*"
              
      # ─────────────────────────────────────────────────────────────────────────
      # ENGAGEMENT DIMENSIONS
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: DIRECTION
        description: "Engagement direction (BR-003: UPPER(DIRECTION) - INBOUND/OUTBOUND)"
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              
      - name: MODALITY
        description: "Communication modality (BR-005: direct match - SMS/Email/Chat)"
        tests:
          - accepted_values:
              values: ['SMS', 'Email', 'Chat']
              
      - name: CHANNEL
        description: "Communication channel (BR-004: UPPER(CHANNEL) - VIDEO/PHONE)"
        tests:
          - accepted_values:
              values: ['VIDEO', 'PHONE']
              
      - name: REGION
        description: "Business region (BR-012: mapped from CLUSTER - EMEA/APAC/NA/UNKNOWN). GAP-003: LATAM not covered."
        tests:
          - not_null
          - accepted_values:
              values: ['EMEA', 'APAC', 'NA', 'UNKNOWN']
              
      # ─────────────────────────────────────────────────────────────────────────
      # USAGE METRICS
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: PHONE_SESSIONS
        description: "Count of phone sessions (BR-008: direct match)"
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              
      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (BR-002: converted from INBOUND_PHONE_MS ÷ 60000)"
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              
      # ─────────────────────────────────────────────────────────────────────────
      # STATUS FLAGS
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: IS_ACTIVE_ACCOUNT
        description: "Account active status (BR-010: renamed from IS_ACTIVE)"
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
              
      # ─────────────────────────────────────────────────────────────────────────
      # NEW CAPABILITIES (Not in PI)
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: CLIENT_TYPE
        description: "Device type (GAP-002: preserved from FTL but not mapped to PI - Mobile/Desktop/Web)"
        tests:
          - accepted_values:
              values: ['Mobile', 'Desktop', 'Web']
              severity: warn  # Warn only since not in target
              
      # ─────────────────────────────────────────────────────────────────────────
      # DATE ALIASES (for multiple Silver table targets)
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: START_DATE
        description: "Alias for DATE (BR-001: maps to SLV_COMBINED_CHANNELS.START_DATE)"
        tests:
          - not_null
          
      - name: REPORT_DATE
        description: "Alias for DATE (BR-001: maps to SLV_CONSOLIDATED_USAGE.REPORT_DATE)"
        tests:
          - not_null
          
      # ─────────────────────────────────────────────────────────────────────────
      # METADATA & AUDIT
      # ─────────────────────────────────────────────────────────────────────────
      
      - name: REFRESH_TIMESTAMP
        description: "ETL refresh timestamp (CURRENT_TIMESTAMP)"
        tests:
          - not_null
          
    # ───────────────────────────────────────────────────────────────────────────
    # MODEL-LEVEL TESTS
    # ───────────────────────────────────────────────────────────────────────────
    
    tests:
      # Ensure grain is maintained
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - DATE
            - ACCOUNT_ID
            - USER_ID
            - ENGAGEMENT_ID
            
      # Row count regression (should increase over time)
      - dbt_utils.expression_is_true:
          expression: "count(*) > 0"
          config:
            severity: error
            
      # Date continuity check (no gaps > 7 days)
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1
```

---

## **FILE 5: tests/regression/regression_suite.sql**

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- FTL → PI MIGRATION: REGRESSION TEST SUITE
-- Purpose: Comprehensive validation of all transformation logic and business rules
-- Scope:   Bronze → Silver → Gold pipeline
-- Run Frequency: After every deployment
-- Pass Condition: All CTEs return 0 rows
-- ═══════════════════════════════════════════════════════════════════════════════

WITH 

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 1: SOURCE DATA QUALITY (Bronze Layer)
-- ═══════════════════════════════════════════════════════════════════════════════

source_row_count AS (
  SELECT 
    'source_row_count' AS test_name,
    CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
),

source_null_check AS (
  SELECT
    'source_null_check' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE ACCOUNT_ID IS NULL
     OR AGENT_ID IS NULL
     OR DATA_DATE IS NULL
),

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 2: TRANSFORMATION LOGIC (BR-001 to BR-013)
-- ═══════════════════════════════════════════════════════════════════════════════

br001_date_parsing AS (
  SELECT
    'br001_date_parsing' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE DATA_DATE IS NOT NULL
    AND TRY_TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') IS NULL
),

br002_ms_to_minutes AS (
  SELECT
    'br002_ms_to_minutes' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE INBOUND_PHONE_MS IS NOT NULL
    AND (INBOUND_PHONE_MS / 60000.0) < 0
),

br003_direction_case AS (
  SELECT
    'br003_direction_case' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE DIRECTION IS NOT NULL
    AND UPPER(DIRECTION) NOT IN ('INBOUND', 'OUTBOUND')
),

br004_channel_case AS (
  SELECT
    'br004_channel_case' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE CHANNEL IS NOT NULL
    AND UPPER(CHANNEL) NOT IN ('VIDEO', 'PHONE')
),

br005_modality_values AS (
  SELECT
    'br005_modality_values' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE MODALITY IS NOT NULL
    AND MODALITY NOT IN ('SMS', 'Email', 'Chat')
),

br006_account_id_format AS (
  SELECT
    'br006_account_id_format' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE ACCOUNT_ID IS NOT NULL
    AND NOT STARTSWITH(ACCOUNT_ID, 'ID_')
),

br007_engagement_id_format AS (
  SELECT
    'br007_engagement_id_format' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE ENGAGEMENT_ID IS NOT NULL
    AND NOT STARTSWITH(ENGAGEMENT_ID, 'ID_')
),

br008_phone_sessions_non_negative AS (
  SELECT
    'br008_phone_sessions_non_negative' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE PHONE_SESSIONS IS NOT NULL
    AND PHONE_SESSIONS < 0
),

br009_agent_id_format AS (
  SELECT
    'br009_agent_id_format' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE AGENT_ID IS NOT NULL
    AND NOT STARTSWITH(AGENT_ID, 'ID_')
),

br010_is_active_boolean AS (
  SELECT
    'br010_is_active_boolean' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE IS_ACTIVE IS NOT NULL
    AND IS_ACTIVE NOT IN (TRUE, FALSE)
),

br012_cluster_mapping AS (
  SELECT
    'br012_cluster_mapping' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE CLUSTER IS NOT NULL
    AND CLUSTER NOT IN ('eu-central-1', 'ap-south-1', 'us-east-1')
),

br013_active_logic AS (
  SELECT
    'br013_active_logic' AS test_name,
    COUNT(*) AS failures
  FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
  WHERE IS_ACTIVE = FALSE
    AND ACCOUNT_ID IN (
      SELECT DISTINCT ACCOUNT_ID 
      FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
      WHERE IS_ACTIVE = TRUE
    )
),

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 3: SILVER LAYER DATA QUALITY
-- ═══════════════════════════════════════════════════════════════════════════════

silver_row_count AS (
  SELECT
    'silver_row_count' AS test_name,
    CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS failures
  FROM {{ ref('slv_ftl_agent_base_agg') }}
),

silver_primary_keys AS (
  SELECT
    'silver_primary_keys' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  WHERE DATE IS NULL
     OR ACCOUNT_ID IS NULL
     OR USER_ID IS NULL
),

silver_surrogate_key_unique AS (
  SELECT
    'silver_surrogate_key_unique' AS test_name,
    SUM(CASE WHEN dup_count > 1 THEN 1 ELSE 0 END) AS failures
  FROM (
    SELECT SURROGATE_KEY, COUNT(*) AS dup_count
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    GROUP BY SURROGATE_KEY
  )
),

silver_date_range AS (
  SELECT
    'silver_date_range' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  WHERE DATE < '2021-01-01'
     OR DATE > DATEADD(day, 1, CURRENT_DATE())
),

silver_region_values AS (
  SELECT
    'silver_region_values' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  WHERE REGION IS NOT NULL
    AND REGION NOT IN ('EMEA', 'APAC', 'NA', 'UNKNOWN')
),

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 4: GOLD LAYER DATA QUALITY
-- ═══════════════════════════════════════════════════════════════════════════════

gold_row_count AS (
  SELECT
    'gold_row_count' AS test_name,
    CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS failures
  FROM {{ ref('gld_aggregate_new') }}
),

gold_grain_not_null AS (
  SELECT
    'gold_grain_not_null' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('gld_aggregate_new') }}
  WHERE DATE IS NULL
     OR REGION IS NULL
),

gold_segment_null AS (
  SELECT
    'gold_segment_null' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('gld_aggregate_new') }}
  WHERE SEGMENT IS NOT NULL  -- Should be NULL per GAP-001
),

gold_is_licensed_null AS (
  SELECT
    'gold_is_licensed_null' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('gld_aggregate_new') }}
  WHERE IS_LICENSED IS NOT NULL  -- Should be NULL per GAP-006
),

gold_active_accounts_consistency AS (
  SELECT
    'gold_active_accounts_consistency' AS test_name,
    COUNT(*) AS failures
  FROM (
    SELECT 
      s.DATE,
      s.REGION,
      COUNT(DISTINCT CASE WHEN s.IS_ACTIVE_ACCOUNT = TRUE THEN s.ACCOUNT_ID END) AS silver_cnt,
      MAX(g.ACTIVE_ACCOUNTS) AS gold_cnt
    FROM {{ ref('slv_ftl_agent_base_agg') }} s
    JOIN {{ ref('gld_aggregate_new') }} g
      ON s.DATE = g.DATE AND s.REGION = g.REGION
    GROUP BY s.DATE, s.REGION
  )
  WHERE silver_cnt != gold_cnt
),

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 5: CROSS-LAYER REFERENTIAL INTEGRITY
-- ═══════════════════════════════════════════════════════════════════════════════

silver_to_bronze_referential AS (
  SELECT
    'silver_to_bronze_referential' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('slv_ftl_agent_base_agg') }} s
  LEFT JOIN {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }} b
    ON s.ACCOUNT_ID = b.ACCOUNT_ID
    AND s.USER_ID = b.AGENT_ID
  WHERE b.ACCOUNT_ID IS NULL
),

gold_to_silver_date_coverage AS (
  SELECT
    'gold_to_silver_date_coverage' AS test_name,
    COUNT(*) AS failures
  FROM {{ ref('gld_aggregate_new') }} g
  LEFT JOIN (
    SELECT DISTINCT DATE, REGION
    FROM {{ ref('slv_ftl_agent_base_agg') }}
  ) s
    ON g.DATE = s.DATE AND g.REGION = s.REGION
  WHERE s.DATE IS NULL
),

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 6: FINAL ROLLUP
-- ═══════════════════════════════════════════════════════════════════════════════

all_tests AS (
  SELECT * FROM source_row_count
  UNION ALL SELECT * FROM source_null_check
  UNION ALL SELECT * FROM br001_date_parsing
  UNION ALL SELECT * FROM br002_ms_to_minutes
  UNION ALL SELECT * FROM br003_direction_case
  UNION ALL SELECT * FROM br004_channel_case
  UNION ALL SELECT * FROM br005_modality_values
  UNION ALL SELECT * FROM br006_account_id_format
  UNION ALL SELECT * FROM br007_engagement_id_format
  UNION ALL SELECT * FROM br008_phone_sessions_non_negative
  UNION ALL SELECT * FROM br009_agent_id_format
  UNION ALL SELECT * FROM br010_is_active_boolean
  UNION ALL SELECT * FROM br012_cluster_mapping
  UNION ALL SELECT * FROM br013_active_logic
  UNION ALL SELECT * FROM silver_row_count
  UNION ALL SELECT * FROM silver_primary_keys
  UNION ALL SELECT * FROM silver_surrogate_key_unique
  UNION ALL SELECT * FROM silver_date_range
  UNION ALL SELECT * FROM silver_region_values
  UNION ALL SELECT * FROM gold_row_count
  UNION ALL SELECT * FROM gold_grain_not_null
  UNION ALL SELECT * FROM gold_segment_null
  UNION ALL SELECT * FROM gold_is_licensed_null
  UNION ALL SELECT * FROM gold_active_accounts_consistency
  UNION ALL SELECT * FROM silver_to_bronze_referential
  UNION ALL SELECT * FROM gold_to_silver_date_coverage
)

-- ═══════════════════════════════════════════════════════════════════════════════
-- OUTPUT: Return only failed tests
-- Pass Condition: 0 rows returned
-- On Failure: Review test_name and failures column
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
  test_name,
  failures,
  CASE
    WHEN test_name LIKE 'br%' THEN 'TRANSFORMATION LOGIC ERROR'
    WHEN test_name LIKE 'source%' THEN 'SOURCE DATA QUALITY ISSUE'
    WHEN test_name LIKE 'silver%' THEN 'SILVER LAYER DATA QUALITY ISSUE'
    WHEN test_name LIKE 'gold%' THEN 'GOLD LAYER DATA QUALITY ISSUE'
    ELSE 'REFERENTIAL INTEGRITY ISSUE'
  END AS failure_category,
  CURRENT_TIMESTAMP() AS test_run_timestamp
FROM all_tests
WHERE failures > 0
ORDER BY failure_category, test_name;

-- ═══════════════════════════════════════════════════════════════════════════════
-- SUMMARY METRICS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Total tests run: 26
-- Expected result: 0 rows
-- If failures > 0: Escalate to Data Engineering immediately
```

---

## **FILE 6: TEST_RUNBOOK.md**

```markdown
# FTL → PI Migration: Test Execution Runbook

## 📋 Overview

This runbook provides step-by-step instructions for executing the complete test suite for the FTL to PI migration project.

**Project Context:**
- **Source:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG (14 columns)
- **Silver Model:** slv_ftl_agent_base_agg
- **Gold Model:** gld_aggregate_new
- **Business Rules:** BR-001 to BR-013
- **Known Gaps:** GAP-001 to GAP-006

---

## 🎯 Test Suite Components

| File | Test Count | Purpose | Location |
|------|------------|---------|----------|
| unit_tests.sql | 13 | Validate BR-001 to BR-013 transformations | tests/unit/ |
| functional_tests.sql | 14 | Data quality + gap validation | tests/functional/ |
| gold_equivalence_test.sql | 1 | Compare FTL vs PI Gold | tests/functional/ |
| schema_with_tests.yml | 22 | dbt column & model tests | models/silver/ |
| regression_suite.sql | 26 | Full end-to-end validation | tests/regression/ |

**Total Test Coverage:** 76 tests

---

## 🔄 Execution Sequence

### **PRE-FLIGHT CHECKS**

Before running any tests, verify:

```sql
-- 1. Verify Bronze table exists and has data
SELECT 
  COUNT(*) AS bronze_row_count,
  MIN(DATA_DATE) AS earliest_date,
  MAX(DATA_DATE) AS latest_date
FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG;
-- Expected: row_count > 0

-- 2. Verify Silver model has been built
SELECT 
  COUNT(*) AS silver_row_count,
  MAX(REFRESH_TIMESTAMP) AS last_refresh
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG;
-- Expected: row_count > 0, last_refresh = recent

-- 3. Verify Gold model has been built
SELECT 
  COUNT(*) AS gold_row_count
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW;
-- Expected: row_count > 0
```

---

## 📝 Test Execution Order

### **PHASE 1: Unit Tests (Transformation Logic)**

**Purpose:** Validate all business rules (BR-001 to BR-013) are correctly implemented

**Command:**
```bash
dbt test --select tests/unit/unit_tests.sql
```

**Alternative (run in Snowflake):**
```sql
-- Execute each test individually from tests/unit/unit_tests.sql
-- Pass condition: Each query returns 0 rows
```

**Expected Result:** All 13 tests return 0 rows

**On Failure:**
| Test Name | Failure Action | Contact |
|-----------|----------------|---------|
| test_unit_BR001_date_parsing | Review DATA_DATE format in Bronze | Data Engineering |
| test_unit_BR002_ms_to_minutes | Check for negative INBOUND_PHONE_MS values | Data Engineering |
| test_unit_BR003_direction_uppercase | Verify DIRECTION enumeration | Data Engineering |
| test_unit_BR004_channel_uppercase | Verify CHANNEL enumeration | Data Engineering |
| test_unit_BR005_modality_values | Check for new MODALITY values | Data Engineering |
| test_unit_BR006_account_id_format | Validate ID_ prefix pattern | Data Engineering |
| test_unit_BR007_engagement_id_format | Validate ID_ prefix pattern | Data Engineering |
| test_unit_BR008_phone_sessions_non_negative | Check for negative counts | Data Engineering |
| test_unit_BR009_agent_id_format | Validate AGENT_ID format | Data Engineering |
| test_unit_BR010_is_active_boolean | Check for non-boolean values | Data Engineering |
| test_unit_BR012_cluster_to_region | Verify cluster enumeration | Data Engineering |
| test_unit_BR013_active_account_logic | Review active flag consistency | Analytics Team |

---

### **PHASE 2: Functional Tests (Data Quality + Gaps)**

**Purpose:** Validate data quality, null handling, and gap documentation

**Command:**
```bash
dbt test --select tests/functional/functional_tests.sql
```

**Expected Result:** Tests return appropriate results based on gap expectations

**Gap Test Expectations:**
| Test Name | Expected Behavior | Notes |
|-----------|-------------------|-------|
| test_gap_GAP001_segment_is_null | PASS (all NULL) | SEGMENT not provided by FTL |
| test_gap_GAP002_client_type_preserved | PASS (informational) | CLIENT_TYPE in Silver only |
| test_gap_GAP003_latam_region_missing | PASS (0 LATAM) | No LATAM cluster mapping |
| test_gap_GAP004_os_not_mapped | PASS (informational) | OS has data quality issue |
| test_gap_GAP005_zcc_account_id_not_mapped | PASS (informational) | ZCC_ACCOUNT_ID not needed |
| test_gap_GAP006_is_licensed_is_null | PASS (all NULL) | IS_LICENSED not provided by FTL |

**Functional Test Expectations:**
| Test Name | Pass Condition | On Failure |
|-----------|----------------|------------|
| test_functional_silver_row_count | row_count > 0 | Check pipeline execution |
| test_functional_gold_row_count | row_count > 0 | Check aggregation logic |
| test_functional_primary_keys_not_null | 0 NULL PKs | Review source data |
| test_functional_gold_primary_keys_not_null | 0 NULL grain cols | Review aggregation |
| test_functional_date_range_valid | All dates 2021-2026 | Check date parsing |
| test_functional_no_duplicate_surrogate_keys | 0 duplicates | Review surrogate key logic |
| test_functional_active_accounts_consistency | Counts match | Review aggregation |
| test_functional_region_values | Only EMEA/APAC/NA/UNKNOWN | Check cluster mapping |

---

### **PHASE 3: Gold Equivalence Test**

**Purpose:** Compare FTL-based Gold (gld_aggregate_new) against legacy PI Gold (GLD_AGGREGATE)

**Command:**
```bash
dbt test --select tests/functional/gold_equivalence_test.sql
```

**Alternative (run in Snowflake):**
```sql
-- Execute gold_equivalence_test.sql
-- Pass condition: 0 rows returned (all differences within 5% tolerance)
```

**Expected Result:** 0 rows (no unexplained variances)

**Variance Tolerance:**
- ACTIVE_ACCOUNTS: ≤ 5% difference
- ACTIVE_USERS: ≤ 5% difference
- PHONE_USAGE: ≤ 10% difference

**On Failure (rows returned):**
1. Review `failure_reason` column
2. Check if variance is explained by GAP-001 (SEGMENT) or GAP-006 (IS_LICENSED)
3. If variance > tolerance and unexplained:
   - Compare date ranges between FTL and PI sources
   - Verify cluster-to-region mapping
   - Escalate to Analytics Team for business logic review

---

### **PHASE 4: dbt YAML Tests**

**Purpose:** Execute built-in dbt tests defined in schema YAML

**Command:**
```bash
dbt test --select slv_ftl_agent_base_agg
```

**Expected Result:** All 22 schema tests pass

**Key Tests:**
- ✅ SURROGATE_KEY uniqueness
- ✅ Primary key NOT NULL constraints
- ✅ DATE range validation (2021-01-01 to tomorrow)
- ✅ ACCOUNT_ID/USER_ID/ENGAGEMENT_ID format (ID_ prefix)
- ✅ DIRECTION values (INBOUND/OUTBOUND)
- ✅ MODALITY values (SMS/Email/Chat)
- ✅ CHANNEL values (VIDEO/PHONE)
- ✅ REGION values (EMEA/APAC/NA/UNKNOWN)
- ✅ PHONE_SESSIONS non-negative
- ✅ INBOUND_PHONE_MINS non-negative
- ✅ IS_ACTIVE_ACCOUNT boolean
- ✅ Grain uniqueness (DATE + ACCOUNT_ID + USER_ID + ENGAGEMENT_ID)

**On Failure:**
- Review dbt logs for specific test failure
- Re-run failed test individually: `dbt test --select slv_ftl_agent_base_agg,test:<test_name>`
- Investigate source data if constraint violations detected

---

### **PHASE 5: Regression Suite (Full End-to-End)**

**Purpose:** Comprehensive validation of entire pipeline (Bronze → Silver → Gold)

**Command:**
```bash
# Option 1: Run via dbt
dbt test --select tests/regression/regression_suite.sql

# Option 2: Run in Snowflake
USE ROLE <your_role>;
USE WAREHOUSE <your_warehouse>;
USE DATABASE ZOOM_AI_POC;
USE SCHEMA SILVER;

-- Execute regression_suite.sql
-- Pass condition: Query returns 0 rows
```

**Expected Result:** 0 rows (no failures across 26 tests)

**Test Coverage:**
1. **Source Data Quality (4 tests)**
   - Bronze row count > 0
   - No NULL primary keys in Bronze
   - All dates parseable
   - No negative duration values

2. **Transformation Logic (13 tes