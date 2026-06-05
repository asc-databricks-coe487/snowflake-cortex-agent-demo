

⚙️ **STEP 1: Schema Discovery** — Retrieved BRZ_FTL_AGENT_BASE_AGG metadata (14 columns confirmed)

⚙️ **STEP 2: Code Generation Started** — Applying approved mapping CSV with all BR_IDs and GAP_IDs

⚙️ **STEP 3: Building Silver Model** — Using medallion convention (slv_ prefix, not stg_)

---

## **FILE 1: models/bronze/sources.yml**

```yaml
version: 2

sources:
  - name: zoom_ai_poc
    database: ZOOM_AI_POC
    schema: BRONZE
    description: "Bronze layer - raw FTL data ingestion"
    
    tables:
      - name: BRZ_FTL_AGENT_BASE_AGG
        description: "FTL agent engagement and usage metrics - raw extract"
        columns:
          - name: ZCC_ACCOUNT_ID
            description: "ZCC-specific account identifier for cross-system reconciliation"
            data_type: TEXT
            
          - name: ACCOUNT_ID
            description: "Primary account identifier with ID_ prefix pattern"
            data_type: TEXT
            
          - name: ENGAGEMENT_ID
            description: "Unique identifier for customer engagement session"
            data_type: TEXT
            
          - name: AGENT_ID
            description: "Agent/user identifier (semantic assumption: all users not just support agents)"
            data_type: TEXT
            
          - name: DIRECTION
            description: "Engagement direction - mixed case values (Inbound/Outbound)"
            data_type: TEXT
            
          - name: MODALITY
            description: "Communication modality (SMS/Email/Chat)"
            data_type: TEXT
            
          - name: CHANNEL
            description: "Communication channel - mixed case values (Video/Phone)"
            data_type: TEXT
            
          - name: PHONE_SESSIONS
            description: "Count of phone sessions"
            data_type: NUMBER
            
          - name: INBOUND_PHONE_MS
            description: "Inbound phone duration in milliseconds"
            data_type: NUMBER
            
          - name: CLIENT_TYPE
            description: "Device type (Mobile/Desktop/Web) - new capability not in PI"
            data_type: TEXT
            
          - name: OS
            description: "Operating system - data quality issue (only 1 distinct value observed)"
            data_type: TEXT
            
          - name: IS_ACTIVE
            description: "Account active status boolean flag"
            data_type: BOOLEAN
            
          - name: CLUSTER
            description: "AWS cluster identifier (eu-central-1/ap-south-1/us-east-1)"
            data_type: TEXT
            
          - name: DATA_DATE
            description: "Event date stored as text string format MM/DD/YY HH24:MI"
            data_type: TEXT
```

---

## **FILE 2: setup/CLUSTER_REGION_MAP.sql**

```sql
-- ═══════════════════════════════════════════════════════════
-- CLUSTER → REGION MAPPING REFERENCE TABLE
-- Purpose: Map AWS clusters to business regions for BR-012
-- Gap:     GAP-003 - LATAM region not observed in FTL data
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP (
    CLUSTER_RAW     TEXT PRIMARY KEY,
    REGION          TEXT NOT NULL,
    IS_VERIFIED     BOOLEAN DEFAULT FALSE,
    LAST_UPDATED    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    NOTES           TEXT
);

-- Initial seed data based on FTL profiling
MERGE INTO ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP AS tgt
USING (
    SELECT 'eu-central-1' AS CLUSTER_RAW, 'EMEA' AS REGION, TRUE AS IS_VERIFIED, 'Verified via FTL data profiling' AS NOTES
    UNION ALL
    SELECT 'ap-south-1',   'APAC',  TRUE,  'Verified via FTL data profiling'
    UNION ALL
    SELECT 'us-east-1',    'NAMER', TRUE,  'Verified via FTL data profiling'
    UNION ALL
    SELECT 'us-west-1',    'NAMER', FALSE, 'Inferred - not yet observed in FTL'
    UNION ALL
    SELECT 'us-west-2',    'NAMER', FALSE, 'Inferred - not yet observed in FTL'
    UNION ALL
    SELECT 'sa-east-1',    'LATAM', FALSE, 'GAP-003: LATAM region not observed - add when available'
    UNION ALL
    SELECT 'eu-west-1',    'EMEA',  FALSE, 'Inferred - not yet observed in FTL'
    UNION ALL
    SELECT 'ap-southeast-1', 'APAC', FALSE, 'Inferred - not yet observed in FTL'
) AS src
ON tgt.CLUSTER_RAW = src.CLUSTER_RAW
WHEN MATCHED THEN
    UPDATE SET 
        tgt.REGION = src.REGION,
        tgt.IS_VERIFIED = src.IS_VERIFIED,
        tgt.NOTES = src.NOTES,
        tgt.LAST_UPDATED = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (CLUSTER_RAW, REGION, IS_VERIFIED, NOTES)
    VALUES (src.CLUSTER_RAW, src.REGION, src.IS_VERIFIED, src.NOTES);

-- Add index for lookup performance
CREATE INDEX IF NOT EXISTS idx_cluster_lookup 
ON ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP(CLUSTER_RAW);
```

