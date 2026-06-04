

⚙️ **STEP 1**: Schema Discovery — Retrieved GLD_AGGREGATE structure (8 columns: DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)

⚙️ **STEP 2**: Tool Error Detected — Generating production-grade Gold models manually following medallion naming standards

⚙️ **STEP 3**: Create Gold Aggregation Model — Building gld_aggregate_new.sql with proper grain (DATE × REGION × SEGMENT × IS_LICENSED) and aggregation logic

---

## 📄 **FILE 1:** `models/gold/gld_aggregate_new.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════
-- GOLD MODEL: gld_aggregate_new
-- Purpose: Daily aggregated metrics by region, segment, and license status
-- Grain: DATE × REGION × SEGMENT × IS_LICENSED (one row per combination)
-- Source: slv_ftl_agent_base_agg (Silver layer)
-- ═══════════════════════════════════════════════════════════════════

{{ config(
    materialized='table',
    schema='GOLD'
) }}

WITH silver_base AS (
    SELECT
        date,                    -- SOURCE: slv_ftl_agent_base_agg.date | BR: BR-001
        region,                  -- SOURCE: slv_ftl_agent_base_agg.region | Derived from CLUSTER
        account_id,              -- SOURCE: slv_ftl_agent_base_agg.account_id
        user_id,                 -- SOURCE: slv_ftl_agent_base_agg.user_id (mapped from AGENT_ID via BR-003)
        is_active,               -- SOURCE: slv_ftl_agent_base_agg.is_active
        phone_sessions,          -- SOURCE: slv_ftl_agent_base_agg.phone_sessions
        inbound_phone_ms         -- SOURCE: slv_ftl_agent_base_agg.inbound_phone_ms
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE date IS NOT NULL       -- Filter out invalid dates
),

aggregated AS (
    SELECT
        date,
        region,
        
        -- GAP-SEGMENT: No source for SEGMENT dimension in FTL data
        -- ASSUMPTION: Defaulting to 0 until business provides segment classification logic
        0 AS segment,            -- GAP: GAP-006 | ASSUMPTION: Segment logic not defined
        
        -- GAP-IS_LICENSED: No source for license status in FTL data
        -- ASSUMPTION: Defaulting to FALSE until business provides license mapping
        FALSE AS is_licensed,    -- GAP: GAP-007 | ASSUMPTION: License status not in FTL
        
        -- ACTIVE_ACCOUNTS: Count distinct active accounts
        -- SOURCE: account_id | BR: BR-002
        COUNT(DISTINCT IFF(is_active = TRUE, account_id, NULL)) AS active_accounts,
        
        -- ACTIVE_USERS: Count distinct active users/agents
        -- SOURCE: user_id (from agent_id) | BR: BR-004
        COUNT(DISTINCT IFF(is_active = TRUE, user_id, NULL)) AS active_users,
        
        -- PHONE_USAGE: Total phone usage in hours (converted from milliseconds)
        -- SOURCE: inbound_phone_ms | BR: BR-008
        ZEROIFNULL(SUM(inbound_phone_ms) / 3600000.0) AS phone_usage,
        
        -- GAP-USERS_ACTIVE_16PLUS_DAYS: Requires historical user activity tracking
        -- CRITICAL GAP: This metric requires 30-day rolling window analysis not available in current grain
        NULL AS users_active_16plus_days  -- GAP: GAP-008 | Requires SLV_USER_ACTIVE_DAYS join
        
    FROM silver_base
    GROUP BY
        date,
        region,
        segment,
        is_licensed
)

SELECT
    -- Column order MUST match ZOOM_AI_POC.GOLD.GLD_AGGREGATE exactly
    date,                           -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-001
    region,                         -- SOURCE: CLUSTER → REGION | CLASS: DERIVED | BR: BR-007
    segment,                        -- GAP: GAP-006 | ASSUMPTION: defaulted to 0
    is_licensed,                    -- GAP: GAP-007 | ASSUMPTION: defaulted to FALSE
    active_accounts,                -- SOURCE: ACCOUNT_ID | CLASS: GRAIN_CHANGE | BR: BR-002
    active_users,                   -- SOURCE: AGENT_ID | CLASS: GRAIN_CHANGE | BR: BR-004
    phone_usage,                    -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-008
    users_active_16plus_days        -- GAP: GAP-008 | Requires historical tracking
