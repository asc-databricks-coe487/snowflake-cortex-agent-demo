

⚙️ **STEP 4: Gold Schema Discovery** — Retrieving GLD_AGGREGATE column order to ensure exact match

⚙️ **STEP 5: Generating Gold Layer Code** — Building gld_aggregate_new.sql with {{ ref("slv_ftl_agent_base_agg") }}

⚙️ **STEP 5 (retry): Re-attempting Gold Code Generation** — Tool execution issue detected, retrying...

⚙️ **STEP 6: Manual Code Generation** — Tool issue detected; generating production-grade code manually using approved mapping

---

## **FILE 1: models/gold/gld_aggregate_new.sql**

```sql
{{
  config(
    materialized='table',
    schema='GOLD'
  )
}}

/* ═══════════════════════════════════════════════════════════════════
   GLD_AGGREGATE_NEW - Gold Layer Aggregate Model
   
   Purpose: Daily aggregate metrics by region, segment, and license status
   Grain:   DATE + REGION + SEGMENT + IS_LICENSED
   Source:  {{ ref('slv_ftl_agent_base_agg') }}
   
   Critical Gaps:
   - GAP-001: SEGMENT column missing in FTL (NULL placeholder)
   - GAP-006: IS_LICENSED column missing in FTL (NULL placeholder)
   - GAP-003: LATAM region not in FTL CLUSTER data
   
   Dependencies:
   - Requires SLV_FTL_AGENT_BASE_AGG (Silver layer)
   - Complex metric USERS_ACTIVE_16PLUS_DAYS requires intermediate 
     table SLV_USER_ACTIVE_DAYS (not yet implemented - returns NULL)
   ═══════════════════════════════════════════════════════════════════ */

WITH silver_base AS (
  SELECT
    date,
    region,
    account_id,
    user_id,
    is_active,
    inbound_phone_ms
  FROM {{ ref('slv_ftl_agent_base_agg') }}
),

aggregated AS (
  SELECT
    -- SOURCE: DATE from slv_ftl_agent_base_agg | CLASS: UNIT_CHANGE | BR: BR-001
    date,
    
    -- SOURCE: REGION from slv_ftl_agent_base_agg (derived from CLUSTER) | CLASS: DERIVED | BR: BR-012 | GAP: GAP-003
    region,
    
    -- GAP GAP-001: no FTL source — SEGMENT column missing in source data | CRITICAL
    NULL AS segment,
    
    -- GAP GAP-006: no FTL source — IS_LICENSED column missing in source data | CRITICAL
    NULL AS is_licensed,
    
    -- SOURCE: ACCOUNT_ID from slv_ftl_agent_base_agg | CLASS: GRAIN_CHANGE | BR: BR-013
    -- Count distinct active accounts per date/region/segment/license
    COUNT(DISTINCT IFF(is_active = TRUE, account_id, NULL)) AS active_accounts,
    
    -- SOURCE: USER_ID from slv_ftl_agent_base_agg (renamed from AGENT_ID) | CLASS: GRAIN_CHANGE | BR: BR-014, BR-009
    -- ASSUMPTION: AGENT_ID represents all users, not just support agents — VALIDATE WITH BUSINESS
    COUNT(DISTINCT IFF(is_active = TRUE, user_id, NULL)) AS active_users,
    
    -- SOURCE: INBOUND_PHONE_MS from slv_ftl_agent_base_agg | CLASS: UNIT_CHANGE | BR: BR-002
    -- Sum milliseconds and cast to FLOAT for Gold layer
    ZEROIFNULL(SUM(inbound_phone_ms))::FLOAT AS phone_usage,
    
    -- GAP: Requires SLV_USER_ACTIVE_DAYS intermediate table | CLASS: DERIVED | BR: BR-015
    -- ASSUMPTION: Rolling 29-day window calculation not yet implemented — returns NULL
    NULL AS users_active_16plus_days
    
  FROM silver_base
  GROUP BY
    date,
    region,
    segment,
    is_licensed
)

SELECT
  date,
  region,
  segment,
  is_licensed,
  active_accounts,
  active_users,
  phone_usage,
  users_active_16plus_days
FROM aggregated
ORDER BY date DESC, region, segment, is_licensed
```

---

