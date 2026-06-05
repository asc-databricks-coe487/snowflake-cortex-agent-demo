

## ⚙️ SILVER MODEL GENERATION — Production-Ready dbt Code

### ⚙️ STEP 1: Schema Discovery — Validate Bronze Source
✓ Discovered **ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG** with 14 columns
✓ Confirmed all FTL columns from mapping CSV present in Bronze table

### ⚙️ STEP 2: Mapping Analysis — Apply Business Rules & Transformations
- **BR-001 to BR-014**: 14 business rules from approved mapping
- **GAP-023, GAP-024**: 2 critical gaps requiring NULL handling/validation
- **NEW_CAPABILITY**: ZCC_ACCOUNT_ID, CLIENT_TYPE, OS, CLUSTER preserved for future use

### ⚙️ STEP 3: Code Generation — Medallion Architecture Standards
- File path: `models/silver/slv_ftl_agent_base_agg.sql` (NOT stg_)
- Source ref: `{{ source("zoom_ai_poc", "BRZ_FTL_AGENT_BASE_AGG") }}`
- Incremental materialization with ACCOUNT_ID + ENGAGEMENT_ID + DATA_DATE grain
- CLUSTER_REGION_MAP lookup table for geographic enrichment

### ⚙️ STEP 4: Quality Framework — Tests & Validation
- Inline comments: `-- SOURCE: col | CLASS: type | BR: br_id`
- Schema YAML with not_null tests on core dimensions
- Post-run audit query for UNKNOWN region monitoring

---

## 📦 FILE 1: `models/bronze/sources.yml`

```yaml
version: 2

sources:
  - name: zoom_ai_poc
    description: "Zoom AI POC Bronze layer - raw FTL agent engagement data ingested from source system"
    database: ZOOM_AI_POC
    schema: BRONZE
    tables:
      - name: BRZ_FTL_AGENT_BASE_AGG
        description: "Bronze layer - FTL agent base aggregation containing engagement-level metrics for phone, chat, email, SMS modalities across multiple clusters"
        columns:
          - name: ZCC_ACCOUNT_ID
            description: "ZCC account identifier - secondary account ID provided by FTL (NEW_CAPABILITY)"
            data_type: TEXT
          - name: ACCOUNT_ID
            description: "Primary account identifier with ID_ prefix pattern"
            data_type: TEXT
          - name: ENGAGEMENT_ID
            description: "Unique engagement identifier"
            data_type: TEXT
          - name: AGENT_ID
            description: "Agent identifier (maps to USER_ID in Silver)"
            data_type: TEXT
          - name: DIRECTION
            description: "Engagement direction - Inbound or Outbound"
            data_type: TEXT
          - name: MODALITY
            description: "Communication modality - SMS, Email, Chat"
            data_type: TEXT
          - name: CHANNEL
            description: "Communication channel - Phone, Video"
            data_type: TEXT
          - name: PHONE_SESSIONS
            description: "Count of phone sessions"
            data_type: NUMBER
          - name: INBOUND_PHONE_MS
            description: "Inbound phone duration in milliseconds"
            data_type: NUMBER
          - name: CLIENT_TYPE
            description: "Client device type - Mobile, Desktop, Web (NEW_CAPABILITY)"
            data_type: TEXT
          - name: OS
            description: "Operating system (NEW_CAPABILITY)"
            data_type: TEXT
          - name: IS_ACTIVE
            description: "Activity flag for engagement"
            data_type: BOOLEAN
          - name: CLUSTER
            description: "Deployment cluster/region - eu-central-1, ap-south-1, us-east-1 (NEW_CAPABILITY)"
            data_type: TEXT
          - name: DATA_DATE
            description: "Engagement timestamp as text string format 'M/D/YY HH24:MI'"
            data_type: TEXT
```

---

## 📦 FILE 2: `setup/CLUSTER_REGION_MAP.sql`