FROM aggregated
ORDER BY date DESC, region, segment, is_licensed
```

---

## 📄 **FILE 2:** `models/gold/gld_aggregate_new.yml`

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold Layer Aggregate Model**
      
      Daily aggregated metrics by region, segment, and license status.
      Replaces legacy GLD_AGGREGATE with FTL data sourced from Bronze layer.
      
      **Grain:** DATE × REGION × SEGMENT × IS_LICENSED
      
      **Data Flow:**
      Bronze (BRZ_FTL_AGENT_BASE_AGG) 
        → Silver (slv_ftl_agent_base_agg) 
        → Gold (gld_aggregate_new)
      
      **Known Gaps:**
      - GAP-006: SEGMENT dimension not available in FTL source (defaulted to 0)
      - GAP-007: IS_LICENSED flag not available in FTL source (defaulted to FALSE)
      - GAP-008: USERS_ACTIVE_16PLUS_DAYS requires 30-day rolling window (set to NULL)
      
      **Assumptions:**
      - All accounts default to SEGMENT = 0 until business provides classification
      - All accounts default to IS_LICENSED = FALSE until license data integrated
      - PHONE_USAGE converted from milliseconds to hours (ms ÷ 3,600,000)
      
      **Business Rules Applied:**
      - BR-001: Date parsing from 'M/D/YY HH24:MI' format
      - BR-002: Active accounts aggregation (WHERE is_active = TRUE)
      - BR-004: Active users aggregation (WHERE is_active = TRUE)
      - BR-007: Region derived from CLUSTER via CLUSTER_REGION_MAP
      - BR-008: Phone usage unit conversion (ms → hours)
    
    config:
      materialized: table
      schema: GOLD
      tags: ['gold', 'aggregate', 'daily_metrics', 'ftl_source']
    
    columns:
      - name: date
        description: |
          Report date (grain dimension).
          Parsed from FTL DATA_DATE text field using BR-001 transformation.
        data_type: DATE
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2024-01-01'"
              config:
                severity: warn
                error_if: ">10"
      
      - name: region
        description: |
          Business region (grain dimension).
          Derived from CLUSTER field via CLUSTER_REGION_MAP lookup (BR-007).
          Possible values: AMER, EMEA, APAC, UNKNOWN.
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['AMER', 'EMEA', 'APAC', 'UNKNOWN']
              quote: true
      
      - name: segment
        description: |
          Customer segment dimension (grain).
          **GAP-006**: Not available in FTL source - defaulted to 0.
          VALIDATE WITH BUSINESS: Requires segment classification logic.
        data_type: NUMBER
        tests:
          - not_null
        meta:
          gap_id: GAP-006
          resolution_required: true
          owner: Business Analytics
      
      - name: is_licensed
        description: |
          License status flag (grain dimension).
          **GAP-007**: Not available in FTL source - defaulted to FALSE.
          VALIDATE WITH BUSINESS: Requires license data integration.
        data_type: BOOLEAN
        tests:
          - not_null
        meta:
          gap_id: GAP-007
          resolution_required: true
          owner: Business Analytics
      
      - name: active_accounts
        description: |
          Count of distinct active accounts per day/region/segment/license.
          Aggregation: COUNT(DISTINCT account_id WHERE is_active = TRUE).
          Business Rule: BR-002.
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: active_users
        description: |
          Count of distinct active users (agents) per day/region/segment/license.
          Aggregation: COUNT(DISTINCT user_id WHERE is_active = TRUE).
          Maps from FTL AGENT_ID field (semantic rename via BR-003).
          Business Rule: BR-004.
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: phone_usage
        description: |
          Total phone usage in hours per day/region/segment/license.
          Calculated from INBOUND_PHONE_MS: SUM(inbound_phone_ms) ÷ 3,600,000.
          Business Rule: BR-008 (unit conversion ms → hours).
        data_type: FLOAT
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: users_active_16plus_days
        description: |
          Count of users active 16+ days in trailing 30-day window.
          **GAP-008**: CRITICAL - Requires 30-day rolling window analysis.
          Currently set to NULL. Requires join to SLV_USER_ACTIVE_DAYS.
          VALIDATE WITH BUSINESS: Confirm 16-day threshold and window logic.
        data_type: NUMBER
        meta:
          gap_id: GAP-008
          resolution_required: true
          critical: true
          owner: Analytics Engineering

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - date
            - region
            - segment
            - is_licensed
          config:
            severity: error
      
      # Functional Equivalence Test: Compare gld_aggregate_new vs GLD_AGGREGATE
      - dbt_utils.equality:
          compare_model: ref('gld_aggregate_legacy')
          compare_columns:
            - date
            - region
            - active_accounts
            - active_users
            - phone_usage
          config:
            severity: warn
            enabled: false  # Enable after parallel run validation
            error_if: ">100"
      
      # Row count variance check
      - dbt_utils.expression_is_true:
          expression: "(SELECT COUNT(*) FROM {{ ref('gld_aggregate_new') }}) BETWEEN 0.8 * (SELECT COUNT(*) FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE) AND 1.2 * (SELECT COUNT(*) FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE)"
          config:
            severity: warn
            enabled: false  # Enable during validation phase

# ═══════════════════════════════════════════════════════════════════
# FUNCTIONAL EQUIVALENCE TEST (ADVANCED)
# Run after both models deployed to compare aggregated totals
# ═══════════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 3:** `tests/gold_functional_equivalence.sql`

```sql
-- ═══════════════════════════════════════════════════════════════════
-- FUNCTIONAL EQUIVALENCE TEST: gld_aggregate_new vs GLD_AGGREGATE
-- Purpose: Validate new FTL-sourced Gold model matches legacy PI data
-- Run after parallel deployment to identify discrepancies
-- ═══════════════════════════════════════════════════════════════════

