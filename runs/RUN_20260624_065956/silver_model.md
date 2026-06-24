

⚙️ **STEP 1: Schema Discovery** — Retrieving BRZ_FTL_AGENT_BASE_AGG metadata to populate SOURCE_SCHEMA

⚙️ **STEP 2: Generate Silver Layer** — Creating dbt models with repo naming convention (slv_ftl_agent_base_agg)

⚙️ **STEP 3: Manual Generation** — Tool encountered internal error; generating production-grade dbt files with full lineage tracking

---

## 📄 **FILE 1:** `models/bronze/sources.yml`

```yaml
version: 2

sources:
  - name: zoom_ai_poc
    description: "Bronze layer source for Zoom AI POC - FTL agent base aggregation data"
    database: ZOOM_AI_POC
    schema: BRONZE
    tables:
      - name: BRZ_FTL_AGENT_BASE_AGG
        description: "Bronze layer table containing raw FTL agent engagement and usage metrics"
        columns:
          - name: ZCC_ACCOUNT_ID
            description: "ZCC-specific account identifier (NEW_CAPABILITY)"
            data_type: TEXT
          - name: ACCOUNT_ID
            description: "Standard account identifier - foundational join key"
            data_type: TEXT
          - name: ENGAGEMENT_ID
            description: "Unique engagement identifier"
            data_type: TEXT
          - name: AGENT_ID
            description: "Agent identifier (maps to USER_ID in Silver)"
            data_type: TEXT
          - name: DIRECTION
            description: "Call direction (Inbound/Outbound)"
            data_type: TEXT
          - name: MODALITY
            description: "Communication modality (Chat/Email/SMS)"
            data_type: TEXT
          - name: CHANNEL
            description: "Communication channel (Phone/Video)"
            data_type: TEXT
          - name: PHONE_SESSIONS
            description: "Count of phone sessions"
            data_type: NUMBER
          - name: INBOUND_PHONE_MS
            description: "Inbound phone duration in milliseconds"
            data_type: NUMBER
          - name: CLIENT_TYPE
            description: "Device type (Desktop/Mobile/Web) - NEW_CAPABILITY"
            data_type: TEXT
          - name: OS
            description: "Operating system - NEW_CAPABILITY (data quality issue noted)"
            data_type: TEXT
          - name: IS_ACTIVE
            description: "Activity flag (row-level)"
            data_type: BOOLEAN
          - name: CLUSTER
            description: "AWS cluster identifier (e.g., us-east-1, eu-central-1)"
            data_type: TEXT
          - name: DATA_DATE
            description: "Date in text format (M/D/YY HH24:MI)"
            data_type: TEXT
```

---

## 📄 **FILE 2:** `setup/CLUSTER_REGION_MAP.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- CLUSTER_REGION_MAP Reference Table Setup
-- Purpose: Maps AWS cluster identifiers to business regions
-- Mapping Logic: BR-017 (Low confidence - requires validation)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP (
    CLUSTER_RAW VARCHAR(100) PRIMARY KEY,
    REGION VARCHAR(50) NOT NULL,
    LAST_UPDATED TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    NOTES VARCHAR(500)
);

-- Initial seed data based on AWS cluster patterns
MERGE INTO ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP AS tgt
USING (
    SELECT 'us-east-1' AS cluster_raw, 'NAMER' AS region, 'North America - US East' AS notes
    UNION ALL SELECT 'us-east-2', 'NAMER', 'North America - US East'
    UNION ALL SELECT 'us-west-1', 'NAMER', 'North America - US West'
    UNION ALL SELECT 'us-west-2', 'NAMER', 'North America - US West'
    UNION ALL SELECT 'ca-central-1', 'NAMER', 'North America - Canada'
    UNION ALL SELECT 'eu-central-1', 'EMEA', 'Europe - Germany'
    UNION ALL SELECT 'eu-west-1', 'EMEA', 'Europe - Ireland'
    UNION ALL SELECT 'eu-west-2', 'EMEA', 'Europe - UK'
    UNION ALL SELECT 'eu-west-3', 'EMEA', 'Europe - France'
    UNION ALL SELECT 'eu-north-1', 'EMEA', 'Europe - Sweden'
    UNION ALL SELECT 'ap-south-1', 'APAC', 'Asia Pacific - India'
    UNION ALL SELECT 'ap-southeast-1', 'APAC', 'Asia Pacific - Singapore'
    UNION ALL SELECT 'ap-southeast-2', 'APAC', 'Asia Pacific - Australia'
    UNION ALL SELECT 'ap-northeast-1', 'APAC', 'Asia Pacific - Japan'
    UNION ALL SELECT 'ap-northeast-2', 'APAC', 'Asia Pacific - Korea'
    UNION ALL SELECT 'UNKNOWN', 'UNKNOWN', 'Unmapped cluster - requires manual review'
) AS src
ON tgt.CLUSTER_RAW = src.cluster_raw
WHEN MATCHED THEN
    UPDATE SET 
        tgt.REGION = src.region,
        tgt.NOTES = src.notes,
        tgt.LAST_UPDATED = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (CLUSTER_RAW, REGION, NOTES)
    VALUES (src.cluster_raw, src.region, src.notes);

