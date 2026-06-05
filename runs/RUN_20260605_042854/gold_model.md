

⚙️ **STEP 1**: Schema Discovery — Retrieved GLD_AGGREGATE target schema (8 columns: DATE, REGION, SEGMENT, IS_LICENSED, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, USERS_ACTIVE_16PLUS_DAYS)

⚙️ **STEP 2**: Gap Analysis — Identified 3 CRITICAL GAPS requiring business rules: SEGMENT, IS_LICENSED, USERS_ACTIVE_16PLUS_DAYS

⚙️ **STEP 3**: Aggregation Logic — Gold model aggregates Silver (slv_ftl_agent_base_agg) by DATE + REGION with COUNT DISTINCT for active accounts/users

⚙️ **STEP 4**: Code Generation — Producing gld_aggregate_new.sql + .yml with functional equivalence test per repo standards

---

## **FILE 1: models/gold/gld_aggregate_new.sql**

```sql
{{
  config(
    materialized='table',
    schema='GOLD'
  )
}}

-- ═══════════════════════════════════════════════════════════════════
-- gld_aggregate_new.sql
-- Purpose: Gold-layer aggregate fact table for daily usage metrics by region
-- Source:  {{ ref("slv_ftl_agent_base_agg") }}
-- Grain:   DATE + REGION (daily regional aggregation)
-- ═══════════════════════════════════════════════════════════════════

WITH silver_base AS (
  SELECT
    date,
    region,
    account_id,
    user_id,
    is_active,
    inbound_phone_mins,
    phone_sessions
  FROM {{ ref("slv_ftl_agent_base_agg") }}
  WHERE date IS NOT NULL  -- Filter out invalid dates
),

daily_region_agg AS (
  SELECT
    date,
    region,
    
    -- ACTIVE_ACCOUNTS: Count distinct active accounts per day/region
    -- SOURCE: account_id + is_active | CLASS: AGGREGATION | BR: BR-003 | GAP: GAP-003
    COUNT(DISTINCT CASE 
      WHEN is_active = TRUE THEN account_id 
    END) AS active_accounts,
    
    -- ACTIVE_USERS: Count distinct active users (agents) per day/region
    -- SOURCE: user_id + is_active | CLASS: AGGREGATION | BR: BR-004 | GAP: GAP-004
    COUNT(DISTINCT CASE 
      WHEN is_active = TRUE THEN user_id 
    END) AS active_users,
    
    -- PHONE_USAGE: Sum of inbound phone minutes per day/region
    -- SOURCE: inbound_phone_mins | CLASS: AGGREGATION | BR: BR-002
    ZEROIFNULL(SUM(inbound_phone_mins)) AS phone_usage
    
  FROM silver_base
  GROUP BY 1, 2
)

SELECT
  -- DATE: Event date dimension
  -- SOURCE: date (from Silver) | CLASS: DIRECT_MATCH | BR: BR-001
  date AS DATE,
  
  -- REGION: Business region dimension (EMEA, APAC, NAMER, LATAM, UNKNOWN)
  -- SOURCE: region (mapped from CLUSTER in Silver) | CLASS: SEMANTIC_MATCH | BR: BR-005
  region AS REGION,
  
  -- SEGMENT: Customer segment dimension
  -- GAP: GAP-001 | CRITICAL GAP: No FTL source identified
  NULL AS SEGMENT,  -- GAP GAP-001: CRITICAL GAP — requires business rule definition
  
  -- IS_LICENSED: Licensed account flag
  -- GAP: GAP-002 | CRITICAL GAP: No FTL source identified
  NULL AS IS_LICENSED,  -- GAP GAP-002: CRITICAL GAP — requires business rule definition
  
  -- ACTIVE_ACCOUNTS: Count of distinct active accounts
  -- SOURCE: Aggregated from account_id WHERE is_active | CLASS: AGGREGATION | BR: BR-003 | GAP: GAP-003
  -- ASSUMPTION: Active account count based on IS_ACTIVE flag — VALIDATE WITH BUSINESS
  active_accounts AS ACTIVE_ACCOUNTS,
  
  -- ACTIVE_USERS: Count of distinct active users/agents
  -- SOURCE: Aggregated from user_id WHERE is_active | CLASS: AGGREGATION | BR: BR-004 | GAP: GAP-004
  -- ASSUMPTION: Active user count based on IS_ACTIVE flag — VALIDATE WITH BUSINESS
  active_users AS ACTIVE_USERS,
  
  -- PHONE_USAGE: Total inbound phone minutes
  -- SOURCE: inbound_phone_mins | CLASS: AGGREGATION | BR: BR-002
  TRY_CAST(phone_usage AS FLOAT) AS PHONE_USAGE,
  
  -- USERS_ACTIVE_16PLUS_DAYS: Count of users active 16+ days in period
  -- GAP: GAP-005 | CRITICAL GAP: No FTL source or logic for 16+ day activity threshold
  NULL AS USERS_ACTIVE_16PLUS_DAYS  -- GAP GAP-005: CRITICAL GAP — requires historical activity tracking

FROM daily_region_agg
ORDER BY date DESC, region
```

