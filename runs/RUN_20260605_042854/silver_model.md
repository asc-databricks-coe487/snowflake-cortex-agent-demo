

⚙️ **STEP 1**: Schema Discovery — Retrieved BRZ_FTL_AGENT_BASE_AGG schema (14 columns verified)

⚙️ **STEP 2**: Code Generation — dbt_code_generator tool unavailable; generating production-grade dbt files manually using approved mapping CSV

⚙️ **STEP 3**: Applying Repo Standards — Using slv_ prefix, models/silver/ path, source("zoom_ai_poc"), incremental materialization

⚙️ **STEP 4**: Inline Documentation — Every column annotated with SOURCE, CLASS, BR ID per requirements

---

## **FILE 1: models/bronze/sources.yml**

```yaml
version: 2

sources:
  - name: zoom_ai_poc
    description: "Bronze layer source tables for Zoom AI POC — raw data from FTL ingestion"
    database: ZOOM_AI_POC
    schema: BRONZE
    tables:
      - name: BRZ_FTL_AGENT_BASE_AGG
        description: "FTL agent-level usage aggregation with engagement, channel, and phone session metrics"
        columns:
          - name: DATA_DATE
            description: "Event date in TEXT format (M/D/YY HH24:MI)"
            data_type: TEXT
          - name: ACCOUNT_ID
            description: "Unique account identifier"
            data_type: TEXT
          - name: AGENT_ID
            description: "Unique agent/user identifier"
            data_type: TEXT
          - name: IS_ACTIVE
            description: "Account active status flag"
            data_type: BOOLEAN
          - name: PHONE_SESSIONS
            description: "Count of phone sessions"
            data_type: NUMBER
          - name: INBOUND_PHONE_MS
            description: "Inbound phone duration in milliseconds"
            data_type: NUMBER
          - name: CLUSTER
            description: "AWS region code (e.g., eu-central-1, us-east-1)"
            data_type: TEXT
          - name: ZCC_ACCOUNT_ID
            description: "Zoom Contact Center account identifier"
            data_type: TEXT
          - name: ENGAGEMENT_ID
            description: "Unique engagement identifier"
            data_type: TEXT
          - name: DIRECTION
            description: "Engagement direction (Inbound, Outbound)"
            data_type: TEXT
          - name: MODALITY
            description: "Communication modality (SMS, Email, Chat)"
            data_type: TEXT
          - name: CHANNEL
            description: "Communication channel (Video, Phone)"
            data_type: TEXT
          - name: CLIENT_TYPE
            description: "Client device type (Mobile, Desktop, Web)"
            data_type: TEXT
          - name: OS
            description: "Operating system"
            data_type: TEXT
```

---

## **FILE 2: setup/CLUSTER_REGION_MAP.sql**