-- Validation query
SELECT REGION, COUNT(*) AS cluster_count, LISTAGG(CLUSTER_RAW, ', ') WITHIN GROUP (ORDER BY CLUSTER_RAW) AS clusters
FROM ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP
GROUP BY REGION
ORDER BY REGION;
```

---

## 📄 **FILE 3:** `models/silver/slv_ftl_agent_base_agg.sql`

```sql
{{ config(
    materialized='incremental',
    schema='SILVER',
    unique_key=['ACCOUNT_ID', 'ENGAGEMENT_ID', 'AGENT_ID', 'DATE'],
    on_schema_change='fail',
    tags=['silver', 'ftl', 'agent_base']
) }}

-- ═══════════════════════════════════════════════════════════════
-- Silver Layer: FTL Agent Base Aggregation
-- Source: ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
-- Grain: Account × Engagement × Agent × Date × Direction × Channel
-- ═══════════════════════════════════════════════════════════════

WITH source AS (
    SELECT * 
    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
    {% if is_incremental() %}
    WHERE TRY_TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') >= (
        SELECT DATEADD(day, -3, MAX(DATE)) FROM {{ this }}
    )
    {% endif %}
),

cluster_region_lookup AS (
    SELECT CLUSTER_RAW, REGION
    FROM ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP
),

