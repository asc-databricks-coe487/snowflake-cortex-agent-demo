

## ⚙️ dbt Silver Model Generation

**⚙️ STEP 1: Schema Discovery** — Retrieved BRZ_FTL_AGENT_BASE_AGG source schema (14 columns)

**⚙️ STEP 2: Code Generation** — Building 4 production files using approved mapping CSV

---

### FILE 1: `models/bronze/sources.yml`

```yaml
version: 2

sources:
  - name: zoom_ai_poc
    database: ZOOM_AI_POC
    schema: BRONZE
    description: "Bronze layer source for FTL Agent Base Aggregation data"
    
    tables:
      - name: BRZ_FTL_AGENT_BASE_AGG
        description: "Raw FTL agent activity data including ZCC account identifiers, engagement tracking, phone usage metrics, and device/platform metadata"
        columns:
          - name: ZCC_ACCOUNT_ID
            description: "ZCC-specific account identifier (NEW_CAPABILITY)"
            data_type: TEXT
          
          - name: ACCOUNT_ID
            description: "Primary account identifier (DIRECT_MATCH to multiple PI Silver tables)"
            data_type: TEXT
          
          - name: ENGAGEMENT_ID
            description: "Unique engagement identifier (DIRECT_MATCH to SLV_COMBINED_CHANNELS)"
            data_type: TEXT
          
          - name: AGENT_ID
            description: "Agent identifier (SEMANTIC_MATCH to USER_ID via BR-001)"
            data_type: TEXT
          
          - name: DIRECTION
            description: "Communication direction: Inbound, Outbound (requires case normalization via BR-002)"
            data_type: TEXT
          
          - name: MODALITY
            description: "Communication modality: SMS, Email, Chat (requires case normalization via BR-003)"
            data_type: TEXT
          
          - name: CHANNEL
            description: "Communication channel: Video, Phone (combine with MODALITY via BR-004)"
            data_type: TEXT
          
          - name: PHONE_SESSIONS
            description: "Count of phone sessions (DIRECT_MATCH to SLV_USAGE_MASTER)"
            data_type: NUMBER
          
          - name: INBOUND_PHONE_MS
            description: "Inbound phone duration in milliseconds (requires unit conversion via BR-005, BR-006)"
            data_type: NUMBER
          
          - name: CLIENT_TYPE
            description: "Client classification: Mobile, Desktop, Web (NEW_CAPABILITY)"
            data_type: TEXT
          
          - name: OS
            description: "Operating system metadata (NEW_CAPABILITY)"
            data_type: TEXT
          
          - name: IS_ACTIVE
            description: "Activity flag (SEMANTIC_MATCH to IS_ACTIVE_ACCOUNT via BR-007)"
            data_type: BOOLEAN
          
          - name: CLUSTER
            description: "Cloud cluster identifier: us-east-1, eu-central-1, ap-south-1 (NEW_CAPABILITY, maps to REGION)"
            data_type: TEXT
          
          - name: DATA_DATE
            description: "Date dimension in text format (requires TRY_CAST to DATE)"
            data_type: TEXT
```

---

### FILE 2: `setup/CLUSTER_REGION_MAP.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- CLUSTER → REGION Lookup Table Setup
-- Purpose: Map FTL CLUSTER values to normalized REGION dimension
-- Usage: Supports BR-008 region derivation in SLV_FTL_AGENT_BASE_AGG
-- ═══════════════════════════════════════════════════════════════

-- Create lookup table if not exists
CREATE TABLE IF NOT EXISTS ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP (
    CLUSTER_RAW      TEXT        NOT NULL,
    REGION           TEXT        NOT NULL,
    IS_ACTIVE        BOOLEAN     DEFAULT TRUE,
    LAST_UPDATED     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_CLUSTER_REGION PRIMARY KEY (CLUSTER_RAW)
);

