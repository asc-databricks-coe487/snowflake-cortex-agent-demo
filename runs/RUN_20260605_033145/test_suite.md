

I'll generate the complete test suite manually based on the approved mapping and dbt code you provided. Let me create all 6 test files following the FTL to PI migration standards.

---

# 🧪 COMPLETE TEST SUITE PACKAGE
## FTL to PI Migration - Data Quality Framework

---

## 📊 SUMMARY TABLE

| Test Type | Count | Files Generated |
|-----------|-------|-----------------|
| Unit Tests (Business Rules) | 14 | tests/unit/unit_tests.sql |
| Unit Tests (Gaps) | 2 | tests/unit/unit_tests.sql |
| Functional Tests | 8 | tests/functional/functional_tests.sql |
| Gold Equivalence Test | 1 | tests/functional/gold_equivalence_test.sql |
| dbt Schema Tests | 18 | models/silver/slv_ftl_agent_base_agg.yml |
| Regression Suite | 1 | tests/regression/regression_suite.sql |
| Test Runbook | 1 | TEST_RUNBOOK.md |
| **TOTAL** | **45** | **6 files** |

---

## 📦 FILE 1: `tests/unit/unit_tests.sql`

```sql
-- =============================================================================
-- UNIT TEST SUITE: FTL to PI Migration
-- MODEL: slv_ftl_agent_base_agg
-- PURPOSE: Validate all 14 business rule transformations + 2 gap validations
-- PASS CONDITION: Each test returns 0 rows = PASS
-- =============================================================================

-- 🧪 STEP 1: BR-001 — ACCOUNT_ID Direct Pass-through
-- Validates ACCOUNT_ID mapping is preserved without transformation
-- TEST: test_unit_BR_001_account_id
-- PASS: 0 rows (all Bronze ACCOUNT_ID values present in Silver)
-- FAIL ACTION: Notify Data Engineering Team — investigate missing ACCOUNT_ID records
WITH test_unit_BR_001_account_id AS (
  SELECT 
    'BR-001' AS test_id,
    'ACCOUNT_ID direct pass-through validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ACCOUNT_ID = slv.ACCOUNT_ID
    AND brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE slv.ACCOUNT_ID IS NULL
    OR brz.ACCOUNT_ID != slv.ACCOUNT_ID
)

-- 🧪 STEP 2: BR-002 — ENGAGEMENT_ID Direct Pass-through
-- Validates unique engagement identifier mapping
-- TEST: test_unit_BR_002_engagement_id
-- PASS: 0 rows (all Bronze ENGAGEMENT_ID values present in Silver)
-- FAIL ACTION: Notify Data Engineering Team — investigate missing ENGAGEMENT_ID records
, test_unit_BR_002_engagement_id AS (
  SELECT 
    'BR-002' AS test_id,
    'ENGAGEMENT_ID direct pass-through validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE slv.ENGAGEMENT_ID IS NULL
    OR brz.ENGAGEMENT_ID != slv.ENGAGEMENT_ID
)

-- 🧪 STEP 3: BR-003 — AGENT_ID to USER_ID Semantic Mapping
-- Validates agent-to-user semantic transformation
-- TEST: test_unit_BR_003_user_id
-- PASS: 0 rows (all Bronze AGENT_ID mapped to Silver USER_ID)
-- FAIL ACTION: Notify BDP Team — validate agent = user assumption
, test_unit_BR_003_user_id AS (
  SELECT 
    'BR-003' AS test_id,
    'AGENT_ID to USER_ID semantic mapping validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE slv.USER_ID IS NULL
    OR brz.AGENT_ID != slv.USER_ID
)

-- 🧪 STEP 4: BR-004 — DIRECTION Case Normalization
-- Validates UPPER(DIRECTION) transformation: Inbound → INBOUND, Outbound → OUTBOUND
-- TEST: test_unit_BR_004_direction
-- PASS: 0 rows (all Bronze DIRECTION values uppercase in Silver)
-- FAIL ACTION: Notify Data Engineering Team — fix case normalization logic
, test_unit_BR_004_direction AS (
  SELECT 
    'BR-004' AS test_id,
    'DIRECTION case normalization validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE UPPER(brz.DIRECTION) != slv.DIRECTION
)

-- 🧪 STEP 5: BR-005 — MODALITY Mapping Logic
-- Validates MODALITY consolidation from CHANNEL/MODALITY merge
-- TEST: test_unit_BR_005_modality
-- PASS: 0 rows (modality correctly derived from channel when applicable)
-- FAIL ACTION: Notify Data Engineering Team — review CASE logic for modality
, test_unit_BR_005_modality AS (
  SELECT 
    'BR-005' AS test_id,
    'MODALITY mapping validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE 
    CASE 
      WHEN brz.CHANNEL IN ('Phone', 'Video') THEN brz.CHANNEL
      WHEN brz.MODALITY IN ('SMS', 'Email', 'Chat') THEN brz.MODALITY
      ELSE NULL
    END != slv.MODALITY
)

-- 🧪 STEP 6: BR-006 — CHANNEL Consolidation Logic
-- Validates CHANNEL merge from MODALITY/CHANNEL columns
-- TEST: test_unit_BR_006_channel
-- PASS: 0 rows (channel correctly consolidated and uppercased)
-- FAIL ACTION: Notify Data Engineering Team — review CASE logic for channel consolidation
, test_unit_BR_006_channel AS (
  SELECT 
    'BR-006' AS test_id,
    'CHANNEL consolidation validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE 
    CASE 
      WHEN brz.MODALITY IN ('Email', 'SMS', 'Chat') THEN UPPER(brz.MODALITY)
      WHEN brz.CHANNEL IN ('Phone', 'Video') THEN UPPER(brz.CHANNEL)
      ELSE 'UNKNOWN'
    END != slv.CHANNEL
)

-- 🧪 STEP 7: BR-007 — PHONE_SESSIONS Direct Pass-through
-- Validates phone sessions count mapping
-- TEST: test_unit_BR_007_phone_sessions
-- PASS: 0 rows (all Bronze PHONE_SESSIONS match Silver)
-- FAIL ACTION: Notify Data Engineering Team — investigate phone sessions discrepancy
, test_unit_BR_007_phone_sessions AS (
  SELECT 
    'BR-007' AS test_id,
    'PHONE_SESSIONS direct pass-through validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE COALESCE(brz.PHONE_SESSIONS, 0) != COALESCE(slv.PHONE_SESSIONS, 0)
)

-- 🧪 STEP 8: BR-008 — INBOUND_PHONE_MS to INBOUND_PHONE_MINS Unit Conversion
-- Validates milliseconds to minutes conversion (divide by 60,000)
-- TEST: test_unit_BR_008_inbound_phone_mins
-- PASS: 0 rows (conversion accurate within 0.001 minute tolerance)
-- FAIL ACTION: Notify Data Engineering Team — review unit conversion formula
, test_unit_BR_008_inbound_phone_mins AS (
  SELECT 
    'BR-008' AS test_id,
    'INBOUND_PHONE_MS to INBOUND_PHONE_MINS conversion validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE ABS((brz.INBOUND_PHONE_MS / 60000.0) - COALESCE(slv.INBOUND_PHONE_MINS, 0)) > 0.001
)

-- 🧪 STEP 9: BR-009 — INBOUND_PHONE_MS to PHONE_USAGE Unit Conversion
-- Validates milliseconds to minutes conversion for aggregated usage
-- TEST: test_unit_BR_009_phone_usage
-- PASS: 0 rows (conversion accurate within 0.001 minute tolerance)
-- FAIL ACTION: Notify Data Engineering Team — review aggregated usage conversion
, test_unit_BR_009_phone_usage AS (
  SELECT 
    'BR-009' AS test_id,
    'INBOUND_PHONE_MS to PHONE_USAGE conversion validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE ABS((brz.INBOUND_PHONE_MS / 60000.0) - COALESCE(slv.PHONE_USAGE, 0)) > 0.001
)

-- 🧪 STEP 10: BR-010 — IS_ACTIVE Semantic Mapping (Engagement to Account)
-- Validates engagement-level activity flag preservation
-- TEST: test_unit_BR_010_is_active
-- PASS: 0 rows (IS_ACTIVE flag preserved at engagement level)
-- FAIL ACTION: Notify Data Engineering Team — validate IS_ACTIVE logic
, test_unit_BR_010_is_active AS (
  SELECT 
    'BR-010' AS test_id,
    'IS_ACTIVE flag validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE COALESCE(brz.IS_ACTIVE, FALSE) != COALESCE(slv.IS_ACTIVE, FALSE)
)

-- 🧪 STEP 11: BR-011 — CLUSTER to REGION Mapping
-- Validates geographic cluster-to-region transformation
-- TEST: test_unit_BR_011_region
-- PASS: 0 rows (all clusters correctly mapped to regions)
-- FAIL ACTION: Notify Data Engineering Team — update CLUSTER_REGION_MAP lookup
, test_unit_BR_011_region AS (
  SELECT 
    'BR-011' AS test_id,
    'CLUSTER to REGION mapping validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE 
    CASE brz.CLUSTER
      WHEN 'US_WEST' THEN 'US West'
      WHEN 'US_EAST' THEN 'US East'
      WHEN 'EU_CENTRAL' THEN 'Europe'
      WHEN 'APAC' THEN 'Asia Pacific'
      ELSE 'UNKNOWN'
    END != slv.REGION
)

-- 🧪 STEP 12: BR-012 — DATA_DATE to DATE Type Conversion
-- Validates TEXT to DATE conversion for DATE column
-- TEST: test_unit_BR_012_date
-- PASS: 0 rows (all DATA_DATE successfully converted to DATE)
-- FAIL ACTION: Notify Data Engineering Team — investigate date parsing failures
, test_unit_BR_012_date AS (
  SELECT 
    'BR-012' AS test_id,
    'DATA_DATE to DATE type conversion validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE TRY_TO_DATE(brz.DATA_DATE) IS NULL
    OR TRY_TO_DATE(brz.DATA_DATE) != slv.DATE
)

-- 🧪 STEP 13: BR-013 — DATA_DATE to REPORT_DATE Type Conversion
-- Validates TEXT to DATE conversion for REPORT_DATE column
-- TEST: test_unit_BR_013_report_date
-- PASS: 0 rows (all DATA_DATE successfully converted to REPORT_DATE)
-- FAIL ACTION: Notify Data Engineering Team — investigate date parsing failures
, test_unit_BR_013_report_date AS (
  SELECT 
    'BR-013' AS test_id,
    'DATA_DATE to REPORT_DATE type conversion validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE TRY_TO_DATE(brz.DATA_DATE) != slv.REPORT_DATE
)

-- 🧪 STEP 14: BR-014 — DATA_DATE to START_DATE Type Conversion
-- Validates TEXT to DATE conversion for START_DATE column
-- TEST: test_unit_BR_014_start_date
-- PASS: 0 rows (all DATA_DATE successfully converted to START_DATE)
-- FAIL ACTION: Notify Data Engineering Team — investigate date parsing failures
, test_unit_BR_014_start_date AS (
  SELECT 
    'BR-014' AS test_id,
    'DATA_DATE to START_DATE type conversion validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
  LEFT JOIN ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
    ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
    AND TRY_TO_DATE(brz.DATA_DATE) = slv.DATE
  WHERE TRY_TO_DATE(brz.DATA_DATE) != slv.START_DATE
)

-- 🧪 STEP 15: GAP-023 — ACCOUNT_FIRST_ACTIVE Derivation
-- Validates MIN(DATA_DATE) window function derivation for account first active date
-- TEST: test_gap_GAP_023_account_first_active_is_null
-- PASS: 0 rows (all accounts have first active date populated)
-- FAIL ACTION: Notify BDP Team — validate Bronze data completeness
, test_gap_GAP_023_account_first_active_is_null AS (
  SELECT 
    'GAP-023' AS test_id,
    'ACCOUNT_FIRST_ACTIVE derivation validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE ACCOUNT_FIRST_ACTIVE IS NULL
)

-- 🧪 STEP 16: GAP-024 — USER_FIRST_ACTIVE Derivation
-- Validates MIN(DATA_DATE) window function derivation for user first active date
-- TEST: test_gap_GAP_024_user_first_active_is_null
-- PASS: 0 rows (all users have first active date populated)
-- FAIL ACTION: Notify BDP Team — validate Bronze data completeness
, test_gap_GAP_024_user_first_active_is_null AS (
  SELECT 
    'GAP-024' AS test_id,
    'USER_FIRST_ACTIVE derivation validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE USER_FIRST_ACTIVE IS NULL
)

-- 🧪 FINAL RESULT: Aggregate all test failures
SELECT * FROM test_unit_BR_001_account_id WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_002_engagement_id WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_003_user_id WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_004_direction WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_005_modality WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_006_channel WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_007_phone_sessions WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_008_inbound_phone_mins WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_009_phone_usage WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_010_is_active WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_011_region WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_012_date WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_013_report_date WHERE failure_count > 0
UNION ALL
SELECT * FROM test_unit_BR_014_start_date WHERE failure_count > 0
UNION ALL
SELECT * FROM test_gap_GAP_023_account_first_active_is_null WHERE failure_count > 0
UNION ALL
SELECT * FROM test_gap_GAP_024_user_first_active_is_null WHERE failure_count > 0;

-- ✅ PASS CONDITION: Query returns 0 rows
-- ❌ FAIL CONDITION: Query returns 1+ rows with test_id and failure_count
```

