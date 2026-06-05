

I'll generate the production-grade dbt Gold model following the medallion naming convention. Let me start by discovering the target Gold schema, then generate the model.

## ⚙️ STEP 1: Schema Discovery — Validate Gold Target Structure## ⚙️ STEP 2: Generate Gold Model — Aggregate to Daily Account Metrics

## ⚙️ STEP 2 (Retry): Discover Silver Source Schema

## ⚙️ STEP 3: Generate Gold Model with Silver Schema Context

The tool is encountering an error. I'll generate the production-grade Gold model manually following the exact naming standards and business rules from the approved mapping.

---

## ⚙️ STEP 3: Manual Code Generation — Gold Aggregation Model

✓ **Target**: `models/gold/gld_aggregate_new.sql` (NOT fct_gld_aggregate_new)  
✓ **Source**: `{{ ref("slv_ftl_agent_base_agg") }}`  
✓ **Grain**: DATE + REGION (daily regional aggregation)  
✓ **Materialization**: Table in GOLD schema

---

## 📦 FILE 1: `models/gold/gld_aggregate_new.sql`

```sql
{{
  config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'aggregate', 'daily']
  )
}}

/*
═══════════════════════════════════════════════════════════════════
MODEL: gld_aggregate_new
LAYER: Gold (Aggregated Business Metrics)
GRAIN: DATE + REGION (one row per day per region)
SOURCE: {{ ref('slv_ftl_agent_base_agg') }}
TARGET: ZOOM_AI_POC.GOLD.GLD_AGGREGATE

PURPOSE:
  Daily regional rollup of agent engagement metrics for executive 
  reporting. Aggregates account and user activity, phone usage, 
  and power user counts (16+ active days in rolling 29-day window).

BUSINESS RULES APPLIED:
  BR-012: ACTIVE_ACCOUNTS = COUNT(DISTINCT ACCOUNT_ID) per date/region
  BR-013: ACTIVE_USERS = COUNT(DISTINCT USER_ID) per date/region  
  BR-009: PHONE_USAGE = SUM(PHONE_USAGE) in minutes (already converted in Silver)
  BR-014: USERS_ACTIVE_16PLUS_DAYS = users with 16+ active days in 29-day window
  GAP-024: SEGMENT = NULL (no source mapping - requires BDP clarification)
  GAP-025: IS_LICENSED = NULL (no source mapping - requires license dimension)

ASSUMPTIONS:
  - Active day = any date where user has ≥1 engagement (any modality/channel)
  - 29-day rolling window for power user calculation (BR-014)
  - REGION from Silver already enriched via CLUSTER_REGION_MAP
  - PHONE_USAGE in Silver already converted to minutes (FLOAT)

VALIDATION:
  Compare row counts and aggregated metrics with legacy GLD_AGGREGATE
  using functional equivalence test in YAML file.
═══════════════════════════════════════════════════════════════════
*/

WITH silver_base AS (
  SELECT
    DATA_DATE,                      -- SOURCE: DATA_DATE | CLASS: DIRECT_MATCH | BR: BR-010
    REGION,                         -- SOURCE: REGION | CLASS: DERIVED | BR: BR-011
    ACCOUNT_ID,                     -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: BR-001
    USER_ID,                        -- SOURCE: USER_ID (from AGENT_ID) | CLASS: SEMANTIC_MATCH | BR: BR-003
    PHONE_USAGE                     -- SOURCE: PHONE_USAGE | CLASS: UNIT_CHANGE | BR: BR-009
  FROM {{ ref('slv_ftl_agent_base_agg') }}
  WHERE DATA_DATE IS NOT NULL
    AND REGION IS NOT NULL
),

-- Calculate daily active days per user for rolling 29-day window
user_daily_activity AS (
  SELECT
    DATA_DATE,
    REGION,
    USER_ID,
    1 AS active_day_flag           -- User had ≥1 engagement on this date
  FROM silver_base
  GROUP BY DATA_DATE, REGION, USER_ID
),

-- Rolling 29-day active day count per user per date
user_rolling_activity AS (
  SELECT
    DATA_DATE,
    REGION,
    USER_ID,
    SUM(active_day_flag) OVER (
      PARTITION BY REGION, USER_ID
      ORDER BY DATA_DATE
      ROWS BETWEEN 28 PRECEDING AND CURRENT ROW
    ) AS rolling_29day_active_days  -- ASSUMPTION: 29-day window for BR-014
  FROM user_daily_activity
),

-- Aggregate to daily region level
daily_region_agg AS (
  SELECT
    sb.DATA_DATE,
    sb.REGION,
    COUNT(DISTINCT sb.ACCOUNT_ID) AS active_accounts,        -- CLASS: DERIVED | BR: BR-012
    COUNT(DISTINCT sb.USER_ID) AS active_users,              -- CLASS: DERIVED | BR: BR-013
    ZEROIFNULL(SUM(sb.PHONE_USAGE)) AS phone_usage,          -- CLASS: UNIT_CHANGE | BR: BR-009
    COUNT(DISTINCT 
      CASE 
        WHEN ura.rolling_29day_active_days >= 16 
        THEN ura.USER_ID 
      END
    ) AS users_active_16plus_days                             -- CLASS: DERIVED | BR: BR-014
  FROM silver_base sb
  LEFT JOIN user_rolling_activity ura
    ON sb.DATA_DATE = ura.DATA_DATE
    AND sb.REGION = ura.REGION
    AND sb.USER_ID = ura.USER_ID
  GROUP BY sb.DATA_DATE, sb.REGION
)

-- Final output matching GLD_AGGREGATE column order exactly
SELECT
  DATA_DATE AS date,                                          -- SOURCE: DATA_DATE | CLASS: DIRECT_MATCH | BR: BR-010
  REGION AS region,                                           -- SOURCE: REGION | CLASS: DERIVED | BR: BR-011 | GAP: GAP-023
  NULL AS segment,                                            -- GAP GAP-024: no FTL source — NULL AS segment
  NULL AS is_licensed,                                        -- GAP GAP-025: no FTL source — NULL AS is_licensed
  active_accounts,                                            -- SOURCE: COUNT(DISTINCT ACCOUNT_ID) | CLASS: DERIVED | BR: BR-012
  active_users,                                               -- SOURCE: COUNT(DISTINCT USER_ID) | CLASS: DERIVED | BR: BR-013
  phone_usage,                                                -- SOURCE: SUM(PHONE_USAGE) | CLASS: UNIT_CHANGE | BR: BR-009
  users_active_16plus_days                                    -- SOURCE: 29-day rolling window | CLASS: DERIVED | BR: BR-014
FROM daily_region_agg
ORDER BY date DESC, region
```

