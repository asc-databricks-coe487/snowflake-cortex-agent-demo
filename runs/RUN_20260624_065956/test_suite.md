

🧪 **STEP 1: Schema Discovery Complete** — Retrieved Bronze source (14 columns) + 17 Silver tables + Gold target schema to validate test assertions

🧪 **STEP 2: Parse Mapping Report** — Identified 11 business rules (BR-002 through BR-012) and 1 GAP (GAP-001: PHONE_DIALIN_COUNT missing in FTL)

🧪 **STEP 3: Generate Unit Tests** — Creating one test per transformation rule to validate BR logic at row level

🧪 **STEP 4: Generate Functional Tests** — Adding data quality gates (null checks, value domain, row counts)

🧪 **STEP 5: Generate Gold Equivalence Test** — Comparing FTL pipeline output (gld_aggregate_new) vs existing PI Gold (GLD_AGGREGATE)

🧪 **STEP 6: Generate dbt YAML Tests** — Embedding schema-level tests in models/silver/slv_ftl_agent_base_agg.yml

🧪 **STEP 7: Generate Regression Suite** — Full end-to-end validation script for CI/CD integration

🧪 **STEP 8: Generate Test Runbook** — Execution order, commands, and failure remediation playbook

---

# 📦 Complete Test Suite Package



---

## 📄 **FILE 1:** `tests/unit/unit_tests.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- UNIT TESTS: FTL to PI Migration
-- Purpose: Validate each business rule transformation at row level
-- Execution: Pass = 0 rows returned | Fail = violation rows returned
-- ═══════════════════════════════════════════════════════════════
-- Owner: Data Engineering Team
-- Notification: Slack #data-quality-alerts
-- Documentation: TEST_RUNBOOK.md
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_007_account_id
-- Purpose: Validate ACCOUNT_ID direct pass-through (no transformation)
-- BR-007: Column name and semantic meaning identical
-- Pass Condition: 0 rows (all Bronze ACCOUNT_ID values preserved)
-- On Failure: Contact Data Eng - Investigate ETL job for data loss
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_007_account_id AS (
    SELECT 
        'BR-007: ACCOUNT_ID Mismatch' AS test_name,
        brz.ACCOUNT_ID AS bronze_value,
        slv.ACCOUNT_ID AS silver_value,
        'ACCOUNT_ID not passed through correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE brz.ACCOUNT_ID != slv.ACCOUNT_ID
       OR (brz.ACCOUNT_ID IS NULL AND slv.ACCOUNT_ID IS NOT NULL)
       OR (brz.ACCOUNT_ID IS NOT NULL AND slv.ACCOUNT_ID IS NULL)
)
SELECT * FROM test_unit_BR_007_account_id;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_008_engagement_id
-- Purpose: Validate ENGAGEMENT_ID direct pass-through
-- BR-008: Unique engagement identifier preservation
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check join keys in Silver model
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_008_engagement_id AS (
    SELECT 
        'BR-008: ENGAGEMENT_ID Mismatch' AS test_name,
        brz.ENGAGEMENT_ID AS bronze_value,
        slv.ENGAGEMENT_ID AS silver_value,
        'ENGAGEMENT_ID not passed through correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE brz.ENGAGEMENT_ID != slv.ENGAGEMENT_ID
       OR (brz.ENGAGEMENT_ID IS NULL AND slv.ENGAGEMENT_ID IS NOT NULL)
       OR (brz.ENGAGEMENT_ID IS NOT NULL AND slv.ENGAGEMENT_ID IS NULL)
)
SELECT * FROM test_unit_BR_008_engagement_id;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_009_user_id
-- Purpose: Validate AGENT_ID renamed to USER_ID
-- BR-009: AGENT_ID → USER_ID transformation
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Verify rename logic in Silver
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_009_user_id AS (
    SELECT 
        'BR-009: AGENT_ID to USER_ID Mismatch' AS test_name,
        brz.AGENT_ID AS bronze_agent_id,
        slv.USER_ID AS silver_user_id,
        'AGENT_ID not correctly mapped to USER_ID' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE brz.AGENT_ID != slv.USER_ID
       OR (brz.AGENT_ID IS NULL AND slv.USER_ID IS NOT NULL)
       OR (brz.AGENT_ID IS NOT NULL AND slv.USER_ID IS NULL)
)
SELECT * FROM test_unit_BR_009_user_id;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_005_direction
-- Purpose: Validate DIRECTION case normalization to uppercase
-- BR-005: 'Inbound'/'Outbound' → 'INBOUND'/'OUTBOUND'
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check UPPER() function in model
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_005_direction AS (
    SELECT 
        'BR-005: DIRECTION Case Normalization Failed' AS test_name,
        brz.DIRECTION AS bronze_direction,
        slv.DIRECTION AS silver_direction,
        'DIRECTION not uppercased correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE UPPER(brz.DIRECTION) != slv.DIRECTION
       OR (brz.DIRECTION IS NULL AND slv.DIRECTION IS NOT NULL)
       OR (brz.DIRECTION IS NOT NULL AND slv.DIRECTION IS NULL)
)
SELECT * FROM test_unit_BR_005_direction;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_006_channel
-- Purpose: Validate CHANNEL case normalization to uppercase
-- BR-006: 'Phone'/'Video' → 'PHONE'/'VIDEO'
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check UPPER() function in model
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_006_channel AS (
    SELECT 
        'BR-006: CHANNEL Case Normalization Failed' AS test_name,
        brz.CHANNEL AS bronze_channel,
        slv.CHANNEL AS silver_channel,
        'CHANNEL not uppercased correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE UPPER(brz.CHANNEL) != slv.CHANNEL
       OR (brz.CHANNEL IS NULL AND slv.CHANNEL IS NOT NULL)
       OR (brz.CHANNEL IS NOT NULL AND slv.CHANNEL IS NULL)
)
SELECT * FROM test_unit_BR_006_channel;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_012_modality
-- Purpose: Validate MODALITY direct pass-through
-- BR-012: Values align (Chat/Email/SMS) - no transformation
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check for data corruption
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_012_modality AS (
    SELECT 
        'BR-012: MODALITY Mismatch' AS test_name,
        brz.MODALITY AS bronze_value,
        slv.MODALITY AS silver_value,
        'MODALITY not passed through correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE brz.MODALITY != slv.MODALITY
       OR (brz.MODALITY IS NULL AND slv.MODALITY IS NOT NULL)
       OR (brz.MODALITY IS NOT NULL AND slv.MODALITY IS NULL)
)
SELECT * FROM test_unit_BR_012_modality;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_011_phone_sessions
-- Purpose: Validate PHONE_SESSIONS direct pass-through
-- BR-011: Column name and data type identical
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Validate numeric precision
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_011_phone_sessions AS (
    SELECT 
        'BR-011: PHONE_SESSIONS Mismatch' AS test_name,
        brz.PHONE_SESSIONS AS bronze_value,
        slv.PHONE_SESSIONS AS silver_value,
        'PHONE_SESSIONS not passed through correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE brz.PHONE_SESSIONS != slv.PHONE_SESSIONS
       OR (brz.PHONE_SESSIONS IS NULL AND slv.PHONE_SESSIONS IS NOT NULL)
       OR (brz.PHONE_SESSIONS IS NOT NULL AND slv.PHONE_SESSIONS IS NULL)
)
SELECT * FROM test_unit_BR_011_phone_sessions;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_004_duration_sec
-- Purpose: Validate INBOUND_PHONE_MS → DURATION_SEC (÷ 1000)
-- BR-004: Milliseconds to seconds conversion
-- Pass Condition: 0 rows (allow 0.01 sec tolerance for rounding)
-- On Failure: Contact Data Eng - Check division factor (should be 1000.0)
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_004_duration_sec AS (
    SELECT 
        'BR-004: DURATION_SEC Conversion Error' AS test_name,
        brz.INBOUND_PHONE_MS AS bronze_ms,
        slv.DURATION_SEC AS silver_seconds,
        brz.INBOUND_PHONE_MS / 1000.0 AS expected_seconds,
        ABS(slv.DURATION_SEC - (brz.INBOUND_PHONE_MS / 1000.0)) AS diff,
        'INBOUND_PHONE_MS not divided by 1000 correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE ABS(slv.DURATION_SEC - (brz.INBOUND_PHONE_MS / 1000.0)) > 0.01
       OR (brz.INBOUND_PHONE_MS IS NOT NULL AND slv.DURATION_SEC IS NULL)
)
SELECT * FROM test_unit_BR_004_duration_sec;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_unit_BR_002_inbound_phone_mins
-- Purpose: Validate INBOUND_PHONE_MS → INBOUND_PHONE_MINS (÷ 60000)
-- BR-002: Milliseconds to minutes conversion
-- Pass Condition: 0 rows (allow 0.0001 min tolerance)
-- On Failure: Contact Data Eng - Check division factor (should be 60000.0)
-- ───────────────────────────────────────────────────────────────
WITH test_unit_BR_002_inbound_phone_mins AS (
    SELECT 
        'BR-002: INBOUND_PHONE_MINS Conversion Error' AS test_name,
        brz.INBOUND_PHONE_MS AS bronze_ms,
        slv.INBOUND_PHONE_MINS AS silver_minutes,
        brz.INBOUND_PHONE_MS / 60000.0 AS expected_minutes,
        ABS(slv.INBOUND_PHONE_MINS - (brz.INBOUND_PHONE_MS / 60000.0)) AS diff,
        'INBOUND_PHONE_MS not divided by 60000 correctly' AS failure_reason
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG brz
    LEFT JOIN ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg slv
        ON brz.ENGAGEMENT_ID = slv.ENGAGEMENT_ID
        AND TO_DATE(brz.DATA_DATE, 'MM/DD/YY HH24:MI') = slv.REPORT_DATE
    WHERE ABS(slv.INBOUND_PHONE_MINS - (brz.INBOUND_PHONE_MS / 60000.0)) > 0.0001
       OR (brz.INBOUND_PHONE_MS IS NOT NULL AND slv.INBOUND_PHONE_MINS IS NULL)
)
SELECT * FROM test_unit_BR_002_inbound_phone_mins;