## **FILE 2: models/gold/gld_aggregate_new.yml**

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold Layer - Daily Aggregate Metrics**
      
      Aggregates user and account activity metrics by date, region, segment, and license status.
      This is a parallel implementation to validate FTL data against existing PI Gold layer.
      
      **Grain:** DATE + REGION + SEGMENT + IS_LICENSED
      
      **Critical Gaps:**
      - GAP-001: SEGMENT column missing in FTL source (returns NULL)
      - GAP-006: IS_LICENSED column missing in FTL source (returns NULL)
      - GAP-003: LATAM region not present in FTL CLUSTER data
      - BR-015: USERS_ACTIVE_16PLUS_DAYS requires SLV_USER_ACTIVE_DAYS (not yet built)
      
      **Assumptions Requiring Business Validation:**
      - BR-009: AGENT_ID in FTL represents entire user population, not just support agents
      - BR-001: Date parsing assumes MM/DD/YY HH24:MI format
      
      **Source:** slv_ftl_agent_base_agg (Silver layer)
      
    config:
      materialized: table
      schema: GOLD
      tags: ['gold', 'aggregate', 'parallel_validation']
      
    columns:
      - name: date
        description: |
          Event date. Parsed from FTL DATA_DATE text field (MM/DD/YY HH24:MI format).
          **Business Rule:** BR-001
        data_type: DATE
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_of_type:
              column_type: DATE
      
      - name: region
        description: |
          Business region derived from AWS CLUSTER field via lookup mapping:
          - eu-central-1 → EMEA
          - ap-south-1 → APAC
          - us-east-1 → AMER
          - Unknown clusters → UNKNOWN
          
          **Business Rule:** BR-012
          **Gap:** GAP-003 - LATAM region not present in FTL source data
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['EMEA', 'APAC', 'AMER', 'UNKNOWN']
              quote: false
      
      - name: segment
        description: |
          Business segment classifier (e.g., Enterprise, SMB, Free).
          **CRITICAL GAP-001:** No FTL source column identified. Returns NULL.
          Requires business segmentation logic or external mapping table.
        data_type: NUMBER
        tests:
          - dbt_expectations.expect_column_values_to_be_null:
              row_condition: "1=1"  # Always NULL until gap resolved
      
      - name: is_licensed
        description: |
          Boolean flag indicating whether account has active paid license.
          **CRITICAL GAP-006:** No FTL source column identified. Returns NULL.
          Requires license status data from billing/entitlement system.
        data_type: BOOLEAN
        tests:
          - dbt_expectations.expect_column_values_to_be_null:
              row_condition: "1=1"  # Always NULL until gap resolved
      
      - name: active_accounts
        description: |
          Count of distinct accounts with IS_ACTIVE=TRUE for the given date/region/segment/license combination.
          **Business Rule:** BR-013
          **Source:** Aggregated from ACCOUNT_ID (BR-006)
        data_type: NUMBER
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 999999999
      
      - name: active_users
        description: |
          Count of distinct users with IS_ACTIVE=TRUE for the given date/region/segment/license combination.
          **Business Rule:** BR-014
          **Source:** Aggregated from USER_ID (renamed from AGENT_ID via BR-009)
          **ASSUMPTION:** AGENT_ID represents full user population, not just support agents.
          VALIDATE WITH BUSINESS before production use.
        data_type: NUMBER
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 999999999
      
      - name: phone_usage
        description: |
          Total inbound phone usage in milliseconds, aggregated and cast to FLOAT.
          **Business Rule:** BR-002
          **Source:** SUM(INBOUND_PHONE_MS) from Silver layer
        data_type: FLOAT
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 999999999999999
      
      - name: users_active_16plus_days
        description: |
          Count of distinct users active 16+ days within a rolling 29-day window.
          **Business Rule:** BR-015
          **CRITICAL:** Requires SLV_USER_ACTIVE_DAYS intermediate table (not yet implemented).
          Returns NULL until dependency is built.
          **Algorithm:** COUNT(DISTINCT USER_ID) WHERE active_days >= 16 IN ROLLING 29 DAY WINDOW
        data_type: NUMBER
        tests:
          - dbt_expectations.expect_column_values_to_be_null:
              row_condition: "1=1"  # Always NULL until BR-015 implemented

    tests:
      # Functional Equivalence Test: Compare gld_aggregate_new vs existing GLD_AGGREGATE
      - dbt_utils.equality:
          name: functional_equivalence_gld_aggregate_new_vs_existing
          description: |
            **FUNCTIONAL EQUIVALENCE TEST**
            
            Compares gld_aggregate_new (FTL-sourced) against existing GLD_AGGREGATE (PI-sourced)
            for overlapping date ranges and non-NULL dimensions.
            
            **Expected Outcome:**
            - PASS: Metrics match within tolerance for dimensions where FTL has complete data
            - FAIL: Highlights data gaps (SEGMENT, IS_LICENSED, USERS_ACTIVE_16PLUS_DAYS)
            
            **Manual Review Required:**
            1. Check row counts: expect LOWER in gld_aggregate_new due to NULL SEGMENT/IS_LICENSED
            2. Compare ACTIVE_ACCOUNTS and ACTIVE_USERS for matching date/region pairs
            3. Validate PHONE_USAGE sums align (allow ±5% variance for data latency)
            4. Document USERS_ACTIVE_16PLUS_DAYS as expected NULL in new model
            
            **Test SQL:**
            ```sql
            SELECT
              COALESCE(new.date, old.date) AS date,
              COALESCE(new.region, old.region) AS region,
              new.active_accounts AS new_active_accounts,
              old.active_accounts AS old_active_accounts,
              ABS(new.active_accounts - old.active_accounts) AS accounts_diff,
              new.active_users AS new_active_users,
              old.active_users AS old_active_users,
              ABS(new.active_users - old.active_users) AS users_diff,
              new.phone_usage AS new_phone_usage,
              old.phone_usage AS old_phone_usage,
              ABS(new.phone_usage - old.phone_usage) / NULLIF(old.phone_usage, 0) AS phone_usage_pct_diff
            FROM {{ ref('gld_aggregate_new') }} new
            FULL OUTER JOIN ZOOM_AI_POC.GOLD.GLD_AGGREGATE old
              ON new.date = old.date
              AND new.region = old.region
              AND new.segment IS NOT DISTINCT FROM old.segment
              AND new.is_licensed IS NOT DISTINCT FROM old.is_licensed
            WHERE
              new.date >= '2026-05-01'  -- Test recent data only
              AND (
                ABS(new.active_accounts - old.active_accounts) > 10  -- Allow ±10 accounts
                OR ABS(new.active_users - old.active_users) > 10     -- Allow ±10 users
                OR ABS(new.phone_usage - old.phone_usage) / NULLIF(old.phone_usage, 0) > 0.05  -- Allow ±5%
              )
            ORDER BY date DESC, region;
            ```
          compare_model: source('zoom_ai_poc_gold', 'GLD_AGGREGATE')
          compare_columns:
            - date
            - region
            # Exclude segment and is_licensed from comparison due to GAP-001 and GAP-006
            # - segment  # EXCLUDED - always NULL in new model
            # - is_licensed  # EXCLUDED - always NULL in new model
            - active_accounts
            - active_users
            - phone_usage
            # - users_active_16plus_days  # EXCLUDED - always NULL in new model
      
      # Grain Test: Ensure unique combination of date + region + segment + is_licensed
      - dbt_utils.unique_combination_of_columns:
          name: unique_grain_date_region_segment_license
          combination_of_columns:
            - date
            - region
            - segment
            - is_licensed
      
      # Recency Test: Ensure data is fresh (within 7 days of current date)
      - dbt_expectations.expect_table_row_count_to_be_between:
          name: recent_data_present
          min_value: 1
          row_condition: "date >= DATEADD(day, -7, CURRENT_DATE())"
      
      # Regional Coverage Test: Ensure all expected regions are present
      - dbt_expectations.expect_column_distinct_values_to_equal_set:
          name: expected_regions_present
          column_name: region
          value_set: ['EMEA', 'APAC', 'AMER', 'UNKNOWN']
          quote: false