---

## 📦 FILE 2: `tests/functional/functional_tests.sql`

```sql
-- =============================================================================
-- FUNCTIONAL TEST SUITE: FTL to PI Migration
-- MODEL: slv_ftl_agent_base_agg
-- PURPOSE: Validate data quality, completeness, and referential integrity
-- PASS CONDITION: Each test returns 0 rows = PASS
-- =============================================================================

-- 🧪 STEP 1: Row Count Reconciliation — Bronze vs Silver
-- Validates no data loss during Bronze to Silver transformation
-- TEST: test_functional_row_count_reconciliation
-- PASS: 0 rows (Bronze row count = Silver row count)
-- FAIL ACTION: Notify Data Engineering Team — investigate missing rows
WITH bronze_count AS (
  SELECT COUNT(*) AS brz_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
),
silver_count AS (
  SELECT COUNT(*) AS slv_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
),
test_functional_row_count_reconciliation AS (
  SELECT 
    'FUNC-001' AS test_id,
    'Row count reconciliation (Bronze vs Silver)' AS test_name,
    CASE 
      WHEN brz_count != slv_count THEN 1
      ELSE 0
    END AS failure_count,
    brz_count,
    slv_count,
    (brz_count - slv_count) AS row_difference
  FROM bronze_count
  CROSS JOIN silver_count
)

-- 🧪 STEP 2: Primary Key Uniqueness — Silver Layer
-- Validates ACCOUNT_ID + ENGAGEMENT_ID + DATE uniqueness
-- TEST: test_functional_primary_key_unique
-- PASS: 0 rows (no duplicate primary keys)
-- FAIL ACTION: Notify Data Engineering Team — deduplicate Silver layer
, test_functional_primary_key_unique AS (
  SELECT 
    'FUNC-002' AS test_id,
    'Primary key uniqueness validation' AS test_name,
    COUNT(*) AS failure_count
  FROM (
    SELECT 
      ACCOUNT_ID,
      ENGAGEMENT_ID,
      DATE,
      COUNT(*) AS duplicate_count
    FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
    GROUP BY ACCOUNT_ID, ENGAGEMENT_ID, DATE
    HAVING COUNT(*) > 1
  )
)

-- 🧪 STEP 3: Core Dimension NOT NULL Validation
-- Validates critical dimensions are never NULL
-- TEST: test_functional_core_dimensions_not_null
-- PASS: 0 rows (ACCOUNT_ID, ENGAGEMENT_ID, USER_ID, DATE never NULL)
-- FAIL ACTION: Notify Data Engineering Team — fix NULL handling in source
, test_functional_core_dimensions_not_null AS (
  SELECT 
    'FUNC-003' AS test_id,
    'Core dimensions NOT NULL validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE ACCOUNT_ID IS NULL
    OR ENGAGEMENT_ID IS NULL
    OR USER_ID IS NULL
    OR DATE IS NULL
)

-- 🧪 STEP 4: DIRECTION Value Domain Validation
-- Validates DIRECTION only contains INBOUND or OUTBOUND
-- TEST: test_functional_direction_value_domain
-- PASS: 0 rows (all DIRECTION values in approved list)
-- FAIL ACTION: Notify Data Engineering Team — investigate unexpected DIRECTION values
, test_functional_direction_value_domain AS (
  SELECT 
    'FUNC-004' AS test_id,
    'DIRECTION value domain validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE DIRECTION NOT IN ('INBOUND', 'OUTBOUND')
    OR DIRECTION IS NULL
)

-- 🧪 STEP 5: CHANNEL Value Domain Validation
-- Validates CHANNEL contains only approved values
-- TEST: test_functional_channel_value_domain
-- PASS: 0 rows (all CHANNEL values in approved list)
-- FAIL ACTION: Notify Data Engineering Team — review channel consolidation logic
, test_functional_channel_value_domain AS (
  SELECT 
    'FUNC-005' AS test_id,
    'CHANNEL value domain validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE CHANNEL NOT IN ('PHONE', 'VIDEO', 'EMAIL', 'SMS', 'CHAT', 'UNKNOWN')
    OR CHANNEL IS NULL
)

-- 🧪 STEP 6: Numeric Metrics Non-Negative Validation
-- Validates PHONE_SESSIONS, INBOUND_PHONE_MINS, PHONE_USAGE >= 0
-- TEST: test_functional_metrics_non_negative
-- PASS: 0 rows (all metrics >= 0)
-- FAIL ACTION: Notify Data Engineering Team — investigate negative metric values
, test_functional_metrics_non_negative AS (
  SELECT 
    'FUNC-006' AS test_id,
    'Numeric metrics non-negative validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE COALESCE(PHONE_SESSIONS, 0) < 0
    OR COALESCE(INBOUND_PHONE_MINS, 0) < 0
    OR COALESCE(PHONE_USAGE, 0) < 0
)

-- 🧪 STEP 7: Date Range Reasonableness Check
-- Validates DATE falls within reasonable business range (2020-01-01 to current + 30 days)
-- TEST: test_functional_date_range_reasonable
-- PASS: 0 rows (all dates within reasonable range)
-- FAIL ACTION: Notify Data Engineering Team — investigate date parsing errors
, test_functional_date_range_reasonable AS (
  SELECT 
    'FUNC-007' AS test_id,
    'Date range reasonableness validation' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE DATE < '2020-01-01'
    OR DATE > DATEADD(DAY, 30, CURRENT_DATE())
)

-- 🧪 STEP 8: REGION UNKNOWN Monitor
-- Monitors unmapped CLUSTER values resulting in UNKNOWN region
-- TEST: test_functional_region_unknown_monitor
-- PASS: 0 rows (no UNKNOWN regions — warning only)
-- FAIL ACTION: Notify BDP Team — provide cluster registry update
, test_functional_region_unknown_monitor AS (
  SELECT 
    'FUNC-008' AS test_id,
    'REGION UNKNOWN monitoring' AS test_name,
    COUNT(*) AS failure_count
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE REGION = 'UNKNOWN'
)

-- 🧪 FINAL RESULT: Aggregate all functional test failures
SELECT * FROM test_functional_row_count_reconciliation WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_primary_key_unique WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_core_dimensions_not_null WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_direction_value_domain WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_channel_value_domain WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_metrics_non_negative WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_date_range_reasonable WHERE failure_count > 0
UNION ALL
SELECT 
  test_id, 
  test_name, 
  failure_count,
  NULL AS brz_count,
  NULL AS slv_count,
  NULL AS row_difference
FROM test_functional_region_unknown_monitor WHERE failure_count > 0;

-- ✅ PASS CONDITION: Query returns 0 rows
-- ⚠️  WARNING CONDITION: FUNC-008 (REGION UNKNOWN) may return rows — requires BDP follow-up
-- ❌ FAIL CONDITION: Any other test returns 1+ rows
```