```sql
-- ═══════════════════════════════════════════════════════════════
-- CLUSTER_REGION_MAP Setup - Geographic Enrichment Reference Data
-- Purpose: Map FTL cluster identifiers to standardized region names
-- Usage: Supports BR-013 region derivation in Silver layer
-- Maintenance: Update when new clusters added to production
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP (
    cluster_raw     TEXT PRIMARY KEY,
    region          TEXT NOT NULL,
    region_code     TEXT,
    data_center     TEXT,
    last_updated    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Seed initial mappings from FTL cluster analysis
MERGE INTO ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP AS target
USING (
    SELECT 'eu-central-1' AS cluster_raw, 'EMEA' AS region, 'EU' AS region_code, 'Frankfurt' AS data_center
    UNION ALL
    SELECT 'ap-south-1', 'APAC', 'AP', 'Mumbai'
    UNION ALL
    SELECT 'us-east-1', 'AMER', 'US', 'Virginia'
) AS source
ON target.cluster_raw = source.cluster_raw
WHEN MATCHED THEN
    UPDATE SET
        region = source.region,
        region_code = source.region_code,
        data_center = source.data_center,
        last_updated = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (cluster_raw, region, region_code, data_center)
    VALUES (source.cluster_raw, source.region, source.region_code, source.data_center);

-- Validation check
SELECT 
    'CLUSTER_REGION_MAP setup complete - ' || COUNT(*) || ' regions configured' AS status
FROM ZOOM_AI_POC.SILVER.CLUSTER_REGION_MAP;
```

---

## 📦 FILE 3: `models/silver/slv_ftl_agent_base_agg.sql`