---

## **FILE 2: models/gold/gld_aggregate_new.yml**

```yaml
version: 2

models:
  - name: gld_aggregate_new
    description: |
      **Gold-layer aggregate fact table** — Daily usage metrics by region
      
      **Grain**: DATE + REGION (one row per day per region)
      
      **Source**: {{ ref("slv_ftl_agent_base_agg") }}
      
      **Business Rules**:
      - BR-001: Date transformation from FTL TEXT format
      - BR-002: Phone usage aggregated from inbound minutes (converted from MS in Silver)
      - BR-003: Active accounts counted via IS_ACTIVE flag (ASSUMPTION)
      - BR-004: Active users counted via IS_ACTIVE flag (ASSUMPTION)
      - BR-005: Region mapped from AWS cluster codes
      
      **Critical Gaps**:
      - GAP-001: SEGMENT dimension missing — NULL placeholder
      - GAP-002: IS_LICENSED dimension missing — NULL placeholder
      - GAP-005: USERS_ACTIVE_16PLUS_DAYS metric missing — NULL placeholder
      
      **Validation Required**:
      1. Verify IS_ACTIVE flag logic aligns with business definition of "active"
      2. Define SEGMENT business rule (e.g., SMB, Enterprise, Commercial)
      3. Define IS_LICENSED business rule (subscription status)
      4. Define 16+ day activity threshold logic (requires historical tracking)
    
    config:
      materialized: table
      schema: GOLD
      tags:
        - gold
        - aggregate
        - daily
        - usage_metrics
    
    columns:
      - name: DATE
        description: "Event date (daily grain)"
        data_type: DATE
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2026-01-01'"
              config:
                severity: warn
        meta:
          source_column: "DATA_DATE (Bronze) → date (Silver)"
          br_id: "BR-001"
          transformation: "TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')"
      
      - name: REGION
        description: "Business region (EMEA, APAC, NAMER, LATAM, UNKNOWN)"
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['EMEA', 'APAC', 'NAMER', 'LATAM', 'UNKNOWN']
              config:
                severity: warn
        meta:
          source_column: "CLUSTER (Bronze) → region (Silver)"
          br_id: "BR-005"
          confidence: "LOW"
          validation_note: "UNKNOWN values require cluster→region mapping updates"
      
      - name: SEGMENT
        description: "Customer segment dimension (CRITICAL GAP — no source)"
        data_type: NUMBER
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: error
                error_if: ">0"
                warn_if: ">0"
        meta:
          gap_id: "GAP-001"
          status: "CRITICAL_GAP"
          resolution: "Requires business rule definition for customer segmentation"
      
      - name: IS_LICENSED
        description: "Licensed account flag (CRITICAL GAP — no source)"
        data_type: BOOLEAN
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: error
                error_if: ">0"
                warn_if: ">0"
        meta:
          gap_id: "GAP-002"
          status: "CRITICAL_GAP"
          resolution: "Requires business rule definition for license status"
      
      - name: ACTIVE_ACCOUNTS
        description: "Count of distinct active accounts (ASSUMPTION: based on IS_ACTIVE flag)"
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
        meta:
          source_column: "account_id (Silver)"
          br_id: "BR-003"
          gap_id: "GAP-003"
          aggregation: "COUNT(DISTINCT CASE WHEN is_active THEN account_id END)"
          assumption: "IS_ACTIVE flag accurately represents active account status"
          validation_required: true
      
      - name: ACTIVE_USERS
        description: "Count of distinct active users/agents (ASSUMPTION: based on IS_ACTIVE flag)"
        data_type: NUMBER
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
        meta:
          source_column: "user_id (Silver)"
          br_id: "BR-004"
          gap_id: "GAP-004"
          aggregation: "COUNT(DISTINCT CASE WHEN is_active THEN user_id END)"
          assumption: "IS_ACTIVE flag accurately represents active user status"
          validation_required: true
      
      - name: PHONE_USAGE
        description: "Total inbound phone minutes (aggregated from Silver inbound_phone_mins)"
        data_type: FLOAT
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
        meta:
          source_column: "inbound_phone_mins (Silver) ← INBOUND_PHONE_MS (Bronze)"
          br_id: "BR-002"
          aggregation: "SUM(inbound_phone_mins)"
          transformation: "MS → minutes conversion applied in Silver layer"
      
      - name: USERS_ACTIVE_16PLUS_DAYS
        description: "Count of users active 16+ days in period (CRITICAL GAP — no source)"
        data_type: NUMBER
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: error
                error_if: ">0"
                warn_if: ">0"
        meta:
          gap_id: "GAP-005"
          status: "CRITICAL_GAP"
          resolution: "Requires historical daily activity tracking to calculate 16+ day threshold"

# ═══════════════════════════════════════════════════════════════════
# FUNCTIONAL EQUIVALENCE TEST
# Purpose: Compare gld_aggregate_new vs existing GLD_AGGREGATE
# Validates row counts, metric totals, and identifies deltas
# ═══════════════════════════════════════════════════════════════════

tests:
  - name: functional_equivalence_row_count
    description: "Validates that gld_aggregate_new has comparable row count to GLD_AGGREGATE"
    test_sql: |
      WITH new_model AS (
        SELECT COUNT(*) AS row_count
        FROM {{ ref('gld_aggregate_new') }}
      ),
      existing_table AS (
        SELECT COUNT(*) AS row_count
        FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
      ),
      comparison AS (
        SELECT
          n.row_count AS new_count,
          e.row_count AS existing_count,
          n.row_count - e.row_count AS delta,
          ROUND(ABS(n.row_count - e.row_count) / NULLIF(e.row_count, 0) * 100, 2) AS delta_pct
        FROM new_model n
        CROSS JOIN existing_table e
      )
      SELECT *
      FROM comparison
      WHERE delta_pct > 10  -- Flag if >10% difference
    config:
      severity: warn

  - name: functional_equivalence_phone_usage_total
    description: "Validates that total PHONE_USAGE in gld_aggregate_new matches GLD_AGGREGATE within tolerance"
    test_sql: |
      WITH new_model AS (
        SELECT
          ZEROIFNULL(SUM(phone_usage)) AS total_phone_usage
        FROM {{ ref('gld_aggregate_new') }}
      ),
      existing_table AS (
        SELECT
          ZEROIFNULL(SUM(phone_usage)) AS total_phone_usage
        FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
      ),
      comparison AS (
        SELECT
          n.total_phone_usage AS new_total,
          e.total_phone_usage AS existing_total,
          n.total_phone_usage - e.total_phone_usage AS delta,
          ROUND(ABS(n.total_phone_usage - e.total_phone_usage) / NULLIF(e.total_phone_usage, 0) * 100, 2) AS delta_pct
        FROM new_model n
        CROSS JOIN existing_table e
      )
      SELECT *
      FROM comparison
      WHERE delta_pct > 5  -- Flag if >5% difference
    config:
      severity: warn

  - name: functional_equivalence_date_range
    description: "Validates that date ranges are comparable between models"
    test_sql: |
      WITH new_model AS (
        SELECT
          MIN(date) AS min_date,
          MAX(date) AS max_date,
          COUNT(DISTINCT date) AS distinct_dates
        FROM {{ ref('gld_aggregate_new') }}
      ),
      existing_table AS (
        SELECT
          MIN(date) AS min_date,
          MAX(date) AS max_date,
          COUNT(DISTINCT date) AS distinct_dates
        FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
      ),
      comparison AS (
        SELECT
          n.min_date AS new_min_date,
          e.min_date AS existing_min_date,
          n.max_date AS new_max_date,
          e.max_date AS existing_max_date,
          n.distinct_dates AS new_distinct_dates,
          e.distinct_dates AS existing_distinct_dates,
          n.distinct_dates - e.distinct_dates AS date_count_delta
        FROM new_model n
        CROSS JOIN existing_table e
      )
      SELECT *
      FROM comparison
      WHERE ABS(date_count_delta) > 0  -- Flag if date counts differ
    config:
      severity: warn

  - name: functional_equivalence_region_coverage
    description: "Validates that region distribution is similar between models"
    test_sql: |
      WITH new_model AS (
        SELECT
          region,
          COUNT(*) AS row_count,
          SUM(active_accounts) AS total_active_accounts,
          SUM(active_users) AS total_active_users
        FROM {{ ref('gld_aggregate_new') }}
        GROUP BY 1
      ),
      existing_table AS (
        SELECT
          region,
          COUNT(*) AS row_count,
          SUM(active_accounts) AS total_active_accounts,
          SUM(active_users) AS total_active_users
        FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE
        GROUP BY 1
      ),
      comparison AS (
        SELECT
          COALESCE(n.region, e.region) AS region,
          n.row_count AS new_row_count,
          e.row_count AS existing_row_count,
          n.total_active_accounts AS new_active_accounts,
          e.total_active_accounts AS existing_active_accounts,
          n.total_active_users AS new_active_users,
          e.total_active_users AS existing_active_users,
          ROUND(ABS(COALESCE(n.total_active_accounts, 0) - COALESCE(e.total_active_accounts, 0)) / 
                NULLIF(e.total_active_accounts, 0) * 100, 2) AS active_accounts_delta_pct
        FROM new_model n
        FULL OUTER JOIN existing_table e ON n.region = e.region
      )
      SELECT *
      FROM comparison
      WHERE active_accounts_delta_pct > 10 OR new_row_count IS NULL OR existing_row_count IS NULL
    config:
      severity: warn
```

