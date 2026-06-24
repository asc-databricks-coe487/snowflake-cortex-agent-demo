

I'll generate the dbt Gold layer model for you. Let me follow the required steps:

⚙️ **STEP 1: Schema Discovery for Gold Layer** — Retrieving GLD_AGGREGATE column metadata to ensure exact column order match

⚙️ **STEP 2: Generate Gold Model** — Creating production-grade dbt Gold model with functional equivalence test

⚙️ **STEP 3: Manual Generation** — Tool encountered internal error; generating production-grade dbt Gold files with full lineage tracking and GAP documentation

---

## 📄 **FILE 1:** `models/gold/gld_aggregate_new.sql`

```sql
{{
    config(
        materialized="table",
        schema="GOLD",
        tags=["gold", "aggregate", "daily"]
    )
}}

-- ═══════════════════════════════════════════════════════════════════════════════
-- Gold Model: gld_aggregate_new
-- Purpose: Daily aggregated metrics by region for account and user activity
-- Source: Silver layer slv_ftl_agent_base_agg
-- Grain: DATE + REGION (daily regional aggregation)
-- 
-- JIRA: CORTEX-2 - GAP columns tracked with GAP IDs
-- ═══════════════════════════════════════════════════════════════════════════════

WITH silver_base AS (
    SELECT
        DATE,
        REGION,
        ACCOUNT_ID,
        USER_ID,
        PHONE_USAGE,
        IS_ACTIVE
    FROM {{ ref("slv_ftl_agent_base_agg") }}
    WHERE DATE IS NOT NULL
      AND REGION IS NOT NULL
),

aggregated AS (
    SELECT
        -- SOURCE: Silver.DATE | CLASS: DIRECT_MATCH | BR: BR-001
        DATE,
        
        -- SOURCE: Silver.REGION | CLASS: DIRECT_MATCH | BR: BR-017
        REGION,
        
        -- GAP GAP-002: No source column - business segmentation logic missing
        NULL AS SEGMENT,
        
        -- GAP GAP-003: No licensing information in FTL source data
        NULL AS IS_LICENSED,
        
        -- SOURCE: Silver.ACCOUNT_ID | CLASS: AGGREGATION | BR: BR-020
        COUNT(DISTINCT IFF(IS_ACTIVE = TRUE, ACCOUNT_ID, NULL)) AS ACTIVE_ACCOUNTS,
        
        -- SOURCE: Silver.USER_ID | CLASS: AGGREGATION | BR: BR-021
        COUNT(DISTINCT IFF(IS_ACTIVE = TRUE, USER_ID, NULL)) AS ACTIVE_USERS,
        
        -- SOURCE: Silver.PHONE_USAGE | CLASS: AGGREGATION | BR: BR-003
        -- ASSUMPTION: Already converted to hours in Silver layer
        ZEROIFNULL(SUM(IFF(IS_ACTIVE = TRUE, PHONE_USAGE, 0))) AS PHONE_USAGE,
        
        -- GAP GAP-004: Requires historical 29-day rolling window calculation
        NULL AS USERS_ACTIVE_16PLUS_DAYS
        
    FROM silver_base
    GROUP BY
        DATE,
        REGION
)

SELECT
    DATE,              -- Grain: daily
    REGION,            -- Grain: regional grouping
    SEGMENT,           -- CRITICAL GAP: Requires business segmentation rules
    IS_LICENSED,       -- CRITICAL GAP: Requires licensing data integration  
    ACTIVE_ACCOUNTS,   -- COUNT(DISTINCT) of active accounts
    ACTIVE_USERS,      -- COUNT(DISTINCT) of active users
    PHONE_USAGE,       -- SUM of phone usage in hours
    USERS_ACTIVE_16PLUS_DAYS  -- CRITICAL GAP: Requires SLV_ROLL_29_DAY_USAGE integration
FROM aggregated
ORDER BY DATE DESC, REGION

-- ═══════════════════════════════════════════════════════════════════════════════
-- TRACKED GAPS FROM JIRA CORTEX-2:
-- GAP-001: PHONE_DIALIN_COUNT - No dial-in count metric in FTL (not in schema)
-- GAP-002: SEGMENT - No segmentation logic available
-- GAP-003: IS_LICENSED - No licensing data in source
-- GAP-004: USERS_ACTIVE_16PLUS_DAYS - Requires rolling window from SLV_ROLL_29_DAY_USAGE
-- 
-- NEW CAPABILITIES NOT INCLUDED (for future):
-- - UNIQUE_ACTIVE_PARTICIPANTS (available in Silver but not in PI Gold schema)
-- - CLIENT_TYPE segmentation
-- - OS segmentation
-- ═══════════════════════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 2:** `models/gold/gld_aggregate_new.yml`

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold Layer: Daily Aggregated Metrics by Region**
      
      Business Purpose: Daily rollup of account and user activity metrics segmented by region.
      
      **Grain**: DATE + REGION (one row per day per region)
      
      **Source Lineage**:
      - Bronze: BRZ_FTL_AGENT_BASE_AGG
      - Silver: slv_ftl_agent_base_agg
      - Gold: gld_aggregate_new (this model)
      
      **JIRA Context**: CORTEX-2 - Migration from PI to FTL data source
      
      **Known Gaps** (tracked with GAP IDs):
      - GAP-001: PHONE_DIALIN_COUNT - Not available in FTL source
      - GAP-002: SEGMENT - Business segmentation logic not defined
      - GAP-003: IS_LICENSED - Licensing data not in FTL
      - GAP-004: USERS_ACTIVE_16PLUS_DAYS - Requires 29-day rolling window (SLV_ROLL_29_DAY_USAGE)
      
      **Validation Status**: Functional equivalence test included (see test: gold_functional_equivalence)
    
    config:
      materialized: table
      schema: GOLD
      tags: ["gold", "aggregate", "daily", "migration"]
    
    columns:
      - name: DATE
        description: "Business date for aggregation (daily grain)"
        data_type: DATE
        tests:
          - not_null
          - dbt_utils.at_least_one
        meta:
          source: "Silver.DATE"
          br_id: "BR-001"
          classification: "DIRECT_MATCH"
      
      - name: REGION
        description: "Business region derived from cluster mapping (e.g., US_EAST, EU_CENTRAL, APAC)"
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['US_EAST', 'US_WEST', 'EU_CENTRAL', 'APAC', 'UNKNOWN']
              quote: true
        meta:
          source: "Silver.REGION"
          br_id: "BR-017"
          classification: "DIRECT_MATCH"
          confidence: "Medium - requires CLUSTER_REGION_MAP validation"
      
      - name: SEGMENT
        description: "**GAP-002**: Business segment (NULL - segmentation logic not defined in FTL)"
        data_type: NUMBER
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100
              inclusive: true
              where: "SEGMENT IS NOT NULL"
        meta:
          gap_id: "GAP-002"
          classification: "GAP"
          severity: "CRITICAL"
          action_required: "Define business segmentation rules and source data"
      
      - name: IS_LICENSED
        description: "**GAP-003**: Licensed account flag (NULL - licensing data not in FTL source)"
        data_type: BOOLEAN
        meta:
          gap_id: "GAP-003"
          classification: "GAP"
          severity: "CRITICAL"
          action_required: "Integrate licensing data from billing/entitlement system"
      
      - name: ACTIVE_ACCOUNTS
        description: "Count of distinct active accounts (WHERE IS_ACTIVE = TRUE)"
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              inclusive: true
        meta:
          source: "Silver.ACCOUNT_ID"
          br_id: "BR-020"
          classification: "AGGREGATION"
          transformation: "COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = TRUE"
      
      - name: ACTIVE_USERS
        description: "Count of distinct active users/agents (WHERE IS_ACTIVE = TRUE)"
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              inclusive: true
        meta:
          source: "Silver.USER_ID (from FTL AGENT_ID)"
          br_id: "BR-021"
          classification: "AGGREGATION"
          transformation: "COUNT(DISTINCT USER_ID) WHERE IS_ACTIVE = TRUE"
      
      - name: PHONE_USAGE
        description: "Total phone usage in hours (aggregated from Silver PHONE_USAGE)"
        data_type: FLOAT
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              inclusive: true
        meta:
          source: "Silver.PHONE_USAGE (converted from FTL INBOUND_PHONE_MS)"
          br_id: "BR-003"
          classification: "AGGREGATION"
          transformation: "SUM(PHONE_USAGE) - already in hours from Silver"
          unit: "hours"
      
      - name: USERS_ACTIVE_16PLUS_DAYS
        description: "**GAP-004**: Users active 16+ days in trailing 29 days (NULL - requires rolling window)"
        data_type: NUMBER
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              inclusive: true
              where: "USERS_ACTIVE_16PLUS_DAYS IS NOT NULL"
        meta:
          gap_id: "GAP-004"
          classification: "GAP"
          severity: "CRITICAL"
          action_required: "Integrate with SLV_ROLL_29_DAY_USAGE or implement rolling window logic"
          related_table: "ZOOM_AI_POC.SILVER.SLV_ROLL_29_DAY_USAGE"

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - DATE
            - REGION
          name: gold_unique_date_region
      
      - dbt_utils.expression_is_true:
          expression: "ACTIVE_USERS >= 0 AND ACTIVE_ACCOUNTS >= 0"
          name: gold_non_negative_counts
      
      - dbt_utils.expression_is_true:
          expression: "PHONE_USAGE >= 0"
          name: gold_non_negative_usage

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTIONAL EQUIVALENCE TEST: gld_aggregate_new vs GLD_AGGREGATE
# ═══════════════════════════════════════════════════════════════════════════════

seeds:
  - name: gold_functional_equivalence_test
    description: |
      **Functional Equivalence Test**: Compares gld_aggregate_new against GLD_AGGREGATE
      
      **Purpose**: Validate migration from PI to FTL data source
      
      **Test Scope**:
      - Row count comparison by DATE + REGION
      - PHONE_USAGE delta analysis (tolerance: ±5% due to unit conversion rounding)
      - ACTIVE_ACCOUNTS and ACTIVE_USERS variance
      - Identify dates with significant differences
      
      **Expected Gaps** (will show as differences):
      - SEGMENT: NULL in new model (GAP-002)
      - IS_LICENSED: NULL in new model (GAP-003)
      - USERS_ACTIVE_16PLUS_DAYS: NULL in new model (GAP-004)
      
      **Run Command**:
      ```bash
      dbt test --select gold_functional_equivalence_test
      ```

tests:
  - name: gold_functional_equivalence_test
    description: "Compares key metrics between gld_aggregate_new and GLD_AGGREGATE"
    config:
      severity: warn
      error_if: ">100"
      warn_if: ">10"
    test:
      sql: |
        WITH new_model AS (
            SELECT
                DATE,
                REGION,
                ACTIVE_ACCOUNTS,
                ACTIVE_USERS,
                PHONE_USAGE
            FROM {{ ref('gld_aggregate_new') }}
            WHERE DATE >= '2026-01-01'  -- Test recent data only
        ),
        
        old_model AS (
            SELECT
                DATE,
                REGION,
                ACTIVE_ACCOUNTS,
                ACTIVE_USERS,
                PHONE_USAGE
            FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
            WHERE DATE >= '2026-01-01'
        ),
        
        comparison AS (
            SELECT
                COALESCE(n.DATE, o.DATE) AS DATE,
                COALESCE(n.REGION, o.REGION) AS REGION,
                n.ACTIVE_ACCOUNTS AS new_active_accounts,
                o.ACTIVE_ACCOUNTS AS old_active_accounts,
                n.ACTIVE_USERS AS new_active_users,
                o.ACTIVE_USERS AS old_active_users,
                n.PHONE_USAGE AS new_phone_usage,
                o.PHONE_USAGE AS old_phone_usage,
                
                -- Delta calculations
                ABS(ZEROIFNULL(n.ACTIVE_ACCOUNTS) - ZEROIFNULL(o.ACTIVE_ACCOUNTS)) AS accounts_delta,
                ABS(ZEROIFNULL(n.ACTIVE_USERS) - ZEROIFNULL(o.ACTIVE_USERS)) AS users_delta,
                ABS(ZEROIFNULL(n.PHONE_USAGE) - ZEROIFNULL(o.PHONE_USAGE)) AS usage_delta,
                
                -- Percentage difference (tolerance: 5%)
                CASE
                    WHEN o.PHONE_USAGE = 0 THEN 0
                    ELSE ABS((n.PHONE_USAGE - o.PHONE_USAGE) / NULLIF(o.PHONE_USAGE, 0)) * 100
                END AS usage_pct_diff,
                
                -- Row presence flags
                IFF(n.DATE IS NULL, 'MISSING_IN_NEW', 
                    IFF(o.DATE IS NULL, 'MISSING_IN_OLD', 'BOTH')) AS row_status
                
            FROM new_model n
            FULL OUTER JOIN old_model o
                ON n.DATE = o.DATE
                AND n.REGION = o.REGION
        )
        
        SELECT
            DATE,
            REGION,
            row_status,
            new_active_accounts,
            old_active_accounts,
            accounts_delta,
            new_active_users,
            old_active_users,
            users_delta,
            new_phone_usage,
            old_phone_usage,
            usage_delta,
            ROUND(usage_pct_diff, 2) AS usage_pct_diff
        FROM comparison
        WHERE
            -- Flag significant differences or missing rows
            row_status != 'BOTH'
            OR accounts_delta > 10
            OR users_delta > 10
            OR usage_pct_diff > 5.0  -- More than 5% difference
        ORDER BY DATE DESC, REGION
```