sources:
  - name: zoom_ai_poc_gold
    database: ZOOM_AI_POC
    schema: GOLD
    description: "Existing PI Gold layer for functional equivalence testing"
    tables:
      - name: GLD_AGGREGATE
        description: "Legacy PI-sourced aggregate table for comparison testing"
```

---

## **Post-Deployment Validation Checklist**

After running `dbt run -s gld_aggregate_new` and `dbt test -s gld_aggregate_new`, execute this audit query:

```sql
-- ═══════════════════════════════════════════════════════════
-- POST-RUN AUDIT: Gold Layer Data Quality
-- ═══════════════════════════════════════════════════════════

-- 1. Row count and date range by region
SELECT
  region,
  COUNT(*) AS total_rows,
  MIN(date) AS first_date,
  MAX(date) AS last_date,
  SUM(active_accounts) AS total_active_accounts,
  SUM(active_users) AS total_active_users,
  SUM(phone_usage) AS total_phone_usage_ms
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
GROUP BY region
ORDER BY total_rows DESC;

-- 2. Verify GAP columns are NULL as expected
SELECT
  'SEGMENT' AS gap_column,
  COUNT(*) AS total_rows,
  COUNT(segment) AS non_null_rows,
  COUNT_IF(segment IS NULL) AS null_rows
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
UNION ALL
SELECT
  'IS_LICENSED' AS gap_column,
  COUNT(*) AS total_rows,
  COUNT(is_licensed) AS non_null_rows,
  COUNT_IF(is_licensed IS NULL) AS null_rows
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
UNION ALL
SELECT
  'USERS_ACTIVE_16PLUS_DAYS' AS gap_column,
  COUNT(*) AS total_rows,
  COUNT(users_active_16plus_days) AS non_null_rows,
  COUNT_IF(users_active_16plus_days IS NULL) AS null_rows
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW;