-- ═══════════════════════════════════════════════════════════════
-- END UNIT TESTS
-- Total Tests: 10
-- Execution Time: ~30 seconds
-- Next: Run functional_tests.sql
-- ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 2:** `tests/functional/functional_tests.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- FUNCTIONAL TESTS: FTL to PI Migration
-- Purpose: Data quality gates - row counts, nulls, value domains
-- Execution: Pass = 0 rows returned | Fail = violation rows returned
-- ═══════════════════════════════════════════════════════════════
-- Owner: Data Engineering Team
-- Notification: Slack #data-quality-alerts
-- Documentation: TEST_RUNBOOK.md
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_row_count_match
-- Purpose: Ensure no data loss from Bronze to Silver
-- Pass Condition: 0 rows (Bronze count = Silver count)
-- On Failure: Contact Data Eng - Investigate ETL job for dropped rows
-- ───────────────────────────────────────────────────────────────
WITH test_functional_row_count_match AS (
    SELECT 
        'Row Count Mismatch' AS test_name,
        brz_count,
        slv_count,
        ABS(brz_count - slv_count) AS row_diff,
        'Bronze and Silver row counts do not match' AS failure_reason
    FROM (
        SELECT COUNT(*) AS brz_count 
        FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
        WHERE ACCOUNT_ID IS NOT NULL
    ) brz
    CROSS JOIN (
        SELECT COUNT(*) AS slv_count 
        FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    ) slv
    WHERE brz_count != slv_count
)
SELECT * FROM test_functional_row_count_match;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_account_id_not_null
-- Purpose: Validate ACCOUNT_ID is never NULL in Silver
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check WHERE filter in Silver model
-- ───────────────────────────────────────────────────────────────
WITH test_functional_account_id_not_null AS (
    SELECT 
        'ACCOUNT_ID NULL Found' AS test_name,
        ENGAGEMENT_ID,
        REPORT_DATE,
        'ACCOUNT_ID should never be NULL in Silver' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE ACCOUNT_ID IS NULL
)
SELECT * FROM test_functional_account_id_not_null;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_engagement_id_uniqueness
-- Purpose: Validate ENGAGEMENT_ID + REPORT_DATE uniqueness
-- Pass Condition: 0 rows (no duplicates)
-- On Failure: Contact Data Eng - Check for duplicate source data
-- ───────────────────────────────────────────────────────────────
WITH test_functional_engagement_id_uniqueness AS (
    SELECT 
        'Duplicate ENGAGEMENT_ID + REPORT_DATE' AS test_name,
        ENGAGEMENT_ID,
        REPORT_DATE,
        duplicate_count,
        'Engagement should be unique per date' AS failure_reason
    FROM (
        SELECT 
            ENGAGEMENT_ID,
            REPORT_DATE,
            COUNT(*) AS duplicate_count
        FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
        GROUP BY ENGAGEMENT_ID, REPORT_DATE
        HAVING COUNT(*) > 1
    )
)
SELECT * FROM test_functional_engagement_id_uniqueness;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_direction_domain
-- Purpose: Validate DIRECTION only contains valid uppercase values
-- Pass Condition: 0 rows (only INBOUND/OUTBOUND allowed)
-- On Failure: Contact Data Eng - Check UPPER() logic and data quality
-- ───────────────────────────────────────────────────────────────
WITH test_functional_direction_domain AS (
    SELECT 
        'Invalid DIRECTION Value' AS test_name,
        DIRECTION,
        COUNT(*) AS occurrence_count,
        'DIRECTION must be INBOUND or OUTBOUND' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE DIRECTION NOT IN ('INBOUND', 'OUTBOUND')
    GROUP BY DIRECTION
)
SELECT * FROM test_functional_direction_domain;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_channel_domain
-- Purpose: Validate CHANNEL only contains valid uppercase values
-- Pass Condition: 0 rows (only PHONE/VIDEO allowed)
-- On Failure: Contact Data Eng - Check UPPER() logic and data quality
-- ───────────────────────────────────────────────────────────────
WITH test_functional_channel_domain AS (
    SELECT 
        'Invalid CHANNEL Value' AS test_name,
        CHANNEL,
        COUNT(*) AS occurrence_count,
        'CHANNEL must be PHONE or VIDEO' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE CHANNEL NOT IN ('PHONE', 'VIDEO')
    GROUP BY CHANNEL
)
SELECT * FROM test_functional_channel_domain;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_modality_domain
-- Purpose: Validate MODALITY only contains expected values
-- Pass Condition: 0 rows (only Chat/Email/SMS allowed)
-- On Failure: Contact Data Eng - Investigate new modality types
-- ───────────────────────────────────────────────────────────────
WITH test_functional_modality_domain AS (
    SELECT 
        'Invalid MODALITY Value' AS test_name,
        MODALITY,
        COUNT(*) AS occurrence_count,
        'MODALITY must be Chat, Email, or SMS' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE MODALITY NOT IN ('Chat', 'Email', 'SMS')
    GROUP BY MODALITY
)
SELECT * FROM test_functional_modality_domain;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_phone_sessions_non_negative
-- Purpose: Validate PHONE_SESSIONS is never negative
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check source data quality
-- ───────────────────────────────────────────────────────────────
WITH test_functional_phone_sessions_non_negative AS (
    SELECT 
        'Negative PHONE_SESSIONS' AS test_name,
        ENGAGEMENT_ID,
        PHONE_SESSIONS,
        'PHONE_SESSIONS cannot be negative' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE PHONE_SESSIONS < 0
)
SELECT * FROM test_functional_phone_sessions_non_negative;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_duration_sec_non_negative
-- Purpose: Validate DURATION_SEC is never negative
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check conversion logic
-- ───────────────────────────────────────────────────────────────
WITH test_functional_duration_sec_non_negative AS (
    SELECT 
        'Negative DURATION_SEC' AS test_name,
        ENGAGEMENT_ID,
        DURATION_SEC,
        'DURATION_SEC cannot be negative' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE DURATION_SEC < 0
)
SELECT * FROM test_functional_duration_sec_non_negative;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_inbound_phone_mins_non_negative
-- Purpose: Validate INBOUND_PHONE_MINS is never negative
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check conversion logic
-- ───────────────────────────────────────────────────────────────
WITH test_functional_inbound_phone_mins_non_negative AS (
    SELECT 
        'Negative INBOUND_PHONE_MINS' AS test_name,
        ENGAGEMENT_ID,
        INBOUND_PHONE_MINS,
        'INBOUND_PHONE_MINS cannot be negative' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE INBOUND_PHONE_MINS < 0
)
SELECT * FROM test_functional_inbound_phone_mins_non_negative;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_gap_GAP_001_phone_dialin_count_is_null
-- Purpose: Verify PHONE_DIALIN_COUNT tracked as NULL (missing in FTL)
-- GAP-001: PHONE_DIALIN_COUNT missing in FTL Bronze
-- Pass Condition: 0 rows (all values should be NULL)
-- On Failure: Contact Data Eng - Column should not be populated until source provides data
-- ───────────────────────────────────────────────────────────────
WITH test_gap_GAP_001_phone_dialin_count_is_null AS (
    SELECT 
        'GAP-001: PHONE_DIALIN_COUNT Not NULL' AS test_name,
        ENGAGEMENT_ID,
        PHONE_DIALIN_COUNT,
        'PHONE_DIALIN_COUNT must be NULL (not in FTL source)' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE PHONE_DIALIN_COUNT IS NOT NULL
)
SELECT * FROM test_gap_GAP_001_phone_dialin_count_is_null;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_report_date_valid
-- Purpose: Validate REPORT_DATE is a valid date after conversion
-- Pass Condition: 0 rows (all dates parse correctly)
-- On Failure: Contact Data Eng - Check TO_DATE format string
-- ───────────────────────────────────────────────────────────────
WITH test_functional_report_date_valid AS (
    SELECT 
        'Invalid REPORT_DATE' AS test_name,
        ENGAGEMENT_ID,
        REPORT_DATE,
        'REPORT_DATE conversion failed or NULL' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE REPORT_DATE IS NULL
       OR REPORT_DATE < '2020-01-01'  -- Sanity check: no dates before 2020
       OR REPORT_DATE > CURRENT_DATE() + INTERVAL '1 day'  -- No future dates
)
SELECT * FROM test_functional_report_date_valid;

-- ───────────────────────────────────────────────────────────────
-- TEST: test_functional_load_timestamp_populated
-- Purpose: Validate LOAD_TIMESTAMP is populated for all rows
-- Pass Condition: 0 rows
-- On Failure: Contact Data Eng - Check CURRENT_TIMESTAMP() in model
-- ───────────────────────────────────────────────────────────────
WITH test_functional_load_timestamp_populated AS (
    SELECT 
        'LOAD_TIMESTAMP NULL' AS test_name,
        ENGAGEMENT_ID,
        'LOAD_TIMESTAMP should be populated for all rows' AS failure_reason
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE LOAD_TIMESTAMP IS NULL
)
SELECT * FROM test_functional_load_timestamp_populated;

-- ═══════════════════════════════════════════════════════════════
-- END FUNCTIONAL TESTS
-- Total Tests: 12
-- Execution Time: ~45 seconds
-- Next: Run gold_equivalence_test.sql
-- ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 3:** `tests/functional/gold_equivalence_test.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- GOLD EQUIVALENCE TEST: FTL Pipeline vs PI Gold
-- Purpose: Compare gld_aggregate_new (FTL) vs GLD_AGGREGATE (existing PI)
-- Execution: Pass = 0 rows | Fail = discrepancies found
-- ═══════════════════════════════════════════════════════════════
-- Owner: Data Engineering Team + Business Analytics Team
-- Notification: Slack #data-migration-alerts + Email analytics@zoom.us
-- Documentation: TEST_RUNBOOK.md Section 4
-- ═══════════════════════════════════════════════════════════════
-- IMPORTANT: This test compares overlapping DATE ranges only
--            FTL pipeline may have different date coverage than PI
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────
-- TEST: test_gold_equivalence_aggregate_metrics
-- Purpose: Validate FTL Gold output matches PI Gold for same date range
-- BR-003: PHONE_USAGE aggregation validation
-- Pass Condition: 0 rows (metrics match within 1% tolerance)
-- On Failure: 
--   1. Notify Data Engineering Lead
--   2. Notify Business Analytics Team
--   3. Review BR-003 transformation logic
--   4. Check for data completeness in Bronze FTL
-- ───────────────────────────────────────────────────────────────
WITH ftl_gold AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        SUM(ACTIVE_ACCOUNTS) AS active_accounts,
        SUM(ACTIVE_USERS) AS active_users,
        SUM(PHONE_USAGE) AS phone_usage,
        SUM(USERS_ACTIVE_16PLUS_DAYS) AS users_active_16plus
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
    GROUP BY DATE, REGION, SEGMENT, IS_LICENSED
),