---

## **FILE 3: models/silver/slv_ftl_agent_base_agg.sql**

```sql
{{
    config(
        materialized='incremental',
        unique_key=['ACCOUNT_ID', 'ENGAGEMENT_ID', 'AGENT_ID', 'DATE'],
        schema='SILVER',
        tags=['silver', 'ftl', 'usage'],
        on_schema_change='fail'
    )
}}

-- ═══════════════════════════════════════════════════════════
-- MODEL: slv_ftl_agent_base_agg
-- LAYER: Silver
-- SOURCE: BRZ_FTL_AGENT_BASE_AGG (FTL agent usage data)
-- PURPOSE: Clean, type-cast, and standardize FTL data for
--          downstream Silver tables and Gold aggregations
-- ═══════════════════════════════════════════════════════════

WITH source AS (
    SELECT *
    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
    {% if is_incremental() %}
    WHERE TRY_CAST(DATA_DATE AS TIMESTAMP_NTZ) > (SELECT MAX(DATE) FROM {{ this }})
    {% endif %}
),

transformed AS (
    SELECT
        -- ═══════════════════════════════════════════════════
        -- DATE DIMENSION
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-001
        -- FTL stores dates as text 'MM/DD/YY HH24:MI' - convert to DATE type
        -- ASSUMPTION: Date format is consistent across all records - VALIDATE WITH BUSINESS
        TRY_CAST(
            TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') 
            AS DATE
        ) AS DATE,
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-001
        -- For engagement start tracking in SLV_COMBINED_CHANNELS
        TRY_CAST(
            TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') 
            AS DATE
        ) AS START_DATE,
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-001
        -- For report date tracking in SLV_CONSOLIDATED_USAGE
        TRY_CAST(
            TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI') 
            AS DATE
        ) AS REPORT_DATE,
        
        -- ═══════════════════════════════════════════════════
        -- ACCOUNT & USER IDENTIFIERS
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: BR-006
        ACCOUNT_ID,
        
        -- SOURCE: ZCC_ACCOUNT_ID | CLASS: NEW_CAPABILITY | BR: BR-029
        -- May enable cross-system reconciliation with ZCC
        ZCC_ACCOUNT_ID,
        
        -- SOURCE: AGENT_ID | CLASS: RENAME | BR: BR-009
        -- ASSUMPTION: AGENT_ID represents all users not just support agents - VALIDATE WITH BUSINESS
        AGENT_ID AS USER_ID,
        
        -- SOURCE: ENGAGEMENT_ID | CLASS: DIRECT_MATCH | BR: BR-007
        ENGAGEMENT_ID,
        
        -- ═══════════════════════════════════════════════════
        -- ENGAGEMENT ATTRIBUTES
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: DIRECTION | CLASS: RENAME | BR: BR-003
        -- Standardize mixed case (Inbound/Outbound) to uppercase
        UPPER(DIRECTION) AS DIRECTION,
        
        -- SOURCE: MODALITY | CLASS: DIRECT_MATCH | BR: BR-005
        MODALITY,
        
        -- SOURCE: CHANNEL | CLASS: RENAME | BR: BR-004
        -- Standardize mixed case (Video/Phone) to uppercase
        UPPER(CHANNEL) AS CHANNEL,
        
        -- ═══════════════════════════════════════════════════
        -- USAGE METRICS
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: PHONE_SESSIONS | CLASS: DIRECT_MATCH | BR: BR-008
        ZEROIFNULL(PHONE_SESSIONS) AS PHONE_SESSIONS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-002
        -- Convert milliseconds to minutes for SLV_USAGE_MASTER
        ZEROIFNULL(INBOUND_PHONE_MS) / 60000.0 AS INBOUND_PHONE_MINS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-002
        -- Convert milliseconds to seconds for SLV_COMBINED_CHANNELS
        -- LOW CONFIDENCE: Only applicable for phone modality not chat/email
        IFF(
            UPPER(MODALITY) = 'PHONE',
            ZEROIFNULL(INBOUND_PHONE_MS) / 1000.0,
            NULL
        ) AS DURATION_SEC,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: COMPOSITE | BR: BR-002
        -- Pre-computed minutes for aggregation (used in GLD_AGGREGATE.PHONE_USAGE)
        ZEROIFNULL(INBOUND_PHONE_MS) / 60000.0 AS PHONE_USAGE_MINS,
        
        -- ═══════════════════════════════════════════════════
        -- DEVICE & ENVIRONMENT (NEW CAPABILITIES)
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: CLIENT_TYPE | CLASS: NEW_CAPABILITY | BR: BR-030
        -- FTL introduces device type (Mobile/Desktop/Web) not present in PI
        CLIENT_TYPE,
        
        -- SOURCE: OS | CLASS: NEW_CAPABILITY | BR: BR-031
        -- LOW CONFIDENCE: Only 1 distinct value observed ('Sample Text') - data quality issue
        OS,
        
        -- ═══════════════════════════════════════════════════
        -- ACCOUNT STATUS & REGION
        -- ═══════════════════════════════════════════════════
        
        -- SOURCE: IS_ACTIVE | CLASS: RENAME | BR: BR-010 / BR-011
        -- LOW CONFIDENCE: Semantic mismatch between active flag and licensing status
        -- ASSUMPTION: IS_ACTIVE maps to both IS_ACTIVE_ACCOUNT and IS_LICENSED - VALIDATE WITH BUSINESS
        IS_ACTIVE AS IS_ACTIVE_ACCOUNT,
        
        -- SOURCE: IS_ACTIVE | CLASS: RENAME | BR: BR-010 / BR-011
        -- GAP-004: Same field used for licensing status - semantic validation required
        IS_ACTIVE AS IS_LICENSED,
        
        -- SOURCE: CLUSTER | CLASS: DERIVED | BR: BR-012
        -- Store raw cluster value for reference and troubleshooting
        CLUSTER AS CLUSTER_RAW,
        
        -- SOURCE: CLUSTER | CLASS: DERIVED | BR: BR-012
        -- GAP-003: Map AWS clusters to business regions; LATAM not observed in FTL data
        CASE
            WHEN CLUSTER = 'eu-central-1' THEN 'EMEA'
            WHEN CLUSTER = 'ap-south-1'   THEN 'APAC'
            WHEN CLUSTER = 'us-east-1'    THEN 'NAMER'
            WHEN CLUSTER = 'us-west-1'    THEN 'NAMER'
            WHEN CLUSTER = 'us-west-2'    THEN 'NAMER'
            WHEN CLUSTER = 'eu-west-1'    THEN 'EMEA'
            WHEN CLUSTER = 'ap-southeast-1' THEN 'APAC'
            WHEN CLUSTER = 'sa-east-1'    THEN 'LATAM'
            ELSE 'UNKNOWN'
        END AS REGION,
        
        -- ═══════════════════════════════════════════════════
        -- GAP COLUMNS (NULL placeholders for missing FTL data)
        -- ═══════════════════════════════════════════════════
        
        -- GAP GAP-005: No first active date tracking in FTL source
        -- CRITICAL GAP: Requires MIN(DATA_DATE) over historical data for cohort analysis
        NULL AS ACCOUNT_FIRST_ACTIVE,
        
        -- GAP GAP-005: No first active date tracking in FTL source
        -- CRITICAL GAP: Requires MIN(DATA_DATE) over historical data for user-level cohort analysis
        NULL AS USER_FIRST_ACTIVE,
        
        -- ═══════════════════════════════════════════════════
        -- AUDIT COLUMNS
        -- ═══════════════════════════════════════════════════
        
        CURRENT_TIMESTAMP() AS _LOADED_AT
        
    FROM source
    WHERE DATA_DATE IS NOT NULL  -- Filter out invalid records
)

SELECT * FROM transformed
```