---

## 📦 FILE 3: `tests/functional/gold_equivalence_test.sql`

```sql
-- =============================================================================
-- GOLD EQUIVALENCE TEST: FTL to PI Migration
-- MODEL: gld_aggregate_new vs GLD_AGGREGATE (legacy)
-- PURPOSE: Validate FTL Gold layer produces equivalent results to legacy PI Gold
-- PASS CONDITION: Row-level match within tolerance thresholds
-- =============================================================================

-- 🧪 GOLD LAYER EQUIVALENCE — Compare FTL Gold vs Legacy PI Gold
-- Validates new FTL pipeline produces same business results as legacy system
-- TEST: test_gold_equivalence_ftl_vs_pi
-- PASS: Row differences <= 5% AND metric variance <= 10%
-- FAIL ACTION: Notify Analytics Lead + Data Engineering Team — investigate pipeline divergence

WITH ftl_gold AS (
  SELECT 
    DATE,
    REGION,
    SEGMENT,
    IS_LICENSED,
    ACTIVE_ACCOUNTS,
    ACTIVE_USERS,
    PHONE_USAGE,
    USERS_ACTIVE_16PLUS_DAYS
  FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
  WHERE DATE >= DATEADD(DAY, -30, CURRENT_DATE())  -- Compare last 30 days
),

legacy_gold AS (
  SELECT 
    DATE,
    REGION,
    SEGMENT,
    IS_LICENSED,
    ACTIVE_ACCOUNTS,
    ACTIVE_USERS,
    PHONE_USAGE,
    USERS_ACTIVE_16PLUS_DAYS
  FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
  WHERE DATE >= DATEADD(DAY, -30, CURRENT_DATE())
),

-- Row-level comparison
row_comparison AS (
  SELECT 
    COALESCE(ftl.DATE, leg.DATE) AS comparison_date,
    COALESCE(ftl.REGION, leg.REGION) AS comparison_region,
    
    -- FTL metrics
    ftl.ACTIVE_ACCOUNTS AS ftl_active_accounts,
    ftl.ACTIVE_USERS AS ftl_active_users,
    ftl.PHONE_USAGE AS ftl_phone_usage,
    
    -- Legacy metrics
    leg.ACTIVE_ACCOUNTS AS legacy_active_accounts,
    leg.ACTIVE_USERS AS legacy_active_users,
    leg.PHONE_USAGE AS legacy_phone_usage,
    
    -- Absolute differences
    ABS(COALESCE(ftl.ACTIVE_ACCOUNTS, 0) - COALESCE(leg.ACTIVE_ACCOUNTS, 0)) AS diff_active_accounts,
    ABS(COALESCE(ftl.ACTIVE_USERS, 0) - COALESCE(leg.ACTIVE_USERS, 0)) AS diff_active_users,
    ABS(COALESCE(ftl.PHONE_USAGE, 0) - COALESCE(leg.PHONE_USAGE, 0)) AS diff_phone_usage,
    
    -- Percentage variance
    CASE 
      WHEN COALESCE(leg.ACTIVE_ACCOUNTS, 0) > 0 
      THEN (ABS(COALESCE(ftl.ACTIVE_ACCOUNTS, 0) - COALESCE(leg.ACTIVE_ACCOUNTS, 0)) / leg.ACTIVE_ACCOUNTS) * 100
      ELSE 0
    END AS pct_var_active_accounts,
    
    CASE 
      WHEN COALESCE(leg.ACTIVE_USERS, 0) > 0 
      THEN (ABS(COALESCE(ftl.ACTIVE_USERS, 0) - COALESCE(leg.ACTIVE_USERS, 0)) / leg.ACTIVE_USERS) * 100
      ELSE 0
    END AS pct_var_active_users,
    
    CASE 
      WHEN COALESCE(leg.PHONE_USAGE, 0) > 0 
      THEN (ABS(COALESCE(ftl.PHONE_USAGE, 0) - COALESCE(leg.PHONE_USAGE, 0)) / leg.PHONE_USAGE) * 100
      ELSE 0
    END AS pct_var_phone_usage,
    
    -- Match flags
    CASE 
      WHEN ftl.DATE IS NULL THEN 'MISSING_IN_FTL'
      WHEN leg.DATE IS NULL THEN 'MISSING_IN_LEGACY'
      ELSE 'PRESENT_IN_BOTH'
    END AS row_match_status
    
  FROM ftl_gold ftl
  FULL OUTER JOIN legacy_gold leg
    ON ftl.DATE = leg.DATE
    AND ftl.REGION = leg.REGION
),

-- Aggregate variance summary
variance_summary AS (
  SELECT 
    'GOLD-001' AS test_id,
    'Gold equivalence test (FTL vs PI Legacy)' AS test_name,
    
    -- Row count comparison
    COUNT(CASE WHEN row_match_status = 'PRESENT_IN_BOTH' THEN 1 END) AS matched_rows,
    COUNT(CASE WHEN row_match_status = 'MISSING_IN_FTL' THEN 1 END) AS missing_in_ftl,
    COUNT(CASE WHEN row_match_status = 'MISSING_IN_LEGACY' THEN 1 END) AS missing_in_legacy,
    
    -- Metric variance stats
    AVG(pct_var_active_accounts) AS avg_variance_active_accounts,
    MAX(pct_var_active_accounts) AS max_variance_active_accounts,
    
    AVG(pct_var_active_users) AS avg_variance_active_users,
    MAX(pct_var_active_users) AS max_variance_active_users,
    
    AVG(pct_var_phone_usage) AS avg_variance_phone_usage,
    MAX(pct_var_phone_usage) AS max_variance_phone_usage,
    
    -- Pass/Fail determination
    CASE 
      WHEN COUNT(CASE WHEN row_match_status = 'MISSING_IN_FTL' THEN 1 END) > 0 THEN 1
      WHEN COUNT(CASE WHEN row_match_status = 'MISSING_IN_LEGACY' THEN 1 END) > 
           (COUNT(*) * 0.05) THEN 1  -- Allow 5% new rows in FTL
      WHEN MAX(pct_var_active_accounts) > 10 THEN 1  -- Max 10% variance threshold
      WHEN MAX(pct_var_active_users) > 10 THEN 1
      WHEN MAX(pct_var_phone_usage) > 10 THEN 1
      ELSE 0
    END AS test_failed
    
  FROM row_comparison
),

-- Detail failures for investigation
failure_details AS (
  SELECT 
    comparison_date,
    comparison_region,
    row_match_status,
    ftl_active_accounts,
    legacy_active_accounts,
    diff_active_accounts,
    pct_var_active_accounts,
    ftl_active_users,
    legacy_active_users,
    diff_active_users,
    pct_var_active_users,
    ftl_phone_usage,
    legacy_phone_usage,
    diff_phone_usage,
    pct_var_phone_usage
  FROM row_comparison
  WHERE row_match_status != 'PRESENT_IN_BOTH'
    OR pct_var_active_accounts > 10
    OR pct_var_active_users > 10
    OR pct_var_phone_usage > 10
  ORDER BY comparison_date DESC, comparison_region
)

-- Output summary if test fails
SELECT 
  test_id,
  test_name,
  matched_rows,
  missing_in_ftl,
  missing_in_legacy,
  ROUND(avg_variance_active_accounts, 2) AS avg_var_pct_accounts,
  ROUND(max_variance_active_accounts, 2) AS max_var_pct_accounts,
  ROUND(avg_variance_active_users, 2) AS avg_var_pct_users,
  ROUND(max_variance_active_users, 2) AS max_var_pct_users,
  ROUND(avg_variance_phone_usage, 2) AS avg_var_pct_phone,
  ROUND(max_variance_phone_usage, 2) AS max_var_pct_phone,
  test_failed
FROM variance_summary
WHERE test_failed = 1

UNION ALL

-- Output detail failures
SELECT 
  'GOLD-001' AS test_id,
  'Detail: ' || comparison_date || ' | ' || comparison_region AS test_name,
  NULL AS matched_rows,
  NULL AS missing_in_ftl,
  NULL AS missing_in_legacy,
  pct_var_active_accounts AS avg_var_pct_accounts,
  NULL AS max_var_pct_accounts,
  pct_var_active_users AS avg_var_pct_users,
  NULL AS max_var_pct_users,
  pct_var_phone_usage AS avg_var_pct_phone,
  NULL AS max_var_pct_phone,
  1 AS test_failed
FROM failure_details
LIMIT 100;  -- Limit detail output to top 100 failures

-- ✅ PASS CONDITION: Query returns 0 rows (test_failed = 0)
-- ❌ FAIL CONDITION: Query returns 1+ rows with variance details
-- 
-- TOLERANCE THRESHOLDS:
-- - Row match: Allow 5% new rows in FTL, 0% missing rows
-- - Metric variance: Max 10% difference per metric per date/region
```