---

## 📊 **POST-RUN VALIDATION CHECKLIST**

After deploying the Gold model, run these validation queries:

### **1. Row Count & Date Range Comparison**
```sql
-- Compare row counts between old and new Gold models
SELECT 
    'GLD_AGGREGATE (Old)' AS model,
    COUNT(*) AS row_count,
    MIN(DATE) AS first_date,
    MAX(DATE) AS last_date,
    COUNT(DISTINCT REGION) AS region_count
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE

UNION ALL

SELECT 
    'gld_aggregate_new' AS model,
    COUNT(*) AS row_count,
    MIN(DATE) AS first_date,
    MAX(DATE) AS last_date,
    COUNT(DISTINCT REGION) AS region_count
FROM {{ ref('gld_aggregate_new') }}

ORDER BY model;
```

### **2. Gap Column Verification**
```sql
-- Verify GAP columns are properly NULL
SELECT
    'SEGMENT' AS gap_column,
    'GAP-002' AS gap_id,
    COUNT(*) AS total_rows,
    COUNT(SEGMENT) AS non_null_count,
    IFF(COUNT(SEGMENT) = 0, '✅ PASS', '❌ FAIL') AS test_result
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    'IS_LICENSED',
    'GAP-003',
    COUNT(*),
    COUNT(IS_LICENSED),
    IFF(COUNT(IS_LICENSED) = 0, '✅ PASS', '❌ FAIL')
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT
    'USERS_ACTIVE_16PLUS_DAYS',
    'GAP-004',
    COUNT(*),
    COUNT(USERS_ACTIVE_16PLUS_DAYS),
    IFF(COUNT(USERS_ACTIVE_16PLUS_DAYS) = 0, '✅ PASS', '❌ FAIL')
FROM {{ ref('gld_aggregate_new') }};
```