WITH legacy_agg AS (
    SELECT
        date,
        region,
        SUM(active_accounts) AS total_active_accounts,
        SUM(active_users) AS total_active_users,
        SUM(phone_usage) AS total_phone_usage,
        COUNT(*) AS row_count
    FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
    WHERE date >= '2026-01-01'  -- Adjust to validation period
    GROUP BY date, region
),

new_agg AS (
    SELECT
        date,
        region,
        SUM(active_accounts) AS total_active_accounts,
        SUM(active_users) AS total_active_users,
        SUM(phone_usage) AS total_phone_usage,
        COUNT(*) AS row_count
    FROM {{ ref('gld_aggregate_new') }}
    WHERE date >= '2026-01-01'  -- Match validation period
    GROUP BY date, region
),

variance AS (
    SELECT
        COALESCE(l.date, n.date) AS date,
        COALESCE(l.region, n.region) AS region,
        
        l.total_active_accounts AS legacy_accounts,
        n.total_active_accounts AS new_accounts,
        ABS(ZEROIFNULL(l.total_active_accounts) - ZEROIFNULL(n.total_active_accounts)) AS accounts_diff,
        
        l.total_active_users AS legacy_users,
        n.total_active_users AS new_users,
        ABS(ZEROIFNULL(l.total_active_users) - ZEROIFNULL(n.total_active_users)) AS users_diff,
        
        l.total_phone_usage AS legacy_phone_hrs,
        n.total_phone_usage AS new_phone_hrs,
        ABS(ZEROIFNULL(l.total_phone_usage) - ZEROIFNULL(n.total_phone_usage)) AS phone_diff,
        
        l.row_count AS legacy_rows,
        n.row_count AS new_rows,
        ABS(ZEROIFNULL(l.row_count) - ZEROIFNULL(n.row_count)) AS row_diff
        
    FROM legacy_agg l
    FULL OUTER JOIN new_agg n
        ON l.date = n.date
        AND l.region = n.region
)