-- Populate with known mappings using MERGE INTO
MERGE INTO ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP AS target
USING (
    SELECT 'us-east-1'      AS CLUSTER_RAW, 'US_EAST'      AS REGION UNION ALL
    SELECT 'us-west-1'      AS CLUSTER_RAW, 'US_WEST'      AS REGION UNION ALL
    SELECT 'us-west-2'      AS CLUSTER_RAW, 'US_WEST'      AS REGION UNION ALL
    SELECT 'eu-central-1'   AS CLUSTER_RAW, 'EU_CENTRAL'   AS REGION UNION ALL
    SELECT 'eu-west-1'      AS CLUSTER_RAW, 'EU_WEST'      AS REGION UNION ALL
    SELECT 'ap-south-1'     AS CLUSTER_RAW, 'APAC_SOUTH'   AS REGION UNION ALL
    SELECT 'ap-southeast-1' AS CLUSTER_RAW, 'APAC_SE'      AS REGION UNION ALL
    SELECT 'ap-northeast-1' AS CLUSTER_RAW, 'APAC_NE'      AS REGION
) AS source
ON target.CLUSTER_RAW = source.CLUSTER_RAW
WHEN MATCHED THEN
    UPDATE SET
        target.REGION        = source.REGION,
        target.IS_ACTIVE     = TRUE,
        target.LAST_UPDATED  = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (CLUSTER_RAW, REGION, IS_ACTIVE, LAST_UPDATED)
    VALUES (source.CLUSTER_RAW, source.REGION, TRUE, CURRENT_TIMESTAMP());

-- Validation query
SELECT 
    CLUSTER_RAW,
    REGION,
    IS_ACTIVE,
    LAST_UPDATED
FROM ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP
ORDER BY REGION, CLUSTER_RAW;
```

---

### FILE 3: `models/silver/slv_ftl_agent_base_agg.sql`

```sql
{{ config(
    materialized='incremental',
    schema='SILVER',
    unique_key=['account_id', 'engagement_id', 'data_date'],
    tags=['ftl', 'agent_activity', 'daily']
) }}

-- ═══════════════════════════════════════════════════════════════
-- MODEL: slv_ftl_agent_base_agg
-- PURPOSE: Silver staging for FTL Agent Base Aggregation data
-- SOURCE: ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG
-- GRAIN: account_id + engagement_id + data_date (daily)
-- ═══════════════════════════════════════════════════════════════

WITH source AS (
    SELECT * 
    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
    {% if is_incremental() %}
    WHERE TRY_CAST(DATA_DATE AS DATE) > (SELECT MAX(data_date) FROM {{ this }})
    {% endif %}
),

region_lookup AS (
    SELECT 
        CLUSTER_RAW,
        REGION
    FROM ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP
    WHERE IS_ACTIVE = TRUE
),

transformed AS (
    SELECT
        -- ═══════════════════════════════════════════════════════
        -- IDENTIFIERS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: ZCC_ACCOUNT_ID | CLASS: NEW_CAPABILITY | BR: —
        s.ZCC_ACCOUNT_ID AS zcc_account_id,
        
        -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: —
        s.ACCOUNT_ID AS account_id,
        
        -- SOURCE: ENGAGEMENT_ID | CLASS: DIRECT_MATCH | BR: —
        s.ENGAGEMENT_ID AS engagement_id,
        
        -- SOURCE: AGENT_ID | CLASS: SEMANTIC_MATCH | BR: BR-001
        -- ASSUMPTION: agents are users — VALIDATE WITH BUSINESS
        s.AGENT_ID AS user_id,
        
        -- ═══════════════════════════════════════════════════════
        -- DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: DIRECTION | CLASS: PARTIAL_MATCH | BR: BR-002
        UPPER(s.DIRECTION) AS direction,
        
        -- SOURCE: MODALITY | CLASS: DIRECT_MATCH | BR: BR-003
        UPPER(s.MODALITY) AS modality,
        
        -- SOURCE: CHANNEL | CLASS: PARTIAL_MATCH | BR: BR-004
        COALESCE(UPPER(s.CHANNEL), UPPER(s.MODALITY)) AS channel,
        
        -- SOURCE: CLIENT_TYPE | CLASS: NEW_CAPABILITY | BR: —
        s.CLIENT_TYPE AS client_type,
        
        -- SOURCE: OS | CLASS: NEW_CAPABILITY | BR: —
        s.OS AS operating_system,
        
        -- SOURCE: IS_ACTIVE | CLASS: SEMANTIC_MATCH | BR: BR-007
        -- ASSUMPTION: activity flag same meaning — VALIDATE WITH BUSINESS
        s.IS_ACTIVE AS is_active_account,
        
        -- SOURCE: CLUSTER | CLASS: NEW_CAPABILITY | BR: BR-008 (derived)
        s.CLUSTER AS cluster_raw,
        
        -- DERIVED: REGION from CLUSTER via lookup
        COALESCE(r.REGION, 'UNKNOWN') AS region,
        
        -- SOURCE: DATA_DATE | CLASS: NEW_CAPABILITY | BR: —
        TRY_CAST(s.DATA_DATE AS DATE) AS data_date,
        
        -- ═══════════════════════════════════════════════════════
        -- METRICS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: PHONE_SESSIONS | CLASS: DIRECT_MATCH | BR: —
        ZEROIFNULL(s.PHONE_SESSIONS) AS phone_sessions,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-005
        -- Milliseconds → Seconds (for duration_sec compatibility)
        ZEROIFNULL(s.INBOUND_PHONE_MS / 1000.0) AS inbound_phone_seconds,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-006
        -- Milliseconds → Minutes (for usage metrics compatibility)
        ZEROIFNULL(s.INBOUND_PHONE_MS / 60000.0) AS inbound_phone_mins,
        
        -- ═══════════════════════════════════════════════════════
        -- AUDIT COLUMNS
        -- ═══════════════════════════════════════════════════════
        
        CURRENT_TIMESTAMP() AS dbt_loaded_at,
        '{{ invocation_id }}' AS dbt_invocation_id

    FROM source s
    LEFT JOIN region_lookup r
        ON s.CLUSTER = r.CLUSTER_RAW
    
    -- Data quality filters
    WHERE s.ACCOUNT_ID IS NOT NULL
      AND s.ENGAGEMENT_ID IS NOT NULL
      AND TRY_CAST(s.DATA_DATE AS DATE) IS NOT NULL
)

