

🔍 **STEP 1: Schema Discovery Complete** — Discovered 1 source table (Bronze FTL), 10 Silver tables, 1 Gold table

🔍 **STEP 2: Data Profiling Complete** — Profiled all 12 tables with column statistics and sample values

🔍 **STEP 3: Silver Layer Mapping Analysis Complete** — Identified 45 transformation rules and 23 gap items

🔍 **STEP 4: Gold Layer Mapping Analysis Complete** — Identified 3 critical blocking gaps

🔍 **STEP 5: Synthesizing Comprehensive Migration Report** — Assigning GAP IDs and BR IDs consistently across all sections

---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 1: EXECUTIVE SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG  
**Target PI Silver Tables:** 10 tables (SLV_CONSOLIDATED_USAGE, SLV_ACCT_FIRST_ACTIVE, SLV_COMBINED_CHANNELS, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_ACTIVE_DAYS, SLV_USER_FIRST_ACTIVE, SLV_WEEKLY_METRICS)  
**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE  

**Migration Readiness Score:** 42/100

**Total FTL columns analyzed:** 14  
**Successfully mapped:** 6 (ACCOUNT_ID, ENGAGEMENT_ID, AGENT_ID, DIRECTION, MODALITY, CHANNEL, PHONE_SESSIONS, INBOUND_PHONE_MS, IS_ACTIVE)  
**Partially mapped:** 2 (DATA_DATE requires parsing, CLUSTER requires region mapping)  
**New capabilities (no PI equivalent):** 4 (ZCC_ACCOUNT_ID, CLIENT_TYPE, OS, CLUSTER)  
**Gaps (PI columns with no FTL source):** 26  
→ GAP-001: PHONE_DIALIN_COUNT (JIRA flagged - not present in FTL profile)  
→ GAP-002: SEGMENT (customer segment classification)  
→ GAP-003: IS_LICENSED (licensing status)  
→ GAP-004: USERS_ACTIVE_16PLUS_DAYS (temporal engagement metric)  
→ GAP-005: CHAT_USAGE / CHAT_SESSIONS (no chat duration or session counts)  
→ GAP-006: VIDEO_USAGE (no video duration data)  
→ GAP-007: ENGAGEMENT_STATUS (status values like Missed, Resolved, Answered)  
→ GAP-008: SLA_ACHIEVED / SLA_ACHIEVED_SESSIONS (SLA compliance data)  
→ GAP-009: IS_PAID_USER (payment/subscription status)  
→ GAP-010: ACTIVE_DAYS_LAST_7 / ACTIVE_DAYS_LAST_28 (rolling window activity)  
→ GAP-011: USERS_ACTIVE_1_DAY, USERS_ACTIVE_4_7_DAYS (activity cohorts)  
→ GAP-012: WINDOW (R1/R7/R28 aggregation window definitions)  
→ GAP-013: PRODUCT_NAME (static metadata)  
→ GAP-014: SOURCE_TABLE (lineage metadata)  
**Blocking items:** 3 (GAP-002 SEGMENT, GAP-003 IS_LICENSED, GAP-004 USERS_ACTIVE_16PLUS_DAYS prevent Gold layer migration)