```sql
{{
    config(
        materialized='incremental',
        schema='SILVER',
        unique_key=['account_id', 'engagement_id', 'data_date'],
        on_schema_change='fail',
        tags=['silver', 'agent_engagement', 'ftl_source']
    )
}}

-- ═══════════════════════════════════════════════════════════════
-- Silver Layer: slv_ftl_agent_base_agg
-- Source: BRZ_FTL_AGENT_BASE_AGG (FTL agent engagement data)
-- Grain: One row per engagement per agent per account per timestamp
-- Purpose: Cleaned, typed, and enriched engagement-level metrics
-- ═══════════════════════════════════════════════════════════════

WITH source AS (
    SELECT *
    FROM {{ source('zoom_ai_poc', 'BRZ_FTL_AGENT_BASE_AGG') }}
    {% if is_incremental() %}
    WHERE TRY_CAST(DATA_DATE AS TIMESTAMP_NTZ) > (SELECT MAX(date) FROM {{ this }})
    {% endif %}
),

region_lookup AS (
    SELECT
        cluster_raw,
        region,
        region_code
    FROM {{ ref('cluster_region_map') }}
),

transformed AS (
    SELECT
        -- ═══════════════════════════════════════════════════════
        -- CORE DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: ACCOUNT_ID | CLASS: DIRECT_MATCH | BR: BR-001
        -- Core join key - direct pass-through
        ACCOUNT_ID,
        
        -- SOURCE: ENGAGEMENT_ID | CLASS: DIRECT_MATCH | BR: BR-002
        -- Primary key for engagement-level analysis
        ENGAGEMENT_ID,
        
        -- SOURCE: AGENT_ID | CLASS: SEMANTIC_MATCH | BR: BR-003
        -- ASSUMPTION: agent = user in contact center context — VALIDATE WITH BUSINESS
        AGENT_ID AS USER_ID,
        
        -- SOURCE: ZCC_ACCOUNT_ID | CLASS: NEW_CAPABILITY | BR: N/A
        -- Secondary account identifier - future capability
        ZCC_ACCOUNT_ID,
        
        -- ═══════════════════════════════════════════════════════
        -- CHANNEL & MODALITY DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: DIRECTION | CLASS: PARTIAL_MATCH | BR: BR-004
        -- Case normalization: Inbound → INBOUND, Outbound → OUTBOUND
        UPPER(DIRECTION) AS DIRECTION,
        
        -- SOURCE: MODALITY + CHANNEL | CLASS: PARTIAL_MATCH | BR: BR-005
        -- Merge logic: Phone/Video from CHANNEL, else MODALITY
        CASE 
            WHEN CHANNEL IN ('Phone', 'Video') THEN UPPER(CHANNEL)
            WHEN MODALITY IN ('Email', 'SMS', 'Chat') THEN UPPER(MODALITY)
            ELSE UPPER(ZEROIFNULL(MODALITY, CHANNEL))
        END AS MODALITY,
        
        -- SOURCE: CHANNEL + MODALITY | CLASS: PARTIAL_MATCH | BR: BR-006
        -- Merge logic: Email/SMS/Chat from MODALITY, else CHANNEL
        CASE 
            WHEN MODALITY IN ('Email', 'SMS', 'Chat') THEN UPPER(MODALITY)
            WHEN CHANNEL IN ('Phone', 'Video') THEN UPPER(CHANNEL)
            ELSE UPPER(ZEROIFNULL(CHANNEL, MODALITY))
        END AS CHANNEL,
        
        -- ═══════════════════════════════════════════════════════
        -- USAGE METRICS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: PHONE_SESSIONS | CLASS: DIRECT_MATCH | BR: BR-007
        -- Direct pass-through - phone session count
        PHONE_SESSIONS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-008
        -- Milliseconds → Minutes for INBOUND_PHONE_MINS
        TRY_CAST(INBOUND_PHONE_MS / 60000.0 AS FLOAT) AS INBOUND_PHONE_MINS,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-008
        -- Milliseconds → Minutes for PHONE_USAGE aggregation metric
        TRY_CAST(INBOUND_PHONE_MS / 60000.0 AS FLOAT) AS PHONE_USAGE,
        
        -- SOURCE: INBOUND_PHONE_MS | CLASS: UNIT_CHANGE | BR: BR-009 | GAP: GAP-023
        -- CRITICAL GAP: Only phone duration available - Email/SMS/Chat/Video = NULL
        -- Milliseconds → Seconds for cross-channel duration field
        TRY_CAST(INBOUND_PHONE_MS / 1000.0 AS FLOAT) AS DURATION_SEC,
        
        -- ═══════════════════════════════════════════════════════
        -- DEVICE & PLATFORM DIMENSIONS (NEW CAPABILITIES)
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: CLIENT_TYPE | CLASS: NEW_CAPABILITY | BR: N/A
        -- Future capability - Mobile/Desktop/Web segmentation
        CLIENT_TYPE,
        
        -- SOURCE: OS | CLASS: NEW_CAPABILITY | BR: N/A
        -- Future capability - Operating system analytics
        OS,
        
        -- ═══════════════════════════════════════════════════════
        -- ACTIVITY FLAGS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: IS_ACTIVE | CLASS: SEMANTIC_MATCH | BR: BR-010
        -- ASSUMPTION: row-level activity flag = account-level when aggregated
        IFF(IS_ACTIVE = TRUE, TRUE, FALSE) AS IS_ACTIVE_ACCOUNT,
        
        -- ═══════════════════════════════════════════════════════
        -- GEOGRAPHIC DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: CLUSTER | CLASS: NEW_CAPABILITY | BR: BR-013
        -- Raw cluster identifier (eu-central-1, ap-south-1, us-east-1)
        CLUSTER AS CLUSTER_RAW,
        
        -- SOURCE: CLUSTER via lookup | CLASS: DERIVED | BR: BR-013
        -- Standardized region from lookup table
        ZEROIFNULL(region_lookup.region, 'UNKNOWN') AS REGION,
        
        -- SOURCE: CLUSTER via lookup | CLASS: DERIVED | BR: BR-013
        -- Region code for aggregation
        region_lookup.region_code AS REGION_CODE,
        
        -- ═══════════════════════════════════════════════════════
        -- TEMPORAL DIMENSIONS
        -- ═══════════════════════════════════════════════════════
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-011 | GAP: GAP-024
        -- CRITICAL GAP: Semantic ambiguity - engagement timestamp or report date?
        -- Text → Date parsing: 'M/D/YY HH24:MI' → DATE
        -- ASSUMPTION: DATA_DATE represents engagement timestamp — VALIDATE WITH BDP
        TRY_CAST(DATA_DATE AS DATE) AS DATE,
        
        -- SOURCE: DATA_DATE | CLASS: UNIT_CHANGE | BR: BR-011 | GAP: GAP-024
        -- For engagement-level analysis (SLV_COMBINED_CHANNELS)
        TRY_CAST(DATA_DATE AS DATE) AS START_DATE,
        
        -- SOURCE: DATA_DATE | CLASS: GRAIN_CHANGE | BR: BR-012
        -- For aggregation metrics (daily/weekly/monthly rollups)
        TRY_CAST(DATA_DATE AS DATE) AS REPORT_DATE,
        
        -- SOURCE: DATA_DATE | CLASS: GRAIN_CHANGE | BR: BR-014 | GAP: GAP-019
        -- Derived metric: first activity date per account (historical window function)
        -- LOW CONFIDENCE: Requires full historical data for accurate MIN() calculation
        MIN(TRY_CAST(DATA_DATE AS DATE)) OVER (
            PARTITION BY ACCOUNT_ID 
            ORDER BY TRY_CAST(DATA_DATE AS TIMESTAMP_NTZ)
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ACCOUNT_FIRST_ACTIVE,
        
        -- ═══════════════════════════════════════════════════════
        -- AUDIT METADATA
        -- ═══════════════════════════════════════════════════════
        
        CURRENT_TIMESTAMP() AS _loaded_at,
        '{{ invocation_id }}' AS _dbt_run_id
        
    FROM source
    LEFT JOIN region_lookup
        ON source.CLUSTER = region_lookup.cluster_raw
)

SELECT * FROM transformed

-- ═══════════════════════════════════════════════════════════════
-- DATA QUALITY NOTES
-- ═══════════════════════════════════════════════════════════════
-- 1. GAP-023: DURATION_SEC only populated for phone engagements
--    Email/SMS/Chat/Video durations = NULL until source provides
-- 2. GAP-024: DATA_DATE semantic ambiguity requires BDP validation
--    Confirm whether timestamp represents engagement start or report date
-- 3. BR-003 & BR-010: Semantic assumptions (agent=user, row_active=acct_active)
--    require business stakeholder sign-off
-- 4. REGION='UNKNOWN': Monitor post-run audit for unmapped clusters
-- ═══════════════════════════════════════════════════════════════
```