---

## 📦 FILE 4: `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **Silver Layer - FTL Agent Base Aggregation**
      
      Transformed engagement-level data from FTL source system with applied business rules:
      - 14 transformation rules (BR-001 to BR-014)
      - 2 gap validations (GAP-023, GAP-024)
      - 3 new capabilities preserved (ZCC_ACCOUNT_ID, CLIENT_TYPE, OS)
      
      **Grain**: ACCOUNT_ID + ENGAGEMENT_ID + DATA_DATE
      **Refresh**: Incremental daily
      **Test Coverage**: 18 dbt schema tests
      
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - ACCOUNT_ID
            - ENGAGEMENT_ID
            - DATE
          config:
            severity: error
            error_if: ">0"
    
    columns:
      - name: ACCOUNT_ID
        description: "Primary account identifier (BR-001: Direct pass-through)"
        tests:
          - not_null:
              config:
                severity: error
          - relationships:
              to: source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG')
              field: ACCOUNT_ID
              config:
                severity: warn
      
      - name: ENGAGEMENT_ID
        description: "Unique engagement identifier (BR-002: Direct pass-through)"
        tests:
          - not_null:
              config:
                severity: error
      
      - name: USER_ID
        description: "User identifier derived from AGENT_ID (BR-003: Semantic mapping)"
        tests:
          - not_null:
              config:
                severity: error
      
      - name: DIRECTION
        description: "Engagement direction normalized to uppercase (BR-004: Case normalization)"
        tests:
          - not_null:
              config:
                severity: error
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              config:
                severity: error
      
      - name: CHANNEL
        description: "Consolidated channel from MODALITY/CHANNEL merge (BR-006)"
        tests:
          - not_null:
              config:
                severity: error
          - accepted_values:
              values: ['PHONE', 'VIDEO', 'EMAIL', 'SMS', 'CHAT', 'UNKNOWN']
              config:
                severity: warn  # UNKNOWN allowed with warning
                warn_if: "= 'UNKNOWN'"
      
      - name: MODALITY
        description: "Communication modality (BR-005)"
        tests:
          - accepted_values:
              values: ['Phone', 'Video', 'SMS', 'Email', 'Chat', NULL]
              config:
                severity: warn
      
      - name: PHONE_SESSIONS
        description: "Count of phone sessions (BR-007: Direct pass-through)"
        tests:
          - not_null:
              config:
                severity: warn
                where: "CHANNEL = 'PHONE'"
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                where: "PHONE_SESSIONS IS NOT NULL"
      
      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (BR-008: Converted from milliseconds)"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                where: "INBOUND_PHONE_MINS IS NOT NULL"
          - dbt_utils.expression_is_true:
              expression: "<= 1440"  # Max 24 hours
              config:
                severity: warn
                where: "INBOUND_PHONE_MINS IS NOT NULL"
      
      - name: PHONE_USAGE
        description: "Phone usage in minutes (BR-009: Converted from milliseconds)"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                where: "PHONE_USAGE IS NOT NULL"
      
      - name: REGION
        description: "Geographic region mapped from CLUSTER (BR-011)"
        tests:
          - not_null:
              config:
                severity: error
          - accepted_values:
              values: ['US West', 'US East', 'Europe', 'Asia Pacific', 'UNKNOWN']
              config:
                severity: warn  # UNKNOWN triggers warning for BDP follow-up
                warn_if: "= 'UNKNOWN'"
      
      - name: DATE
        description: "Engagement date converted from TEXT to DATE (BR-012)"
        tests:
          - not_null:
              config:
                severity: error
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
              config:
                severity: error
          - dbt_utils.expression_is_true:
              expression: "<= DATEADD(DAY, 30, CURRENT_DATE())"
              config:
                severity: warn
      
      - name: REPORT_DATE
        description: "Reporting date converted from TEXT to DATE (BR-013)"
        tests:
          - not_null:
              config:
                severity: error
          - dbt_utils.expression_is_true:
              expression: "= DATE"  # Should match DATE column
              config:
                severity: error
      
      - name: START_DATE
        description: "Engagement start date converted from TEXT to DATE (BR-014)"
        tests:
          - not_null:
              config:
                severity: error
          - dbt_utils.expression_is_true:
              expression: "= DATE"  # Should match DATE column
              config:
                severity: error
      
      - name: ACCOUNT_FIRST_ACTIVE
        description: "First active date for account (GAP-023: Derived via MIN window function)"
        tests:
          - not_null:
              config:
                severity: warn  # Warn if NULL due to incomplete Bronze data
          - dbt_utils.expression_is_true:
              expression: "<= DATE"
              config:
                severity: error
                where: "ACCOUNT_FIRST_ACTIVE IS NOT NULL"
      
      - name: USER_FIRST_ACTIVE
        description: "First active date for user (GAP-024: Derived via MIN window function)"
        tests:
          - not_null:
              config:
                severity: warn  # Warn if NULL due to incomplete Bronze data
          - dbt_utils.expression_is_true:
              expression: "<= DATE"
              config:
                severity: error
                where: "USER_FIRST_ACTIVE IS NOT NULL"
      
      - name: ZCC_ACCOUNT_ID
        description: "Secondary ZCC account identifier (NEW_CAPABILITY)"
        tests:
          - relationships:
              to: source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG')
              field: ZCC_ACCOUNT_ID
              config:
                severity: warn
                where: "ZCC_ACCOUNT_ID IS NOT NULL"
      
      - name: CLIENT_TYPE
        description: "Client device type (NEW_CAPABILITY)"
      
      - name: OS
        description: "Operating system (NEW_CAPABILITY)"
      
      - name: IS_ACTIVE
        description: "Engagement active flag (BR-010)"
        tests:
          - not_null:
              config:
                severity: error
          - accepted_values:
              values: [true, false]
              config:
                severity: error
      
      - name: CLUSTER
        description: "Original cluster value preserved for audit"
      
      - name: DATA_DATE_RAW
        description: "Original TEXT date value preserved for audit"
      
      - name: REFRESH_TIMESTAMP
        description: "Timestamp of last refresh"
        tests:
          - not_null:
              config:
                severity: error
