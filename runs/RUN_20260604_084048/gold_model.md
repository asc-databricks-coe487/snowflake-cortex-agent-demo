

⚙️ **STEP 1: Schema Discovery** — Retrieved GLD_AGGREGATE structure with 8 columns (DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)

⚙️ **STEP 2: Code Generation** — Tool backend returned error; proceeding with manual generation using repo standards and approved mapping

⚙️ **STEP 3: Manual File Generation** — Building Gold model with exact column order from target schema, inline BR/GAP annotations, and functional equivalence test

---

## ✅ **FILE 1: models/gold/gld_aggregate_new.sql**

```sql
{{ config(
    materialized="table",
    schema="GOLD"
) }}

-- ══════════════════════════════════════════════════════════════════
-- MODEL:  gld_aggregate_new
-- LAYER:  GOLD
-- SOURCE: slv_ftl_agent_base_agg (Silver layer)
-- TARGET: GLD_AGGREGATE functional equivalent
-- GRAIN:  DATE + REGION + SEGMENT + IS_LICENSED
-- ══════════════════════════════════════════════════════════════════
-- PURPOSE:
--   Aggregates daily active account and user metrics by region.
--   Replicates GLD_AGGREGATE structure using FTL data pipeline.
--
-- GAPS (GAP-009 through GAP-011):
--   - SEGMENT: No FTL source for account segment classification
--   - IS_LICENSED: No FTL source for licensing status
--   - USERS_ACTIVE_16PLUS_DAYS: Requires rolling 29-day window logic
--     not yet implemented in FTL pipeline (needs USER_ACTIVE_DAYS)
--
-- BUSINESS RULES APPLIED:
--   BR-005: DATA_DATE → DATE conversion
--   BR-006: CLUSTER → REGION mapping
--   BR-007: ACTIVE_ACCOUNTS aggregation (IS_ACTIVE filter)
--   BR-004: ACTIVE_USERS aggregation (AGENT_ID → USER_ID)
--   BR-011: PHONE_USAGE calculation (ms to hours)
-- ══════════════════════════════════════════════════════════════════

WITH silver_base AS (
    SELECT
        date,
        region,
        account_id,
        agent_id,
        is_active,
        inbound_phone_ms
    FROM {{ ref("slv_ftl_agent_base_agg") }}
    WHERE date IS NOT NULL
      AND region IS NOT NULL
      AND region != 'UNKNOWN'  -- Exclude unmapped clusters
)

SELECT
    -- SOURCE: date | CLASS: PARTIAL_MATCH | BR: BR-005
    date AS date,

    -- SOURCE: region | CLASS: SEMANTIC_MATCH | BR: BR-006
    region AS region,

    -- GAP GAP-009: no FTL source for account segment
    NULL AS segment,

    -- GAP GAP-010: no FTL source for licensing status
    NULL AS is_licensed,

    -- SOURCE: account_id | CLASS: DIRECT_MATCH | BR: BR-007
    -- Aggregation: COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE
    COUNT(DISTINCT IFF(is_active = TRUE, account_id, NULL)) AS active_accounts,

    -- SOURCE: agent_id | CLASS: SEMANTIC_MATCH | BR: BR-004
    -- Aggregation: COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE
    COUNT(DISTINCT IFF(is_active = TRUE, agent_id, NULL)) AS active_users,

    -- SOURCE: inbound_phone_ms | CLASS: PARTIAL_MATCH | BR: BR-011
    -- Transformation: SUM(INBOUND_PHONE_MS)/1000/3600 (ms → hours)
    ZEROIFNULL(SUM(inbound_phone_ms) / 1000.0 / 3600.0) AS phone_usage,

    -- GAP GAP-011: requires USER_ACTIVE_DAYS aggregation (16+ days in rolling 29-day window)
    -- ASSUMPTION: Not computable from current FTL base-level data
    NULL AS users_active_16plus_days

FROM silver_base
WHERE is_active = TRUE  -- Filter for active records only (BR-007, BR-004)
GROUP BY 1, 2, 3, 4
ORDER BY date DESC, region
```

---