### **3. Phone Usage Aggregation Validation**
```sql
-- Validate PHONE_USAGE aggregation from Silver to Gold
WITH silver_agg AS (
    SELECT
        DATE,
        REGION,
        SUM(PHONE_USAGE) AS silver_phone_usage_sum,
        COUNT(*) AS silver_row_count
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    WHERE IS_ACTIVE = TRUE
    GROUP BY DATE, REGION
),

gold AS (
    SELECT
        DATE,
        REGION,
        PHONE_USAGE AS gold_phone_usage
    FROM {{ ref('gld_aggregate_new') }}
)

SELECT
    g.DATE,
    g.REGION,
    s.silver_phone_usage_sum,
    g.gold_phone_usage,
    ABS(s.silver_phone_usage_sum - g.gold_phone_usage) AS delta,
    s.silver_row_count,
    IFF(ABS(s.silver_phone_usage_sum - g.gold_phone_usage) < 0.01, '✅ PASS', '❌ FAIL') AS test_result
FROM gold g
INNER JOIN silver_agg s
    ON g.DATE = s.DATE
    AND g.REGION = s.REGION
WHERE ABS(s.silver_phone_usage_sum - g.gold_phone_usage) >= 0.01
ORDER BY delta DESC
LIMIT 20;
```

### **4. Active Accounts & Users Validation**
```sql
-- Validate distinct count logic
WITH silver_counts AS (
    SELECT
        DATE,
        REGION,
        COUNT(DISTINCT IFF(IS_ACTIVE = TRUE, ACCOUNT_ID, NULL)) AS silver_active_accounts,
        COUNT(DISTINCT IFF(IS_ACTIVE = TRUE, USER_ID, NULL)) AS silver_active_users
    FROM {{ ref('slv_ftl_agent_base_agg') }}
    GROUP BY DATE, REGION
),

gold_counts AS (
    SELECT
        DATE,
        REGION,
        ACTIVE_ACCOUNTS,
        ACTIVE_USERS
    FROM {{ ref('gld_aggregate_new') }}
)

SELECT
    g.DATE,
    g.REGION,
    s.silver_active_accounts,
    g.ACTIVE_ACCOUNTS AS gold_active_accounts,
    s.silver_active_users,
    g.ACTIVE_USERS AS gold_active_users,
    IFF(s.silver_active_accounts = g.ACTIVE_ACCOUNTS, '✅', '❌') AS accounts_match,
    IFF(s.silver_active_users = g.ACTIVE_USERS, '✅', '❌') AS users_match
FROM gold_counts g
INNER JOIN silver_counts s
    ON g.DATE = s.DATE
    AND g.REGION = s.REGION
WHERE s.silver_active_accounts != g.ACTIVE_ACCOUNTS
   OR s.silver_active_users != g.ACTIVE_USERS
ORDER BY g.DATE DESC
LIMIT 20;
```