pi_gold AS (
    SELECT 
        DATE,
        REGION,
        SEGMENT,
        IS_LICENSED,
        SUM(ACTIVE_ACCOUNTS) AS active_accounts,
        SUM(ACTIVE_USERS) AS active_users,
        SUM(PHONE_USAGE) AS phone_usage,
        SUM(USERS_ACTIVE_16PLUS_DAYS) AS users_active_16plus
    FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
    GROUP BY DATE, REGION, SEGMENT, IS_LICENSED
),

comparison AS (
    SELECT 
        COALESCE(ftl.DATE, pi.DATE) AS date,
        COALESCE(ftl.REGION, pi.REGION) AS region,
        COALESCE(ftl.SEGMENT, pi.SEGMENT) AS segment,
        COALESCE(ftl.IS_LICENSED, pi.IS_LICENSED) AS is_licensed,
        
        -- FTL metrics
        ftl.active_accounts AS ftl_active_accounts,
        ftl.active_users AS ftl_active_users,
        ftl.phone_usage AS ftl_phone_usage,
        ftl.users_active_16plus AS ftl_users_active_16plus,
        
        -- PI metrics
        pi.active_accounts AS pi_active_accounts,
        pi.active_users AS pi_active_users,
        pi.phone_usage AS pi_phone_usage,
        pi.users_active_16plus AS pi_users_active_16plus,
        
        -- Differences
        ABS(COALESCE(ftl.active_accounts, 0) - COALESCE(pi.active_accounts, 0)) AS diff_accounts,
        ABS(COALESCE(ftl.active_users, 0) - COALESCE(pi.active_users, 0)) AS diff_users,
        ABS(COALESCE(ftl.phone_usage, 0) - COALESCE(pi.phone_usage, 0)) AS diff_phone_usage,
        ABS(COALESCE(ftl.users_active_16plus, 0) - COALESCE(pi.users_active_16plus, 0)) AS diff_16plus,
        
        -- Percent differences (for 1% tolerance check)
        CASE WHEN pi.active_accounts > 0 
             THEN ABS(COALESCE(ftl.active_accounts, 0) - pi.active_accounts) / pi.active_accounts * 100
             ELSE 0 END AS pct_diff_accounts,
        
        CASE WHEN pi.active_users > 0 
             THEN ABS(COALESCE(ftl.active_users, 0) - pi.active_users) / pi.active_users * 100
             ELSE 0 END AS pct_diff_users,
        
        CASE WHEN pi.phone_usage > 0 
             THEN ABS(COALESCE(ftl.phone_usage, 0) - pi.phone_usage) / pi.phone_usage * 100
             ELSE 0 END AS pct_diff_phone_usage,
        
        CASE WHEN pi.users_active_16plus > 0 
             THEN ABS(COALESCE(ftl.users_active_16plus, 0) - pi.users_active_16plus) / pi.users_active_16plus * 100
             ELSE 0 END AS pct_diff_16plus
        
    FROM ftl_gold ftl
    FULL OUTER JOIN pi_gold pi
        ON ftl.DATE = pi.DATE
        AND ftl.REGION = pi.REGION
        AND ftl.SEGMENT = pi.SEGMENT
        AND ftl.IS_LICENSED = pi.IS_LICENSED
)