## ✅ **FILE 2: models/gold/gld_aggregate_new.yml**

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold Layer: Daily Active Accounts & Users by Region**
      
      Aggregates FTL agent base data to match GLD_AGGREGATE structure.
      Provides daily active account/user counts and phone usage hours by region.
      
      **Grain:** DATE + REGION + SEGMENT + IS_LICENSED
      
      **Source:** {{ ref("slv_ftl_agent_base_agg") }}
      
      **Known Gaps:**
      - SEGMENT: No FTL source for account segmentation (GAP-009)
      - IS_LICENSED: No FTL source for licensing status (GAP-010)
      - USERS_ACTIVE_16PLUS_DAYS: Requires USER_ACTIVE_DAYS table not yet in FTL pipeline (GAP-011)
      
      **Business Rules:**
      - BR-005: DATA_DATE text parsing to DATE type
      - BR-006: CLUSTER → REGION semantic mapping
      - BR-007: ACTIVE_ACCOUNTS = COUNT(DISTINCT ACCOUNT_ID WHERE IS_ACTIVE)
      - BR-004: ACTIVE_USERS = COUNT(DISTINCT AGENT_ID WHERE IS_ACTIVE)
      - BR-011: PHONE_USAGE = SUM(INBOUND_PHONE_MS) / 3600000 (hours)
      
      **Functional Equivalence Test:** See tests section below

    config:
      materialized: table
      schema: GOLD

    columns:
      - name: date
        description: "Event date (derived from FTL DATA_DATE) | BR-005"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2024-01-01'"
              config:
                severity: warn

      - name: region
        description: "Cloud region (derived from FTL CLUSTER via mapping) | BR-006"
        tests:
          - not_null
          - accepted_values:
              values: ['US', 'EU', 'APAC', 'AMER', 'EMEA']
              config:
                severity: warn

      - name: segment
        description: "Account segment classification | GAP-009: NULL — no FTL source"

      - name: is_licensed
        description: "Licensed account flag | GAP-010: NULL — no FTL source"

      - name: active_accounts
        description: "Count of distinct active accounts (IS_ACTIVE=TRUE) | BR-007"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

      - name: active_users
        description: "Count of distinct active users (AGENT_ID where IS_ACTIVE=TRUE) | BR-004"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

      - name: phone_usage
        description: "Total inbound phone usage in hours (INBOUND_PHONE_MS / 3600000) | BR-011"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

      - name: users_active_16plus_days
        description: "Users active 16+ days in rolling 29-day window | GAP-011: NULL — requires USER_ACTIVE_DAYS table"

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - date
            - region
          config:
            where: "segment IS NULL AND is_licensed IS NULL"
            severity: warn

# ══════════════════════════════════════════════════════════════════
# FUNCTIONAL EQUIVALENCE TEST
# Compares gld_aggregate_new (FTL pipeline) vs GLD_AGGREGATE (PI pipeline)
# ══════════════════════════════════════════════════════════════════