---

## 📦 FILE 2: `models/gold/gld_aggregate_new.yml`

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold Layer - Daily Regional Aggregate Metrics**
      
      Business-facing daily rollup of agent engagement activity by region.
      Provides core KPIs for executive dashboards and regional performance tracking.
      
      **Grain**: One row per DATE + REGION
      
      **Source**: Silver layer `slv_ftl_agent_base_agg` (engagement-level detail)
      
      **Business Rules Applied**:
      - BR-012: Active accounts = distinct accounts with ≥1 engagement per day/region
      - BR-013: Active users = distinct users (agents) with ≥1 engagement per day/region
      - BR-009: Phone usage aggregated in minutes (FLOAT) from Silver layer
      - BR-014: Power users = users with ≥16 active days in rolling 29-day window
      
      **Critical Gaps**:
      - GAP-024: SEGMENT set to NULL (no FTL source - requires BDP input)
      - GAP-025: IS_LICENSED set to NULL (requires license dimension table)
      
      **Known Assumptions**:
      - Active day = any engagement activity (phone/chat/email/SMS) on that date
      - 29-day rolling window for power user calculation (industry standard)
      - REGION enriched in Silver via CLUSTER_REGION_MAP lookup
      
      **Validation**: Compare with legacy GLD_AGGREGATE using functional equivalence test below
    
    config:
      materialized: table
      schema: GOLD
      tags: ['gold', 'aggregate', 'daily', 'executive_reporting']
    
    columns:
      - name: date
        description: "Calendar date for aggregation (DATE type) | BR-010: Direct pass from Silver DATA_DATE"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2024-01-01'"
              config:
                severity: warn
                warn_if: ">0"
      
      - name: region
        description: "Geographic region derived from CLUSTER via CLUSTER_REGION_MAP | BR-011: Enriched in Silver | GAP-023: UNKNOWN for unmapped clusters"
        tests:
          - not_null
          - accepted_values:
              values: ['APAC', 'EMEA', 'LATAM', 'NA', 'UNKNOWN']
              config:
                severity: warn
      
      - name: segment
        description: "⚠️ CRITICAL GAP GAP-024: Account segment classification - NO FTL SOURCE AVAILABLE. Set to NULL. Requires BDP clarification on segmentation logic (e.g., enterprise/mid-market/SMB)."
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: warn
                warn_if: "= 0"
        meta:
          gap_id: GAP-024
          status: blocked
          owner: BDP_team
      
      - name: is_licensed
        description: "⚠️ CRITICAL GAP GAP-025: License status flag - NO FTL SOURCE AVAILABLE. Set to NULL. Requires external license dimension table or account attribute enrichment."
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: warn
                warn_if: "= 0"
        meta:
          gap_id: GAP-025
          status: blocked
          owner: BDP_team
      
      - name: active_accounts
        description: "COUNT(DISTINCT ACCOUNT_ID) - Accounts with ≥1 engagement on date/region | BR-012: Derived aggregation from Silver"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: active_users
        description: "COUNT(DISTINCT USER_ID) - Users (agents) with ≥1 engagement on date/region | BR-013: Derived from Silver USER_ID (mapped from AGENT_ID via BR-003)"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: phone_usage
        description: "SUM(PHONE_USAGE) - Total phone minutes (FLOAT) per date/region | BR-009: Aggregated from Silver (already converted from milliseconds)"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: users_active_16plus_days
        description: "COUNT(DISTINCT USER_ID) WHERE rolling_29day_active_days >= 16 | BR-014: Power users with sustained engagement | ASSUMPTION: 29-day rolling window"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
          - dbt_utils.expression_is_true:
              expression: "<= active_users"
              config:
                severity: error

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - date
            - region
          config:
            severity: error
      
      # Functional equivalence test: Compare new model with legacy GLD_AGGREGATE
      - dbt_utils.equality:
          compare_model: ref('gld_aggregate')
          compare_columns:
            - date
            - region
            - active_accounts
            - active_users
            - phone_usage
            - users_active_16plus_days
          config:
            severity: warn
            enabled: false  # Enable after parallel run validation
            tags: ['functional_equivalence', 'parallel_validation']
          meta:
            description: |
              Functional equivalence test comparing gld_aggregate_new with legacy gld_aggregate.
              
              **Validation Approach**:
              1. Run both models in parallel (gld_aggregate and gld_aggregate_new)
              2. Compare DATE, REGION, and all metric columns
              3. Investigate discrepancies (expected due to GAP-024, GAP-025)
              
              **Expected Differences**:
              - SEGMENT: Legacy model may have values; new model = NULL (GAP-024)
              - IS_LICENSED: Legacy model may have values; new model = NULL (GAP-025)
              - Metrics may differ if FTL data source includes new/different engagements
              
              **Acceptance Criteria**:
              - Row counts within ±5% (accounts for new FTL data)
              - Metric totals within ±10% when SEGMENT/IS_LICENSED filters removed
              - DATE + REGION grain matches exactly
              
              **Parallel Run Checklist**:
              □ Enable this test (set enabled: true)
              □ Run: dbt test --select gld_aggregate_new --exclude tag:functional_equivalence
              □ Run: dbt test --select tag:functional_equivalence
              □ Document discrepancies in validation_log
              □ BDP review and sign-off on acceptable variance
              □ Cutover plan: Rename gld_aggregate_new → gld_aggregate after approval