**Assessment:** The FTL Bronze source provides strong foundational data for account, agent, and phone-centric metrics, but critical gaps exist in multi-channel usage tracking (chat, video), business dimension enrichment (segment, licensing), and temporal engagement analytics. Migration to Silver is feasible with caveats for 8 of 10 tables, but Gold layer migration is blocked by missing business dimensions. Historical data accumulation and external enrichment sources are required before full migration can proceed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 2: GAP IMPACT SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold/Silver Column | Why It's a Gap | Impact on Gold Output | Blocks Migration? | Action Required | Raise With |
|--------|----------------------|----------------|----------------------|-------------------|-----------------|------------|
| GAP-001 | PHONE_DIALIN_COUNT | Flagged in JIRA CORTEX-2 but not present in actual FTL profile | Cannot calculate dial-in phone usage if column expected | **PENDING** | Verify if column exists in production FTL vs dev/test environment | Zoom FTL Team + BDP |
| GAP-002 | SEGMENT (Gold) | No customer segment classification data in FTL source | Gold layer cannot produce segment-based reports (e.g., Enterprise vs SMB metrics) | **YES** | Requires external dimension table join or FTL enhancement | BDP Team + Data Governance |
| GAP-003 | IS_LICENSED (Gold) | No licensing/subscription status in FTL source | Cannot distinguish licensed users from trial/free tier in Gold aggregates | **YES** | Requires external subscription data source | BDP Team + Billing Systems |
| GAP-004 | USERS_ACTIVE_16PLUS_DAYS (Gold) | No temporal activity tracking in FTL - single snapshot per row | Gold layer engagement KPI missing - core retention metric unavailable | **YES** | Requires historical data accumulation + window function logic | BDP Team |
| GAP-005 | CHAT_USAGE / CHAT_SESSIONS | FTL has MODALITY='Chat' but no duration or session count fields | Chat metrics across Silver tables will be NULL or 0 | NO | Can filter MODALITY but usage will show 0 minutes until FTL adds chat duration | Zoom FTL Team |
| GAP-006 | VIDEO_USAGE | FTL has CHANNEL='Video' but no duration field (only INBOUND_PHONE_MS for phone) | Video metrics in MONTHLY_METRICS will be NULL | NO | Can identify video engagements but not measure duration | Zoom FTL Team |
| GAP-007 | ENGAGEMENT_STATUS | No status field (Missed, Resolved, Answered, etc.) in FTL | SLV_COMBINED_CHANNELS.ENGAGEMENT_STATUS will be NULL | NO | Can populate once FTL adds status tracking | Zoom FTL Team |
| GAP-008 | SLA_ACHIEVED / SLA_ACHIEVED_SESSIONS | No SLA compliance data in FTL | SLA metrics in USAGE_MASTER and COMBINED_CHANNELS will be NULL | NO | Requires SLA calculation logic or external SLA target data | BDP Team |
| GAP-009 | IS_PAID_USER | No payment/subscription indicator in FTL | SLV_ROLL_29_DAY_USAGE cannot segment by paid vs free users | NO | Requires external billing data join | Billing Systems Team |
| GAP-010 | ACTIVE_DAYS_LAST_7 / ACTIVE_DAYS_LAST_28 | FTL is snapshot data - no historical activity tracking | Rolling window metrics in SLV_ROLL_29_DAY_USAGE will be NULL until history accumulated | NO | Requires 28+ days of FTL data accumulation + window function implementation | BDP Team |
| GAP-011 | USERS_ACTIVE_1_DAY, USERS_ACTIVE_4_7_DAYS, USERS_ACTIVE_16PLUS_DAYS | No activity cohort tracking in FTL | Activity cohort tables (SLV_USER_ACTIVE_DAYS, daily/weekly/monthly metrics) cannot classify users by activity frequency | NO | Requires historical data + cohort classification logic | BDP Team |
| GAP-012 | WINDOW | No R1/R7/R28 window indicator in FTL | All metrics tables requiring WINDOW column need windowing logic added in Silver transformation | NO | Generate WINDOW values in Silver DBT models based on aggregation date ranges | BDP Team |
| GAP-013 | PRODUCT_NAME | Not in FTL | SLV_CONSOLIDATED_USAGE will use hardcoded 'ZCC Platform' value | NO | Hardcode in Silver transformation | BDP Team |
| GAP-014 | SOURCE_TABLE | Lineage metadata not in FTL | SLV_COMBINED_CHANNELS will use static value or NULL | NO | Populate with 'BRZ_FTL_AGENT_BASE_AGG' in Silver transformation | BDP Team |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 3: TRANSFORMATION GUIDE (Business Rules)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | REPORT_DATE / DATE / START_DATE | TYPE_CHANGE | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | FTL stores date as TEXT in M/D/YY format - all Silver/Gold tables require DATE type | DATA_DATE format consistency | [ASSUMPTION] Date format is M/D/YY HH24:MI based on sample '5/29/26 13:01' |
| BR-002 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS | UNIT_CHANGE | `INBOUND_PHONE_MS / 60000.0` | Convert milliseconds to minutes for PI standard | INBOUND_PHONE_MS not NULL | Standard conversion - 1 minute = 60,000 ms |
| BR-003 | INBOUND_PHONE_MS | PHONE_USAGE (hours) | UNIT_CHANGE | `SUM(INBOUND_PHONE_MS) / 3600000.0` | Convert milliseconds to hours and aggregate for usage metrics | INBOUND_PHONE_MS, grouping dimensions | [ASSUMPTION] Usage measured in hours in Gold layer |
| BR-004 | INBOUND_PHONE_MS | DURATION_SEC | UNIT_CHANGE | `INBOUND_PHONE_MS / 1000.0` | Convert milliseconds to seconds for SLV_COMBINED_CHANNELS | INBOUND_PHONE_MS not NULL | Standard conversion - 1 second = 1,000 ms |
| BR-005 | DIRECTION | DIRECTION | CASE_CHANGE | `UPPER(DIRECTION)` | FTL uses 'Inbound'/'Outbound' - PI uses 'INBOUND'/'OUTBOUND' | DIRECTION not NULL | Distinct value query confirms only case differs |
| BR-006 | CHANNEL | CHANNEL | CASE_CHANGE | `UPPER(CHANNEL)` | FTL uses 'Phone'/'Video' - PI uses 'PHONE'/'VIDEO' | CHANNEL not NULL | Distinct value query confirms only case differs |
| BR-007 | ACCOUNT_ID | ACCOUNT_ID | DIRECT_MATCH | `ACCOUNT_ID` | Direct column match - no transformation needed | None | Semantic and structural alignment confirmed |
| BR-008 | ENGAGEMENT_ID | ENGAGEMENT_ID | DIRECT_MATCH | `ENGAGEMENT_ID` | Direct column match - no transformation needed | None | Semantic and structural alignment confirmed |
| BR-009 | AGENT_ID | USER_ID | RENAME | `AGENT_ID AS USER_ID` | FTL uses AGENT_ID - PI uses USER_ID for same concept | AGENT_ID not NULL | [ASSUMPTION] Agent and User represent same entity - requires business validation |
| BR-010 | IS_ACTIVE | IS_ACTIVE_ACCOUNT | SEMANTIC_MATCH | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | Row-level IS_ACTIVE assumed to indicate account activity | IS_ACTIVE not NULL | [LOW CONFIDENCE] Unclear if IS_ACTIVE means account or user activity |
| BR-011 | PHONE_SESSIONS | PHONE_SESSIONS | DIRECT_MATCH | `PHONE_SESSIONS` | Direct column match - no transformation needed | None | Semantic and structural alignment confirmed |
| BR-012 | MODALITY | MODALITY | DIRECT_MATCH | `MODALITY` | Direct column match - values align (Chat, Email, SMS) | None | Semantic and structural alignment confirmed |
| BR-013 | DATA_DATE | ACCOUNT_FIRST_ACTIVE | AGGREGATION | `MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY ACCOUNT_ID)` | First occurrence of account in FTL = first active date | DATA_DATE not NULL | [ASSUMPTION] First record = first active date (no historical backfill) |
| BR-014 | DATA_DATE | USER_FIRST_ACTIVE | AGGREGATION | `MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY AGENT_ID)` | First occurrence of agent in FTL = first active date | DATA_DATE not NULL | [ASSUMPTION] First record = first active date |
| BR-015 | AGENT_ID | ACTIVE_USERS | AGGREGATION | `COUNT(DISTINCT CASE WHEN IS_ACTIVE THEN AGENT_ID END)` | Count distinct active agents per grouping dimension | IS_ACTIVE, AGENT_ID, grouping keys | Assumes AGENT_ID represents unique users |
| BR-016 | ACCOUNT_ID | ACTIVE_ACCOUNTS | AGGREGATION | `COUNT(DISTINCT CASE WHEN IS_ACTIVE THEN ACCOUNT_ID END)` | Count distinct active accounts per grouping dimension | IS_ACTIVE, ACCOUNT_ID, grouping keys | Account-level activity aggregation |
| BR-017 | CLUSTER | REGION | LOOKUP | `CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'OTHER' END` | Map AWS cluster regions to business regions for Gold layer | CLUSTER not NULL, CLUSTER_REGION_MAP table | [ASSUMPTION] Mapping logic based on AWS region prefixes - requires validation with business region definitions |
| BR-018 | — | REFRESH_TIMESTAMP | SYSTEM_GENERATED | `CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP` | System-generated timestamp for ETL metadata | None | Standard practice for tracking data freshness |
| BR-019 | — | PRODUCT_NAME | STATIC_VALUE | `'ZCC Platform' AS PRODUCT_NAME` | Hardcoded product name - FTL source is ZCC-specific | None | GAP-013: No product dimension in FTL |
| BR-020 | — | SOURCE_TABLE | STATIC_VALUE | `'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE` | Lineage metadata for tracking data origin | None | GAP-014: No source tracking in FTL |
| BR-021 | — | WINDOW | DERIVED | `CASE WHEN DATE_DIFF = 1 THEN 'R1' WHEN DATE_DIFF <= 7 THEN 'R7' WHEN DATE_DIFF <= 28 THEN 'R28' END` | Generate rolling window indicator based on date range | Date calculation logic | GAP-012: Window logic must be implemented in Silver - requires business rule validation |
| BR-022 | MODALITY | CHAT_USAGE | CONDITIONAL_AGGREGATION | `SUM(CASE WHEN MODALITY = 'Chat' THEN 0 ELSE 0 END) -- GAP-005` | Filter for chat modality but no duration data available | MODALITY | GAP-005: Chat duration not in FTL - will produce 0 until source enhanced |
| BR-023 | CHANNEL | VIDEO_USAGE | CONDITIONAL_AGGREGATION | `SUM(CASE WHEN CHANNEL = 'Video' THEN 0 ELSE 0 END) -- GAP-006` | Filter for video channel but no duration data available | CHANNEL | GAP-006: Video duration not in FTL - will produce 0 until source enhanced |
| BR-024 | — | ENGAGEMENT_STATUS | NULL_PLACEHOLDER | `NULL AS ENGAGEMENT_STATUS -- GAP-007` | Status field not available in FTL source | None | GAP-007: Requires FTL enhancement or external data source |
| BR-025 | — | SLA_ACHIEVED | NULL_PLACEHOLDER | `NULL AS SLA_ACHIEVED -- GAP-008` | SLA compliance not tracked in FTL | None | GAP-008: Requires SLA target data and calculation logic |
| BR-026 | — | SLA_ACHIEVED_SESSIONS | NULL_PLACEHOLDER | `NULL AS SLA_ACHIEVED_SESSIONS -- GAP-008` | SLA session count not available | None | GAP-008: Requires SLA tracking enhancement |
| BR-027 | — | IS_PAID_USER | NULL_PLACEHOLDER | `NULL AS IS_PAID_USER -- GAP-009` | Payment status not in FTL | None | GAP-009: Requires billing system data join |
| BR-028 | — | ACTIVE_DAYS_LAST_7 | NULL_PLACEHOLDER | `NULL AS ACTIVE_DAYS_LAST_7 -- GAP-010` | Rolling window requires 7+ days of historical data | Historical FTL data | GAP-010: Will populate once historical data accumulated |
| BR-029 | — | ACTIVE_DAYS_LAST_28 | NULL_PLACEHOLDER | `NULL AS ACTIVE_DAYS_LAST_28 -- GAP-010` | Rolling window requires 28+ days of historical data | Historical FTL data | GAP-010: Will populate once historical data accumulated |
| BR-030 | MODALITY | CHAT_SESSIONS | CONDITIONAL_COUNT | `SUM(CASE WHEN MODALITY = 'Chat' THEN 1 ELSE 0 END) -- GAP-005` | Count chat engagements (not sessions - session concept unclear in FTL) | MODALITY | GAP-005: FTL granularity may not match PI session definition |
| BR-031 | — | USERS_ACTIVE_1_DAY | NULL_PLACEHOLDER | `NULL AS USERS_ACTIVE_1_DAY -- GAP-011` | Requires historical activity tracking and cohort classification | Historical data + cohort logic | GAP-011: Activity cohort logic not yet implemented |
| BR-032 | — | USERS_ACTIVE_4_7_DAYS | NULL_PLACEHOLDER | `NULL AS USERS_ACTIVE_4_7_DAYS -- GAP-011` | Requires historical activity tracking and cohort classification | Historical data + cohort logic | GAP-011: Activity cohort logic not yet implemented |
| BR-033 | — | USERS_ACTIVE_16PLUS_DAYS | NULL_PLACEHOLDER | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP-004, GAP-011` | Requires historical activity tracking - BLOCKS GOLD MIGRATION | Historical data + cohort logic | GAP-004: Critical Gold metric - migration blocked until resolved |
| BR-034 | — | SEGMENT | NULL_PLACEHOLDER | `NULL AS SEGMENT -- GAP-002` | Customer segment not in FTL - BLOCKS GOLD MIGRATION | External segment dimension table | GAP-002: Critical Gold dimension - requires external data source |
| BR-035 | — | IS_LICENSED | NULL_PLACEHOLDER | `NULL AS IS_LICENSED -- GAP-003` | Licensing status not in FTL - BLOCKS GOLD MIGRATION | External subscription/billing data | GAP-003: Critical Gold dimension - requires external data source |
| BR-036 | — | PHONE_DIALIN_COUNT | NULL_PLACEHOLDER | `NULL AS PHONE_DIALIN_COUNT -- GAP-001` | Column mentioned in JIRA CORTEX-2 but not present in FTL profile | Unknown - requires investigation | GAP-001: Verify if column exists in production vs profiled environment |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 4: NEW FTL CAPABILITIES**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|-------------------|-------------------|----------------|
| ZCC_ACCOUNT_ID | TEXT | Zoom Contact Center account identifier (distinct from standard ACCOUNT_ID) | ZCC-specific account tracking and cross-referencing with standard accounts | PENDING DECISION | Confirm with BDP: Is this a separate dimension from ACCOUNT_ID or a duplicate? If separate, add to Silver for ZCC lineage tracking. Propose Gold extension if ZCC vs non-ZCC segmentation is needed. |
| CLIENT_TYPE | TEXT | Client application type (Desktop, Mobile, Web) | Client-based usage analytics - can segment by device type | YES | Add to Silver now (SLV_COMBINED_CHANNELS, SLV_USAGE_MASTER). Propose Gold extension for client-type usage reporting (e.g., mobile vs desktop adoption metrics). Valuable for UX and product analytics. |
| OS | TEXT | Operating system (currently only 'Sample Text' in profile - needs validation) | OS-based usage segmentation | PENDING DECISION | Validate data quality first (profile shows only 1 distinct value 'Sample Text'). If production data has real OS values, add to Silver. Gold extension depends on business need for OS-level reporting. |
| CLUSTER | TEXT | AWS cluster/region identifier (us-east-1, ap-south-1, eu-central-1) | Infrastructure-level tracking and region-based usage (currently mapped to REGION in Gold via BR-017) | YES (already mapped) | Keep in Silver for detailed infrastructure analysis. Already mapped to Gold REGION dimension via BR-017 business rule. Consider adding raw CLUSTER to Silver for troubleshooting and infrastructure reporting. |
| UNIQUE_ACTIVE_PARTICIPANTS | (not found in profile) | JIRA CORTEX-2 mentions this as NEW in FTL, but column not present in profiled table | Participant count per engagement (if present) | PENDING INVESTIGATION | **CRITICAL ISSUE**: JIRA CORTEX-2 states this column is new in FTL but it's not present in the profiled ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG table. Action required: Verify if this column exists in production or if profiling is against an older version. If column exists, it should be added to Silver engagement tables and could enrich Gold with participant-level metrics. |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 5: FEASIBILITY VERDICT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| SLV_ACCT_FIRST_ACTIVE | 75% | None (only date parsing required) | **Feasible** | Implement BR-001 (date parsing) and BR-013 (first active aggregation). Test date format consistency across all FTL records. |
| SLV_USER_FIRST_ACTIVE | 75% | None (only date parsing required) | **Feasible** | Implement BR-001 (date parsing) and BR-014 (first active aggregation). Validate AGENT_ID = USER_ID semantic mapping (BR-009). |
| SLV_USAGE_MASTER | 60% | GAP-005 (chat sessions), GAP-008 (SLA sessions) - non-blocking | **Feasible with Caveats** | Accept NULL values for CHAT_SESSIONS and SLA_ACHIEVED_SESSIONS initially. Implement BR-001, BR-002, BR-007, BR-008, BR-009, BR-011, BR-013, BR-014. Phone metrics will be accurate; chat/SLA metrics will populate when FTL source enhanced (GAP-005, GAP-008 resolution). |
| SLV_COMBINED_CHANNELS | 50% | GAP-007 (engagement status), GAP-008 (SLA achieved), GAP-014 (source table) - non-blocking | **Feasible with Caveats** | Accept NULL for ENGAGEMENT_STATUS and SLA_ACHIEVED. Implement BR-001, BR-004, BR-005, BR-006, BR-007, BR-008, BR-009, BR-012, BR-020. Duration only available for phone channel via INBOUND_PHONE_MS; video/chat/email durations will be NULL (GAP-006). |
| SLV_CONSOLIDATED_USAGE | 45% | GAP-012 (window logic), GAP-013 (product name), aggregation complexity | **Feasible with Caveats** | Implement windowing logic (BR-021) and validate business rules for R1/R7/R28 definitions. Hardcode PRODUCT_NAME (BR-019). Implement aggregation logic (BR-015, BR-016). Phone usage accurate via BR-003; accept initial limitation to phone-only metrics. |
| SLV_DAILY_METRICS | 40% | GAP-005 (chat usage), GAP-011 (users active 1 day), GAP-012 (window) | **Feasible with Caveats** | Accept NULL for CHAT_USAGE and USERS_ACTIVE_1_DAY until GAP-005 and GAP-011 resolved. Implement BR-021 (window), BR-015 (active users aggregation). Requires historical data accumulation for activity cohorts. |
| SLV_WEEKLY_METRICS | 40% | GAP-005 (chat usage), GAP-011 (users active 4-7 days), GAP-012 (window) | **Feasible with Caveats** | Accept NULL for CHAT_USAGE and USERS_ACTIVE_4_7_DAYS until gaps resolved. Implement BR-021 (window logic) and BR-015 (aggregation). Requires historical data for cohort classification (GAP-011). |
| SLV_MONTHLY_METRICS | 40% | GAP-006 (video usage), GAP-011 (users active 16+ days), GAP-012 (window) | **Feasible with Caveats** | Accept NULL for VIDEO_USAGE and USERS_ACTIVE_16PLUS_DAYS. Implement BR-021 (window), BR-015 (active users). Requires historical data accumulation and cohort logic implementation (GAP-011). |
| SLV_ROLL_29_DAY_USAGE | 25% | GAP-009 (is_paid_user), GAP-010 (active days last 7/28), GAP-005 (chat usage) - multiple blocking items for meaningful output | **Not Feasible** | Requires 28+ days of historical FTL data accumulation (GAP-010), external billing data integration (GAP-009), and chat duration tracking (GAP-005). Implement rolling window functions (BR-028, BR-029) only after historical data available. Block until minimum 28 days of FTL data accumulated. |
| SLV_USER_ACTIVE_DAYS | 20% | GAP-011 (all activity cohort columns), GAP-010 (rolling window calculations) | **Not Feasible** | All 4 activity cohort columns (ACTIVE_1_DAY_L7, ACTIVE_4_7_DAYS_L7, ACTIVE_1_DAY_L28, ACTIVE_16PLUS_DAYS_L28) require historical data and complex cohort classification logic. Block until historical data accumulated and cohort business rules defined and implemented (BR-031, BR-032). |
| GLD_AGGREGATE | 25% | GAP-002 (SEGMENT), GAP-003 (IS_LICENSED), GAP-004 (USERS_ACTIVE_16PLUS_DAYS) - **ALL BLOCKING** | **Not Feasible** | Gold migration blocked by 3 critical business dimensions. Conditions: (1) External customer segment dimension table must be created and joined via BR-034. (2) External licensing/subscription data source must be integrated via BR-035. (3) Historical activity tracking must be implemented via BR-033 (depends on GAP-011 resolution). Gold layer cannot produce meaningful business intelligence reports without these dimensions. |

**OVERALL VERDICT: Feasible with Major Caveats for Silver, Not Feasible for Gold**

**Silver Layer Summary:** 6 of 10 tables are feasible (2 fully feasible, 4 with caveats), 2 are not feasible (require historical data). Phone-centric metrics will be accurate; multi-channel metrics will be incomplete until FTL source enhanced.

**Gold Layer Summary:** Migration blocked. Cannot proceed until external dimension sources (segment, licensing) are integrated and historical data accumulation enables temporal engagement metrics.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 6: DBT MODEL IMPACT ANALYSIS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**6.1 — NEW TABLES TO CREATE**

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| INT_FTL_DAILY_BASE | Silver (Intermediate) | Daily grain base table with parsed dates and unit conversions from FTL source | BRZ_FTL_AGENT_BASE_AGG + BR-001, BR-002 |
| INT_FTL_ACCOUNT_FIRST_ACTIVE | Silver (Intermediate) | Account-level first active date calculation | INT_FTL_DAILY_BASE + BR-013 |
| INT_FTL_USER_FIRST_ACTIVE | Silver (Intermediate) | User-level first active date calculation | INT_FTL_DAILY_BASE + BR-014 |
| INT_FTL_ROLLING_WINDOWS | Silver (Intermediate) | Pre-calculated rolling window metrics (7-day, 28-day) for performance | INT_FTL_DAILY_BASE + 28 days historical data |
| INT_FTL_ACTIVITY_COHORTS | Silver (Intermediate) | User activity cohort classification (1-day, 4-7 day, 16+ day users) | INT_FTL_ROLLING_WINDOWS + cohort business rules |
| DIM_CUSTOMER_SEGMENT | Gold (Dimension) | External customer segment dimension table (if not exists) | External data source or manual classification |
| DIM_LICENSING_STATUS | Gold (Dimension) | External licensing/subscription status dimension | Billing system integration or external data source |
| STG_FTL_REGION_MAPPING | Staging/Seed | AWS CLUSTER to business REGION mapping reference table | Business region definitions (BR-017) |

**6.2 — EXISTING TABLES TO ALTER**

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|----------------|----------------|------------------|--------|
| SLV_USAGE_MASTER | Silver | Add new device/platform columns from FTL capabilities | CLIENT_TYPE (TEXT), CLUSTER (TEXT) | None | Low impact - additive only. Enables client-type and infrastructure-level analysis. Existing queries unaffected. |
| SLV_COMBINED_CHANNELS | Silver | Add device tracking and update source logic | CLIENT_TYPE (TEXT), OS (TEXT - pending validation) | SOURCE_TABLE (now 'BRZ_FTL_AGENT_BASE_AGG'), DURATION_SEC (now NULL for non-phone channels) | Medium impact - DURATION_SEC will be NULL for video/chat/email until FTL enhanced. Queries filtering on DURATION_SEC need NULL handling. |
| SLV_CONSOLIDATED_USAGE | Silver | Accept NULL for non-phone usage, add window generation logic | None | PHONE_USAGE (accurate from FTL), add derived WINDOW column logic | Medium impact - table will only show phone usage initially. Chat/video usage columns remain in schema but return 0/NULL until FTL source enhanced. |
| SLV_DAILY_METRICS | Silver | Accept NULL for chat usage and activity cohorts | None | CHAT_USAGE (NULL/0 initially), USERS_ACTIVE_1_DAY (NULL initially) | Medium impact - metrics will be incomplete until historical data accumulated. Reports dependent on these metrics will show NULL. |
| SLV_WEEKLY_METRICS | Silver | Accept NULL for chat usage and activity cohorts | None | CHAT_USAGE (NULL/0 initially), USERS_ACTIVE_4_7_DAYS (NULL initially) | Medium impact - incomplete metrics initially. |
| SLV_MONTHLY_METRICS | Silver | Accept NULL for video usage and 16+ day cohorts | None | VIDEO_USAGE (NULL/0 initially), USERS_ACTIVE_16PLUS_DAYS (NULL initially) | Medium impact - Gold dependency on USERS_ACTIVE_16PLUS_DAYS blocks Gold layer. |
| SLV_ROLL_29_DAY_USAGE | Silver | **DEFER CREATION** until historical data available | N/A - table creation deferred | N/A | High impact - table not feasible to create until 28+ days of FTL data accumulated. Downstream dependencies blocked. |
| SLV_USER_ACTIVE_DAYS | Silver | **DEFER CREATION** until cohort logic implemented | N/A - table creation deferred | N/A | High impact - all activity cohort columns infeasible without historical data. Defer until historical accumulation + cohort rules implemented. |
| GLD_AGGREGATE | Gold | **BLOCK MIGRATION** until external dimensions available | None | SEGMENT (requires external dimension join - GAP-002), IS_LICENSED (requires external billing data - GAP-003), USERS_ACTIVE_16PLUS_DAYS (requires historical data - GAP-004) | **CRITICAL IMPACT** - Gold layer cannot be migrated. All 3 columns are core business dimensions. Table will not function as business intelligence layer without these fields. Migration must be blocked until gaps resolved. |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 7: RECOMMENDED ACTIONS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**1. BLOCKING ITEMS (Must resolve before full migration)**

1.1. **Resolve Gold Layer Dimension Gaps (GAP-002, GAP-003, GAP-004)**  
   - **GAP-002 (SEGMENT):** Identify customer segment data source. Options: (a) External dimension table from CRM/sales systems, (b) Manual classification file, (c) Derived business rules based on account attributes. Assign to Data Governance + BDP team.
   - **GAP-003 (IS_LICENSED):** Integrate licensing/subscription status. Source: Billing system API or subscription management database. Requires cross-team coordination with Billing Systems team. Assign to BDP + Billing integration lead.
   - **GAP-004 (USERS_ACTIVE_16PLUS_DAYS):** Cannot be derived until historical data accumulated. Requires minimum 28 days of FTL data. Implement historical storage strategy first (see item 2.1).

1.2. **Investigate JIRA CORTEX-2 Column Discrepancies (GAP-001 + UNIQUE_ACTIVE_PARTICIPANTS)**  
   - JIRA states PHONE_DIALIN_COUNT is missing in FTL and UNIQUE_ACTIVE_PARTICIPANTS is new in FTL, but neither column appears in the profiled table.
   - Action: Verify profiled table (ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG) is production version, not dev/test. Contact Zoom FTL team to confirm column presence in production schema.
   - If columns exist in production but missing in profiled environment, re-run profiling against production. If columns truly missing, update JIRA ticket status and adjust mapping accordingly.

1.3. **Implement Historical Data Accumulation Strategy**  
   - FTL source is daily snapshot data. Silver/Gold layers require rolling windows (7-day, 28-day).
   - Action: Design and implement daily incremental load process to accumulate FTL history. Target: Minimum 28 days retained, ideally 90+ days for trending.
   - Blocks: SLV_ROLL_29_DAY_USAGE (GAP-010), SLV_USER_ACTIVE_DAYS (GAP-011), GLD_AGGREGATE USERS_ACTIVE_16PLUS_DAYS (GAP-004).

**2. SILVER DBT MODEL CHANGES (Transformation implementation)**

2.1. **Implement Core Transformation Rules (High Priority - BR-001 to BR-010)**  
   - **BR-001:** Date parsing from TEXT to DATE - validate format consistency across all FTL records. Test with NULL handling and invalid formats.
   - **BR-002, BR-003, BR-004:** Unit conversions (milliseconds to minutes/hours/seconds) - create reusable macro for consistency.
   - **BR-005, BR-006:** Case normalization for DIRECTION and CHANNEL - implement UPPER() transformations.
   - **BR-007, BR-008, BR-011, BR-012:** Direct matches - verify alignment in production data (distinct value checks).
   - **BR-009:** AGENT_ID to USER_ID rename - validate semantic equivalence with business stakeholders.
   - **BR-010:** IS_ACTIVE to IS_ACTIVE_ACCOUNT mapping - confirm interpretation with Zoom team.

2.2. **Implement Aggregation Logic (Medium Priority - BR-013 to BR-016)**  
   - **BR-013, BR-014:** First active date calculations - implement window functions (MIN OVER PARTITION BY).
   - **BR-015, BR-016:** Active users/accounts aggregation - implement COUNT DISTINCT with IS_ACTIVE filter.
   - Create intermediate models (INT_FTL_ACCOUNT_FIRST_ACTIVE, INT_FTL_USER_FIRST_ACTIVE) for reusability.

2.3. **Implement Window and Region Logic (Medium Priority - BR-017, BR-021)**  
   - **BR-017:** CLUSTER to REGION mapping - create seed/reference table STG_FTL_REGION_MAPPING with AWS region to business region mappings. Validate mapping rules with business (NAMER, EMEA, APAC, LATAM alignment).
   - **BR-021:** Window generation (R1/R7/R28) - define business rules for rolling window date range calculation. Implement in intermediate model for reuse across metrics tables.

2.4. **Implement GAP Placeholder Logic (Low Priority - BR-018 to BR-036)**  
   - Create standardized approach for NULL placeholders with GAP ID comments in SQL (e.g., `NULL AS COLUMN_NAME -- GAP-XXX: Reason`).
   - Document GAP columns in dbt model YAML configs with resolution tracking.
   - **BR-019, BR-020:** Static value assignments (PRODUCT_NAME, SOURCE_TABLE).
   - **BR-022, BR-023:** Conditional aggregations that currently return 0 (CHAT_USAGE, VIDEO_USAGE) - implement filtering logic but accept 0 values until FTL enhanced.
   - **BR-024 to BR-036:** NULL placeholders for all GAP columns - implement with clear documentation.

**3. UNIT CONVERSIONS AND RENAMES TO APPLY (Reference BR IDs)**

- **Date Conversions:** BR-001 (TEXT to DATE)
- **Duration Conversions:** BR-002 (MS to minutes), BR-003 (MS to hours), BR-004 (MS to seconds)
- **Case Normalization:** BR-005 (DIRECTION), BR-006 (CHANNEL)
- **Column Renames:** BR-009 (AGENT_ID → USER_ID)
- **Semantic Mapping:** BR-010 (IS_ACTIVE → IS_ACTIVE_ACCOUNT), BR-017 (CLUSTER → REGION)

**4. ITEMS TO RAISE WITH BDP TEAM**

4.1. **Historical Data Retention Requirements**  
   - Confirm retention policy for FTL Bronze data (recommend 90+ days for trending).
   - Define incremental load strategy for daily FTL ingestion.

4.2. **External Dimension Integration**  
   - **GAP-002:** Customer segment dimension - identify data source and integration approach.
   - **GAP-003:** Licensing status - coordinate with Billing Systems team for data access.

4.3. **Cohort Business Rules Definition**  
   - **GAP-011:** Define activity cohort classification rules (what qualifies as "1-day active", "4-7 days active", "16+ days active").
   - Align definitions with existing PI business logic if available.

4.4. **Window Logic Validation**  
   - **GAP-012:** Validate R1/R7/R28 window definitions (rolling vs fixed windows, date range inclusive/exclusive boundaries).

4.5. **SLA Calculation Requirements**  
   - **GAP-008:** Define SLA target thresholds and calculation methodology if not already documented.

4.6. **Multi-Channel Usage Tracking Gap**  
   - Acknowledge limitation: Initial Silver layer will only have accurate phone metrics. Chat/video usage will be NULL/0.
   - Define acceptance criteria: Can Silver tables launch with incomplete channel coverage, or is multi-channel a requirement for go-live?

**5. ITEMS TO CONFIRM WITH ZOOM TEAM**

5.1. **JIRA CORTEX-2 Column Discrepancy Investigation (GAP-001 + UNIQUE_ACTIVE_PARTICIPANTS)**  
   - Confirm PHONE_DIALIN_COUNT and UNIQUE_ACTIVE_PARTICIPANTS column presence in production FTL table.
   - If present, provide column definitions, data types, and sample values for mapping.

5.2. **FTL Source Enhancement Roadmap**  
   - **GAP-005:** When will chat duration/session data be added to FTL?
   - **GAP-006:** When will video duration data be added to FTL?
   - **GAP-007:** When will engagement status (Missed, Resolved, Answered) be added?
   - Request feature roadmap to align Silver layer enhancements with FTL source improvements.

5.3. **Data Quality Validation**  
   - **OS Column:** Currently shows only 'Sample Text' in profile - is this test data or production issue?
   - **DATA_DATE Format:** Confirm date format is consistently 'M/D/YY HH24:MI' across all records (BR-001 dependency).
   - **IS_ACTIVE Semantic:** Confirm whether IS_ACTIVE indicates account-level or user-level activity.

5.4. **AGENT_ID vs USER_ID Semantic Equivalence (BR-009)**  
   - Confirm that AGENT_ID in FTL represents the same entity as USER_ID in PI tables.
   - Clarify if there's a distinction between "agent" (customer service representative) and "user" (general platform user).

5.5. **ZCC_ACCOUNT_ID vs ACCOUNT_ID Relationship**  
   - Clarify if ZCC_ACCOUNT_ID is a separate dimension or duplicate of ACCOUNT_ID.
   - Provide guidance on when to use each identifier.

**6. NEW CAPABILITIES — DECISION NEEDED FROM PI TEAM LEADS**

6.1. **CLIENT_TYPE Enrichment (Recommended: YES)**  
   - Proposal: Add CLIENT_TYPE to SLV_USAGE_MASTER and SLV_COMBINED_CHANNELS for device-based analytics.
   - Business value: Enables mobile vs desktop vs web usage segmentation, informs UX/product decisions.
   - Decision needed: Approve addition to Silver schema.

6.2. **CLUSTER Infrastructure Tracking (Recommended: YES for Silver, already mapped in Gold)**  
   - Proposal: Keep raw CLUSTER value in Silver tables for infrastructure troubleshooting and detailed region analysis.
   - Already mapped to REGION in Gold via BR-017.
   - Decision needed: Confirm CLUSTER retention in Silver is acceptable (adds column but valuable for ops).

6.3. **ZCC_ACCOUNT_ID Usage (Decision Required)**  
   - Proposal: Clarify purpose and relationship to ACCOUNT_ID.
   - Options: (a) Add to Silver for ZCC-specific lineage, (b) Exclude if duplicate, (c) Use for cross-referencing.
   - Decision needed: Confirm whether to include in Silver schema.

6.4. **OS Column (Decision Deferred - Data Quality Issue)**  
   - Current state: Only 'Sample Text' value in profile suggests test data.
   - Action: Defer decision until data quality validated in production.
   - If production has real OS values (Windows, Mac, Linux, etc.), revisit decision to add to Silver.

6.5. **UNIQUE_ACTIVE_PARTICIPANTS (Investigation Required)**  
   - Status: JIRA mentions column but not present in profiled table.
   - Action: Pending Zoom team confirmation (see item 5.1).
   - If column exists: Recommend adding to SLV_COMBINED_CHANNELS for participant-level engagement metrics.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**SECTION 8: FULL COLUMN LINEAGE MAPPING TABLE**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | No matching column found in PI Silver or Gold schema - appears to be ZCC-specific account identifier distinct from standard ACCOUNT_ID | — | — | Not mapped (new capability) | Add to Silver if ZCC-specific tracking needed; clarify relationship to ACCOUNT_ID |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_ACCT_FIRST_ACTIVE, SLV_COMBINED_CHANNELS, SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_ACTIVE_DAYS, SLV_USER_FIRST_ACTIVE, SLV_WEEKLY_METRICS | — | — | DIRECT_MATCH | High | Column name and semantic meaning identical across source and all Silver tables; confirmed via distinct value queries | BR-007 | — | Direct pass-through | Foundational join key - no transformation |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Column name and semantic meaning identical; engagement-level granularity matches | BR-008 | — | Direct pass-through | Unique engagement identifier |
| AGENT_ID | TEXT | USER_ID | SLV_COMBINED_CHANNELS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE | — | — | RENAME | Medium | FTL uses AGENT_ID while PI uses USER_ID - assumed semantic equivalence but requires business validation | BR-009 | — | `AGENT_ID AS USER_ID` | ASSUMPTION: Agent = User in this context - validate with Zoom team |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | High | Distinct value query confirms FTL has 'Inbound'/'Outbound' vs PI 'INBOUND'/'OUTBOUND' - only case differs | BR-005 | — | `UPPER(DIRECTION)` | Case normalization required |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Values align (Chat, Email, SMS) - confirmed via distinct value comparison | BR-012 | — | Direct pass-through | Multi-channel indicator |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | High | Distinct value query confirms FTL has 'Phone'/'Video' vs PI 'PHONE'/'VIDEO' - only case differs | BR-006 | — | `UPPER(CHANNEL)` | Case normalization required |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column name and data type identical; semantic meaning matches (count of phone sessions) | BR-011 | — | Direct pass-through | Phone session count metric |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | — | — | UNIT_CHANGE | High | Milliseconds to minutes conversion - standard unit transformation | BR-002 | — | `INBOUND_PHONE_MS / 60000.0` | Unit conversion: 1 min = 60,000 ms |
| INBOUND_PHONE_MS | NUMBER | DURATION_SEC | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | High | Milliseconds to seconds conversion for duration metric | BR-004 | — | `INBOUND_PHONE_MS / 1000.0` | Unit conversion: 1 sec = 1,000 ms |
| INBOUND_PHONE_MS | NUMBER | PHONE_USAGE | SLV_CONSOLIDATED_USAGE, SLV_ROLL_29_DAY_USAGE (WEEKLY_PHONE_USAGE) | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE | Medium | Milliseconds to hours conversion with aggregation; ASSUMPTION: Gold measures usage in hours | BR-003 | — | `SUM(INBOUND_PHONE_MS) / 3600000.0` | Unit + aggregation; only inbound calls counted |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | No matching column in PI schema - provides device type segmentation (Desktop, Mobile, Web) | — | — | Not mapped (new capability) | Recommend adding to Silver for client-type analytics |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | No matching column in PI schema - provides OS-level segmentation; DATA QUALITY ISSUE: profile shows only 'Sample Text' | — | — | Not mapped (new capability) | Validate data quality in production before adding to Silver |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | — | — | SEMANTIC_MATCH | Medium | FTL row-level IS_ACTIVE assumed to indicate account-level activity; LOW CONFIDENCE - interpretation unclear | BR-010 | — | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | ASSUMPTION: Confirm if IS_ACTIVE means account or user activity |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | DERIVED | Low | AWS cluster (us-east-1, eu-central-1, ap-south-1) mapped to business regions (NAMER, EMEA, APAC); ASSUMPTION: Mapping logic requires validation | BR-017 | — | `CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'OTHER' END` | Requires CLUSTER_REGION_MAP reference table validation |
| DATA_DATE | TEXT | REPORT_DATE | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USER_ACTIVE_DAYS, SLV_WEEKLY_METRICS | DATE | GLD_AGGREGATE | TYPE_CHANGE | Medium | Text date format (M/D/YY HH:MI) requires parsing to DATE type; ASSUMPTION: Format consistent across all records | BR-001 | — | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | Format assumption based on sample '5/29/26 13:01' - test with production data |
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER | DATE | GLD_AGGREGATE | TYPE_CHANGE | Medium | Same date parsing transformation as REPORT_DATE | BR-001 | — | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | Same transformation as above |
| DATA_DATE | TEXT | START_DATE | SLV_COMBINED_CHANNELS | — | — | TYPE_CHANGE | Medium | Same date parsing transformation for engagement start date | BR-001 | — | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | Same transformation as above |
| DATA_DATE | TEXT | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE, SLV_USAGE_MASTER | — | — | AGGREGATION | Medium | Minimum date per account represents first active date; ASSUMPTION: First FTL record = first active (no historical backfill) | BR-013 | — | `MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY ACCOUNT_ID)` | Window function for first active calculation |
| DATA_DATE | TEXT | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE, SLV_USAGE_MASTER | — | — | AGGREGATION | Medium | Minimum date per user (agent) represents first active date; same assumption as account first active | BR-014 | — | `MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY AGENT_ID)` | Window function for first active calculation |
| AGENT_ID | TEXT | ACTIVE_USERS | Multiple metrics tables | ACTIVE_USERS | GLD_AGGREGATE | AGGREGATION | Medium | Count distinct active agents as proxy for active users; filtered by IS_ACTIVE flag | BR-015 | — | `COUNT(DISTINCT CASE WHEN IS_ACTIVE THEN AGENT_ID END)` | Aggregation with IS_ACTIVE filter |
| ACCOUNT_ID | TEXT | ACTIVE_ACCOUNTS | — | ACTIVE_ACCOUNTS | GLD_AGGREGATE | AGGREGATION | Medium | Count distinct active accounts; filtered by IS_ACTIVE flag | BR-016 | — | `COUNT(DISTINCT CASE WHEN IS_ACTIVE THEN ACCOUNT_ID END)` | Aggregation with IS_ACTIVE filter |
| — | — | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE, SLV_USER_FIRST_ACTIVE | — | — | SYSTEM_GENERATED | High | ETL metadata timestamp - generated at runtime, not sourced from FTL | BR-018 | — | `CURRENT_TIMESTAMP()` | Standard ETL metadata practice |
| — | — | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | — | — | STATIC_VALUE | High | No product dimension in FTL - hardcoded to 'ZCC Platform' | BR-019 | GAP-013 | `'ZCC Platform' AS PRODUCT_NAME` | GAP-013: Static value since FTL is ZCC-specific |
| — | — | SOURCE_TABLE | SLV_COMBINED_CHANNELS | — | — | STATIC_VALUE | High | Lineage metadata - hardcoded to source table name | BR-020 | GAP-014 | `'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE` | GAP-014: Metadata field for tracking data origin |
| — | — | WINDOW | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | — | — | DERIVED | Low | Rolling window indicator (R1/R7/R28) requires business rule definition for date range logic | BR-021 | GAP-012 | `CASE WHEN date_diff = 1 THEN 'R1' WHEN date_diff <= 7 THEN 'R7' WHEN date_diff <= 28 THEN 'R28' END` | GAP-012: Window logic requires validation with business |
| MODALITY | TEXT | CHAT_USAGE | SLV_DAILY_METRICS, SLV_ROLL_29_DAY_USAGE (DAILY_CHAT_USAGE), SLV_WEEKLY_METRICS | — | — | CONDITIONAL_AGGREGATION | Low | Can filter MODALITY='Chat' but no duration data available - will return 0 | BR-022 | GAP-005 | `SUM(CASE WHEN MODALITY = 'Chat' THEN 0 ELSE 0 END)` | GAP-005: Chat duration not in FTL - placeholder logic |
| MODALITY | TEXT | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | CONDITIONAL_COUNT | Low | Can count chat engagements but session concept unclear in FTL granularity | BR-030 | GAP-005 | `SUM(CASE WHEN MODALITY = 'Chat' THEN 1 ELSE 0 END)` | GAP-005: Session definition may not align with FTL grain |
| CHANNEL | TEXT | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | CONDITIONAL_AGGREGATION | Low | Can filter CHANNEL='Video' but no duration data available - will return 0 | BR-023 | GAP-006 | `SUM(CASE WHEN CHANNEL = 'Video' THEN 0 ELSE 0 END)` | GAP-006: Video duration not in FTL - placeholder logic |
| — | — | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | — | — | GAP | High | No status field (Missed, Resolved, Answered) in FTL source | BR-024 | GAP-007 | `NULL AS ENGAGEMENT_STATUS` | GAP-007: Requires FTL enhancement or external data |
| — | — | SLA_ACHIEVED | SLV_COMBINED_CHANNELS | — | — | GAP | High | No SLA compliance tracking in FTL | BR-025 | GAP-008 | `NULL AS SLA_ACHIEVED` | GAP-008: Requires SLA target data and calculation logic |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No SLA session count available in FTL | BR-026 | GAP-008 | `NULL AS SLA_ACHIEVED_SESSIONS` | GAP-008: Same gap as SLA_ACHIEVED |
| — | — | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No payment/subscription status in FTL | BR-027 | GAP-009 | `NULL AS IS_PAID_USER` | GAP-009: Requires billing system data join |
| — | — | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Rolling 7-day window requires 7+ days of historical FTL data | BR-028 | GAP-010 | `NULL AS ACTIVE_DAYS_LAST_7` | GAP-010: Historical data accumulation required |
| — | — | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Rolling 28-day window requires 28+ days of historical FTL data | BR-029 | GAP-010 | `NULL AS ACTIVE_DAYS_LAST_28` | GAP-010: Historical data accumulation required |
| — | — | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | — | — | GAP | High | Activity cohort requires historical tracking and cohort classification logic | BR-031 | GAP-011 | `NULL AS USERS_ACTIVE_1_DAY` | GAP-011: Cohort business rules not yet implemented |
| — | — | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | — | — | GAP | High | Activity cohort requires historical tracking and cohort classification logic | BR-032 | GAP-011 | `NULL AS USERS_ACTIVE_4_7_DAYS` | GAP-011: Cohort business rules not yet implemented |
| — | — | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Rolling window + activity cohort - requires historical data and cohort logic | — | GAP-011 | `NULL AS ACTIVE_1_DAY_L7` | GAP-011: Historical + cohort logic required |
| — | — | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Rolling window + activity cohort - requires historical data and cohort logic | — | GAP-011 | `NULL AS ACTIVE_4_7_DAYS_L7` | GAP-011: Historical + cohort logic required |
| — | — | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Rolling window + activity cohort - requires historical data and cohort logic | — | GAP-011 | `NULL AS ACTIVE_1_DAY_L28` | GAP-011: Historical + cohort logic required |
| — | — | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Rolling window + activity cohort - requires historical data and cohort logic | — | GAP-011 | `NULL AS ACTIVE_16PLUS_DAYS_L28` | GAP-011: Historical + cohort logic required |
| — | — | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | 16+ day activity cohort requires 28+ days historical data and cohort logic - BLOCKS GOLD MIGRATION | BR-033 | GAP-004, GAP-011 | `NULL AS USERS_ACTIVE_16PLUS_DAYS` | GAP-004: Critical Gold metric - migration blocked |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No customer segment classification data in FTL - BLOCKS GOLD MIGRATION | BR-034 | GAP-002 | `NULL AS SEGMENT` | GAP-002: Requires external dimension table or manual classification |
| — | — | — | — | IS_LICENSED | GLD_AGGREGATE | GAP | High | No licensing/subscription status in FTL - BLOCKS GOLD MIGRATION | BR-035 | GAP-003 | `NULL AS IS_LICENSED` | GAP-003: Requires external billing data or subscription system integration |
| — | — | PHONE_DIALIN_COUNT | (mentioned in JIRA) | — | — | GAP | N/A | JIRA CORTEX-2 flags this column as missing in FTL, but column not found in PI Silver/Gold schema either - requires investigation | BR-036 | GAP-001 | `