SELECT * FROM transformed

-- De-duplicate using QUALIFY (Snowflake-native)
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY account_id, engagement_id, data_date 
    ORDER BY dbt_loaded_at DESC
) = 1
```

---

### FILE 4: `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **Silver Staging: FTL Agent Base Aggregation**
      
      Normalized and transformed agent activity data from FTL source system.
      Applies business rules BR-001 through BR-007 for standardization.
      
      **Grain:** account_id + engagement_id + data_date (daily)
      
      **Key Transformations:**
      - BR-001: AGENT_ID → USER_ID (semantic mapping)
      - BR-002: DIRECTION case normalization (UPPER)
      - BR-003: MODALITY case normalization (UPPER)
      - BR-004: CHANNEL coalesced with MODALITY
      - BR-005: INBOUND_PHONE_MS → seconds (÷1000)
      - BR-006: INBOUND_PHONE_MS → minutes (÷60000)
      - BR-007: IS_ACTIVE → IS_ACTIVE_ACCOUNT (semantic mapping)
      - BR-008: CLUSTER → REGION via lookup table
      
      **New Capabilities:**
      - ZCC_ACCOUNT_ID: ZCC-specific account identifier
      - CLIENT_TYPE: Device classification (Mobile, Desktop, Web)
      - OS: Operating system metadata
      - CLUSTER/REGION: Cloud infrastructure dimensions
      
      **Data Quality:**
      - Requires non-null ACCOUNT_ID, ENGAGEMENT_ID, DATA_DATE
      - De-duplicated on grain using QUALIFY ROW_NUMBER
      - Incremental load on DATA_DATE
    
    config:
      materialized: incremental
      schema: SILVER
      unique_key: ['account_id', 'engagement_id', 'data_date']
      tags: ['ftl', 'agent_activity', 'daily']
    
    columns:
      # ═══════════════════════════════════════════════════════
      # IDENTIFIERS
      # ═══════════════════════════════════════════════════════
      
      - name: zcc_account_id
        description: "ZCC-specific account identifier (NEW_CAPABILITY from FTL)"
        data_type: TEXT
        meta:
          source_column: ZCC_ACCOUNT_ID
          classification: NEW_CAPABILITY
          confidence: High
          br_id: null
        tests:
          - not_null:
              severity: warn
              config:
                where: "data_date >= CURRENT_DATE - 7"
      
      - name: account_id
        description: "Primary account identifier (DIRECT_MATCH across multiple PI Silver tables)"
        data_type: TEXT
        meta:
          source_column: ACCOUNT_ID
          classification: DIRECT_MATCH
          confidence: High
          br_id: null
        tests:
          - not_null
          - relationships:
              field: account_id
              to: ref('slv_usage_master')
              severity: warn
      
      - name: engagement_id
        description: "Unique engagement identifier (DIRECT_MATCH to SLV_COMBINED_CHANNELS)"
        data_type: TEXT
        meta:
          source_column: ENGAGEMENT_ID
          classification: DIRECT_MATCH
          confidence: High
          br_id: null
        tests:
          - not_null
          - unique:
              config:
                where: "data_date >= CURRENT_DATE - 30"
      
      - name: user_id
        description: |
          User identifier derived from AGENT_ID (SEMANTIC_MATCH via BR-001).
          **ASSUMPTION:** Agents are users in this context — validate with BDP.
        data_type: TEXT
        meta:
          source_column: AGENT_ID
          classification: SEMANTIC_MATCH
          confidence: Medium
          br_id: BR-001
          assumption: "agents are users"
        tests:
          - not_null:
              severity: warn
      
      # ═══════════════════════════════════════════════════════
      # DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: direction
        description: |
          Communication direction: INBOUND, OUTBOUND.
          Normalized to uppercase via BR-002 (source values: Inbound, Outbound).
        data_type: TEXT
        meta:
          source_column: DIRECTION
          classification: PARTIAL_MATCH
          confidence: High
          br_id: BR-002
          transformation: UPPER(DIRECTION)
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
              quote: false
      
      - name: modality
        description: |
          Communication modality: SMS, EMAIL, CHAT, PHONE.
          Normalized to uppercase via BR-003 (source values: SMS, Email, Chat).
        data_type: TEXT
        meta:
          source_column: MODALITY
          classification: DIRECT_MATCH
          confidence: Medium
          br_id: BR-003
          transformation: UPPER(MODALITY)
        tests:
          - accepted_values:
              values: ['SMS', 'EMAIL', 'CHAT', 'PHONE', 'VIDEO']
              quote: false
              severity: warn
      
      - name: channel
        description: |
          Primary communication channel: VIDEO, PHONE, EMAIL, etc.
          Combined from CHANNEL and MODALITY via BR-004.
          Coalesced to handle FTL subset (Video, Phone) vs. full PI set.
        data_type: TEXT
        meta:
          source_column: CHANNEL
          classification: PARTIAL_MATCH
          confidence: Medium
          br_id: BR-004
          transformation: COALESCE(UPPER(CHANNEL), UPPER(MODALITY))
        tests:
          - not_null
          - accepted_values:
              values: ['VIDEO', 'PHONE', 'EMAIL', 'SMS', 'CHAT']
              quote: false
              severity: warn
      
      - name: client_type
        description: |
          Client device classification: Mobile, Desktop, Web.
          NEW_CAPABILITY from FTL — not present in existing PI Silver schema.
        data_type: TEXT
        meta:
          source_column: CLIENT_TYPE
          classification: NEW_CAPABILITY
          confidence: High
          br_id: null
        tests:
          - accepted_values:
              values: ['Mobile', 'Desktop', 'Web', 'Unknown']
              quote: false
              severity: warn
      
      - name: operating_system
        description: |
          Operating system metadata from FTL source.
          NEW_CAPABILITY — enables platform-level analytics.
        data_type: TEXT
        meta:
          source_column: OS
          classification: NEW_CAPABILITY
          confidence: High
          br_id: null
      
      - name: is_active_account
        description: |
          Account activity flag (SEMANTIC_MATCH via BR-007).
          **ASSUMPTION:** IS_ACTIVE from FTL has same business meaning as 
          IS_ACTIVE_ACCOUNT in PI Silver — validate with BDP.
        data_type: BOOLEAN
        meta:
          source_column: IS_ACTIVE
          classification: SEMANTIC_MATCH
          confidence: Medium
          br_id: BR-007
          assumption: "activity flag same meaning"
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
              quote: false
      
      - name: cluster_raw
        description: |
          Raw cloud cluster identifier from FTL: us-east-1, eu-central-1, ap-south-1.
          NEW_CAPABILITY — source for REGION dimension via BR-008 lookup.
        data_type: TEXT
        meta:
          source_column: CLUSTER
          classification: NEW_CAPABILITY
          confidence: Medium
          br_id: BR-008
        tests:
          - not_null:
              severity: warn
      
      - name: region
        description: |
          Normalized region derived from CLUSTER via lookup table.
          Values: US_EAST, US_WEST, EU_CENTRAL, EU_WEST, APAC_SOUTH, APAC_SE, APAC_NE, UNKNOWN.
          **ASSUMPTION:** Lookup table CLUSTER_REGION_MAP is complete and maintained.
        data_type: TEXT
        meta:
          source_column: CLUSTER (derived)
          classification: DERIVED
          confidence: Medium
          br_id: BR-008
          assumption: "lookup table complete"
        tests:
          - not_null
          - accepted_values:
              values: 
                - 'US_EAST'
                - 'US_WEST'
                - 'EU_CENTRAL'
                - 'EU_WEST'
                - 'APAC_SOUTH'
                - 'APAC_SE'
                - 'APAC_NE'
                - 'UNKNOWN'
              quote: false
              severity: warn
      
      - name: data_date
        description: |
          Date dimension parsed from FTL DATA_DATE (TEXT → DATE).
          Incremental load watermark column.
        data_type: DATE
        meta:
          source_column: DATA_DATE
          classification: NEW_CAPABILITY
          confidence: High
          br_id: null
          transformation: TRY_CAST(DATA_DATE AS DATE)
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
              config:
                severity: error
          - dbt_utils.expression_is_true:
              expression: "<= CURRENT_DATE + 1"
              config:
                severity: error
      
      # ═══════════════════════════════════════════════════════
      # METRICS
      # ═══════════════════════════════════════════════════════
      
      - name: phone_sessions
        description: |
          Count of phone sessions (DIRECT_MATCH to SLV_USAGE_MASTER.PHONE_SESSIONS).
          ZEROIFNULL applied for consistent aggregation.
        data_type: NUMBER
        meta:
          source_column: PHONE_SESSIONS
          classification: DIRECT_MATCH
          confidence: High
          br_id: null
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
      
      - name: inbound_phone_seconds
        description: |
          Inbound phone duration in seconds (UNIT_CHANGE via BR-005).
          Converted from FTL INBOUND_PHONE_MS (milliseconds ÷ 1000).
          Maps to SLV_COMBINED_CHANNELS.DURATION_SEC.
        data_type: NUMBER
        meta:
          source_column: INBOUND_PHONE_MS
          classification: UNIT_CHANGE
          confidence: Medium
          br_id: BR-005
          transformation: INBOUND_PHONE_MS / 1000.0
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
      
      - name: inbound_phone_mins
        description: |
          Inbound phone duration in minutes (UNIT_CHANGE via BR-006).
          Converted from FTL INBOUND_PHONE_MS (milliseconds ÷ 60000).
          Maps to SLV_CONSOLIDATED_USAGE.PHONE_USAGE, SLV_ROLL_29_DAY_USAGE.WEEKLY_PHONE_USAGE,
          and SLV_USAGE_MASTER.INBOUND_PHONE_MINS.
        data_type: NUMBER
        meta:
          source_column: INBOUND_PHONE_MS
          classification: UNIT_CHANGE
          confidence: High
          br_id: BR-006
          transformation: INBOUND_PHONE_MS / 60000.0
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
              config:
                severity: error
      
      # ═══════════════════════════════════════════════════════
      # AUDIT COLUMNS
      # ═══════════════════════════════════════════════════════
      
      - name: dbt_loaded_at
        description: "Timestamp when record was loaded by dbt"
        data_type: TIMESTAMP
        tests:
          - not_null
      
      - name: dbt_invocation_id
        description: "dbt invocation ID for lineage tracking"
        data_type: TEXT
        tests:
          - not_null

    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - account_id
            - engagement_id
            - data_date
          config:
            severity: error