```sql
-- ═══════════════════════════════════════════════════════════════════
-- CLUSTER_REGION_MAP.sql
-- Purpose: Reference table for AWS cluster → business region mapping
-- BR-005: Maps FTL CLUSTER codes to PI REGION dimension
-- Confidence: LOW — requires business validation for completeness
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP (
    CLUSTER_CODE VARCHAR(50) PRIMARY KEY,
    REGION VARCHAR(20) NOT NULL,
    REGION_DESCRIPTION VARCHAR(100),
    IS_VERIFIED BOOLEAN DEFAULT FALSE,
    LAST_UPDATED TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Populate initial mappings from BR-005
MERGE INTO ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP AS target
USING (
    SELECT 'eu-central-1' AS CLUSTER_CODE, 'EMEA' AS REGION, 'Europe, Middle East, Africa' AS REGION_DESCRIPTION, FALSE AS IS_VERIFIED
    UNION ALL
    SELECT 'ap-south-1', 'APAC', 'Asia Pacific', FALSE
    UNION ALL
    SELECT 'us-east-1', 'NAMER', 'North America', FALSE
    UNION ALL
    SELECT 'us-west-2', 'NAMER', 'North America', FALSE
    UNION ALL
    SELECT 'eu-west-1', 'EMEA', 'Europe, Middle East, Africa', FALSE
    UNION ALL
    SELECT 'ap-southeast-1', 'APAC', 'Asia Pacific', FALSE
    UNION ALL
    SELECT 'sa-east-1', 'LATAM', 'Latin America', FALSE
) AS source
ON target.CLUSTER_CODE = source.CLUSTER_CODE
WHEN MATCHED THEN
    UPDATE SET
        target.REGION = source.REGION,
        target.REGION_DESCRIPTION = source.REGION_DESCRIPTION,
        target.LAST_UPDATED = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (CLUSTER_CODE, REGION, REGION_DESCRIPTION, IS_VERIFIED)
    VALUES (source.CLUSTER_CODE, source.REGION, source.REGION_DESCRIPTION, source.IS_VERIFIED);

-- ═══════════════════════════════════════════════════════════════════
-- VALIDATION QUERY: Identify unmapped clusters in production data
-- ═══════════════════════════════════════════════════════════════════
-- SELECT DISTINCT b.CLUSTER
-- FROM ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG b
-- LEFT JOIN ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP m
--     ON b.CLUSTER = m.CLUSTER_CODE
-- WHERE m.CLUSTER_CODE IS NULL
--   AND b.CLUSTER IS NOT NULL;
```

---

## **FILE 3: models/silver/slv_ftl_agent_base_agg.sql**