---

## 🎯 **SUMMARY: Gold Layer Generation**

✅ **Generated Files**:
1. `models/gold/gld_aggregate_new.sql` — Daily aggregated metrics by region
2. `models/gold/gld_aggregate_new.yml` — Schema documentation with functional equivalence test

✅ **Naming Convention Compliance**:
- Model name: `gld_aggregate_new` (NOT `fct_gld_aggregate_new`)
- File path: `models/gold/` (NOT `models/marts/`)
- Silver ref: `{{ ref("slv_ftl_agent_base_agg") }}`
- Config: `schema="GOLD"`, `materialized="table"`

✅ **GAP Columns Tracked** (per JIRA CORTEX-2):
- **GAP-001**: PHONE_DIALIN_COUNT (not in schema, documented in notes)
- **GAP-002**: SEGMENT (NULL with CRITICAL GAP comment)
- **GAP-003**: IS_LICENSED (NULL with CRITICAL GAP comment)
- **GAP-004**: USERS_ACTIVE_16PLUS_DAYS (NULL with CRITICAL GAP comment)

✅ **Business Rules Applied**:
- **BR-001**: DATE pass-through from Silver
- **BR-003**: PHONE_USAGE aggregation (SUM, already in hours)
- **BR-017**: REGION from cluster mapping
- **BR-020**: ACTIVE_ACCOUNTS = COUNT(DISTINCT ACCOUNT_ID WHERE IS_ACTIVE)
- **BR-021**: ACTIVE_USERS = COUNT(DISTINCT USER_ID WHERE IS_ACTIVE)

✅ **Data Quality Tests**:
- Uniqueness: DATE + REGION composite key
- Non-null: DATE, REGION, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE
- Range validation: All counts and usage >= 0
- Functional equivalence test vs GLD_AGGREGATE (tolerance: 5%)

🔄 **Next Steps**:
1. Deploy: `dbt run --select gld_aggregate_new`
2. Test: `dbt test --select gld_aggregate_new`
3. Run validation queries above
4. Review functional equivalence test results
5. Document GAP resolution plan with business stakeholders