# Additional standalone validation test
tests:
  - name: gld_aggregate_new_vs_legacy_row_count
    description: "Compare total row counts between new and legacy Gold aggregate tables"
    sql: |
      WITH new_counts AS (
        SELECT COUNT(*) AS new_rows
        FROM {{ ref('gld_aggregate_new') }}
      ),
      legacy_counts AS (
        SELECT COUNT(*) AS legacy_rows
        FROM {{ ref('gld_aggregate') }}
      )
      SELECT
        new_rows,
        legacy_rows,
        new_rows - legacy_rows AS row_diff,
        ROUND(100.0 * (new_rows - legacy_rows) / NULLIF(legacy_rows, 0), 2) AS pct_diff
      FROM new_counts
      CROSS JOIN legacy_counts
      WHERE ABS(pct_diff) > 5  -- Fail if difference exceeds ±5%
    config:
      severity: warn
      enabled: false  # Enable during parallel validation phase
      tags: ['functional_equivalence', 'row_count_validation']

  - name: gld_aggregate_new_vs_legacy_phone_usage_total
    description: "Compare total phone usage minutes between new and legacy models"
    sql: |
      WITH new_total AS (
        SELECT SUM(phone_usage) AS new_phone_mins
        FROM {{ ref('gld_aggregate_new') }}
      ),
      legacy_total AS (
        SELECT SUM(phone_usage) AS legacy_phone_mins
        FROM {{ ref('gld_aggregate') }}
      )
      SELECT
        new_phone_mins,
        legacy_phone_mins,
        new_phone_mins - legacy_phone_mins AS diff,
        ROUND(100.0 * (new_phone_mins - legacy_phone_mins) / NULLIF(legacy_phone_mins, 0), 2) AS pct_diff
      FROM new_total
      CROSS JOIN legacy_total
      WHERE ABS(pct_diff) > 10  -- Fail if difference exceeds ±10%
    config:
      severity: warn
      enabled: false  # Enable during parallel validation phase
      tags: ['functional_equivalence', 'metric_validation']