```sql
{{
    config(
        materialized='incremental',
        unique_key=['DATE', 'ACCOUNT_ID', 'AGENT_ID', 'ENGAGEMENT_ID'],
        schema='SILVER',
        tags=['silver', 'usage', 'ftl_migration']
    )
}}

-- ═══════════════════════════════════════════════════════════════════
-- Silver Model: slv_ftl_agent_base_agg
-- Source: ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
-- Grain: One row per date × account × agent × engagement
-- Purpose: Cleaned, typed, and enriched FTL agent usage data
-- ═══════════════════════════════════════════════════════════════════

WITH source_data AS (
    SELECT
        -- ═══════════════════════════════════════════════════════════
        -- PRIMARY KEYS & IDENTIFIERS
        -- ═══════════════════════════════════════════════════════════
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-001
        -- Converts TEXT date to DATE type; validates format consistency
        TRY_CAST(TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') AS DATE) AS DATE,
        
        -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: —
        -- Pass-through; used for aggregation in Gold
        ACCOUNT_ID,
        
        -- SOURCE: AGENT_ID | CLASS: SEMANTIC_MATCH | BR: BR-004
        -- ASSUMPTION: AGENT_ID represents end users
        AGENT_ID AS USER_ID,
        
        -- SOURCE: ENGAGEMENT_ID | CLASS: DIRECT_MATCH | BR: —
        -- Unique engagement identifier for channel-level detail
        ENGAGEMENT_ID,
        
        -- SOURCE: ZCC_ACCOUNT_ID | CLASS: NEW_CAPABILITY | BR: —
        -- New dimension: Zoom Contact Center account identifier
        ZCC_ACCOUNT_ID,
        
        -- ═══════════════════════════════════════════════════════════
        -- ENGAGEMENT & CHANNEL ATTRIBUTES
        -- ═══════════════════════════════════════════════════════════
        
        -- SOURCE: DIRECTION | CLASS: CASE_CHANGE | BR: BR-006
        -- Standardizes to uppercase (Inbound → INBOUND)
        UPPER(DIRECTION) AS DIRECTION,
        
        -- SOURCE: MODALITY | CLASS: CASE_CHANGE | BR: BR-007
        -- Standardizes to uppercase (SMS, Email, Chat → SMS, EMAIL, CHAT)
        UPPER(MODALITY) AS MODALITY,
        
        -- SOURCE: CHANNEL | CLASS: PARTIAL_MATCH | BR: BR-008
        -- FTL has subset (Video, Phone); standardizes to uppercase
        UPPER(CHANNEL) AS CHANNEL,
        
        -- SOURCE: CLIENT_TYPE | CLASS: NEW_CAPABILITY | BR: —
        -- New dimension: Device type (Mobile, Desktop, Web)
        CLIENT_TYPE,
        
        -- SOURCE: OS | CLASS: NEW_CAPABILITY | BR: —
        -- New dimension: Operating system (data quality concern: 1 distinct value)
        OS,
        
        -- ═══════════════════════════════════════════════════════════
        -- PHONE METRICS
        -- ═══════════════════════════════════════════════════════════
        
        -- SOURCE: PHONE_SESSIONS | CLASS: DIRECT_MATCH | BR: —
        -- Count of phone sessions; direct pass-through
        ZEROIFNULL(PHONE_SESSIONS) AS PHONE_SESSIONS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-002
        -- Converts milliseconds to minutes (÷ 60,000)
        ZEROIFNULL(INBOUND_PHONE_MS / 60000.0) AS INBOUND_PHONE_MINS,
        
        -- ═══════════════════════════════════════════════════════════
        -- STATUS & CLASSIFICATION
        -- ═══════════════════════════════════════════════════════════
        
        -- SOURCE: IS_ACTIVE | CLASS: SEMANTIC_MATCH | BR: BR-003
        -- ASSUMPTION: IS_ACTIVE applies at account level
        IFF(IS_ACTIVE IS NULL, FALSE, IS_ACTIVE) AS IS_ACTIVE_ACCOUNT,
        
        -- SOURCE: CLUSTER | CLASS: SEMANTIC_MATCH | BR: BR-005
        -- LOW CONFIDENCE: Maps AWS region codes to business regions using lookup
        COALESCE(
            m.REGION,
            CASE
                WHEN CLUSTER = 'eu-central-1' THEN 'EMEA'
                WHEN CLUSTER = 'ap-south-1' THEN 'APAC'
                WHEN CLUSTER = 'us-east-1' THEN 'NAMER'
                WHEN CLUSTER = 'us-west-2' THEN 'NAMER'
                WHEN CLUSTER = 'eu-west-1' THEN 'EMEA'
                WHEN CLUSTER = 'ap-southeast-1' THEN 'APAC'
                WHEN CLUSTER = 'sa-east-1' THEN 'LATAM'
                ELSE 'UNKNOWN'
            END
        ) AS REGION,
        
        -- Store raw cluster code for audit and unmapped region detection
        CLUSTER AS CLUSTER_RAW,
        
        -- ═══════════════════════════════════════════════════════════
        -- AUDIT COLUMNS
        -- ═══════════════════════════════════════════════════════════
        
        CURRENT_TIMESTAMP() AS _LOADED_AT,
        '{{ invocation_id }}' AS _DBT_INVOCATION_ID

    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }} src
    
    -- LEFT JOIN to CLUSTER_REGION_MAP for verified mappings
    LEFT JOIN ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP m
        ON src.CLUSTER = m.CLUSTER_CODE
    
    {% if is_incremental() %}
        -- Incremental load: only process new or updated records
        WHERE TRY_CAST(TO_DATE(src.DATA_DATE, 'M/D/YY HH24:MI') AS DATE) > (
            SELECT MAX(DATE) FROM {{ this }}
        )
    {% endif %}
)

SELECT * FROM source_data
WHERE DATE IS NOT NULL  -- Filter out invalid date formats
```

---