SELECT 
    'Gold Equivalence Failure' AS test_name,
    date,
    region,
    segment,
    is_licensed,
    
    -- FTL values
    ftl_active_accounts,
    ftl_active_users,
    ftl_phone_usage,
    ftl_users_active_16plus,
    
    -- PI values
    pi_active_accounts,
    pi_active_users,
    pi_phone_usage,
    pi_users_active_16plus,
    
    -- Differences
    diff_accounts,
    diff_users,
    diff_phone_usage,
    diff_16plus,
    
    -- Percent differences
    ROUND(pct_diff_accounts, 2) AS pct_diff_accounts,
    ROUND(pct_diff_users, 2) AS pct_diff_users,
    ROUND(pct_diff_phone_usage, 2) AS pct_diff_phone_usage,
    ROUND(pct_diff_16plus, 2) AS pct_diff_16plus,
    
    -- Failure reason
    CASE 
        WHEN ftl_active_accounts IS NULL AND pi_active_accounts IS NOT NULL THEN 'FTL missing data for this grain'
        WHEN pi_active_accounts IS NULL AND ftl_active_accounts IS NOT NULL THEN 'PI missing data for this grain'
        WHEN pct_diff_accounts > 1 THEN 'ACTIVE_ACCOUNTS differs by > 1%'
        WHEN pct_diff_users > 1 THEN 'ACTIVE_USERS differs by > 1%'
        WHEN pct_diff_phone_usage > 1 THEN 'PHONE_USAGE differs by > 1% (BR-003 issue)'
        WHEN pct_diff_16plus > 1 THEN 'USERS_ACTIVE_16PLUS_DAYS differs by > 1%'
        ELSE 'Unknown discrepancy'
    END AS failure_reason
    