---

## **Post-Run Validation Checklist**

After deploying `gld_aggregate_new`, execute these validation queries:

### **1. Row Count & Date Range Comparison**
```sql
SELECT 
  'NEW MODEL' AS source,
  COUNT(*) AS row_count,
  COUNT(DISTINCT date) AS distinct_dates,
  MIN(date) AS min_date,
  MAX(date) AS max_date
FROM {{ ref('gld_aggregate_new') }}

UNION ALL

SELECT 
  'EXISTING TABLE' AS source,
  COUNT(*) AS row_count,
  COUNT(DISTINCT date) AS distinct_dates,
  MIN(date) AS min_date,
  MAX(date) AS max_date
FROM ZOOM_AI_POC.GOLD.GLD_AGGREGATE;
```

### **2. Region Distribution & UNKNOWN Values**
```sql
SELECT 
  region,
  COUNT(*) AS row_count,
  SUM(active_accounts) AS total_active_accounts,
  SUM(active_users) AS total_active_users,
  SUM(phone_usage) AS total_phone_usage,
  ROUND(SUM(phone_usage) / NULLIF(SUM(active_users), 0), 2) AS avg_phone_usage_per_user
FROM {{ ref('gld_aggregate_new') }}
GROUP BY region
ORDER BY total_phone_usage DESC;
```