## **FILE 4: models/silver/slv_ftl_agent_base_agg.yml**

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **Silver Layer: FTL Agent-Level Usage Aggregation**
      
      Grain: One row per DATE × ACCOUNT_ID × USER_ID × ENGAGEMENT_ID
      
      Source: {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
      
      **Key Transformations:**
      - BR-001: Converts DATA_DATE from TEXT to DATE type
      - BR-002: Converts INBOUND_PHONE_MS to INBOUND_PHONE_MINS (÷ 60,000)
      - BR-003: Maps IS_ACTIVE to IS_ACTIVE_ACCOUNT (account-level assumption)
      - BR-004: Renames AGENT_ID to USER_ID (semantic alignment)
      - BR-005: Maps CLUSTER (AWS codes) to REGION (business regions) — LOW CONFIDENCE
      - BR-006: Standardizes DIRECTION to uppercase
      - BR-007: Standardizes MODALITY to uppercase
      - BR-008: Standardizes CHANNEL to uppercase
      
      **New Capabilities:**
      - ZCC_ACCOUNT_ID: Zoom Contact Center identifier (not in current PI pipeline)
      - CLIENT_TYPE: Device type dimension (Mobile, Desktop, Web)
      - OS: Operating system dimension (data quality concern: 1 distinct value)
      
      **Quality Concerns:**
      - BR-005 mapping incomplete; UNKNOWN region requires business validation
      - Date format consistency not validated across all records
      - OS column has low cardinality (single value observed)

    config:
      materialized: incremental
      unique_key: ['DATE', 'ACCOUNT_ID', 'USER_ID', 'ENGAGEMENT_ID']
      schema: SILVER
      tags: ['silver', 'usage', 'ftl_migration']

    columns:
      # ═══════════════════════════════════════════════════════════
      # PRIMARY KEYS & IDENTIFIERS
      # ═══════════════════════════════════════════════════════════
      
      - name: DATE
        description: "Event date (converted from TEXT to DATE) | BR-001"
        data_type: DATE
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
              config:
                severity: warn
      
      - name: ACCOUNT_ID
        description: "Unique account identifier | Direct match from FTL"
        data_type: TEXT
        tests:
          - not_null
      
      - name: USER_ID
        description: "End user identifier (sourced from AGENT_ID) | BR-004 | ASSUMPTION: AGENT_ID = USER_ID"
        data_type: TEXT
        tests:
          - not_null
      
      - name: ENGAGEMENT_ID
        description: "Unique engagement identifier for channel-level tracking | Direct match from FTL"
        data_type: TEXT
        tests:
          - not_null
      
      - name: ZCC_ACCOUNT_ID
        description: "Zoom Contact Center account identifier | New capability not in current PI pipeline"
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════════
      # ENGAGEMENT & CHANNEL ATTRIBUTES
      # ═══════════════════════════════════════════════════════════
      
      - name: DIRECTION
        description: "Engagement direction (INBOUND, OUTBOUND) | BR-006 | Case standardization applied"
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              config:
                severity: warn
      
      - name: MODALITY
        description: "Communication modality (SMS, EMAIL, CHAT) | BR-007 | Case standardization applied"
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['SMS', 'EMAIL', 'CHAT', 'VOICE']
              config:
                severity: warn
      
      - name: CHANNEL
        description: "Communication channel (VIDEO, PHONE) | BR-008 | FTL subset; case standardization applied"
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['EMAIL', 'VIDEO', 'PHONE', 'SMS', 'CHAT']
              config:
                severity: warn
      
      - name: CLIENT_TYPE
        description: "Client device type (Mobile, Desktop, Web) | New capability for device analytics"
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['Mobile', 'Desktop', 'Web']
              config:
                severity: warn
      
      - name: OS
        description: "Operating system | New capability | DATA QUALITY CONCERN: Only 1 distinct value observed"
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════════
      # PHONE METRICS
      # ═══════════════════════════════════════════════════════════
      
      - name: PHONE_SESSIONS
        description: "Count of phone sessions | Direct pass-through from FTL"
        data_type: NUMBER
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: INBOUND_PHONE_MINS
        description: "Inbound phone duration in minutes (converted from MS ÷ 60,000) | BR-002"
        data_type: FLOAT
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      # ═══════════════════════════════════════════════════════════
      # STATUS & CLASSIFICATION
      # ═══════════════════════════════════════════════════════════
      
      - name: IS_ACTIVE_ACCOUNT
        description: "Account active status flag | BR-003 | ASSUMPTION: IS_ACTIVE applies at account level"
        data_type: BOOLEAN
        tests:
          - not_null
      
      - name: REGION
        description: "Business region (EMEA, APAC, NAMER, LATAM, UNKNOWN) | BR-005 | LOW CONFIDENCE: Incomplete mapping"
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['EMEA', 'APAC', 'NAMER', 'LATAM', 'UNKNOWN']
              config:
                severity: warn
                warn_if: ">100"  # Alert if >100 rows have UNKNOWN region
      
      - name: CLUSTER_RAW
        description: "Raw AWS cluster code for audit and unmapped region detection | Used to identify BR-005 gaps"
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════════
      # AUDIT COLUMNS
      # ═══════════════════════════════════════════════════════════
      
      - name: _LOADED_AT
        description: "Timestamp of Silver layer load"
        data_type: TIMESTAMP_NTZ
        tests:
          - not_null
      
      - name: _DBT_INVOCATION_ID
        description: "dbt invocation ID for lineage tracking"
        data_type: TEXT
        tests:
          - not_null

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - DATE
            - ACCOUNT_ID
            - USER_ID
            - ENGAGEMENT_ID
          config:
            severity: error
```

---

## **POST-RUN AUDIT QUERY**

After deploying the Silver model, run this query to identify unmapped regions that require business validation (BR-005):

```sql
-- ═══════════════════════════════════════════════════════════════════
-- UNMAPPED REGION AUDIT — BR-005 Validation
-- Purpose: Identify CLUSTER values mapping to UNKNOWN region
-- Action: Add missing mappings to CLUSTER_REGION_MAP table
-- ═══════════════════════════════════════════════════════════════════

SELECT 
    CLUSTER_RAW,
    COUNT(*) AS row_count,
    MIN(DATE) AS first_seen,
    MAX(DATE) AS last_seen,
    COUNT(DISTINCT ACCOUNT_ID) AS affected_accounts
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
WHERE REGION = 'UNKNOWN'
GROUP BY CLUSTER_RAW
ORDER BY row_count DESC;
```

---

## **DEPLOYMENT CHECKLIST**

✅ **Step 1**: Deploy `setup/CLUSTER_REGION_MAP.sql` to create and populate the region lookup table

✅ **Step 2**: Validate `models/bronze/sources.yml` references correct database/schema (ZOOM_AI_POC.BRONZE)

✅ **Step 3**: Run `dbt run --models slv_ftl_agent_base_agg` to build the Silver model

✅ **Step 4**: Run `dbt test --models slv_ftl_agent_base_agg` to execute all data quality tests

✅ **Step 5**: Execute post-run audit query to identify UNKNOWN regions

✅ **Step 6**: Update `CLUSTER_REGION_MAP` with missing cluster codes (coordinate with BDP)

✅ **Step 7**: Verify data lineage using `_DBT_INVOCATION_ID` and `_LOADED_AT` audit columns

---

## **KNOWN LIMITATIONS & RISKS**

⚠️ **BR-005 (Region Mapping)**: LOW CONFIDENCE — Incomplete AWS cluster → business region mapping. Requires business validation for all observed CLUSTER values.

⚠️ **BR-001 (Date Parsing)**: Date format `'M/D/YY HH24:MI'` validated against sample data but not exhaustively tested across full dataset. TRY_CAST applied to handle parse failures gracefully.

⚠️ **BR-004 (User ID)**: ASSUMPTION that AGENT_ID represents end users. Requires confirmation from business/data stewards.

⚠️ **OS Column**: Data quality concern — only 1 distinct value observed in source. May not provide analytical value until FTL ingestion improves.