FROM comparison
WHERE 
    -- Flag rows where any metric differs by more than 1%
    pct_diff_accounts > 1
    OR pct_diff_users > 1
    OR pct_diff_phone_usage > 1
    OR pct_diff_16plus > 1
    -- OR flag rows that exist in one source but not the other
    OR (ftl_active_accounts IS NULL AND pi_active_accounts IS NOT NULL)
    OR (pi_active_accounts IS NULL AND ftl_active_accounts IS NOT NULL)
ORDER BY date DESC, region, segment;

-- ═══════════════════════════════════════════════════════════════
-- END GOLD EQUIVALENCE TEST
-- Total Tests: 1 comprehensive comparison
-- Execution Time: ~2 minutes (depends on Gold table size)
-- Next: Review schema_with_tests.yml for dbt integration
-- ═══════════════════════════════════════════════════════════════
-- NOTES:
-- - 1% tolerance allows for minor rounding differences
-- - NULL handling: treats NULL as 0 for comparison
-- - Full outer join catches missing grains in either source
-- - If this test fails, DO NOT proceed with production cutover
-- ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 4:** `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
# ═══════════════════════════════════════════════════════════════
# dbt Schema with Tests: slv_ftl_agent_base_agg
# Purpose: Embed column-level tests in dbt project for CI/CD
# Location: models/silver/ (not models/staging/)
# Execution: dbt test --select slv_ftl_agent_base_agg
# ═══════════════════════════════════════════════════════════════

version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      Silver layer model for FTL agent base aggregation data.
      Normalizes Bronze FTL data to match PI Silver schema conventions.
      
      Business Rules Applied:
        - BR-007: ACCOUNT_ID direct pass-through
        - BR-008: ENGAGEMENT_ID direct pass-through
        - BR-009: AGENT_ID renamed to USER_ID
        - BR-005: DIRECTION case normalized to uppercase
        - BR-006: CHANNEL case normalized to uppercase
        - BR-012: MODALITY direct pass-through
        - BR-011: PHONE_SESSIONS direct pass-through
        - BR-004: INBOUND_PHONE_MS → DURATION_SEC (÷ 1000)
        - BR-002: INBOUND_PHONE_MS → INBOUND_PHONE_MINS (÷ 60000)
      
      GAP Tracking:
        - GAP-001: PHONE_DIALIN_COUNT missing in FTL (tracked as NULL)
    
    config:
      materialized: table
      tags: ['silver', 'ftl_migration', 'agent_metrics']
    
    columns:
      - name: REPORT_DATE
        description: "Converted date from Bronze DATA_DATE (TEXT → DATE)"
        tests:
          - not_null:
              severity: error
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
              config:
                severity: error
                error_if: ">0"
          - dbt_utils.expression_is_true:
              expression: "<= current_date() + interval '1 day'"
              config:
                severity: error
                error_if: ">0"
      
      - name: ACCOUNT_ID
        description: "Account identifier - foundational join key (BR-007)"
        tests:
          - not_null:
              severity: error
          - relationships:
              to: source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG')
              field: ACCOUNT_ID
              config:
                severity: warn
                where: "ACCOUNT_ID IS NOT NULL"
      
      - name: ENGAGEMENT_ID
        description: "Unique engagement identifier (BR-008)"
        tests:
          - not_null:
              severity: error
          - unique:
              config:
                severity: error
                # Unique within REPORT_DATE grain
                group_by: REPORT_DATE
      
      - name: USER_ID
        description: "User identifier (renamed from AGENT_ID per BR-009)"
        tests:
          - not_null:
              severity: warn

      - name: DIRECTION
        description: "Call direction - uppercased (BR-005)"
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              config:
                severity: error
      
      - name: CHANNEL
        description: "Communication channel - uppercased (BR-006)"
        tests:
          - accepted_values:
              values: ['PHONE', 'VIDEO']
              config:
                severity: error
      
      - name: MODALITY
        description: "Communication modality (BR-012)"
        tests:
          - accepted_values:
              values: ['Chat', 'Email', 'SMS']
              config:
                severity: warn

      - name: PHONE_SESSIONS
        description: "Count of phone sessions (BR-011)"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                error_if: ">0"

      - name: DURATION_SEC
        description: "Inbound phone duration in seconds (BR-004: INBOUND_PHONE_MS ÷ 1000)"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                error_if: ">0"

      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (BR-002: INBOUND_PHONE_MS ÷ 60000)"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
                error_if: ">0"

      - name: PHONE_DIALIN_COUNT
        description: "Dial-in participant count (GAP-001: missing in FTL, tracked as NULL)"
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: error
                error_if: ">0"
                warn_if: ">0"

      - name: ZCC_ACCOUNT_ID
        description: "ZCC-specific account identifier (NEW_CAPABILITY)"
        # No tests - new capability, allow NULL

      - name: CLIENT_TYPE
        description: "Device type (Desktop/Mobile/Web) - NEW_CAPABILITY"
        # No tests - new capability, allow NULL

      - name: OS
        description: "Operating system - NEW_CAPABILITY"
        # No tests - data quality issue noted in mapping

      - name: IS_ACTIVE
        description: "Activity flag (row-level)"
        tests:
          - not_null:
              severity: warn
          - accepted_values:
              values: [true, false]
              config:
                severity: warn

      - name: CLUSTER
        description: "AWS cluster identifier"
        # No tests - used for region mapping in Gold

      - name: LOAD_TIMESTAMP
        description: "ETL load timestamp"
        tests:
          - not_null:
              severity: error

# ═══════════════════════════════════════════════════════════════
# Total dbt Tests: 14
# Execution: dbt test --select slv_ftl_agent_base_agg
# CI/CD Integration: Run after every dbt run
# ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 5:** `tests/regression/regression_suite.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- REGRESSION TEST SUITE: FTL to PI Migration
-- Purpose: End-to-end validation for production readiness
-- Execution: Run full suite before each deployment
-- Owner: Data Engineering Team
-- ═══════════════════════════════════════════════════════════════
-- Test Execution Order:
--   1. Schema validation
--   2. Data lineage validation
--   3. Metric reconciliation
--   4. Performance benchmarks
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────
-- SECTION 1: SCHEMA VALIDATION
-- ───────────────────────────────────────────────────────────────