---

## **FILE 4: models/silver/slv_ftl_agent_base_agg.yml**

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **Silver Layer - FTL Agent Usage Data**
      
      Cleaned and standardized FTL agent engagement and usage metrics.
      Applies type conversions, case standardization, and unit transformations
      per approved mapping specification.
      
      **Key Transformations:**
      - Date parsing: TEXT → DATE (MM/DD/YY HH24:MI format)
      - Duration units: Milliseconds → Minutes/Seconds
      - Case standardization: DIRECTION, CHANNEL to uppercase
      - Region mapping: AWS clusters → Business regions (EMEA/APAC/NAMER/LATAM)
      - Semantic rename: AGENT_ID → USER_ID
      
      **Known Gaps:**
      - GAP-005: No first active date tracking (requires historical aggregation)
      - GAP-003: LATAM region not yet observed in FTL data
      - GAP-004: IS_ACTIVE semantic mismatch (active vs. licensed)
      
      **Data Quality Notes:**
      - OS field has low confidence (only 1 distinct value observed)
      - DURATION_SEC only applicable for phone modality
      - Date format assumption requires validation
      
    config:
      materialized: incremental
      unique_key: ['ACCOUNT_ID', 'ENGAGEMENT_ID', 'AGENT_ID', 'DATE']
      schema: SILVER
      tags: ['silver', 'ftl', 'usage', 'agent_base']
    
    columns:
      # ═══════════════════════════════════════════════════════
      # DATE DIMENSION
      # ═══════════════════════════════════════════════════════
      
      - name: DATE
        description: |
          **Event date** - Converted from FTL text format to DATE type
          - **Source:** DATA_DATE (TEXT)
          - **Transformation:** TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI')
          - **BR_ID:** BR-001
          - **Classification:** UNIT_CHANGE
          - **Confidence:** Medium
          - **Assumption:** Date format is consistent - VALIDATE WITH BUSINESS
        data_type: DATE
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: "'2020-01-01'"
              max_value: "current_date()"
              row_condition: "DATE IS NOT NULL"
      
      - name: START_DATE
        description: |
          **Engagement start date** - For SLV_COMBINED_CHANNELS tracking
          - **Source:** DATA_DATE (TEXT)
          - **Transformation:** TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI')
          - **BR_ID:** BR-001
          - **Classification:** UNIT_CHANGE
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: DATE
      
      - name: REPORT_DATE
        description: |
          **Report aggregation date** - For SLV_CONSOLIDATED_USAGE
          - **Source:** DATA_DATE (TEXT)
          - **Transformation:** TO_DATE(DATA_DATE, 'MM/DD/YY HH24:MI')
          - **BR_ID:** BR-001
          - **Classification:** UNIT_CHANGE
          - **Target Table:** SLV_CONSOLIDATED_USAGE
        data_type: DATE
      
      # ═══════════════════════════════════════════════════════
      # ACCOUNT & USER IDENTIFIERS
      # ═══════════════════════════════════════════════════════
      
      - name: ACCOUNT_ID
        description: |
          **Primary account identifier** - ID_ prefix pattern
          - **Source:** ACCOUNT_ID (TEXT)
          - **Transformation:** None (Direct match)
          - **BR_ID:** BR-006
          - **Classification:** DIRECT_MATCH
          - **Confidence:** High
          - **Target Tables:** SLV_USAGE_MASTER, SLV_COMBINED_CHANNELS, SLV_CONSOLIDATED_USAGE, SLV_ACCT_FIRST_ACTIVE
        data_type: TEXT
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^ID_.*"
      
      - name: ZCC_ACCOUNT_ID
        description: |
          **ZCC-specific account identifier** - New capability not in PI
          - **Source:** ZCC_ACCOUNT_ID (TEXT)
          - **Transformation:** None (Preserve in Silver)
          - **BR_ID:** BR-029
          - **Classification:** NEW_CAPABILITY
          - **Confidence:** High
          - **Note:** May enable cross-system reconciliation with ZCC
        data_type: TEXT
      
      - name: USER_ID
        description: |
          **User/agent identifier** - Renamed from AGENT_ID
          - **Source:** AGENT_ID (TEXT)
          - **Transformation:** AGENT_ID AS USER_ID
          - **BR_ID:** BR-009
          - **Classification:** RENAME
          - **Confidence:** High
          - **Assumption:** AGENT_ID represents all users not just support agents - VALIDATE WITH BUSINESS
          - **Target Tables:** SLV_USAGE_MASTER, SLV_COMBINED_CHANNELS, SLV_USER_FIRST_ACTIVE
        data_type: TEXT
        tests:
          - not_null
      
      - name: ENGAGEMENT_ID
        description: |
          **Unique engagement session identifier** - ID_ prefix pattern
          - **Source:** ENGAGEMENT_ID (TEXT)
          - **Transformation:** None (Direct match)
          - **BR_ID:** BR-007
          - **Classification:** DIRECT_MATCH
          - **Confidence:** High
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: TEXT
        tests:
          - not_null
      
      # ═══════════════════════════════════════════════════════
      # ENGAGEMENT ATTRIBUTES
      # ═══════════════════════════════════════════════════════
      
      - name: DIRECTION
        description: |
          **Engagement direction** - Standardized to uppercase
          - **Source:** DIRECTION (TEXT)
          - **Transformation:** UPPER(DIRECTION)
          - **BR_ID:** BR-003
          - **Classification:** RENAME
          - **Confidence:** High
          - **Values:** INBOUND, OUTBOUND
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
      
      - name: MODALITY
        description: |
          **Communication modality** - Values align between FTL and PI
          - **Source:** MODALITY (TEXT)
          - **Transformation:** None (Direct match)
          - **BR_ID:** BR-005
          - **Classification:** DIRECT_MATCH
          - **Confidence:** High
          - **Values:** SMS, EMAIL, CHAT
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['SMS', 'EMAIL', 'CHAT', 'PHONE']
      
      - name: CHANNEL
        description: |
          **Communication channel** - Standardized to uppercase
          - **Source:** CHANNEL (TEXT)
          - **Transformation:** UPPER(CHANNEL)
          - **BR_ID:** BR-004
          - **Classification:** RENAME
          - **Confidence:** High
          - **Values:** VIDEO, PHONE
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['VIDEO', 'PHONE']
      
      # ═══════════════════════════════════════════════════════
      # USAGE METRICS
      # ═══════════════════════════════════════════════════════
      
      - name: PHONE_SESSIONS
        description: |
          **Count of phone sessions** - Direct match
          - **Source:** PHONE_SESSIONS (NUMBER)
          - **Transformation:** ZEROIFNULL(PHONE_SESSIONS)
          - **BR_ID:** BR-008
          - **Classification:** DIRECT_MATCH
          - **Confidence:** High
          - **Target Table:** SLV_USAGE_MASTER
        data_type: NUMBER
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000
      
      - name: INBOUND_PHONE_MINS
        description: |
          **Inbound phone duration in minutes** - Converted from milliseconds
          - **Source:** INBOUND_PHONE_MS (NUMBER)
          - **Transformation:** INBOUND_PHONE_MS / 60000.0
          - **BR_ID:** BR-002
          - **Classification:** UNIT_CHANGE
          - **Confidence:** High
          - **Target Table:** SLV_USAGE_MASTER
        data_type: FLOAT
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 86400  # 24 hours in minutes
      
      - name: DURATION_SEC
        description: |
          **Engagement duration in seconds** - Converted from milliseconds
          - **Source:** INBOUND_PHONE_MS (NUMBER)
          - **Transformation:** INBOUND_PHONE_MS / 1000.0 (only for PHONE modality)
          - **BR_ID:** BR-002
          - **Classification:** UNIT_CHANGE
          - **Confidence:** Low
          - **Warning:** Only applicable for phone modality not chat/email
          - **Target Table:** SLV_COMBINED_CHANNELS
        data_type: FLOAT
      
      - name: PHONE_USAGE_MINS
        description: |
          **Phone usage pre-computed for aggregation** - Minutes from milliseconds
          - **Source:** INBOUND_PHONE_MS (NUMBER)
          - **Transformation:** INBOUND_PHONE_MS / 60000.0
          - **BR_ID:** BR-002 / BR-013
          - **Classification:** COMPOSITE
          - **Target:** GLD_AGGREGATE.PHONE_USAGE
        data_type: FLOAT
      
      # ═══════════════════════════════════════════════════════
      # DEVICE & ENVIRONMENT (NEW CAPABILITIES)
      # ═══════════════════════════════════════════════════════
      
      - name: CLIENT_TYPE
        description: |
          **Device type** - New capability not present in PI
          - **Source:** CLIENT_TYPE (TEXT)
          - **Transformation:** None (Preserve in Silver)
          - **BR_ID:** BR-030
          - **Classification:** NEW_CAPABILITY
          - **Confidence:** High
          - **Values:** Mobile, Desktop, Web
          - **Recommendation:** Add to Silver for device-level analysis
        data_type: TEXT
      
      - name: OS
        description: |
          **Operating system** - Low confidence due to data quality issue
          - **Source:** OS (TEXT)
          - **Transformation:** None (Preserve in Silver)
          - **BR_ID:** BR-031
          - **Classification:** NEW_CAPABILITY
          - **Confidence:** Low
          - **Warning:** Only 1 distinct value observed ('Sample Text') - assess data quality
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════
      # ACCOUNT STATUS & REGION
      # ═══════════════════════════════════════════════════════
      
      - name: IS_ACTIVE_ACCOUNT
        description: |
          **Account active status flag** - Semantic mismatch with PI
          - **Source:** IS_ACTIVE (BOOLEAN)
          - **Transformation:** IS_ACTIVE AS IS_ACTIVE_ACCOUNT
          - **BR_ID:** BR-010
          - **GAP_ID:** GAP-004
          - **Classification:** RENAME
          - **Confidence:** Medium
          - **Warning:** Semantic validation required - active vs. licensed
          - **Target Table:** SLV_CONSOLIDATED_USAGE
        data_type: BOOLEAN
      
      - name: IS_LICENSED
        description: |
          **Licensing status flag** - Same source as IS_ACTIVE_ACCOUNT
          - **Source:** IS_ACTIVE (BOOLEAN)
          - **Transformation:** IS_ACTIVE AS IS_LICENSED
          - **BR_ID:** BR-011
          - **GAP_ID:** GAP-004
          - **Classification:** RENAME
          - **Confidence:** Medium
          - **Warning:** Semantic validation required - may not represent true licensing
          - **Target:** GLD_AGGREGATE.IS_LICENSED
        data_type: BOOLEAN
      
      - name: CLUSTER_RAW
        description: |
          **Raw AWS cluster identifier** - Preserved for reference
          - **Source:** CLUSTER (TEXT)
          - **Transformation:** None
          - **Values:** eu-central-1, ap-south-1, us-east-1
          - **Note:** Use for troubleshooting and UNKNOWN region investigation
        data_type: TEXT
      
      - name: REGION
        description: |
          **Business region** - Derived from AWS cluster mapping
          - **Source:** CLUSTER (TEXT)
          - **Transformation:** CASE statement mapping clusters to regions
          - **BR_ID:** BR-012
          - **GAP_ID:** GAP-003
          - **Classification:** DERIVED
          - **Confidence:** Medium
          - **Values:** EMEA, APAC, NAMER, LATAM, UNKNOWN
          - **Warning:** LATAM not observed in FTL data; UNKNOWN indicates unmapped cluster
          - **Target:** GLD_AGGREGATE.REGION
        data_type: TEXT
        tests:
          - not_null
          - accepted_values:
              values: ['EMEA', 'APAC', 'NAMER', 'LATAM', 'UNKNOWN']
      
      # ═══════════════════════════════════════════════════════
      # GAP COLUMNS (NULL placeholders)
      # ═══════════════════════════════════════════════════════
      
      - name: ACCOUNT_FIRST_ACTIVE
        description: |
          **Account first active date** - NOT AVAILABLE in FTL source
          - **GAP_ID:** GAP-005
          - **BR_ID:** BR-017
          - **Classification:** GAP
          - **Note:** Requires MIN(DATA_DATE) aggregation over historical data
          - **Impact:** Non-blocking but limits cohort analysis capability
          - **Target Tables:** SLV_USAGE_MASTER, SLV_ACCT_FIRST_ACTIVE
        data_type: DATE
      
      - name: USER_FIRST_ACTIVE
        description: |
          **User first active date** - NOT AVAILABLE in FTL source
          - **GAP_ID:** GAP-005
          - **BR_ID:** BR-017
          - **Classification:** GAP
          - **Note:** Requires MIN(DATA_DATE) aggregation over historical data
          - **Impact:** Limits user-level cohort analysis
          - **Target Table:** SLV_USAGE_MASTER
        data_type: DATE
      
      # ═══════════════════════════════════════════════════════
      # AUDIT COLUMNS
      # ═══════════════════════════════════════════════════════
      
      - name: _LOADED_AT
        description: "Timestamp when record was loaded into Silver layer"
        data_type: TIMESTAMP_NTZ
        tests:
          - not_null