-- 3. Compare NEW vs EXISTING for most recent 7 days
WITH comparison AS (
  SELECT
    COALESCE(n.date, e.date) AS date,
    COALESCE(n.region, e.region) AS region,
    n.active_accounts AS new_accounts,
    e.active_accounts AS existing_accounts,
    n.active_accounts - e.active_accounts AS accounts_delta,
    n.active_users AS new_users,
    e.active_users AS existing_users,
    n.active_users - e.active_users AS users_delta,
    ROUND(n.phone_usage, 2) AS new_phone_usage,
    ROUND(e.phone_usage, 2) AS existing_phone_usage,
    ROUND(n.phone_usage - e.phone_usage, 2) AS phone_usage_delta
  FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW n
  FULL OUTER JOIN ZOOM_AI_POC.GOLD.GLD_AGGREGATE e
    ON n.date = e.date
    AND n.region = e.region
    AND n.segment IS NOT DISTINCT FROM e.segment
    AND n.is_licensed IS NOT DISTINCT FROM e.is_licensed
  WHERE COALESCE(n.date, e.date) >= DATEADD(day, -7, CURRENT_DATE())
)
SELECT *
FROM comparison
ORDER BY date DESC, region
LIMIT 100;

-- 4. Identify UNKNOWN regions requiring CLUSTER mapping fix
SELECT
  date,
  region,
  active_accounts,
  active_users
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE_NEW
WHERE region = 'UNKNOWN'
ORDER BY date DESC, active_accounts DESC
LIMIT 50;
```

---

⚙️ **STEP 7: Deliverables Complete** — Generated production-grade Gold model with functional equivalence test

## **Summary**

✅ **FILE 1:** `models/gold/gld_aggregate_new.sql`
- Uses `{{ ref("slv_ftl_agent_base_agg") }}` as source (not hardcoded schema)
- Config: `materialized='table'`, `schema='GOLD'`
- Column order matches GLD_AGGREGATE exactly (8 columns)
- Inline comments include BR IDs and GAP IDs on every column
- NULL placeholders for GAP-001 (SEGMENT), GAP-006 (IS_LICENSED), BR-015 (USERS_ACTIVE_16PLUS_DAYS)

✅ **FILE 2:** `models/gold/gld_aggregate_new.yml`
- Comprehensive column documentation with business rules and gap analysis
- **Functional equivalence test** comparing `gld_aggregate_new` vs existing `GLD_AGGREGATE`
- dbt tests: grain uniqueness, recency check, regional coverage, data type validation
- Test exclusions documented for NULL gap columns

✅ **Post-run audit queries** provided for validation

⚠️ **Critical Gaps Requiring Action:**
1. **GAP-001:** SEGMENT column - requires business segmentation logic or external mapping
2. **GAP-006:** IS_LICENSED column - requires integration with billing/entitlement system
3. **BR-015:** USERS_ACTIVE_16PLUS_DAYS - requires `SLV_USER_ACTIVE_DAYS` intermediate table with rolling 29-day window logic
4. **GAP-003:** LATAM region not in CLUSTER data - may require additional source or region mapping

⚠️ **Assumptions Requiring Business Validation:**
- **BR-009:** AGENT_ID = all users (not just support agents) — validate with product team before production use