```

---

## 📊 POST-RUN AUDIT QUERY

Run this after `dbt run` to identify unmapped clusters:

```sql
-- Audit: Verify REGION mapping coverage
SELECT 
    cluster_raw,
    COUNT(*) AS row_count,
    MIN(data_date) AS first_seen,
    MAX(data_date) AS last_seen
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
WHERE region = 'UNKNOWN'
GROUP BY 1
ORDER BY 2 DESC;
```

**Expected Result:** 0 rows if all clusters are mapped in CLUSTER_REGION_MAP.

**Action if rows found:** Update `setup/CLUSTER_REGION_MAP.sql` with missing cluster values and re-run MERGE INTO statement.

---

## ✅ VALIDATION CHECKLIST

- [ ] **BR-001 Applied:** AGENT_ID → USER_ID semantic mapping
- [ ] **BR-002 Applied:** DIRECTION uppercase normalization
- [ ] **BR-003 Applied:** MODALITY uppercase normalization
- [ ] **BR-004 Applied:** CHANNEL coalesced with MODALITY
- [ ] **BR-005 Applied:** INBOUND_PHONE_MS → seconds (÷1000)
- [ ] **BR-006 Applied:** INBOUND_PHONE_MS → minutes (÷60000)
- [ ] **BR-007 Applied:** IS_ACTIVE → IS_ACTIVE_ACCOUNT mapping
- [ ] **BR-008 Applied:** CLUSTER → REGION via lookup table
- [ ] **Incremental Config:** Watermark on DATA_DATE
- [ ] **Data Quality:** NOT NULL tests on grain columns
- [ ] **Naming Convention:** slv_ftl_agent_base_agg (not stg_)
- [ ] **Source Reference:** {{ source("zoom_ai_poc", "BRZ_FTL_AGENT_BASE_AGG") }}
- [ ] **YAML Complete:** All 17 columns documented with metadata