### **3. CRITICAL GAP Verification**
```sql
SELECT 
  COUNT(*) AS total_rows,
  COUNT(CASE WHEN segment IS NOT NULL THEN 1 END) AS segment_populated,
  COUNT(CASE WHEN is_licensed IS NOT NULL THEN 1 END) AS is_licensed_populated,
  COUNT(CASE WHEN users_active_16plus_days IS NOT NULL THEN 1 END) AS users_16plus_populated,
  -- All should be 0 until gaps resolved
  COUNT(CASE WHEN segment IS NULL THEN 1 END) AS segment_nulls,
  COUNT(CASE WHEN is_licensed IS NULL THEN 1 END) AS is_licensed_nulls,
  COUNT(CASE WHEN users_active_16plus_days IS NULL THEN 1 END) AS users_16plus_nulls
FROM {{ ref('gld_aggregate_new') }};
```

### **4. Active Accounts/Users Validation**
```sql
-- Verify active counts align with business expectations
SELECT 
  date,
  region,
  active_accounts,
  active_users,
  phone_usage,
  ROUND(phone_usage / NULLIF(active_users, 0), 2) AS phone_usage_per_user
FROM {{ ref('gld_aggregate_new') }}
WHERE date >= DATEADD(day, -7, CURRENT_DATE)
ORDER BY date DESC, region;
```

---

## **⚠️ CRITICAL ASSUMPTIONS — BUSINESS VALIDATION REQUIRED**

| Assumption | Impact | Validation Action |
|-----------|--------|-------------------|
| **IS_ACTIVE flag = Active Account/User** | Defines ACTIVE_ACCOUNTS and ACTIVE_USERS metrics | Confirm with business: Does IS_ACTIVE accurately represent active status? |
| **REGION mapping from CLUSTER** | 'UNKNOWN' values will appear for unmapped clusters | Run post-run audit query to identify unmapped clusters and update CLUSTER_REGION_MAP |
| **SEGMENT = NULL** | GAP-001: No customer segmentation | Define business rule: SMB/Enterprise/Commercial logic |
| **IS_LICENSED = NULL** | GAP-002: No license status tracking | Define business rule: Subscription/license status source |
| **USERS_ACTIVE_16PLUS_DAYS = NULL** | GAP-005: No 16+ day activity metric | Define business rule: Requires daily activity history |

---

## **Deployment Commands**

```bash
# Run Silver model first (if not already deployed)
dbt run --select slv_ftl_agent_base_agg

# Run Gold model
dbt run --select gld_aggregate_new

# Run all functional equivalence tests
dbt test --select gld_aggregate_new

# Generate documentation
dbt docs generate
```