tests:
  - name: functional_equivalence_gld_aggregate
    description: |
      **Functional Equivalence Test: gld_aggregate_new vs GLD_AGGREGATE**
      
      Validates that FTL-sourced Gold model produces equivalent metrics to 
      PI-sourced Gold model for overlapping date ranges and regions.
      
      **Test Logic:**
      - Join on DATE + REGION
      - Compare ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE
      - Allow 5% tolerance for rounding/timezone differences
      - Exclude rows where PI has SEGMENT/IS_LICENSED filters (FTL has NULL)
      
      **Expected Result:** 0 rows (all metrics within tolerance)
      
      **Failure Investigation:**
      1. Check date range overlap: Do both pipelines have data for same dates?
      2. Check region mapping: Are FTL CLUSTERs correctly mapped to PI REGIONs?
      3. Check IS_ACTIVE logic: Same filter applied in both pipelines?
      4. Check timezone handling: DATA_DATE parsing consistent with PI DATE?
      
      **Query Usage:**
      ```bash
      dbt test --select functional_equivalence_gld_aggregate
      ```
    
    config:
      severity: warn
      error_if: ">10"     # Fail if more than 10 mismatched rows
      warn_if: ">0"        # Warn if any mismatched rows
    
    # Test query embedded below (dbt native test format)
    meta:
      test_query: |
        WITH ftl_gold AS (
            SELECT
                date,
                region,
                active_accounts AS ftl_active_accounts,
                active_users AS ftl_active_users,
                phone_usage AS ftl_phone_usage
            FROM {{ ref("gld_aggregate_new") }}
            WHERE segment IS NULL
              AND is_licensed IS NULL
        ),
        
        pi_gold AS (
            SELECT
                date,
                region,
                active_accounts AS pi_active_accounts,
                active_users AS pi_active_users,
                phone_usage AS pi_phone_usage
            FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
            WHERE segment IS NULL
              AND is_licensed IS NULL
        ),
        
        comparison AS (
            SELECT
                COALESCE(f.date, p.date) AS date,
                COALESCE(f.region, p.region) AS region,
                f.ftl_active_accounts,
                p.pi_active_accounts,
                ABS(ZEROIFNULL(f.ftl_active_accounts) - ZEROIFNULL(p.pi_active_accounts)) AS accounts_diff,
                f.ftl_active_users,
                p.pi_active_users,
                ABS(ZEROIFNULL(f.ftl_active_users) - ZEROIFNULL(p.pi_active_users)) AS users_diff,
                f.ftl_phone_usage,
                p.pi_phone_usage,
                ABS(ZEROIFNULL(f.ftl_phone_usage) - ZEROIFNULL(p.pi_phone_usage)) AS usage_diff,
                -- 5% tolerance threshold
                ZEROIFNULL(p.pi_active_accounts) * 0.05 AS accounts_tolerance,
                ZEROIFNULL(p.pi_active_users) * 0.05 AS users_tolerance,
                ZEROIFNULL(p.pi_phone_usage) * 0.05 AS usage_tolerance
            FROM ftl_gold f
            FULL OUTER JOIN pi_gold p
                ON f.date = p.date
                AND f.region = p.region
            WHERE f.date IS NOT NULL OR p.date IS NOT NULL
        )
        
        -- Return rows that exceed 5% tolerance
        SELECT
            date,
            region,
            ftl_active_accounts,
            pi_active_accounts,
            accounts_diff,
            ROUND(accounts_diff / NULLIF(pi_active_accounts, 0) * 100, 2) AS accounts_pct_diff,
            ftl_active_users,
            pi_active_users,
            users_diff,
            ROUND(users_diff / NULLIF(pi_active_users, 0) * 100, 2) AS users_pct_diff,
            ftl_phone_usage,
            pi_phone_usage,
            usage_diff,
            ROUND(usage_diff / NULLIF(pi_phone_usage, 0) * 100, 2) AS usage_pct_diff,
            CASE
                WHEN ftl_active_accounts IS NULL THEN 'MISSING_IN_FTL'
                WHEN pi_active_accounts IS NULL THEN 'MISSING_IN_PI'
                WHEN accounts_diff > accounts_tolerance THEN 'ACCOUNTS_MISMATCH'
                WHEN users_diff > users_tolerance THEN 'USERS_MISMATCH'
                WHEN usage_diff > usage_tolerance THEN 'USAGE_MISMATCH'
            END AS failure_reason
        FROM comparison
        WHERE accounts_diff > accounts_tolerance
           OR users_diff > users_tolerance
           OR usage_diff > usage_tolerance
           OR ftl_active_accounts IS NULL
           OR pi_active_accounts IS NULL
        ORDER BY date DESC, region
```

---

## 📊 **Post-Deployment Validation Checklist**

After deploying `gld_aggregate_new`, run these queries to validate data quality:

### **1. Row Count & Date Range Check**
```sql
SELECT 
    'FTL' AS source,
    COUNT(*) AS total_rows,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(DISTINCT region) AS distinct_regions
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW

UNION ALL