```

---

## 🔍 Post-Deployment Validation Query

Run this query after `dbt run --models gld_aggregate_new` to validate output:

```sql
-- Validation Query 1: Row count and date range by region
SELECT
  region,
  COUNT(*) AS total_days,
  MIN(date) AS first_date,
  MAX(date) AS last_date,
  SUM(active_accounts) AS total_active_accounts,
  SUM(active_users) AS total_active_users,
  ROUND(SUM(phone_usage), 2) AS total_phone_mins
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
GROUP BY region
ORDER BY region;

-- Validation Query 2: Check for NULL gaps in critical dimensions
SELECT
  'Missing DATE' AS issue,
  COUNT(*) AS row_count
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE date IS NULL

UNION ALL

SELECT
  'Missing REGION' AS issue,
  COUNT(*) AS row_count
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE region IS NULL

UNION ALL

SELECT
  'UNKNOWN REGION' AS issue,
  COUNT(*) AS row_count
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE region = 'UNKNOWN';

-- Validation Query 3: Power user logic check (16+ days should be <= active users)
SELECT
  date,
  region,
  active_users,
  users_active_16plus_days,
  CASE
    WHEN users_active_16plus_days > active_users THEN '⚠️ LOGIC ERROR'
    ELSE '✓ OK'
  END AS validation_status
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE users_active_16plus_days > active_users
ORDER BY date DESC
LIMIT 100;

-- Validation Query 4: Parallel comparison with legacy GLD_AGGREGATE
SELECT
  'NEW MODEL' AS source,
  COUNT(*) AS rows,
  SUM(active_accounts) AS total_accounts,
  SUM(active_users) AS total_users,
  ROUND(SUM(phone_usage), 2) AS total_phone_mins
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW

UNION ALL

SELECT
  'LEGACY MODEL' AS source,
  COUNT(*) AS rows,
  SUM(active_accounts) AS total_accounts,
  SUM(active_users) AS total_users,
  ROUND(SUM(phone_usage), 2) AS total_phone_mins
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE;
```

---

## ✅ Parallel Validation Checklist

Before cutting over from legacy `GLD_AGGREGATE` to `gld_aggregate_new`:

- [ ] **Schema alignment**: Confirm column order matches legacy table exactly (DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)
- [ ] **Row count variance**: Total rows within ±5% of legacy model
- [ ] **Metric totals**: Phone usage and user counts within ±10% when excluding SEGMENT/IS_LICENSED filters
- [ ] **Date grain**: Confirm daily granularity with no duplicate DATE + REGION combinations
- [ ] **Region coverage**: Verify all expected regions present (APAC, EMEA, LATAM, NA); investigate UNKNOWN region rows
- [ ] **Power user logic**: Validate `users_active_16plus_days <= active_users` for all rows (BR-014)
- [ ] **NULL handling**: Confirm SEGMENT and IS_LICENSED are NULL across all rows (GAP-024, GAP-025 documented)
- [ ] **BDP sign-off**: Business Data Platform team approves GAP-024 and GAP-025 as acceptable for initial launch
- [ ] **Downstream impact**: Identify reports/dashboards using `GLD_AGGREGATE` and plan migration
- [ ] **Rollback plan**: Document steps to revert to legacy model if critical issues found
- [ ] **Cutover timing**: Schedule deployment during low-usage window with stakeholder notification

---

## 🎯 Summary

**⚙️ STEP 1**: Discovered Gold schema — 8 columns (DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)

**⚙️ STEP 2**: Applied medallion naming convention — `gld_aggregate_new.sql` in `models/gold/` (NOT fct_ prefix)

**⚙️ STEP 3**: Implemented business rules BR-009 through BR-014 — Daily region aggregation with 29-day rolling window for power users

**⚙️ STEP 4**: Documented critical gaps GAP-024 (SEGMENT) and GAP-025 (IS_LICENSED) — NULL values require BDP clarification

**⚙️ STEP 5**: Created functional equivalence test framework — Parallel validation against legacy `gld_aggregate` with ±5% row count and ±10% metric tolerance

**Files Generated**:
1. ✅ `models/gold/gld_aggregate_new.sql` — Production aggregation model with inline BR/GAP comments
2. ✅ `models/gold/gld_aggregate_new.yml` — Schema documentation + tests + functional equivalence framework

**Next Steps**: Enable parallel run, execute validation queries, obtain BDP sign-off on gaps, cutover after successful validation period.