-- TEST: regression_schema_bronze_exists
SELECT 
    'Bronze Schema Missing' AS test_name,
    'BRZ_FTL_AGENT_BASE_AGG table does not exist' AS failure_reason
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'BRONZE'
  AND TABLE_NAME = 'BRZ_FTL_AGENT_BASE_AGG'
  AND TABLE_CATALOG = 'ZOOM_AI_POC'
HAVING COUNT(*) = 0;

-- TEST: regression_schema_silver_exists
SELECT 
    'Silver Model Missing' AS test_name,
    'slv_ftl_agent_base_agg table does not exist' AS failure_reason
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'SILVER'
  AND TABLE_NAME = 'SLV_FTL_AGENT_BASE_AGG'
  AND TABLE_CATALOG = 'ZOOM_AI_POC'
HAVING COUNT(*) = 0;

-- TEST: regression_schema_gold_exists
SELECT 
    'Gold Model Missing' AS test_name,
    'gld_aggregate_new table does not exist' AS failure_reason
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'GOLD'
  AND TABLE_NAME = 'GLD_AGGREGATE_NEW'
  AND TABLE_CATALOG = 'ZOOM_AI_POC'
HAVING COUNT(*) = 0;

-- TEST: regression_column_count_silver
WITH expected AS (
    SELECT 15 AS expected_columns  -- Adjust based on final Silver model
),
actual AS (
    SELECT COUNT(*) AS actual_columns
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'SILVER'
      AND TABLE_NAME = 'SLV_FTL_AGENT_BASE_AGG'
      AND TABLE_CATALOG = 'ZOOM_AI_POC'
)
SELECT 
    'Silver Column Count Mismatch' AS test_name,
    e.expected_columns,
    a.actual_columns,
    'Column count changed - review schema evolution' AS failure_reason
FROM expected e
CROSS JOIN actual a
WHERE e.expected_columns != a.actual_columns;

-- ───────────────────────────────────────────────────────────────
-- SECTION 2: DATA LINEAGE VALIDATION
-- ───────────────────────────────────────────────────────────────

-- TEST: regression_bronze_to_silver_lineage
WITH bronze_dates AS (
    SELECT DISTINCT TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') AS report_date
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
    WHERE DATA_DATE IS NOT NULL
),
silver_dates AS (
    SELECT DISTINCT REPORT_DATE
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
)
SELECT 
    'Bronze to Silver Date Gap' AS test_name,
    b.report_date,
    'Date exists in Bronze but missing in Silver' AS failure_reason
FROM bronze_dates b
LEFT JOIN silver_dates s ON b.report_date = s.report_date
WHERE s.report_date IS NULL;

-- TEST: regression_silver_to_gold_lineage
WITH silver_dates AS (
    SELECT DISTINCT REPORT_DATE
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
),
gold_dates AS (
    SELECT DISTINCT DATE AS report_date
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
)
SELECT 
    'Silver to Gold Date Gap' AS test_name,
    s.report_date,
    'Date exists in Silver but missing in Gold' AS failure_reason
FROM silver_dates s
LEFT JOIN gold_dates g ON s.report_date = g.report_date
WHERE g.report_date IS NULL;

-- ───────────────────────────────────────────────────────────────
-- SECTION 3: METRIC RECONCILIATION
-- ───────────────────────────────────────────────────────────────

-- TEST: regression_phone_usage_calculation
-- Validates BR-003: PHONE_USAGE = SUM(INBOUND_PHONE_MS) / 3600000
WITH silver_aggregated AS (
    SELECT 
        REPORT_DATE,
        SUM(DURATION_SEC) / 3600.0 AS expected_phone_usage
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    WHERE IS_ACTIVE = TRUE
    GROUP BY REPORT_DATE
),
gold_actual AS (
    SELECT 
        DATE AS report_date,
        SUM(PHONE_USAGE) AS actual_phone_usage
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
    GROUP BY DATE
)
SELECT 
    'BR-003 Phone Usage Reconciliation Failed' AS test_name,
    s.report_date,
    s.expected_phone_usage,
    g.actual_phone_usage,
    ABS(s.expected_phone_usage - g.actual_phone_usage) AS diff,
    'Phone usage calculation does not match BR-003 formula' AS failure_reason