-- Return rows where variance exceeds 5% threshold
SELECT
    date,
    region,
    legacy_accounts,
    new_accounts,
    accounts_diff,
    ROUND(100.0 * accounts_diff / NULLIF(legacy_accounts, 0), 2) AS accounts_pct_diff,
    
    legacy_users,
    new_users,
    users_diff,
    ROUND(100.0 * users_diff / NULLIF(legacy_users, 0), 2) AS users_pct_diff,
    
    legacy_phone_hrs,
    new_phone_hrs,
    phone_diff,
    ROUND(100.0 * phone_diff / NULLIF(legacy_phone_hrs, 0), 2) AS phone_pct_diff,
    
    legacy_rows,
    new_rows,
    row_diff
    
FROM variance
WHERE
    -- Flag variance > 5% OR missing data in either model
    (accounts_diff > 0.05 * NULLIF(GREATEST(legacy_accounts, new_accounts), 0))
    OR (users_diff > 0.05 * NULLIF(GREATEST(legacy_users, new_users), 0))
    OR (phone_diff > 0.05 * NULLIF(GREATEST(legacy_phone_hrs, new_phone_hrs), 0))
    OR (legacy_accounts IS NULL OR new_accounts IS NULL)
    OR (legacy_users IS NULL OR new_users IS NULL)
ORDER BY date DESC, region
```

---

## 📄 **FILE 4:** `docs/gold_validation_checklist.md`

```markdown
# Gold Model Validation Checklist

## Pre-Deployment Validation

### 1. Schema Alignment
- [ ] Column count matches GLD_AGGREGATE (8 columns)
- [ ] Column order matches exactly (DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)
- [ ] Data types match target Gold table
- [ ] Nullability constraints validated

### 2. Grain Validation
- [ ] Unique combination of DATE × REGION × SEGMENT × IS_LICENSED confirmed
- [ ] No duplicate rows in output
- [ ] Aggregation logic tested with sample data

### 3. Business Rule Application
- [ ] BR-001: Date parsing tested (sample: '5/29/26 13:01' → 2026-05-29)
- [ ] BR-002: Active accounts aggregation verified (is_active = TRUE filter)
- [ ] BR-004: Active users aggregation verified (is_active = TRUE filter)
- [ ] BR-007: Region derivation from CLUSTER confirmed
- [ ] BR-008: Phone usage unit conversion tested (ms → hours ÷ 3,600,000)

### 4. Gap Documentation
- [ ] GAP-006 (SEGMENT): Documented in YAML and inline comments
- [ ] GAP-007 (IS_LICENSED): Documented in YAML and inline comments
- [ ] GAP-008 (USERS_ACTIVE_16PLUS_DAYS): Documented in YAML and inline comments
- [ ] Business stakeholders notified of assumptions

## Post-Deployment Validation

### 5. Functional Equivalence Test
```sql
-- Run: dbt test --select test_name:gold_functional_equivalence
```
- [ ] Row count variance < 20% (expected due to data source differences)
- [ ] Date range coverage matches legacy model
- [ ] REGION distribution similar to legacy
- [ ] Variance report reviewed and discrepancies explained

### 6. Data Quality Metrics
```sql
SELECT
    MIN(date) AS earliest_date,
    MAX(date) AS latest_date,
    COUNT(DISTINCT date) AS distinct_dates,
    COUNT(DISTINCT region) AS distinct_regions,
    SUM(active_accounts) AS total_accounts,
    SUM(active_users) AS total_users,
    SUM(phone_usage) AS total_phone_hours
FROM {{ ref('gld_aggregate_new') }};
```
- [ ] Date range: Expected start and end dates
- [ ] Region coverage: AMER, EMEA, APAC present
- [ ] No UNKNOWN regions (or < 5% if present)
- [ ] Active accounts/users > 0 for majority of rows
- [ ] Phone usage values reasonable (no extreme outliers)

### 7. Stakeholder Sign-Off
- [ ] Business Analytics Team reviewed GAP assumptions
- [ ] Data Platform Lead approved deployment plan
- [ ] End users validated sample output (spot checks)

## Known Limitations (Sign-Off Required)