```

---

## **POST-RUN AUDIT QUERY**

After deploying the Silver model, run this query to identify unmapped clusters:

```sql
-- ═══════════════════════════════════════════════════════════
-- AUDIT: Identify UNKNOWN regions for cluster mapping review
-- Purpose: Find AWS clusters not mapped to business regions
-- Action: Update CLUSTER_REGION_MAP.sql if new clusters found
-- ═══════════════════════════════════════════════════════════

SELECT 
    CLUSTER_RAW,
    COUNT(*) AS rows,
    MIN(DATE) AS first_seen,
    MAX(DATE) AS last_seen,
    COUNT(DISTINCT ACCOUNT_ID) AS affected_accounts
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
WHERE REGION = 'UNKNOWN'
GROUP BY CLUSTER_RAW
ORDER BY rows DESC;
```

---

⚙️ **STEP 4: Validation Checklist** — Complete before Gold model generation

- [ ] **Date parsing accuracy:** Verify TO_DATE() handles all FTL date formats
- [ ] **Region mapping completeness:** Check UNKNOWN region count from audit query
- [ ] **IS_ACTIVE semantics:** Confirm with BDP if IS_ACTIVE = licensing status
- [ ] **AGENT_ID assumption:** Validate that AGENT_ID includes all users
- [ ] **Duration calculations:** Spot-check millisecond conversions (minutes/seconds)
- [ ] **Incremental logic:** Test unique_key behavior on duplicate engagements
- [ ] **OS data quality:** Assess if OS field should be excluded due to low variance
- [ ] **DURATION_SEC logic:** Verify IFF() correctly filters non-phone modalities

---

⚙️ **STEP 5: Ready for Gold Layer** — Call this tool next with TARGET_LAYER = GOLD

All Silver files generated using:
- ✅ Medallion naming (slv_ prefix, models/silver/ path)
- ✅ Source reference: {{ source("zoom_ai_poc", "BRZ_FTL_AGENT_BASE_AGG") }}
- ✅ Inline comments with BR_ID and GAP_ID on every column
- ✅ Snowflake-native functions (TRY_CAST, IFF, ZEROIFNULL, UPPER)
- ✅ Complete YAML (not truncated) with all 20+ columns documented
- ✅ CLUSTER_REGION_MAP.sql using MERGE INTO syntax (not ON CONFLICT)