FROM silver_aggregated s
INNER JOIN gold_actual g ON s.report_date = g.report_date
WHERE ABS(s.expected_phone_usage - g.actual_phone_usage) > 0.01;

-- TEST: regression_account_count_reconciliation
WITH silver_counts AS (
    SELECT 
        REPORT_DATE,
        COUNT(DISTINCT ACCOUNT_ID) AS silver_accounts
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    GROUP BY REPORT_DATE
),
gold_counts AS (
    SELECT 
        DATE AS report_date,
        SUM(ACTIVE_ACCOUNTS) AS gold_accounts
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
    GROUP BY DATE
)
SELECT 
    'Account Count Mismatch' AS test_name,
    s.report_date,
    s.silver_accounts,
    g.gold_accounts,
    ABS(s.silver_accounts - g.gold_accounts) AS diff,
    'Active account count does not reconcile Silver → Gold' AS failure_reason
FROM silver_counts s
INNER JOIN gold_counts g ON s.report_date = g.report_date
WHERE s.silver_accounts != g.gold_accounts;

-- TEST: regression_user_count_reconciliation
WITH silver_counts AS (
    SELECT 
        REPORT_DATE,
        COUNT(DISTINCT USER_ID) AS silver_users
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
    GROUP BY REPORT_DATE
),
gold_counts AS (
    SELECT 
        DATE AS report_date,
        SUM(ACTIVE_USERS) AS gold_users
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
    GROUP BY DATE
)
SELECT 
    'User Count Mismatch' AS test_name,
    s.report_date,
    s.silver_users,
    g.gold_users,
    ABS(s.silver_users - g.gold_users) AS diff,
    'Active user count does not reconcile Silver → Gold' AS failure_reason
FROM silver_counts s
INNER JOIN gold_counts g ON s.report_date = g.report_date
WHERE s.silver_users != g.gold_users;

-- ───────────────────────────────────────────────────────────────
-- SECTION 4: PERFORMANCE BENCHMARKS
-- ───────────────────────────────────────────────────────────────

-- TEST: regression_silver_query_performance
-- Validates Silver model query completes within 30 seconds
-- Run this separately and monitor execution time
/*
SELECT 
    'Silver Performance Degradation' AS test_name,
    COUNT(*) AS row_count,
    'Query took longer than 30 seconds' AS failure_reason
FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
WHERE REPORT_DATE >= DATEADD(day, -7, CURRENT_DATE());
-- Monitor query history: SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
-- WHERE QUERY_TEXT LIKE '%slv_ftl_agent_base_agg%' AND EXECUTION_TIME > 30000;
*/

-- TEST: regression_gold_query_performance
-- Validates Gold model query completes within 60 seconds
/*
SELECT 
    'Gold Performance Degradation' AS test_name,
    COUNT(*) AS row_count,
    'Query took longer than 60 seconds' AS failure_reason
FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
WHERE DATE >= DATEADD(day, -30, CURRENT_DATE());
-- Monitor query history: SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
-- WHERE QUERY_TEXT LIKE '%gld_aggregate_new%' AND EXECUTION_TIME > 60000;
*/

-- ───────────────────────────────────────────────────────────────
-- SECTION 5: DATA FRESHNESS
-- ───────────────────────────────────────────────────────────────