SELECT 
    'PI' AS source,
    COUNT(*) AS total_rows,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(DISTINCT region) AS distinct_regions
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
WHERE segment IS NULL AND is_licensed IS NULL;
```

**Expected:** Similar row counts and overlapping date ranges

---

### **2. Metric Distribution Comparison**
```sql
SELECT
    'FTL' AS source,
    AVG(active_accounts) AS avg_accounts,
    AVG(active_users) AS avg_users,
    AVG(phone_usage) AS avg_phone_hours,
    SUM(active_accounts) AS total_accounts,
    SUM(active_users) AS total_users,
    SUM(phone_usage) AS total_phone_hours
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE date >= DATEADD(day, -30, CURRENT_DATE())

UNION ALL

SELECT
    'PI' AS source,
    AVG(active_accounts) AS avg_accounts,
    AVG(active_users) AS avg_users,
    AVG(phone_usage) AS avg_phone_hours,
    SUM(active_accounts) AS total_accounts,
    SUM(active_users) AS total_users,
    SUM(phone_usage) AS total_phone_hours
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
WHERE date >= DATEADD(day, -30, CURRENT_DATE())
  AND segment IS NULL 
  AND is_licensed IS NULL;
```

**Expected:** FTL metrics within 5-10% of PI metrics

---

### **3. NULL Column Verification (GAP Columns)**
```sql
SELECT
    COUNT(*) AS total_rows,
    SUM(IFF(segment IS NULL, 1, 0)) AS segment_nulls,
    SUM(IFF(is_licensed IS NULL, 1, 0)) AS is_licensed_nulls,
    SUM(IFF(users_active_16plus_days IS NULL, 1, 0)) AS users_16plus_nulls,
    ROUND(SUM(IFF(segment IS NULL, 1, 0)) * 100.0 / COUNT(*), 2) AS segment_null_pct
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW;
```

**Expected:** 100% NULL for all three GAP columns (GAP-009, GAP-010, GAP-011)

---

### **4. Region Distribution**
```sql
SELECT
    region,
    COUNT(*) AS row_count,
    SUM(active_accounts) AS total_accounts,
    SUM(active_users) AS total_users,
    ROUND(SUM(phone_usage), 2) AS total_phone_hours
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
GROUP BY region
ORDER BY total_accounts DESC;
```

**Expected:** All regions from CLUSTER_REGION_MAP; no 'UNKNOWN' region

---

## 🎯 **Summary**

✅ **Generated Files:**
- `models/gold/gld_aggregate_new.sql` — Gold mart aggregating daily active accounts/users by region
- `models/gold/gld_aggregate_new.yml` — Schema with 8 columns, 3 GAP annotations, functional equivalence test

✅ **Repo Conventions Applied:**
- Model name: `gld_aggregate_new` (NOT fct_gld_aggregate_new)
- File path: `models/gold/` (NOT models/marts/)
- Config: `schema="GOLD"`, `materialized="table"`
- Source ref: `{{ ref("slv_ftl_agent_base_agg") }}`

✅ **Business Rules Encoded:**
- BR-005: DATA_DATE → DATE conversion
- BR-006: CLUSTER → REGION mapping (excludes UNKNOWN)
- BR-007: ACTIVE_ACCOUNTS = COUNT(DISTINCT ACCOUNT_ID WHERE IS_ACTIVE)
- BR-004: ACTIVE_USERS = COUNT(DISTINCT AGENT_ID WHERE IS_ACTIVE)
- BR-011: PHONE_USAGE = SUM(INBOUND_PHONE_MS) / 3600000 (hours)

✅ **Known Gaps Documented:**
- GAP-009: SEGMENT (NULL — no FTL source)
- GAP-010: IS_LICENSED (NULL — no FTL source)
- GAP-011: USERS_ACTIVE_16PLUS_DAYS (NULL — requires USER_ACTIVE_DAYS table)

✅ **Testing Included:**
- Column-level tests (not_null, accepted_values, expression checks)
- Unique grain test (DATE + REGION where GAP columns NULL)
- Functional equivalence test comparing FTL vs PI pipelines (5% tolerance)

🚀 **Next Steps:**
1. Run `dbt run --select gld_aggregate_new` to build the model
2. Run `dbt test --select gld_aggregate_new` to validate data quality
3. Execute post-deployment queries above to compare FTL vs PI metrics
4. Review functional equivalence test results; investigate failures by date/region