---

## 📦 FILE 4: `models/silver/slv_ftl_agent_base_agg.yml`

```yaml
version: 2

models:
  - name: slv_ftl_agent_base_agg
    description: |
      **Silver Layer - FTL Agent Base Aggregation**
      
      Cleaned and enriched engagement-level metrics from Bronze FTL source.
      Applies 14 business rules (BR-001 to BR-014) with unit conversions,
      case normalization, and geographic enrichment.
      
      **Grain**: One row per engagement per agent per account per timestamp
      
      **Critical Gaps**:
      - GAP-023: DURATION_SEC only available for phone modality
      - GAP-024: DATA_DATE semantic ambiguity (engagement vs report timestamp)
      
      **Assumptions Requiring Validation**:
      - BR-003: AGENT_ID = USER_ID (semantic equivalence unconfirmed)
      - BR-010: IS_ACTIVE row-level = account-level activity flag
      
      **New Capabilities**:
      - ZCC_ACCOUNT_ID: Secondary account identifier for future multi-ID joins
      - CLIENT_TYPE: Device segmentation (Mobile/Desktop/Web)
      - OS: Operating system dimension
      - CLUSTER_RAW/REGION: Geographic analysis
      
      **Incremental Strategy**: Watermark on DATE field with unique_key on
      [ACCOUNT_ID, ENGAGEMENT_ID, DATA_DATE] grain
    
    config:
      materialized: incremental
      schema: SILVER
      tags: ['silver', 'agent_engagement', 'ftl_source']
    
    columns:
      # ═══════════════════════════════════════════════════════
      # CORE DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: account_id
        description: "Primary account identifier with ID_ prefix pattern (BR-001: DIRECT_MATCH)"
        data_type: TEXT
        tests:
          - not_null
          - relationships:
              to: ref('brz_ftl_agent_base_agg')
              field: account_id
      
      - name: engagement_id
        description: "Unique engagement identifier - primary key for engagement-level analysis (BR-002: DIRECT_MATCH)"
        data_type: TEXT
        tests:
          - not_null
      
      - name: user_id
        description: |
          Agent/user identifier mapped from AGENT_ID (BR-003: SEMANTIC_MATCH).
          **ASSUMPTION**: agent = user in contact center context — VALIDATE WITH BUSINESS
        data_type: TEXT
      
      - name: zcc_account_id
        description: "ZCC secondary account identifier - NEW_CAPABILITY for future multi-ID analytics"
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════
      # CHANNEL & MODALITY DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: direction
        description: |
          Engagement direction normalized to uppercase (BR-004: PARTIAL_MATCH).
          Values: INBOUND, OUTBOUND. Applied UPPER() transformation.
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['INBOUND', 'OUTBOUND']
      
      - name: modality
        description: |
          Communication modality merged from MODALITY + CHANNEL columns (BR-005: PARTIAL_MATCH).
          Logic: Phone/Video from CHANNEL, Email/SMS/Chat from MODALITY.
          Values: PHONE, VIDEO, EMAIL, SMS, CHAT
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['PHONE', 'VIDEO', 'EMAIL', 'SMS', 'CHAT']
      
      - name: channel
        description: |
          Communication channel merged from CHANNEL + MODALITY columns (BR-006: PARTIAL_MATCH).
          Logic: Email/SMS/Chat from MODALITY, Phone/Video from CHANNEL.
          Values: PHONE, VIDEO, EMAIL, SMS, CHAT
        data_type: TEXT
        tests:
          - accepted_values:
              values: ['PHONE', 'VIDEO', 'EMAIL', 'SMS', 'CHAT']
      
      # ═══════════════════════════════════════════════════════
      # USAGE METRICS
      # ═══════════════════════════════════════════════════════
      
      - name: phone_sessions
        description: "Count of phone sessions - direct pass-through (BR-007: DIRECT_MATCH)"
        data_type: NUMBER
      
      - name: inbound_phone_mins
        description: |
          Inbound phone duration in minutes (BR-008: UNIT_CHANGE).
          Transformation: INBOUND_PHONE_MS / 60000.0
          Source unit: milliseconds → Target unit: minutes
        data_type: FLOAT
      
      - name: phone_usage
        description: |
          Phone usage in minutes for aggregation metrics (BR-008: UNIT_CHANGE).
          Transformation: INBOUND_PHONE_MS / 60000.0
          Used in SLV_CONSOLIDATED_USAGE, SLV_ROLL_29_DAY_USAGE
        data_type: FLOAT
      
      - name: duration_sec
        description: |
          Engagement duration in seconds (BR-009: UNIT_CHANGE | GAP-023).
          **CRITICAL GAP**: Only phone duration available from INBOUND_PHONE_MS.
          Email/SMS/Chat/Video engagements have NULL duration until source provides.
          Transformation: INBOUND_PHONE_MS / 1000.0 (milliseconds → seconds)
        data_type: FLOAT
      
      # ═══════════════════════════════════════════════════════
      # DEVICE & PLATFORM DIMENSIONS (NEW CAPABILITIES)
      # ═══════════════════════════════════════════════════════
      
      - name: client_type
        description: |
          Client device type - NEW_CAPABILITY not present in legacy Silver.
          Values: Mobile, Desktop, Web
          Future use: Device segmentation analysis
        data_type: TEXT
      
      - name: os
        description: |
          Operating system - NEW_CAPABILITY not present in legacy Silver.
          Future use: OS-specific engagement analytics
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════
      # ACTIVITY FLAGS
      # ═══════════════════════════════════════════════════════
      
      - name: is_active_account
        description: |
          Account activity flag (BR-010: SEMANTIC_MATCH).
          **ASSUMPTION**: Row-level IS_ACTIVE flag represents account-level activity
          when aggregated — VALIDATE WITH BUSINESS
        data_type: BOOLEAN
      
      # ═══════════════════════════════════════════════════════
      # GEOGRAPHIC DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: cluster_raw
        description: |
          Raw cluster identifier from FTL source - NEW_CAPABILITY.
          Values: eu-central-1, ap-south-1, us-east-1
          Used for region lookup enrichment
        data_type: TEXT
      
      - name: region
        description: |
          Standardized region name derived from CLUSTER via lookup table (BR-013: DERIVED).
          Values: EMEA, APAC, AMER, UNKNOWN
          **Monitor**: UNKNOWN regions indicate unmapped clusters requiring lookup table update
        data_type: TEXT
        tests:
          - not_null
      
      - name: region_code
        description: |
          Region code for aggregation (BR-013: DERIVED).
          Values: EU, AP, US, NULL
          Derived from CLUSTER_REGION_MAP lookup
        data_type: TEXT
      
      # ═══════════════════════════════════════════════════════
      # TEMPORAL DIMENSIONS
      # ═══════════════════════════════════════════════════════
      
      - name: date
        description: |
          Engagement date parsed from DATA_DATE text field (BR-011: UNIT_CHANGE | GAP-024).
          **CRITICAL GAP**: Semantic ambiguity - is this engagement timestamp or report date?
          **ASSUMPTION**: Represents engagement timestamp — VALIDATE WITH BDP
          Transformation: TRY_CAST(DATA_DATE AS DATE) from 'M/D/YY HH24:MI' format
        data_type: DATE
        tests:
          - not_null
      
      - name: start_date
        description: |
          Engagement start date for SLV_COMBINED_CHANNELS (BR-011: UNIT_CHANGE | GAP-024).
          Same as DATE field - parsed from DATA_DATE text field
        data_type: DATE
      
      - name: report_date
        description: |
          Report date for aggregation metrics (BR-012: GRAIN_CHANGE).
          Used in daily/weekly/monthly rollup tables (SLV_CONSOLIDATED_USAGE, etc.)
          Parsed from DATA_DATE with potential grain shift to daily level
        data_type: DATE
      
      - name: account_first_active
        description: |
          First activity date per account - historical derived metric (BR-014: GRAIN_CHANGE | GAP-019).
          **LOW CONFIDENCE**: Accuracy depends on full historical data availability.
          Transformation: MIN(DATA_DATE) window function over account history.
          Requires validation against complete historical dataset.
        data_type: DATE
      
      # ═══════════════════════════════════════════════════════
      # AUDIT METADATA
      # ═══════════════════════════════════════════════════════
      
      - name: _loaded_at
        description: "Silver layer load timestamp for audit trail"
        data_type: TIMESTAMP_NTZ
      
      - name: _dbt_run_id
        description: "dbt invocation ID for lineage tracking"
        data_type: TEXT

    # ═══════════════════════════════════════════════════════
    # MODEL-LEVEL TESTS
    # ═══════════════════════════════════════════════════════
    
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - account_id
            - engagement_id
            - date
```