| Gap ID | Column | Impact | Mitigation | Owner | Target Date |
|--------|--------|--------|------------|-------|-------------|
| GAP-006 | SEGMENT | All rows defaulted to 0 | Business to provide segment logic | Analytics | TBD |
| GAP-007 | IS_LICENSED | All rows defaulted to FALSE | Integrate license data source | Data Eng | TBD |
| GAP-008 | USERS_ACTIVE_16PLUS_DAYS | NULL for all rows | Build 30-day rolling window model | Analytics Eng | TBD |

## Rollback Plan
If functional equivalence test fails or critical issues identified:
1. Revert to legacy GLD_AGGREGATE immediately
2. Investigate discrepancies using variance query
3. Document root cause in GitHub issue
4. Fix and redeploy gld_aggregate_new after validation
```

---

## 🔍 **Post-Run Audit Query**

After deploying the Gold model, run this query to validate output:

```sql
-- ═══════════════════════════════════════════════════════════════════
-- GOLD MODEL VALIDATION QUERY
-- Purpose: Verify gld_aggregate_new output structure and data quality
-- ═══════════════════════════════════════════════════════════════════

SELECT
    '1. Row Count' AS metric_category,
    'Total Rows' AS metric_name,
    COUNT(*)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '2. Date Coverage' AS metric_category,
    'Date Range' AS metric_name,
    MIN(date)::TEXT || ' to ' || MAX(date)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '3. Region Distribution' AS metric_category,
    region AS metric_name,
    COUNT(*)::TEXT || ' rows' AS metric_value
FROM {{ ref('gld_aggregate_new') }}
GROUP BY region

UNION ALL

SELECT
    '4. Segment Values' AS metric_category,
    'Distinct Segments' AS metric_name,
    COUNT(DISTINCT segment)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '5. Aggregation Totals' AS metric_category,
    'Total Active Accounts' AS metric_name,
    SUM(active_accounts)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '5. Aggregation Totals' AS metric_category,
    'Total Active Users' AS metric_name,
    SUM(active_users)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '5. Aggregation Totals' AS metric_category,
    'Total Phone Hours' AS metric_name,
    ROUND(SUM(phone_usage), 2)::TEXT AS metric_value
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    '6. Gap Columns' AS metric_category,
    'Rows with NULL users_active_16plus_days' AS metric_name,
    COUNT(*)::TEXT || ' (' || ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM {{ ref('gld_aggregate_new') }}), 0), 1)::TEXT || '%)' AS metric_value
FROM {{ ref('gld_aggregate_new') }}
WHERE users_active_16plus_days IS NULL

ORDER BY metric_category, metric_name;
```

---

## ✅ **Summary**

**Generated Files:**
1. ✅ `models/gold/gld_aggregate_new.sql` — Aggregation model using medallion naming (NOT fct_ prefix)
2. ✅ `models/gold/gld_aggregate_new.yml` — Schema with tests + functional equivalence framework
3. ✅ `tests/gold_functional_equivalence.sql` — Variance analysis comparing new vs legacy
4. ✅ `docs/gold_validation_checklist.md` — Pre/post deployment validation steps

**Key Features:**
- ✅ Medallion naming: `gld_aggregate_new` (not `fct_gld_aggregate_new`)
- ✅ Config: `schema="GOLD"`, `materialized="table"`
- ✅ Silver ref: `{{ ref('slv_ftl_agent_base_agg') }}`
- ✅ Column order matches GLD_AGGREGATE exactly
- ✅ Inline comments: BR-IDs and GAP-IDs on every column
- ✅ ASSUMPTION flags for SEGMENT (GAP-006), IS_LICENSED (GAP-007), USERS_ACTIVE_16PLUS_DAYS (GAP-008)
- ✅ Snowflake-native functions: IFF(), ZEROIFNULL()
- ✅ Grain documented: DATE × REGION × SEGMENT × IS_LICENSED
- ✅ Functional equivalence test with 5% variance threshold

**Known Gaps Requiring Business Sign-Off:**
- **GAP-006**: SEGMENT defaulted to 0 (requires business classification logic)
- **GAP-007**: IS_LICENSED defaulted to FALSE (requires license data integration)
- **GAP-008**: USERS_ACTIVE_16PLUS_DAYS set to NULL (requires 30-day rolling window)

Run the validation checklist before deploying to production. Enable functional equivalence test after parallel run validation period.