```

---

## 📦 FILE 5: `tests/regression/regression_suite.sql`

```sql
-- =============================================================================
-- REGRESSION TEST SUITE: FTL to PI Migration
-- PURPOSE: Validate production stability across Bronze, Silver, and Gold layers
-- EXECUTION: Run after every deployment to production
-- PASS CONDITION: All tests return 0 rows
-- =============================================================================

-- =============================================================================
-- SECTION 1: BRONZE LAYER STABILITY
-- =============================================================================

-- 🧪 REGRESSION-001: Bronze Row Count Stability
-- Validates Bronze layer has consistent daily ingestion
-- TEST: Flags days with 0 rows or >50% variance from 7-day avg
-- PASS: 0 rows (no anomalies detected)
-- FAIL ACTION: Notify Data Engineering Team — investigate ingestion pipeline
WITH daily_bronze_counts AS (
  SELECT 
    TRY_TO_DATE(DATA_DATE) AS load_date,
    COUNT(*) AS row_count
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
  WHERE TRY_TO_DATE(DATA_DATE) >= DATEADD(DAY, -14, CURRENT_DATE())
  GROUP BY TRY_TO_DATE(DATA_DATE)
),
rolling_avg AS (
  SELECT 
    load_date,
    row_count,
    AVG(row_count) OVER (
      ORDER BY load_date 
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS avg_7day_row_count
  FROM daily_bronze_counts
),
regression_001 AS (
  SELECT 
    'REGR-001' AS test_id,
    'Bronze row count stability check' AS test_name,
    load_date,
    row_count,
    ROUND(avg_7day_row_count, 0) AS avg_7day,
    CASE 
      WHEN row_count = 0 THEN 'ZERO_ROWS'
      WHEN avg_7day_row_count > 0 AND 
           ABS(row_count - avg_7day_row_count) / avg_7day_row_count > 0.5 
      THEN 'HIGH_VARIANCE'
      ELSE 'STABLE'
    END AS status
  FROM rolling_avg
  WHERE load_date >= DATEADD(DAY, -7, CURRENT_DATE())
)

-- =============================================================================
-- SECTION 2: SILVER LAYER REGRESSION
-- =============================================================================

-- 🧪 REGRESSION-002: Silver Transformation Consistency
-- Validates Silver transformations produce consistent patterns
-- TEST: Checks key metric ratios remain stable week-over-week
-- PASS: 0 rows (metric ratios within ±20% of prior week)
-- FAIL ACTION: Notify Data Engineering Team — investigate transformation logic changes
, weekly_silver_metrics AS (
  SELECT 
    DATE_TRUNC('WEEK', DATE) AS week_start,
    COUNT(*) AS total_engagements,
    COUNT(DISTINCT ACCOUNT_ID) AS unique_accounts,
    COUNT(DISTINCT USER_ID) AS unique_users,
    SUM(PHONE_SESSIONS) AS total_phone_sessions,
    SUM(PHONE_USAGE) AS total_phone_usage_mins,
    COUNT(CASE WHEN IS_ACTIVE = TRUE THEN 1 END) AS active_engagements
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  WHERE DATE >= DATEADD(WEEK, -4, CURRENT_DATE())
  GROUP BY DATE_TRUNC('WEEK', DATE)
),
week_over_week AS (
  SELECT 
    week_start,
    total_engagements,
    
    -- Calculate ratios
    CASE WHEN unique_accounts > 0 
         THEN total_engagements::FLOAT / unique_accounts 
         ELSE 0 END AS engagements_per_account,
    
    CASE WHEN unique_users > 0 
         THEN total_phone_sessions::FLOAT / unique_users 
         ELSE 0 END AS sessions_per_user,
    
    CASE WHEN total_engagements > 0 
         THEN active_engagements::FLOAT / total_engagements 
         ELSE 0 END AS active_engagement_rate,
    
    -- Get prior week values
    LAG(CASE WHEN unique_accounts > 0 
             THEN total_engagements::FLOAT / unique_accounts 
             ELSE 0 END) 
        OVER (ORDER BY week_start) AS prev_engagements_per_account,
    
    LAG(CASE WHEN unique_users > 0 
             THEN total_phone_sessions::FLOAT / unique_users 
             ELSE 0 END) 
        OVER (ORDER BY week_start) AS prev_sessions_per_user,
    
    LAG(CASE WHEN total_engagements > 0 
             THEN active_engagements::FLOAT / total_engagements 
             ELSE 0 END) 
        OVER (ORDER BY week_start) AS prev_active_engagement_rate
  FROM weekly_silver_metrics
),
regression_002 AS (
  SELECT 
    'REGR-002' AS test_id,
    'Silver transformation consistency check' AS test_name,
    week_start,
    ROUND(engagements_per_account, 2) AS curr_eng_per_acct,
    ROUND(prev_engagements_per_account, 2) AS prev_eng_per_acct,
    ROUND(sessions_per_user, 2) AS curr_sess_per_user,
    ROUND(prev_sessions_per_user, 2) AS prev_sess_per_user,
    ROUND(active_engagement_rate * 100, 2) AS curr_active_rate_pct,
    ROUND(prev_active_engagement_rate * 100, 2) AS prev_active_rate_pct,
    CASE 
      WHEN prev_engagements_per_account > 0 AND 
           ABS(engagements_per_account - prev_engagements_per_account) / prev_engagements_per_account > 0.2 
      THEN 'ENGAGEMENTS_PER_ACCOUNT_VARIANCE'
      WHEN prev_sessions_per_user > 0 AND 
           ABS(sessions_per_user - prev_sessions_per_user) / prev_sessions_per_user > 0.2 
      THEN 'SESSIONS_PER_USER_VARIANCE'
      WHEN prev_active_engagement_rate > 0 AND 
           ABS(active_engagement_rate - prev_active_engagement_rate) / prev_active_engagement_rate > 0.2 
      THEN 'ACTIVE_RATE_VARIANCE'
      ELSE 'STABLE'
    END AS status
  FROM week_over_week
  WHERE prev_engagements_per_account IS NOT NULL
    AND week_start >= DATEADD(WEEK, -2, CURRENT_DATE())
)

-- =============================================================================
-- SECTION 3: GOLD LAYER REGRESSION
-- =============================================================================

-- 🧪 REGRESSION-003: Gold Aggregation Consistency
-- Validates Gold layer aggregations remain consistent with Silver source
-- TEST: Reconciles Gold ACTIVE_USERS and PHONE_USAGE back to Silver
-- PASS: 0 rows (Gold = Silver within 1% tolerance)
-- FAIL ACTION: Notify Analytics Lead — investigate Gold aggregation logic
, silver_to_gold_reconciliation AS (
  SELECT 
    slv.DATE,
    slv.REGION,
    
    -- Silver aggregated metrics
    COUNT(DISTINCT slv.USER_ID) AS silver_active_users,
    SUM(slv.PHONE_USAGE) AS silver_phone_usage,
    
    -- Gold metrics
    gld.ACTIVE_USERS AS gold_active_users,
    gld.PHONE_USAGE AS gold_phone_usage,
    
    -- Variance calculation
    ABS(COUNT(DISTINCT slv.USER_ID) - COALESCE(gld.ACTIVE_USERS, 0)) AS user_diff,
    ABS(SUM(slv.PHONE_USAGE) - COALESCE(gld.PHONE_USAGE, 0)) AS usage_diff,
    
    CASE 
      WHEN COUNT(DISTINCT slv.USER_ID) > 0 
      THEN (ABS(COUNT(DISTINCT slv.USER_ID) - COALESCE(gld.ACTIVE_USERS, 0))::FLOAT / 
            COUNT(DISTINCT slv.USER_ID)) * 100
      ELSE 0 
    END AS user_variance_pct,
    
    CASE 
      WHEN SUM(slv.PHONE_USAGE) > 0 
      THEN (ABS(SUM(slv.PHONE_USAGE) - COALESCE(gld.PHONE_USAGE, 0))::FLOAT / 
            SUM(slv.PHONE_USAGE)) * 100
      ELSE 0 
    END AS usage_variance_pct
    
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG slv
  LEFT JOIN ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW gld
    ON slv.DATE = gld.DATE
    AND slv.REGION = gld.REGION
  WHERE slv.DATE >= DATEADD(DAY, -7, CURRENT_DATE())
  GROUP BY slv.DATE, slv.REGION, gld.ACTIVE_USERS, gld.PHONE_USAGE
),
regression_003 AS (
  SELECT 
    'REGR-003' AS test_id,
    'Gold aggregation consistency check' AS test_name,
    DATE,
    REGION,
    silver_active_users,
    gold_active_users,
    user_diff,
    ROUND(user_variance_pct, 2) AS user_var_pct,
    ROUND(silver_phone_usage, 2) AS silver_usage,
    ROUND(gold_phone_usage, 2) AS gold_usage,
    ROUND(usage_diff, 2) AS usage_diff,
    ROUND(usage_variance_pct, 2) AS usage_var_pct,
    CASE 
      WHEN user_variance_pct > 1 THEN 'USER_COUNT_MISMATCH'
      WHEN usage_variance_pct > 1 THEN 'USAGE_MISMATCH'
      ELSE 'CONSISTENT'
    END AS status
  FROM silver_to_gold_reconciliation
)

-- =============================================================================
-- SECTION 4: DATA FRESHNESS
-- =============================================================================

-- 🧪 REGRESSION-004: Data Freshness Check
-- Validates all layers have recent data (within 2 days)
-- TEST: Checks MAX(DATE) across Bronze, Silver, Gold
-- PASS: 0 rows (all layers have data from last 48 hours)
-- FAIL ACTION: Notify Data Engineering Team — investigate stale data
, data_freshness AS (
  SELECT 
    'Bronze' AS layer,
    MAX(TRY_TO_DATE(DATA_DATE)) AS max_date,
    DATEDIFF(DAY, MAX(TRY_TO_DATE(DATA_DATE)), CURRENT_DATE()) AS days_stale
  FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
  
  UNION ALL
  
  SELECT 
    'Silver' AS layer,
    MAX(DATE) AS max_date,
    DATEDIFF(DAY, MAX(DATE), CURRENT_DATE()) AS days_stale
  FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
  
  UNION ALL
  
  SELECT 
    'Gold' AS layer,
    MAX(DATE) AS max_date,
    DATEDIFF(DAY, MAX(DATE), CURRENT_DATE()) AS days_stale
  FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
),
regression_004 AS (
  SELECT 
    'REGR-004' AS test_id,
    'Data freshness check - ' || layer AS test_name,
    layer,
    max_date,
    days_stale,
    CASE 
      WHEN days_stale > 2 THEN 'STALE'
      ELSE 'FRESH'
    END AS status
  FROM data_freshness
)

-- =============================================================================
-- FINAL OUTPUT: All Regression Test Results
-- =============================================================================

SELECT test_id, test_name, load_date AS detail, NULL AS metric1, NULL AS metric2, status 
FROM regression_001 
WHERE status != 'STABLE'

UNION ALL

SELECT test_id, test_name, week_start AS detail, curr_eng_per_acct AS metric1, prev_eng_per_acct AS metric2, status 
FROM regression_002 
WHERE status != 'STABLE'

UNION ALL

SELECT test_id, test_name, DATE || ' | ' || REGION AS detail, user_var_pct AS metric1, usage_var_pct AS metric2, status 
FROM regression_003 
WHERE status != 'CONSISTENT'

UNION ALL

SELECT test_id, test_name, layer AS detail, days_stale AS metric1, NULL AS metric2, status 
FROM regression_004 
WHERE status != 'FRESH';

-- ✅ PASS CONDITION: Query returns 0 rows
-- ❌ FAIL CONDITION: Query returns 1+ rows with regression details
-- 
-- EXECUTION SCHEDULE: Run daily at 6 AM UTC after nightly ETL completion
```

---

## 📦 FILE 6: `TEST_RUNBOOK.md`

```markdown
# 🧪 TEST RUNBOOK: FTL to PI Migration
## Complete Test Execution Guide

---

## 📋 OVERVIEW

| Item | Details |
|------|---------|
| **Project** | FTL to PI Migration |
| **Models** | Bronze → Silver (slv_ftl_agent_base_agg) → Gold (gld_aggregate_new) |
| **Test Files** | 6 total (unit, functional, gold equivalence, schema, regression, runbook) |
| **Total Tests** | 45 test cases |
| **Owner** | Data Engineering Team |
| **Last Updated** | 2026-06-05 |

---

## 🎯 TEST EXECUTION ORDER

### Phase 1: Pre-Deployment Validation (Development Environment)

**STEP 1: Unit Tests**
```bash
# Execute unit test suite
snowsql -c dev_connection -f tests/unit/unit_tests.sql -o output_format=csv > unit_test_results.csv

# Expected result: 0 rows returned = ALL TESTS PASS
# If failures: Review failure_count and test_name columns
```

**Purpose**: Validate all 14 business rule transformations (BR-001 to BR-014) + 2 gap validations (GAP-023, GAP-024)

**Pass Condition**: Query returns 0 rows

**Failure Actions**:
- **BR-001 to BR-014 failures**: Notify Data Engineering Team — fix transformation logic in `slv_ftl_agent_base_agg.sql`
- **GAP-023 or GAP-024 failures**: Notify BDP Team — validate Bronze data completeness

---

**STEP 2: Functional Tests**
```bash
# Execute functional test suite
snowsql -c dev_connection -f tests/functional/functional_tests.sql -o output_format=csv > functional_test_results.csv

# Expected result: 0 rows returned = ALL TESTS PASS
```

**Purpose**: Validate data quality, completeness, and referential integrity

**Pass Condition**: Query returns 0 rows (or only FUNC-008 with warnings)

**Failure Actions**:
- **FUNC-001 (Row Count)**: Investigate missing rows in Silver layer
- **FUNC-002 (PK Unique)**: Deduplicate Silver layer — check incremental logic
- **FUNC-003 (NOT NULL)**: Fix NULL handling in Bronze source or transformation
- **FUNC-004 (DIRECTION)**: Review UPPER() transformation
- **FUNC-005 (CHANNEL)**: Review channel consolidation CASE logic
- **FUNC-006 (Metrics)**: Investigate negative values — data quality issue in Bronze
- **FUNC-007 (Date Range)**: Investigate date parsing errors
- **FUNC-008 (REGION UNKNOWN)**: ⚠️ **WARNING ONLY** — Notify BDP Team for cluster registry update

---

**STEP 3: dbt Schema Tests**
```bash
# Execute dbt tests
dbt test --select slv_ftl_agent_base_agg --profiles-dir ./profiles

# Expected result: All tests pass
```

**Purpose**: Run 18 dbt schema tests defined in YAML file

**Pass Condition**: All tests pass (0 failures)

**Failure Actions**:
- Review dbt test output for specific column/test failures
- Common failures:
  - `not_null`: NULL values in critical dimensions
  - `accepted_values`: Unexpected values in controlled vocabularies
  - `unique_combination_of_columns`: Duplicate primary keys
  - `expression_is_true`: Business rule violations

---

### Phase 2: Pre-Production Validation (Staging Environment)

**STEP 4: Gold Equivalence Test**
```bash
# Execute Gold equivalence test (compare FTL vs Legacy PI)
snowsql -c staging_connection -f tests/functional/gold_equivalence_test.sql -o output_format=csv > gold_equivalence_results.csv

# Expected result: 0 rows returned = EQUIVALENCE ACHIEVED
```

**Purpose**: Validate FTL Gold layer produces equivalent results to leg