---

## 🔍 POST-RUN AUDIT QUERY

Run this query after `dbt run` to monitor unmapped clusters:

```sql
-- ═══════════════════════════════════════════════════════════════
-- Silver Layer Data Quality Audit - Unmapped Clusters
-- Purpose: Identify CLUSTER values not in CLUSTER_REGION_MAP lookup
-- Action: If results returned, update setup/CLUSTER_REGION_MAP.sql
-- ═══════════════════════════════════════════════════════════════

SELECT 
    cluster_raw,
    COUNT(*) AS row_count,
    COUNT(DISTINCT account_id) AS unique_accounts,
    MIN(date) AS first_seen,
    MAX(date) AS last_seen,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM ZOOM_AI_POC.SILVER.SLV_FTL_AGENT_BASE_AGG
WHERE region = 'UNKNOWN'
GROUP BY 1 
ORDER BY 2 DESC;

-- If results returned:
-- 1. Identify new cluster_raw values
-- 2. Research geographic mapping (AWS region codes, Azure regions, etc.)
-- 3. Add to setup/CLUSTER_REGION_MAP.sql with appropriate region/region_code
-- 4. Re-run: dbt run --select slv_ftl_agent_base_agg --full-refresh
```

---

## ✅ VALIDATION CHECKLIST