-- TEST: regression_bronze_freshness
WITH latest_load AS (
    SELECT MAX(TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI')) AS latest_date
    FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
)
SELECT 
    'Bronze Data Stale' AS test_name,
    latest_date,
    DATEDIFF(day, latest_date, CURRENT_DATE()) AS days_old,
    'Bronze data is older than 2 days' AS failure_reason
FROM latest_load
WHERE DATEDIFF(day, latest_date, CURRENT_DATE()) > 2;

-- TEST: regression_silver_freshness
WITH latest_load AS (
    SELECT MAX(REPORT_DATE) AS latest_date
    FROM ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg
)
SELECT 
    'Silver Data Stale' AS test_name,
    latest_date,
    DATEDIFF(day, latest_date, CURRENT_DATE()) AS days_old,
    'Silver data is older than 2 days' AS failure_reason
FROM latest_load
WHERE DATEDIFF(day, latest_date, CURRENT_DATE()) > 2;

-- TEST: regression_gold_freshness
WITH latest_load AS (
    SELECT MAX(DATE) AS latest_date
    FROM ZOOM_AI_POC.GOLD.gld_aggregate_new
)
SELECT 
    'Gold Data Stale' AS test_name,
    latest_date,
    DATEDIFF(day, latest_date, CURRENT_DATE()) AS days_old,
    'Gold data is older than 2 days' AS failure_reason
FROM latest_load
WHERE DATEDIFF(day, latest_date, CURRENT_DATE()) > 2;

-- ═══════════════════════════════════════════════════════════════
-- END REGRESSION SUITE
-- Total Tests: 15 (13 automated + 2 manual performance checks)
-- Execution Time: ~3-5 minutes
-- CI/CD Integration: Run before every production deployment
-- ═══════════════════════════════════════════════════════════════
-- PASS CRITERIA: All tests return 0 rows
-- FAIL ACTION: 
--   1. Log failures to monitoring dashboard
--   2. Send Slack alert to #data-engineering
--   3. Block production deployment
--   4. Assign investigation ticket to Data Eng Lead
-- ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 6:** `TEST_RUNBOOK.md`

```markdown
# 🧪 FTL to PI Migration — Test Runbook

**Project:** FTL Agent Base Aggregation to PI Data Warehouse  
**JIRA Epic:** CORTEX-2  
**Owner:** Data Engineering Team  
**Last Updated:** 2026-06-24  

---

## 📋 Table of Contents

1. [Test Suite Overview](#test-suite-overview)
2. [Pre-Execution Checklist](#pre-execution-checklist)
3. [Test Execution Order](#test-execution-order)
4. [Failure Response Playbook](#failure-response-playbook)
5. [Validation Criteria](#validation-criteria)
6. [Rollback Procedure](#rollback-procedure)

---

## 1. Test Suite Overview

### 📦 Complete Test Inventory

| Test Type | File Location | Test Count | Execution Time | Severity |
|-----------|---------------|------------|----------------|----------|
| **Unit Tests** | `tests/unit/unit_tests.sql` | 10 | ~30 sec | CRITICAL |
| **Functional Tests** | `tests/functional/functional_tests.sql` | 12 | ~45 sec | CRITICAL |
| **Gold Equivalence** | `tests/functional/gold_equivalence_test.sql` | 1 | ~2 min | BLOCKER |
| **dbt YAML Tests** | `models/silver/slv_ftl_agent_base_agg.yml` | 14 | ~20 sec | CRITICAL |
| **Regression Suite** | `tests/regression/regression_suite.sql` | 15 | ~3-5 min | BLOCKER |
| **Total** | — | **52** | **~8 min** | — |

### 🎯 Pass Criteria

- **PASS:** Test query returns **0 rows**
- **FAIL:** Test query returns **1+ rows** (violations found)

---

## 2. Pre-Execution Checklist

Before running any tests, verify:

- [ ] Bronze table `ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG` is populated
- [ ] Silver model `ZOOM_AI_POC.SILVER.slv_ftl_agent_base_agg` has been run via dbt
- [ ] Gold model `ZOOM_AI_POC.GOLD.gld_aggregate_new` has been run via dbt
- [ ] Existing PI Gold table `ZOOM_AI_POC.GOLD.GLD_AGGREGATE` is accessible
- [ ] User has `SELECT` permissions on all tables
- [ ] Snowflake warehouse is running (use `COMPUTE_WH` or equivalent)
- [ ] dbt CLI is installed and configured (for YAML tests)

---

## 3. Test Execution Order

### 🚀 **PHASE 1: Unit Tests** (30 seconds)

**Purpose:** Validate individual business rule transformations

```bash
# Execute unit tests
snowsql -f tests/unit/unit_tests.sql -o output_format=csv -o header=true
```

**What's Being Tested:**
- ✅ BR-007: ACCOUNT_ID pass-through
- ✅ BR-008: ENGAGEMENT_ID pass-through
- ✅ BR-009: AGENT_ID → USER_ID rename
- ✅ BR-005: DIRECTION case normalization
- ✅ BR-006: CHANNEL case normalization
- ✅ BR-012: MODALITY pass-through
- ✅ BR-011: PHONE_SESSIONS pass-through
- ✅ BR-004: INBOUND_PHONE_MS → DURATION_SEC (÷ 1000)
- ✅ BR-002: INBOUND_PHONE_MS → INBOUND_PHONE_MINS (÷ 60000)

**Pass Condition:** All 10 tests return 0 rows

**On Failure:**
1. Note which BR-ID test failed
2. Review corresponding transformation logic in `slv_ftl_agent_base_agg.sql`
3. Notify Data Engineering Lead via Slack `#data-quality-alerts`
4. **DO NOT PROCEED** to Phase 2 until resolved

---

### 🚀 **PHASE 2: Functional Tests** (45 seconds)

**Purpose:** Validate data quality and schema integrity

```bash
# Execute functional tests
snowsql -f tests/functional/functional_tests.sql -o output_format=csv -o header=true
```

**What's Being Tested:**
- ✅ Row count match (Bronze → Silver)
- ✅ ACCOUNT_ID not null
- ✅ ENGAGEMENT_ID uniqueness
- ✅ DIRECTION domain (INBOUND/OUTBOUND only)
- ✅ CHANNEL domain (PHONE/VIDEO only)
- ✅ MODALITY domain (Chat/Email/SMS only)
- ✅ PHONE_SESSIONS non-negative
- ✅ DURATION_SEC non-negative
- ✅ INBOUND_PHONE_MINS non-negative
- ✅ **GAP-001:** PHONE_DIALIN_COUNT is NULL
- ✅ REPORT_DATE valid range
- ✅ LOAD_TIMESTAMP populated

**Pass Condition:** All 12 tests return 0 rows

**On Failure:**
1. Identify which data quality check failed
2. Review source data in Bronze table
3. Check for data corruption or ETL job issues
4. Notify Data Engineering Lead
5. **DO NOT PROCEED** to Phase 3 until resolved

---

### 🚀 **PHASE 3: Gold Equivalence Test** (2 minutes) ⚠️ BLOCKER

**Purpose:** Validate FTL Gold output matches existing PI Gold

```bash
# Execute gold equivalence test
snowsql -f tests/functional/gold_equivalence_test.sql -o output_format=csv -o header=true
```

**What's Being Tested:**
- ✅ ACTIVE_ACCOUNTS match (±1% tolerance)
- ✅ ACTIVE_USERS match (±1% tolerance)
- ✅ PHONE_USAGE match (±1% tolerance) — validates BR-003
- ✅ USERS_ACTIVE_16PLUS_DAYS match (±1% tolerance)

**Pass Condition:** 0 rows returned (all metrics within 1% tolerance)

**On Failure:**
1. **CRITICAL:** This is a BLOCKER — production cutover cannot proceed
2. Review discrepancies by DATE/REGION/SEGMENT
3. Notify:
   - Data Engineering Lead (Slack `#data-migration-alerts`)
   - Business Analytics Team (Email: `analytics@zoom.us`)
4. Investigate:
   - BR-003 transformation logic
   - Data completeness in Bronze FTL
   - Region mapping logic (BR-017 low confidence)
   - Segment classification assumptions
5. **DO NOT PROCEED** to production until discrepancies are resolved

---

### 🚀 **PHASE 4: dbt YAML Tests** (20 seconds)

**Purpose:** Run dbt-native schema tests

```bash
# Execute dbt tests
dbt test --select slv_ftl_agent_base_agg
```

**What's Being Tested:**
- ✅ Column not_null constraints
- ✅ Column accepted_values constraints
- ✅ Column uniqueness constraints
- ✅ Column relationship constraints
- ✅ Custom expression tests (non-negative, date ranges)

**Pass Condition:** All 14 tests pass (dbt output: `Completed successfully`)

**On Failure:**
1. Review dbt test output for specific column failures
2. Check YAML file `models/silver/slv_ftl_agent_base_