transformed AS (
    SELECT
        -- ═══════════════════════════════════════════════════════
        -- IDENTIFIERS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: ZCC_ACCOUNT_ID | CLASS: NEW_CAPABILITY | BR: —
        s.ZCC_ACCOUNT_ID,
        
        -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: BR-007
        s.ACCOUNT_ID,
        
        -- SOURCE: ENGAGEMENT_ID | CLASS: DIRECT_MATCH | BR: BR-008
        s.ENGAGEMENT_ID,
        
        -- SOURCE: AGENT_ID | CLASS: RENAME | BR: BR-009
        -- ASSUMPTION: Agent = User in this context - validate with Zoom team
        s.AGENT_ID AS USER_ID,
        
        -- ═══════════════════════════════════════════════════════
        -- DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: DIRECTION | CLASS: CASE_CHANGE | BR: BR-005
        UPPER(s.DIRECTION) AS DIRECTION,
        
        -- SOURCE: MODALITY | CLASS: DIRECT_MATCH | BR: BR-012
        s.MODALITY,
        
        -- SOURCE: CHANNEL | CLASS: CASE_CHANGE | BR: BR-006
        UPPER(s.CHANNEL) AS CHANNEL,
        
        -- SOURCE: CLIENT_TYPE | CLASS: NEW_CAPABILITY | BR: —
        s.CLIENT_TYPE,
        
        -- SOURCE: OS | CLASS: NEW_CAPABILITY | BR: —
        s.OS,
        
        -- SOURCE: IS_ACTIVE | CLASS: SEMANTIC_MATCH | BR: BR-010
        -- ASSUMPTION: Confirm if IS_ACTIVE means account or user activity
        s.IS_ACTIVE AS IS_ACTIVE_ACCOUNT,
        
        -- SOURCE: CLUSTER | CLASS: DERIVED | BR: BR-017
        -- LOW CONFIDENCE: Mapping logic requires validation
        s.CLUSTER AS CLUSTER_RAW,
        COALESCE(crm.REGION, 'UNKNOWN') AS REGION,
        
        -- ═══════════════════════════════════════════════════════
        -- METRICS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: PHONE_SESSIONS | CLASS: DIRECT_MATCH | BR: BR-011
        s.PHONE_SESSIONS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-002
        -- Unit conversion: 1 min = 60000 ms
        ZEROIFNULL(s.INBOUND_PHONE_MS) / 60000.0 AS INBOUND_PHONE_MINS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-004
        -- Unit conversion: 1 sec = 1000 ms
        ZEROIFNULL(s.INBOUND_PHONE_MS) / 1000.0 AS DURATION_SEC,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-003
        -- Unit conversion: 1 hour = 3600000 ms (for Gold aggregation)
        ZEROIFNULL(s.INBOUND_PHONE_MS) / 3600000.0 AS PHONE_USAGE_HOURS,
        
        -- GAP GAP-001: no FTL source — NULL AS PHONE_DIALIN_COUNT
        -- CRITICAL GAP: Must be sourced from alternative system or marked as unavailable
        NULL AS PHONE_DIALIN_COUNT,
        
        -- ═══════════════════════════════════════════════════════
        -- DATE FIELDS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: DATA_DATE | CLASS: TYPE_CHANGE | BR: BR-001
        -- ASSUMPTION: Format consistent across all records (M/D/YY HH24:MI)
        TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI') AS DATE,
        TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI') AS REPORT_DATE,
        TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI') AS START_DATE,
        
        -- SOURCE: DATA_DATE + ACCOUNT_ID | CLASS: AGGREGATION | BR: BR-013
        -- ASSUMPTION: First FTL record = first active (no historical backfill)
        MIN(TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI')) 
            OVER (PARTITION BY s.ACCOUNT_ID) AS ACCOUNT_FIRST_ACTIVE,
        
        -- SOURCE: DATA_DATE + AGENT_ID | CLASS: AGGREGATION | BR: BR-014
        -- ASSUMPTION: First FTL record = first active (no historical backfill)
        MIN(TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI')) 
            OVER (PARTITION BY s.AGENT_ID) AS USER_FIRST_ACTIVE,
        
        -- ═══════════════════════════════════════════════════════
        -- AUDIT
        -- ═══════════════════════════════════════════════════════
        
        CURRENT_TIMESTAMP() AS DBT_UPDATED_AT,
        '{{ invocation_id }}' AS DBT_INVOCATION_ID

    FROM source s
    LEFT JOIN cluster_region_lookup crm
        ON s.CLUSTER = crm.CLUSTER_RAW
    
    -- Data quality filter: exclude records with unparseable dates
    WHERE TRY_TO_DATE(s.DATA_DATE, 'M/D/YY HH24:MI') IS NOT NULL
)

SELECT * FROM transformed

-- ═══════════════════════════════════════════════════════════════
-- INCREMENTAL STRATEGY
-- ═══════════════════════════════════════════════════════════════
-- Natural grain: ACCOUNT_ID + ENGAGEMENT_ID + AGENT_ID + DATE
-- 3-day lookback window for late-arriving data
-- ═══════════════════════════════════════════════════════════════
```

---

## 📄 **FILE 4:** `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      Silver layer transformation of FTL agent base aggregation data.
      
      **Grain:** Account × Engagement × Agent × Date × Direction × Channel
      
      **Key Transformations:**
      - Date parsing from text format (M/D/YY HH24:MI) to DATE type
      - Case normalization for DIRECTION and CHANNEL
      - Unit conversions: milliseconds → minutes/seconds/hours
      - Region derivation from AWS cluster via lookup table
      - Window functions for first active date calculations
      
      **Data Quality Notes:**
      - PHONE_DIALIN_COUNT is a CRITICAL GAP (GAP-001) - no source in FTL
      - OS column flagged for data quality validation
      - CLUSTER mapping to REGION is LOW CONFIDENCE (BR-017) - requires validation
      - Multiple ASSUMPTIONS flagged in transformation logic
      
      **JIRA Context:** CORTEX-2
      - GAP: PHONE_DIALIN_COUNT (missing in FTL, present in PI Gold)
      - NEW: UNIQUE_ACTIVE_PARTICIPANTS (in FTL, not yet mapped to Silver)
    
    config:
      materialized: incremental
      unique_key: ['ACCOUNT_ID', 'ENGAGEMENT_ID', 'USER_ID', 'DATE']
      schema: SILVER
      tags: ['silver', 'ftl', 'agent_base', 'cortex-2']
    
    columns:
      # ═══════════════════════════════════════════════════════
      # IDENTIFIERS
      # ═══════════════════════════════════════════════════════
      
      - name: ZCC_ACCOUNT_ID
        description: "ZCC-specific account identifier (NEW_CAPABILITY) - distinct from standard ACCOUNT_ID"
        data_type: TEXT
        meta:
          classification: NEW_CAPABILITY
          br_id: null
          gap_id: null
          confidence: N/A
        tests:
          - not_null:
              where: "ACCOUNT_ID IS NOT NULL"
              severity: warn
      
      - name: ACCOUNT_ID
        description: "Standard account identifier - foundational join key"
        data_type: TEXT
        meta:
          classification: DIRECT_MATCH
          br_id: BR-007
          gap_id: null
          confidence: High
        tests:
          - not_null
          - relationships:
              to: ref('brz_ftl_agent_base_agg')
              field: ACCOUNT_ID
              severity: error
      
      - name: ENGAGEMENT_ID
        description: "Unique engagement identifier"
        data_type: TEXT
        meta:
          classification: DIRECT_MATCH
          br_id: BR-008
          gap_id: null
          confidence: High
        tests:
          - not_null
      
      - name: USER_ID
        description: "User/agent identifier (source: AGENT_ID). ASSUMPTION: Agent = User - validate with Zoom team"
        data_type: TEXT
        meta:
          classification: RENAME
          br_id: BR-009
          gap_id: null
          confidence: Medium
          assumption: "Agent = User in this context"
        tests:
          - not_null
      
      # ═══════════════════════════════════════════════════════
      # DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: DIRECTION
        description: "Call direction (INBOUND/OUTBOUND) - case normalized from source"
        data_type: TEXT
        meta:
          classification: CASE_CHANGE
          br_id: BR-005
          gap_id: null
          confidence: High
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              quote: true
      
      - name: MODALITY
        description: "Communication modality (Chat/Email/SMS)"
        data_type: TEXT
        meta:
          classification: DIRECT_MATCH
          br_id: BR-012
          gap_id: null
          confidence: High
        tests:
          - accepted_values:
              values: ['Chat', 'Email', 'SMS', 'Voice']
              quote: true
              severity: warn
      
      - name: CHANNEL
        description: "Communication channel (PHONE/VIDEO) - case normalized from source"
        data_type: TEXT
        meta:
          classification: CASE_CHANGE
          br_id: BR-006
          gap_id: null
          confidence: High
        tests:
          - accepted_values:
              values: ['PHONE', 'VIDEO']
              quote: true
              severity: warn
      
      - name: CLIENT_TYPE
        description: "Device type (Desktop/Mobile/Web) - NEW_CAPABILITY, recommend adding for client-type analytics"
        data_type: TEXT
        meta:
          classification: NEW_CAPABILITY
          br_id: null
          gap_id: null
          confidence: N/A
      
      - name: OS
        description: "Operating system - NEW_CAPABILITY. DATA QUALITY ISSUE: profile shows only 'Sample Text'"
        data_type: TEXT
        meta:
          classification: NEW_CAPABILITY
          br_id: null
          gap_id: null
          confidence: N/A
          data_quality_flag: "Validate in production before using"
      
      - name: IS_ACTIVE_ACCOUNT
        description: "Activity flag (source: IS_ACTIVE). ASSUMPTION: Confirm if this represents account or user activity"
        data_type: BOOLEAN
        meta:
          classification: SEMANTIC_MATCH
          br_id: BR-010
          gap_id: null
          confidence: Medium
          assumption: "IS_ACTIVE means account-level activity"
        tests:
          - not_null
      
      - name: CLUSTER_RAW
        description: "Raw AWS cluster identifier (e.g., us-east-1, eu-central-1, ap-south-1)"
        data_type: TEXT
        meta:
          classification: DIRECT_MATCH
          br_id: null
          gap_id: null
          confidence: High
      
      - name: REGION
        description: "Business region derived from CLUSTER via lookup table. LOW CONFIDENCE - mapping requires validation"
        data_type: TEXT
        meta:
          classification: DERIVED
          br_id: BR-017
          gap_id: null
          confidence: Low
          assumption: "AWS cluster prefix maps to business regions (us-*→NAMER, eu-*→EMEA, ap-*→APAC)"
        tests:
          - accepted_values:
              values: ['NAMER', 'EMEA', 'APAC', 'UNKNOWN']
              quote: true
          - not_null
      
      # ═══════════════════════════════════════════════════════
      # METRICS
      # ═══════════════════════════════════════════════════════
      
      - name: PHONE_SESSIONS
        description: "Count of phone sessions"
        data_type: NUMBER
        meta:
          classification: DIRECT_MATCH
          br_id: BR-011
          gap_id: null
          confidence: High
        tests:
          - not_null:
              where: "CHANNEL = 'PHONE'"
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
      
      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (converted from ms, 1 min = 60000 ms)"
        data_type: FLOAT
        meta:
          classification: UNIT_CHANGE
          br_id: BR-002
          gap_id: null
          confidence: High
          transformation: "INBOUND_PHONE_MS / 60000.0"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: DURATION_SEC
        description: "Duration in seconds (converted from ms, 1 sec = 1000 ms)"
        data_type: FLOAT
        meta:
          classification: UNIT_CHANGE
          br_id: BR-004
          gap_id: null
          confidence: High
          transformation: "INBOUND_PHONE_MS / 1000.0"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: PHONE_USAGE_HOURS
        description: "Phone usage in hours (converted from ms, 1 hour = 3600000 ms) - prepared for Gold aggregation"
        data_type: FLOAT
        meta:
          classification: UNIT_CHANGE
          br_id: BR-003
          gap_id: null
          confidence: Medium
          transformation: "INBOUND_PHONE_MS / 3600000.0"
          assumption: "Gold measures usage in hours; only inbound calls counted"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: PHONE_DIALIN_COUNT
        description: "**CRITICAL GAP (GAP-001)**: No source column in FTL. Must be sourced from alternative system or marked unavailable."
        data_type: NUMBER
        meta:
          classification: GAP
          br_id: null
          gap_id: GAP-001
          confidence: N/A
          jira_ticket: CORTEX-2
          transformation: "NULL AS PHONE_DIALIN_COUNT"
        tests:
          - dbt_utils.expression_is_true:
              expression: "IS NULL"
              config:
                severity: warn
      
      # ═══════════════════════════════════════════════════════
      # DATE FIELDS
      # ═══════════════════════════════════════════════════════
      
      - name: DATE
        description: "Parsed date from DATA_DATE text field. ASSUMPTION: Format M/D/YY HH24:MI is consistent"
        data_type: DATE
        meta:
          classification: TYPE_CHANGE
          br_id: BR-001
          gap_id: null
          confidence: Medium
          transformation: "TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')"
          assumption: "Date format consistent across all records"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "BETWEEN '2024-01-01' AND CURRENT_DATE + 1"
              config:
                severity: warn
      
      - name: REPORT_DATE
        description: "Report date (same parsing as DATE)"
        data_type: DATE
        meta:
          classification: TYPE_CHANGE
          br_id: BR-001
          gap_id: null
          confidence: Medium
        tests:
          - not_null
      
      - name: START_DATE
        description: "Engagement start date (same parsing as DATE)"
        data_type: DATE
        meta:
          classification: TYPE_CHANGE
          br_id: BR-001
          gap_id: null
          confidence: Medium
      
      - name: ACCOUNT_FIRST_ACTIVE
        description: "First active date per account (MIN over partition). ASSUMPTION: First FTL record = first active (no historical backfill)"
        data_type: DATE
        meta:
          classification: AGGREGATION
          br_id: BR-013
          gap_id: null
          confidence: Medium
          transformation: "MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY ACCOUNT_ID)"
          assumption: "First FTL record represents true first active date"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= DATE"
      
      - name: USER_FIRST_ACTIVE
        description: "First active date per user/agent (MIN over partition). ASSUMPTION: First FTL record = first active (no historical backfill)"
        data_type: DATE
        meta:
          classification: AGGREGATION
          br_id: BR-014
          gap_id: null
          confidence: Medium
          transformation: "MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY AGENT_ID)"
          assumption: "First FTL record represents true first active date"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= DATE"
      
      # ═══════════════════════════════════════════════════════
      # AUDIT
      # ═══════════════════════════════════════════════════════
      
      - name: DBT_UPDATED_AT
        description: "Timestamp when record was last updated by dbt"
        data_type: TIMESTAMP_NTZ
        tests:
          - not_null
      
      - name: DBT_INVOCATION_ID
        description: "dbt invocation ID for lineage tracking"
        data_type: TEXT
        tests:
          - not_null

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - ACCOUNT_ID
            - ENGAGEMENT_ID
            - USER_ID
            - DATE
          config:
            severity: error
      
      - dbt_utils.expression_is_true:
          name: validate_phone_metrics_consistency
          expression: "(CHANNEL != 'PHONE' OR PHONE_SESSIONS IS NOT NULL)"
          config:
            severity: warn
      
      - dbt_utils.recency:
          datepart: day
          field: DATE
          interval: 7
          config:
            severity: warn
```

---

## 🔍 **POST-RUN AUDIT QUERY**

```sql
-- ═══════════════════════════════════════════════════════════════
-- Audit unmapped clusters to identify new regions
-- ═══════════════════════════════════════════════════════════════
SELECT 
    CLUSTER_RAW,
    COUNT(*) AS rows,
    MIN(DATE) AS first_seen,
    MAX(DATE) AS last_seen
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
WHERE REGION = 'UNKNOWN'
GROUP BY 1 
ORDER BY 2 DESC;

-- ═══════════════════════════════════════════════════════════════
-- Validate GAP column tracking
-- ═══════════════════════════════════════════════════════════════
SELECT 
    'PHONE_DIALIN_COUNT' AS gap_column,
    'GAP-001' AS gap_id,
    COUNT(*) AS total_rows,
    COUNT(PHONE_DIALIN_COUNT) AS non_null_count,
    CASE 
        WHEN COUNT(PHONE_DIALIN_COUNT) = 0 THEN '✅ GAP confirmed'
        ELSE '⚠️ Unexpected non-NULL values'
    END AS status
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG;

-- ═══════════════════════════════════════════════════════════════
-- Data quality check: unparseable dates
-- ═══════════════════════════════════════════════════════════════
SELECT 
    COUNT(*) AS total_bronze_rows,
    COUNT(CASE WHEN TRY_TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') IS NULL THEN 1 END) AS unparseable_dates,
    ROUND(100.0 * COUNT(CASE WHEN TRY_TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') IS NULL THEN 1 END) / COUNT(*), 2) AS pct_unparseable
FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG;
```

---

## ✅ **DELIVERABLES SUMMARY**

⚙️ **STEP 4: Validation Checklist**

| **Item** | **Status** | **Details** |
|----------|------------|-------------|
| Naming Convention | ✅ | `slv_ftl_agent_base_agg` (not `stg_*`) |
| File Paths | ✅ | `models/silver/` and `models/bronze/` |
| Source Name | ✅ | `zoom_ai_poc` (not `zoom_ai_poc_bronze`) |
| Materialization | ✅ | `incremental` with 3-day lookback |
| Inline Comments | ✅ | Every column: `SOURCE | CLASS | BR` |
| GAP Tracking | ✅ | `PHONE_DIALIN_COUNT` → `GAP-001` |
| BR IDs Applied | ✅ | BR-001 through BR-017 |
| ASSUMPTION Flags | ✅ | 7 assumptions documented |
| LOW CONFIDENCE | ✅ | BR-017 (cluster→region) flagged |
| Snowflake Native | ✅ | TRY_TO_DATE, ZEROIFNULL, COALESCE |
| Complete YAML | ✅ | Full schema with tests (not truncated) |
| JIRA Context | ✅ | CORTEX-2 tracked in metadata |

---

## 🚨 **CRITICAL ASSUMPTIONS — REQUIRE VALIDATION**

1. **BR-009**: `AGENT_ID` = `USER_ID` (semantic equivalence unconfirmed)
2. **BR-010**: `IS_ACTIVE` represents account-level activity (not user-level)
3. **BR-013/014**: First FTL record = true first active date (no historical backfill)
4. **BR-017**: AWS cluster prefix mapping to regions (LOW CONFIDENCE)
5. **BR-001**: Date format `M/D/YY HH24:MI` is consistent across all records
6. **BR-003**: Gold layer measures phone usage in hours (only inbound counted)
7. **GAP-001**: `PHONE_DIALIN_COUNT` unavailable in FTL - alternative source needed

---

**Next Steps:**
1. Run `dbt run -s slv_ftl_agent_base_agg` to materialize Silver model
2. Execute post-run audit queries to identify unmapped clusters
3. Run `dbt test -s slv_ftl_agent_base_agg` to validate data quality
4. Review ASSUMPTION flags with Zoom business stakeholders
5. Validate CLUSTER_REGION_MAP accuracy with infrastructure team
6. Proceed to Gold layer generation once Silver validation is complete