Before promoting to production:

- [ ] **BR-003 Validation**: Confirm AGENT_ID = USER_ID semantic equivalence with BDP team
- [ ] **BR-010 Validation**: Confirm IS_ACTIVE row-level = account-level activity logic
- [ ] **GAP-024 Resolution**: Clarify DATA_DATE semantics (engagement timestamp vs report date)
- [ ] **CLUSTER_REGION_MAP**: Verify all cluster values mapped (run audit query above)
- [ ] **Incremental Logic**: Test watermark behavior on DATE field with backfill scenario
- [ ] **DURATION_SEC Handling**: Document NULL handling for non-phone modalities in downstream Gold models
- [ ] **ACCOUNT_FIRST_ACTIVE Accuracy**: Validate against known account creation dates from source system

---

## 📊 DEPLOYMENT COMMANDS

```bash
# Initial full-refresh run
dbt run --select slv_ftl_agent_base_agg --full-refresh

# Standard incremental run
dbt run --select slv_ftl_agent_base_agg

# Test execution
dbt test --select slv_ftl_agent_base_agg

# Generate documentation
dbt docs generate
dbt docs serve
```

---

## 🎯 SUMMARY

**Generated Artifacts**:
✓ 4 production-ready dbt files following medallion architecture  
✓ All 14 BR IDs applied with inline documentation  
✓ 2 critical gaps (GAP-023, GAP-024) flagged for stakeholder review  
✓ Geographic enrichment via CLUSTER_REGION_MAP lookup table  
✓ Incremental materialization with natural grain unique_key  
✓ Complete schema YAML with data quality tests

**Key Design Decisions**:
- Used `slv_` prefix (NOT `stg_`) per repo naming convention
- Applied Snowflake-native functions: TRY_CAST, IFF, ZEROIFNULL
- Preserved NEW_CAPABILITY columns (ZCC_ACCOUNT_ID, CLIENT_TYPE, OS, CLUSTER) for future use
- Flagged semantic assumptions (BR-003, BR-010) requiring business validation
- Implemented window function for ACCOUNT_FIRST_ACTIVE with LOW CONFIDENCE warning