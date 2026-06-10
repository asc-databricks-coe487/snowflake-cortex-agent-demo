

🔍 **STEP 1: Schema Discovery** — Discovered 1 Bronze source, 20 Silver tables, 1 Gold table

🔍 **STEP 2: Data Profiling** — Profiled BRZ_FTL_AGENT_BASE_AGG (14 columns, 5 rows) + all Silver/Gold targets

🔍 **STEP 3: Silver Layer Mapping Analysis** — Analyzed 10 unique Silver table structures for column-level mapping

🔍 **STEP 4: Gold Layer Mapping Analysis** — Analyzed GLD_AGGREGATE (8 columns) against FTL source

🔍 **STEP 5: Gap Identification & ID Assignment** — Assigning sequential GAP-001 through GAP-016 and BR-001 through BR-012

---

# 🎯 COMPREHENSIVE MIGRATION MAPPING REPORT
## FTL Bronze → PI Silver/Gold Migration Analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1: EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG

**Target PI Silver Tables:** 
- ZOOM_AI_POC.SILVER.SLV_ACCT_FIRST_ACTIVE
- ZOOM_AI_POC.SILVER.SLV_COMBINED_CHANNELS
- ZOOM_AI_POC.SILVER.SLV_CONSOLIDATED_USAGE
- ZOOM_AI_POC.SILVER.SLV_DAILY_METRICS
- ZOOM_AI_POC.SILVER.SLV_MONTHLY_METRICS
- ZOOM_AI_POC.SILVER.SLV_ROLL_29_DAY_USAGE
- ZOOM_AI_POC.SILVER.SLV_USAGE_MASTER
- ZOOM_AI_POC.SILVER.SLV_USER_ACTIVE_DAYS
- ZOOM_AI_POC.SILVER.SLV_USER_FIRST_ACTIVE
- ZOOM_AI_POC.SILVER.SLV_WEEKLY_METRICS

**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE

**Migration Readiness Score:** 42/100

**Total FTL columns analyzed:** 14
- **Successfully mapped:** 8 (ACCOUNT_ID, ENGAGEMENT_ID, AGENT_ID, DIRECTION, MODALITY, CHANNEL, PHONE_SESSIONS, INBOUND_PHONE_MS)
- **Partially mapped:** 3 (DATA_DATE, IS_ACTIVE, CLUSTER)
- **New capabilities (no PI equivalent):** 3 (ZCC_ACCOUNT_ID, CLIENT_TYPE, OS)
- **Gaps (PI columns with no FTL source):** 16 total

**Critical Gaps:**
→ GAP-001: SEGMENT (Gold) - No customer segmentation data
→ GAP-002: IS_LICENSED (Gold) - No licensing status information
→ GAP-003: USERS_ACTIVE_16PLUS_DAYS (Gold & Silver) - No temporal activity tracking
→ GAP-004: All CHAT metrics - No chat session or usage data
→ GAP-005: SLA_ACHIEVED - No SLA achievement tracking
→ GAP-006: Historical first active dates - Requires lookup tables

**Blocking items:** 3 (GAP-001, GAP-002, GAP-003)

**Overall Assessment:** The FTL Bronze source provides basic engagement and phone usage data but lacks critical business dimensions required for Gold layer reporting (segmentation, licensing, user engagement metrics). Silver layer tables can be partially populated with significant caveats and NULL values for missing metrics. Gold layer migration is **NOT FEASIBLE** without additional data sources or requirement modifications. Two Silver tables (SLV_ROLL_29_DAY_USAGE, SLV_USER_ACTIVE_DAYS) cannot be meaningfully populated due to missing historical activity tracking data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2: GAP IMPACT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Column | Why It's a Gap | Impact on Output | Blocks Migration? | Action Required | Raise With |
|--------|-----------|----------------|------------------|-------------------|-----------------|------------|
| GAP-001 | SEGMENT (Gold) | No customer/account segmentation dimension in FTL source | Cannot segment reporting by customer tier/size - breaks existing dashboards | **YES** | Source additional segmentation data from account master or CRM | BDP Team & Zoom Team |
| GAP-002 | IS_LICENSED (Gold) | No licensing status flag in FTL source | Cannot differentiate licensed vs trial accounts - impacts revenue reporting | **YES** | Source licensing data from subscription/billing system | BDP Team |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS (Gold & Silver) | No historical user activity tracking in FTL source | Cannot calculate power user engagement metrics - core KPI missing | **YES** | Requires historical activity data or daily incremental builds | BDP Team |
| GAP-004 | CHAT_USAGE (Multiple Silver tables) | FTL source only contains phone/video - no chat data | Chat channel metrics will be NULL - incomplete omnichannel view | NO | Confirm chat data is in separate source or accept limitation | Zoom Team |
| GAP-005 | CHAT_SESSIONS (SLV_USAGE_MASTER) | No chat session count in FTL source | Usage master incomplete for chat interactions | NO | Accept NULL or source from legacy Bronze views | Zoom Team |
| GAP-006 | SLA_ACHIEVED / SLA_ACHIEVED_SESSIONS | No SLA achievement tracking in FTL source | Cannot report on service level compliance | NO | Confirm if SLA data exists elsewhere or calculate separately | Zoom Team |
| GAP-007 | ENGAGEMENT_STATUS (SLV_COMBINED_CHANNELS) | No engagement outcome status in FTL source | Cannot track answered/missed/resolved status | NO | Accept NULL or derive from other engagement data | Zoom Team |
| GAP-008 | ACCOUNT_FIRST_ACTIVE (SLV_USAGE_MASTER) | No historical first active date in FTL source | Requires lookup table or historical aggregation | NO | Build separate dimension table from historical data | Data Engineering |
| GAP-009 | USER_FIRST_ACTIVE (SLV_USAGE_MASTER) | No historical first active date in FTL source | Requires lookup table or historical aggregation | NO | Build separate dimension table from historical data | Data Engineering |
| GAP-010 | IS_PAID_USER (SLV_ROLL_29_DAY_USAGE) | No payment/subscription status in FTL source | Cannot segment by paid vs free users in rolling usage | NO | Source from subscription system or accept NULL | BDP Team |
| GAP-011 | ACTIVE_DAYS_LAST_7 (SLV_ROLL_29_DAY_USAGE) | No historical activity tracking for rolling windows | Rolling usage table cannot be populated | **YES** | Requires daily incremental activity tracking | Data Engineering |
| GAP-012 | ACTIVE_DAYS_LAST_28 (SLV_ROLL_29_DAY_USAGE) | No historical activity tracking for rolling windows | Rolling usage table cannot be populated | **YES** | Requires daily incremental activity tracking | Data Engineering |
| GAP-013 | ACTIVE_1_DAY_L7 through ACTIVE_16PLUS_DAYS_L28 (SLV_USER_ACTIVE_DAYS) | No activity cohort segmentation data in FTL source | User active days table cannot be populated - all metrics missing | **YES** | Requires daily user activity tracking and cohort logic | Data Engineering |
| GAP-014 | PRODUCT_NAME (SLV_CONSOLIDATED_USAGE) | No product dimension in FTL source | Cannot segment by product line | NO | Hardcode 'ZCC Platform' or derive from account metadata | Data Engineering |
| GAP-015 | VIDEO_USAGE (SLV_MONTHLY_METRICS) | FTL only has phone usage - no video duration metrics | Video usage will be NULL in monthly metrics | NO | Confirm video data availability or accept limitation | Zoom Team |
| GAP-016 | USERS_ACTIVE_1_DAY / USERS_ACTIVE_4_7_DAYS (Multiple Silver tables) | No activity cohort counts in FTL source | User activity segmentation metrics missing | NO | Requires activity tracking logic or accept NULL | Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3: TRANSFORMATION GUIDE (Business Rules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | DATE (Gold), REPORT_DATE (Silver), START_DATE (Silver) | UNIT_CHANGE | `CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)` | Convert text timestamp to DATE type for temporal analysis | DATA_DATE format validation | [ASSUMPTION] Format is M/D/YY H:MI based on sample "5/29/26 13:01" |
| BR-002 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS (SLV_USAGE_MASTER) | UNIT_CHANGE | `INBOUND_PHONE_MS / 1000.0 / 60.0` | Convert milliseconds to minutes for business reporting | INBOUND_PHONE_MS | None |
| BR-003 | INBOUND_PHONE_MS | DURATION_SEC (SLV_COMBINED_CHANNELS) | UNIT_CHANGE | `INBOUND_PHONE_MS / 1000.0` | Convert milliseconds to seconds for engagement duration | INBOUND_PHONE_MS | [ASSUMPTION] Only inbound phone duration available - outbound not tracked |
| BR-004 | INBOUND_PHONE_MS | PHONE_USAGE (Gold & Silver aggregated tables) | UNIT_CHANGE | `SUM(INBOUND_PHONE_MS) / 1000.0 / 60.0` | Aggregate phone time in minutes grouped by date/region/account | INBOUND_PHONE_MS | [ASSUMPTION] Usage represents total minutes, not average |
| BR-005 | AGENT_ID | USER_ID (Multiple Silver tables) | RENAME | `AGENT_ID AS USER_ID` | Semantic mapping - agents are users in the system | AGENT_ID | [ASSUMPTION] Agent ID represents user identity - needs business confirmation |
| BR-006 | ACCOUNT_ID | ACCOUNT_ID (All Silver/Gold tables) | DIRECT_MATCH | `ACCOUNT_ID` | Direct pass-through | ACCOUNT_ID | None |
| BR-007 | IS_ACTIVE | IS_ACTIVE_ACCOUNT (Multiple Silver tables) | RENAME | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | Map engagement-level activity to account-level active flag | IS_ACTIVE | [ASSUMPTION] Engagement activity implies account is active |
| BR-008 | AGENT_ID | ACTIVE_USERS (Gold & Silver metrics) | GRAIN_CHANGE | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, ACCOUNT_ID` | Count distinct active agents as user count metric | AGENT_ID, IS_ACTIVE | [ASSUMPTION] Agents represent active users |
| BR-009 | ACCOUNT_ID | ACTIVE_ACCOUNTS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION` | Count distinct active accounts per date/region | ACCOUNT_ID, IS_ACTIVE, CLUSTER | [ASSUMPTION] IS_ACTIVE represents account-level activity |
| BR-010 | CLUSTER | REGION (Gold) | SEMANTIC_CHANGE | `CASE WHEN CLUSTER = 'us-east-1' THEN 'NAMER' WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' ELSE 'UNKNOWN' END` | Map AWS cluster regions to business regions | CLUSTER, CLUSTER_REGION_MAP lookup table | [LOW CONFIDENCE] [ASSUMPTION] LATAM region mapping unclear - may need additional lookup |
| BR-011 | — | WINDOW (Multiple Silver metrics tables) | GAP | `NULL AS WINDOW -- GAP ID: GAP-014` | No temporal window dimension in FTL - hardcode based on table purpose | None | [ASSUMPTION] Can hardcode 'DAILY', 'WEEKLY', 'MONTHLY' based on target table |
| BR-012 | — | REFRESH_TIMESTAMP (Multiple Silver tables) | GAP | `CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP` | No refresh timestamp in source - use system time | None | Standard metadata field |
| — | ENGAGEMENT_ID | ENGAGEMENT_ID (SLV_COMBINED_CHANNELS) | DIRECT_MATCH | `ENGAGEMENT_ID` | Direct pass-through | ENGAGEMENT_ID | None |
| — | DIRECTION | DIRECTION (SLV_COMBINED_CHANNELS) | DIRECT_MATCH | `DIRECTION` | Direct pass-through | DIRECTION | None |
| — | MODALITY | MODALITY (SLV_COMBINED_CHANNELS) | DIRECT_MATCH | `MODALITY` | Direct pass-through | MODALITY | None |
| — | CHANNEL | CHANNEL (SLV_COMBINED_CHANNELS) | DIRECT_MATCH | `CHANNEL` | Direct pass-through | CHANNEL | None |
| — | PHONE_SESSIONS | PHONE_SESSIONS (SLV_USAGE_MASTER) | DIRECT_MATCH | `PHONE_SESSIONS` | Direct pass-through | PHONE_SESSIONS | None |
| — | — | SEGMENT (Gold) | GAP | `NULL AS SEGMENT -- GAP ID: GAP-001` | No customer segmentation dimension in FTL source - requires external data source (account master or CRM) | Account master table or CRM integration | **CRITICAL** Blocks Gold migration |
| — | — | IS_LICENSED (Gold) | GAP | `NULL AS IS_LICENSED -- GAP ID: GAP-002` | No licensing status in FTL source - requires subscription/billing system data | Subscription/billing system | **CRITICAL** Blocks Gold migration |
| — | — | USERS_ACTIVE_16PLUS_DAYS (Gold & Silver) | GAP | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-003` | No historical activity tracking in FTL - requires daily user activity aggregation over 28-day windows | Daily user activity tracking table | **CRITICAL** Blocks Gold migration |
| — | — | CHAT_USAGE (Multiple Silver tables) | GAP | `NULL AS CHAT_USAGE -- GAP ID: GAP-004` | FTL source only contains phone/video - chat data not available | Chat history data source | Non-blocking but incomplete metric |
| — | — | CHAT_SESSIONS (SLV_USAGE_MASTER) | GAP | `NULL AS CHAT_SESSIONS -- GAP ID: GAP-005` | No chat session count in FTL source | Chat history data source | Non-blocking but incomplete metric |
| — | — | SLA_ACHIEVED (SLV_COMBINED_CHANNELS) | GAP | `NULL AS SLA_ACHIEVED -- GAP ID: GAP-006` | No SLA achievement tracking in FTL source | Engagement SLA calculation logic or separate data source | Non-blocking but compliance reporting impacted |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4: NEW FTL CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|-------------------|-------------------|-----------------|
| ZCC_ACCOUNT_ID | TEXT | Zoom Contact Center account identifier (distinct from ACCOUNT_ID) | Account reconciliation / dual ID tracking | PENDING DECISION | Add to Silver now - clarify relationship with ACCOUNT_ID before Gold extension |
| CLIENT_TYPE | TEXT | Client application type (Mobile, Web, Desktop) | Device/platform segmentation and adoption analysis | YES | Add to Silver now, propose Gold extension for device adoption metrics |
| OS | TEXT | Operating system information | Platform compatibility and usage analytics | NO | Keep in Silver only - too granular for Gold aggregation unless platform strategy KPI needed |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5: FEASIBILITY VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Silver Layer Feasibility

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| SLV_ACCT_FIRST_ACTIVE | 40% | GAP-008 (Historical first active date) | Feasible with Caveats | Build from historical aggregation or accept MIN(DATA_DATE) approximation |
| SLV_COMBINED_CHANNELS | 65% | GAP-005, GAP-007 (SLA, engagement status) | Feasible with Caveats | Accept NULL for SLA/status or source from legacy Bronze views |
| SLV_CONSOLIDATED_USAGE | 55% | GAP-004, GAP-014 (Chat metrics, product name) | Feasible with Caveats | Accept NULL for chat usage, hardcode product name |
| SLV_DAILY_METRICS | 45% | GAP-004, GAP-016 (Chat usage, activity cohorts) | Feasible with Caveats | Accept NULL for chat and user activity day counts |
| SLV_MONTHLY_METRICS | 45% | GAP-003, GAP-015 (16+ day users, video usage) | Feasible with Caveats | Accept NULL for video and engagement metrics |
| SLV_ROLL_29_DAY_USAGE | 25% | GAP-010, GAP-011, GAP-012 (All rolling window metrics) | **Not Feasible** | Requires daily incremental activity tracking - cannot populate from single-date snapshot |
| SLV_USAGE_MASTER | 60% | GAP-005, GAP-006, GAP-008, GAP-009 (Chat, SLA, first active dates) | Feasible with Caveats | Accept NULL for chat/SLA, build first active date lookup tables |
| SLV_USER_ACTIVE_DAYS | 20% | GAP-013 (All activity cohort metrics) | **Not Feasible** | Entire table purpose is activity day tracking - no source data available |
| SLV_USER_FIRST_ACTIVE | 50% | GAP-009 (Historical first active date) | Feasible with Caveats | Build from historical aggregation or accept MIN(DATA_DATE) approximation |
| SLV_WEEKLY_METRICS | 45% | GAP-004, GAP-016 (Chat usage, activity cohorts) | Feasible with Caveats | Accept NULL for chat and user activity day counts |

### Gold Layer Feasibility

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| GLD_AGGREGATE | 35% | GAP-001, GAP-002, GAP-003 | **Not Feasible** | **BLOCKING:** Must source SEGMENT from account master/CRM, IS_LICENSED from subscription system, USERS_ACTIVE_16PLUS_DAYS requires daily activity tracking infrastructure. Gold migration cannot proceed without these three critical dimensions. |

**Overall Migration Verdict:** **Feasible with Major Caveats for Silver, Not Feasible for Gold**

**Conditions to Proceed:**
1. **RESOLVE GAP-001:** Source customer segmentation data (SEGMENT) from account master or CRM system
2. **RESOLVE GAP-002:** Source licensing status (IS_LICENSED) from subscription/billing system
3. **RESOLVE GAP-003:** Build daily user activity tracking infrastructure for engagement metrics
4. **ACCEPT LIMITATIONS:** Silver tables will have NULL values for chat metrics, SLA data, and some user cohort fields
5. **CONFIRM WITH BDP:** Validate that partial Silver tables meet minimum reporting requirements
6. **ABANDON OR REDESIGN:** Tables SLV_ROLL_29_DAY_USAGE and SLV_USER_ACTIVE_DAYS cannot be populated - confirm if they can be deprecated or require alternate data sources

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 6: DBT MODEL IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 6.1 — NEW TABLES TO CREATE

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| ZOOM_AI_POC.SILVER.DIM_ACCOUNT_FIRST_ACTIVE | SILVER | Historical account first activity lookup dimension | BRZ_FTL_AGENT_BASE_AGG (historical aggregation) |
| ZOOM_AI_POC.SILVER.DIM_USER_FIRST_ACTIVE | SILVER | Historical user first activity lookup dimension | BRZ_FTL_AGENT_BASE_AGG (historical aggregation) |
| ZOOM_AI_POC.SILVER.MAP_CLUSTER_REGION | SILVER | AWS cluster to business region mapping reference | Manual mapping configuration or external source |
| ZOOM_AI_POC.SILVER.DIM_ACCOUNT_SEGMENT | SILVER | Account segmentation dimension | Account master or CRM integration |
| ZOOM_AI_POC.SILVER.DIM_ACCOUNT_LICENSE | SILVER | Account licensing status dimension | Subscription/billing system |

### 6.2 — EXISTING TABLES TO ALTER

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|-----------------|----------------|------------------|--------|
| SLV_COMBINED_CHANNELS | SILVER | Add new FTL capabilities | CLIENT_TYPE (TEXT), OS (TEXT) | DURATION_SEC: accept NULL when not phone channel | MINOR - Extends existing schema with optional fields |
| SLV_USAGE_MASTER | SILVER | Mark missing metrics as nullable | None | CHAT_SESSIONS, SLA_ACHIEVED_SESSIONS: must accept NULL | MEDIUM - Changes NOT NULL constraints if present |
| SLV_CONSOLIDATED_USAGE | SILVER | Handle missing product dimension | None | PRODUCT_NAME: hardcode 'ZCC Platform' or accept NULL | MINOR - Default value strategy |
| SLV_DAILY_METRICS | SILVER | Accept missing chat/cohort metrics | None | CHAT_USAGE, USERS_ACTIVE_1_DAY: must accept NULL | MEDIUM - Incomplete metric set |
| SLV_MONTHLY_METRICS | SILVER | Accept missing video/cohort metrics | None | VIDEO_USAGE, USERS_ACTIVE_16PLUS_DAYS: must accept NULL | MEDIUM - Core engagement metric missing |
| SLV_WEEKLY_METRICS | SILVER | Accept missing chat/cohort metrics | None | CHAT_USAGE, USERS_ACTIVE_4_7_DAYS: must accept NULL | MEDIUM - Incomplete metric set |
| GLD_AGGREGATE | GOLD | **CANNOT MIGRATE** - Missing critical dimensions | None | SEGMENT, IS_LICENSED, USERS_ACTIVE_16PLUS_DAYS: all NULL | **CRITICAL** - Table becomes non-functional for existing use cases |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 7: RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Priority 1: Blocking Items (MUST RESOLVE before migration)

1. **Resolve GAP-001 (SEGMENT):** Source customer segmentation dimension from account master or CRM system. This is a core business dimension required for Gold layer reporting.

2. **Resolve GAP-002 (IS_LICENSED):** Integrate licensing status from subscription/billing system. Critical for differentiating licensed vs trial accounts in revenue reporting.

3. **Resolve GAP-003 (USERS_ACTIVE_16PLUS_DAYS):** Build daily user activity tracking infrastructure to calculate power user engagement metrics over rolling 28-day windows. This requires architectural decision on incremental activity aggregation.

4. **Validate DATA_DATE format:** Confirm the date format is consistently 'M/D/YY H:MI' across all data. Incorrect parsing will break all temporal joins and aggregations (impacts BR-001).

5. **Clarify ACCOUNT_ID vs ZCC_ACCOUNT_ID:** Determine authoritative account identifier for business logic. Source has both - business must confirm which represents customer accounts for reporting.

### Priority 2: Silver DBT Model Changes Needed

6. **Implement BR-001 through BR-004:** Create date parsing and unit conversion macros in DBT for reusability across all Silver models.

7. **Implement BR-010 (Region Mapping):** Build CLUSTER → REGION mapping logic. Create MAP_CLUSTER_REGION reference table with all AWS regions mapped to business regions (NAMER, EMEA, APAC, LATAM).

8. **Create dimension lookup tables:** Build DIM_ACCOUNT_FIRST_ACTIVE and DIM_USER_FIRST_ACTIVE from historical BRZ_FTL_AGENT_BASE_AGG data using MIN(DATA_DATE) aggregation (addresses GAP-008, GAP-009).

9. **Add CLIENT_TYPE and OS columns:** Extend SLV_COMBINED_CHANNELS with new FTL capabilities for device analytics.

10. **Modify NOT NULL constraints:** Update schema definitions for SLV_USAGE_MASTER, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS to accept NULL for missing metrics (CHAT_USAGE, VIDEO_USAGE, activity cohorts).

### Priority 3: Unit Conversions and Renames to Apply

11. **Apply BR-002:** Convert INBOUND_PHONE_MS to minutes (`/ 1000.0 / 60.0`) for SLV_USAGE_MASTER and aggregated usage tables.

12. **Apply BR-003:** Convert INBOUND_PHONE_MS to seconds (`/ 1000.0`) for SLV_COMBINED_CHANNELS duration field.

13. **Apply BR-005:** Rename AGENT_ID → USER_ID with semantic validation that agents represent users.

14. **Apply BR-007:** Map IS_ACTIVE → IS_ACTIVE_ACCOUNT with logic confirmation.

### Priority 4: Items to Raise with BDP Team

15. **GAP-001 (SEGMENT):** Request customer segmentation data source integration.

16. **GAP-002 (IS_LICENSED):** Request licensing status data source integration.

17. **GAP-003 (USERS_ACTIVE_16PLUS_DAYS):** Discuss architecture for daily user activity tracking - requires incremental build strategy.

18. **GAP-010 (IS_PAID_USER):** Confirm if payment status dimension is available in subscription system.

19. **SLV_ROLL_29_DAY_USAGE feasibility:** Confirm whether this table can be deprecated or if alternate historical data source exists.

20. **SLV_USER_ACTIVE_DAYS feasibility:** Confirm whether this table can be deprecated or if alternate activity tracking source exists.

### Priority 5: Items to Confirm with Zoom Team

21. **GAP-004, GAP-005 (Chat data):** Confirm if chat metrics exist in separate FTL source or if chat has been consolidated into MODALITY='Chat' in current source.

22. **GAP-006 (SLA data):** Confirm if SLA achievement metrics exist in separate engagement outcome tracking system or if SLA can be calculated from duration/response time fields.

23. **GAP-007 (Engagement status):** Confirm if engagement outcome status (Answered/Missed/Resolved) is tracked in separate system or derivable from engagement metadata.

24. **GAP-015 (Video usage):** Confirm if video duration metrics exist separately or if consolidated under CHANNEL='Video' in current source.

25. **DIRECTION coverage:** Validate that FTL source captures both Inbound and Outbound phone sessions - current sample shows both but INBOUND_PHONE_MS suggests only inbound duration is tracked.

### Priority 6: New Capabilities — Decision Needed from PI Team Leads

26. **CLIENT_TYPE dimension:** Decide whether to add device/platform segmentation to Silver layer for adoption analytics. Recommend YES - adds value for understanding mobile vs web vs desktop usage patterns.

27. **OS dimension:** Decide whether to track operating system granularity. Recommend keep in Silver only unless platform compatibility is a strategic KPI.

28. **ZCC_ACCOUNT_ID:** Clarify business purpose and relationship to ACCOUNT_ID. Recommend add to Silver for reconciliation but needs business definition before Gold inclusion.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 8: FULL COLUMN LINEAGE MAPPING TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_ACCT_FIRST_ACTIVE | — | — | DIRECT_MATCH | High | Column names identical, both TEXT type, semantic purpose matches | — | — | None | Direct pass-through |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Column names identical, both TEXT type, semantic purpose matches | — | — | None | Direct pass-through |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_CONSOLIDATED_USAGE | — | — | DIRECT_MATCH | High | Column names identical, both TEXT type, semantic purpose matches | — | — | None | Direct pass-through |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column names identical, both TEXT type, semantic purpose matches | — | — | None | Direct pass-through |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | Multiple Silver tables | — | GLD_AGGREGATE | GRAIN_CHANGE | High | Used in COUNT(DISTINCT) aggregation for active accounts metric | BR-009 | — | `COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION` | Aggregation to account count |
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER | DATE | GLD_AGGREGATE | UNIT_CHANGE | Low | Text timestamp requires parsing to DATE - format unclear from sample | BR-001 | — | `CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)` | [LOW CONFIDENCE] Format assumption |
| DATA_DATE | TEXT | REPORT_DATE | SLV_CONSOLIDATED_USAGE | — | — | UNIT_CHANGE | Low | Text timestamp requires parsing to DATE - format unclear from sample | BR-001 | — | `CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)` | [LOW CONFIDENCE] Format assumption |
| DATA_DATE | TEXT | START_DATE | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Low | Text timestamp requires parsing to DATE - format unclear from sample | BR-001 | — | `CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)` | [LOW CONFIDENCE] Format assumption |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Column names identical, both TEXT type, semantic purpose matches | — | — | None | Direct pass-through |
| AGENT_ID | TEXT | USER_ID | SLV_COMBINED_CHANNELS | — | — | RENAME | Medium | Semantic mapping - agents represent users in contact center context | BR-005 | — | `AGENT_ID AS USER_ID` | [ASSUMPTION] Requires business confirmation |
| AGENT_ID | TEXT | USER_ID | SLV_USAGE_MASTER | — | — | RENAME | Medium | Semantic mapping - agents represent users in contact center context | BR-005 | — | `AGENT_ID AS USER_ID` | [ASSUMPTION] Requires business confirmation |
| AGENT_ID | TEXT | USER_ID | SLV_USER_FIRST_ACTIVE | — | — | RENAME | Medium | Semantic mapping - agents represent users in contact center context | BR-005 | — | `AGENT_ID AS USER_ID` | [ASSUMPTION] Requires business confirmation |
| AGENT_ID | TEXT | — | — | ACTIVE_USERS | GLD_AGGREGATE | GRAIN_CHANGE | High | Aggregated to distinct count for user activity metric | BR-008 | — | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT` | Aggregation to user count |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values match (Inbound/Outbound vs INBOUND/OUTBOUND) - only case differs | — | — | None | Case insensitive match confirmed |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values confirmed overlapping (Email, SMS, Chat) - semantic match | — | — | None | Direct pass-through |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values match (Video, Phone) - semantic purpose identical | — | — | None | Direct pass-through |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column names identical, both NUMBER type, semantic purpose matches | — | — | None | Direct pass-through |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | — | — | UNIT_CHANGE | High | Milliseconds to minutes conversion for business reporting | BR-002 | — | `INBOUND_PHONE_MS / 1000.0 / 60.0` | Standard unit conversion |
| INBOUND_PHONE_MS | NUMBER | DURATION_SEC | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Medium | Milliseconds to seconds conversion - only inbound calls have duration | BR-003 | — | `INBOUND_PHONE_MS / 1000.0` | [ASSUMPTION] Outbound duration not available |
| INBOUND_PHONE_MS | NUMBER | PHONE_USAGE | SLV_CONSOLIDATED_USAGE | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE | High | Milliseconds to minutes with aggregation for usage reporting | BR-004 | — | `SUM(INBOUND_PHONE_MS) / 1000.0 / 60.0 GROUP BY DATE, ACCOUNT_ID` | Aggregate and convert units |
| INBOUND_PHONE_MS | NUMBER | WEEKLY_PHONE_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | UNIT_CHANGE | Medium | Milliseconds to minutes - requires weekly aggregation logic | BR-004 | — | `SUM(INBOUND_PHONE_MS) / 1000.0 / 60.0 GROUP BY WEEK` | [ASSUMPTION] Weekly window aggregation needed |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE | — | — | RENAME | Medium | Engagement-level activity mapped to account-level active flag | BR-007 | — | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | [ASSUMPTION] Engagement implies account active |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_DAILY_METRICS | — | — | RENAME | Medium | Engagement-level activity mapped to account-level active flag | BR-007 | — | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | [ASSUMPTION] Engagement implies account active |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_MONTHLY_METRICS | — | — | RENAME | Medium | Engagement-level activity mapped to account-level active flag | BR-007 | — | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | [ASSUMPTION] Engagement implies account active |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_WEEKLY_METRICS | — | — | RENAME | Medium | Engagement-level activity mapped to account-level active flag | BR-007 | — | `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` | [ASSUMPTION] Engagement implies account active |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | SEMANTIC_CHANGE | Medium | AWS cluster regions mapped to business regions via lookup | BR-010 | — | `CASE WHEN CLUSTER = 'us-east-1' THEN 'NAMER' WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' ELSE 'UNKNOWN' END` | [LOW CONFIDENCE] LATAM mapping unclear |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | Device/platform dimension not present in PI schema - new FTL capability | — | — | Available for Silver extension | Recommend add to SLV_COMBINED_CHANNELS |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | Operating system dimension not present in PI schema - new FTL capability | — | — | Available for Silver extension | Consider adding to SLV_COMBINED_CHANNELS |
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | ZCC-specific account ID not present in PI schema - relationship to ACCOUNT_ID unclear | — | — | Available for Silver extension | Clarify business purpose before use |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE | — | — | GAP | High | No historical first active date in FTL - requires MIN(DATA_DATE) or lookup table | — | GAP-008 | `NULL AS ACCOUNT_FIRST_ACTIVE -- Requires historical aggregation` | Build dimension table from history |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | No historical first active date in FTL - requires lookup table | — | GAP-008 | `NULL AS ACCOUNT_FIRST_ACTIVE -- Requires historical aggregation` | Build dimension table from history |
| — | — | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE | — | — | GAP | High | No historical first active date in FTL - requires MIN(DATA_DATE) or lookup table | — | GAP-009 | `NULL AS USER_FIRST_ACTIVE -- Requires historical aggregation` | Build dimension table from history |
| — | — | USER_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | No historical first active date in FTL - requires lookup table | — | GAP-009 | `NULL AS USER_FIRST_ACTIVE -- Requires historical aggregation` | Build dimension table from history |
| — | — | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE | — | — | GAP | High | No refresh timestamp in source - use system time | BR-012 | — | `CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP` | Standard metadata field |
| — | — | REFRESH_TIMESTAMP | SLV_USER_FIRST_ACTIVE | — | — | GAP | High | No refresh timestamp in source - use system time | BR-012 | — | `CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP` | Standard metadata field |
| — | — | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | — | — | GAP | High | No engagement outcome status in FTL source | — | GAP-007 | `NULL AS ENGAGEMENT_STATUS -- No FTL source available` | Confirm if exists in separate system |
| — | — | SLA_ACHIEVED | SLV_COMBINED_CHANNELS | — | — | GAP | High | No SLA achievement tracking in FTL source | — | GAP-006 | `NULL AS SLA_ACHIEVED -- No FTL source available` | Confirm if exists in separate system |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No SLA session count in FTL source | — | GAP-006 | `NULL AS SLA_ACHIEVED_SESSIONS -- No FTL source available` | Confirm if exists in separate system |
| — | — | SOURCE_TABLE | SLV_COMBINED_CHANNELS | — | — | GAP | High | No source table metadata in FTL - hardcode source name | — | — | `'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE` | Hardcoded metadata |
| — | — | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | — | — | GAP | Medium | No product dimension in FTL source | — | GAP-014 | `'ZCC Platform' AS PRODUCT_NAME -- Hardcoded default` | Default or derive from metadata |
| — | — | WINDOW | SLV_CONSOLIDATED_USAGE | — | — | GAP | Medium | No temporal window dimension in FTL - hardcode based on table purpose | BR-011 | — | `'DAILY' AS WINDOW` | [ASSUMPTION] Based on table granularity |
| — | — | WINDOW | SLV_DAILY_METRICS | — | — | GAP | Medium | No temporal window dimension in FTL - hardcode based on table purpose | BR-011 | — | `'DAILY' AS WINDOW` | [ASSUMPTION] Based on table granularity |
| — | — | WINDOW | SLV_MONTHLY_METRICS | — | — | GAP | Medium | No temporal window dimension in FTL - hardcode based on table purpose | BR-011 | — | `'MONTHLY' AS WINDOW` | [ASSUMPTION] Based on table granularity |
| — | — | WINDOW | SLV_WEEKLY_METRICS | — | — | GAP | Medium | No temporal window dimension in FTL - hardcode based on table purpose | BR-011 | — | `'WEEKLY' AS WINDOW` | [ASSUMPTION] Based on table granularity |
| — | — | ACTIVE_USERS | SLV_CONSOLIDATED_USAGE | — | — | GAP | Medium | Count distinct agents as active users - requires aggregation | BR-008 | — | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true` | [ASSUMPTION] Agents = users |
| — | — | ACTIVE_USERS | SLV_DAILY_METRICS | — | — | GAP | Medium | Count distinct agents as active users - requires aggregation | BR-008 | — | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true` | [ASSUMPTION] Agents = users |
| — | — | ACTIVE_USERS | SLV_MONTHLY_METRICS | — | — | GAP | Medium | Count distinct agents as active users - requires aggregation | BR-008 | — | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true` | [ASSUMPTION] Agents = users |
| — | — | ACTIVE_USERS | SLV_WEEKLY_METRICS | — | — | GAP | Medium | Count distinct agents as active users - requires aggregation | BR-008 | — | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true` | [ASSUMPTION] Agents = users |
| — | — | CHAT_USAGE | SLV_CONSOLIDATED_USAGE | — | — | GAP | High | No chat metrics in FTL source - only phone/video available | — | GAP-004 | `NULL AS CHAT_USAGE -- No FTL source available` | **BLOCKS** complete usage reporting |
| — | — | CHAT_USAGE | SLV_DAILY_METRICS | — | — | GAP | High | No chat metrics in FTL source - only phone/video available | — | GAP-004 | `NULL AS CHAT_USAGE -- No FTL source available` | **BLOCKS** complete usage reporting |
| — | — | CHAT_USAGE | SLV_WEEKLY_METRICS | — | — | GAP | High | No chat metrics in FTL source - only phone/video available | — | GAP-004 | `NULL AS CHAT_USAGE -- No FTL source available` | **BLOCKS** complete usage reporting |
| — | — | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No chat session count in FTL source | — | GAP-005 | `NULL AS CHAT_SESSIONS -- No FTL source available` | **BLOCKS** complete usage master |
| — | — | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | GAP | High | No video duration metrics in FTL source - only phone available | — | GAP-015 | `NULL AS VIDEO_USAGE -- No FTL source available` | **BLOCKS** complete usage reporting |
| — | — | DAILY_CHAT_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No chat metrics in FTL source | — | GAP-004 | `NULL AS DAILY_CHAT_USAGE -- No FTL source available` | **BLOCKS** table functionality |
| — | — | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No payment/subscription status in FTL source | — | GAP-010 | `NULL AS IS_PAID_USER -- No FTL source available` | Source from subscription system |
| — | — | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No historical activity tracking for rolling windows in FTL source | — | GAP-011 | `NULL AS ACTIVE_DAYS_LAST_7 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No historical activity tracking for rolling windows in FTL source | — | GAP-012 | `NULL AS ACTIVE_DAYS_LAST_28 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No activity cohort segmentation data in FTL source | — | GAP-013 | `NULL AS ACTIVE_1_DAY_L7 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No activity cohort segmentation data in FTL source | — | GAP-013 | `NULL AS ACTIVE_4_7_DAYS_L7 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No activity cohort segmentation data in FTL source | — | GAP-013 | `NULL AS ACTIVE_1_DAY_L28 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No activity cohort segmentation data in FTL source | — | GAP-013 | `NULL AS ACTIVE_16PLUS_DAYS_L28 -- No FTL source available` | **BLOCKS** table functionality |
| — | — | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | — | — | GAP | High | No activity day tracking in FTL source | — | GAP-016 | `NULL AS USERS_ACTIVE_1_DAY -- No FTL source available` | Incomplete metric set |
| — | — | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | — | — | GAP | High | No activity day tracking in FTL source | — | GAP-016 | `NULL AS USERS_ACTIVE_4_7_DAYS -- No FTL source available` | Incomplete metric set |
| — | — | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | No historical activity tracking in FTL - requires daily user activity aggregation | — | GAP-003 | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- No FTL source available` | **CRITICAL** Blocks Gold migration |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No customer segmentation dimension in FTL source - requires account master or CRM integration | — | GAP-001 | `NULL AS SEGMENT -- No FTL source available` | **CRITICAL** Blocks Gold migration |
| — | — | — | — | IS_LICENSED | GLD_AGGREGATE | GAP | High | No licensing status in FTL source - requires subscription/billing system integration | — | GAP-002 | `NULL AS IS_LICENSED -- No FTL source available` | **CRITICAL** Blocks Gold migration |
| — | — | — | — | ACTIVE_ACCOUNTS | GLD_AGGREGATE | GAP | High | Derivable via COUNT(DISTINCT ACCOUNT_ID) but depends on REGION mapping | BR-009 | — | `COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION` | Depends on BR-010 region mapping |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 9: MAPPING CSV FOR REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```csv
FTL_Bronze_Column,FTL_Data_Type,PI_Silver_Column,PI_Silver_Table,PI_Gold_Column,PI_Gold_Table,Classification,Confidence,Mapping_Reason,BR_ID,GAP_ID,Transformation,Notes
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_ACCT_FIRST_ACTIVE,—,—,DIRECT_MATCH,High,Column names identical both TEXT type semantic purpose matches,—,—,None,Direct pass-through
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Column names identical both TEXT type semantic purpose matches,—,—,None,Direct pass-through
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_CONSOLIDATED_USAGE,—,—,DIRECT_MATCH,High,Column names identical both TEXT type semantic purpose matches,—,—,None,Direct pass-through
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,Column names identical both TEXT type semantic purpose matches,—,—,None,Direct pass-through
ACCOUNT_ID,TEXT,—,Multiple Silver tables,—,GLD_AGGREGATE,GRAIN_CHANGE,High,Used in COUNT(DISTINCT) aggregation for active accounts metric,BR-009,—,"COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION",Aggregation to account count
DATA_DATE,TEXT,DATE,SLV_USAGE_MASTER,DATE,GLD_AGGREGATE,UNIT_CHANGE,Low,Text timestamp requires parsing to DATE - format unclear from sample,BR-001,—,"CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)",[LOW CONFIDENCE] Format assumption
DATA_DATE,TEXT,REPORT_DATE,SLV_CONSOLIDATED_USAGE,—,—,UNIT_CHANGE,Low,Text timestamp requires parsing to DATE - format unclear from sample,BR-001,—,"CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)",[LOW CONFIDENCE] Format assumption
DATA_DATE,TEXT,START_DATE,SLV_COMBINED_CHANNELS,—,—,UNIT_CHANGE,Low,Text timestamp requires parsing to DATE - format unclear from sample,BR-001,—,"CAST(TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS DATE)",[LOW CONFIDENCE] Format assumption
ENGAGEMENT_ID,TEXT,ENGAGEMENT_ID,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Column names identical both TEXT type semantic purpose matches,—,—,None,Direct pass-through
AGENT_ID,TEXT,USER_ID,SLV_COMBINED_CHANNELS,—,—,RENAME,Medium,Semantic mapping - agents represent users in contact center context,BR-005,—,AGENT_ID AS USER_ID,[ASSUMPTION] Requires business confirmation
AGENT_ID,TEXT,USER_ID,SLV_USAGE_MASTER,—,—,RENAME,Medium,Semantic mapping - agents represent users in contact center context,BR-005,—,AGENT_ID AS USER_ID,[ASSUMPTION] Requires business confirmation
AGENT_ID,TEXT,USER_ID,SLV_USER_FIRST_ACTIVE,—,—,RENAME,Medium,Semantic mapping - agents represent users in contact center context,BR-005,—,AGENT_ID AS USER_ID,[ASSUMPTION] Requires business confirmation
AGENT_ID,TEXT,—,—,ACTIVE_USERS,GLD_AGGREGATE,GRAIN_CHANGE,High,Aggregated to distinct count for user activity metric,BR-008,—,"COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT",Aggregation to user count
DIRECTION,TEXT,DIRECTION,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Distinct values match (Inbound/Outbound vs INBOUND/OUTBOUND) - only case differs,—,—,None,Case insensitive match confirmed
MODALITY,TEXT,MODALITY,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,"Distinct values confirmed overlapping (Email, SMS, Chat) - semantic match",—,—,None,Direct pass-through
CHANNEL,TEXT,CHANNEL,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,"Distinct values match (Video, Phone) - semantic purpose identical",—,—,None,Direct pass-through
PHONE_SESSIONS,NUMBER,PHONE_SESSIONS,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,Column names identical both NUMBER type semantic purpose matches,—,—,None,Direct pass-through
INBOUND_PHONE_MS,NUMBER,INBOUND_PHONE_MINS,SLV_USAGE_MASTER,—,—,UNIT_CHANGE,High,Milliseconds to minutes conversion for business reporting,BR-002,—,INBOUND_PHONE_MS / 1000.0 / 60.0,Standard unit conversion
INBOUND_PHONE_MS,NUMBER,DURATION_SEC,SLV_COMBINED_CHANNELS,—,—,UNIT_CHANGE,Medium,Milliseconds to seconds conversion - only inbound calls have duration,BR-003,—,INBOUND_PHONE_MS / 1000.0,[ASSUMPTION] Outbound duration not available
INBOUND_PHONE_MS,NUMBER,PHONE_USAGE,SLV_CONSOLIDATED_USAGE,PHONE_USAGE,GLD_AGGREGATE,UNIT_CHANGE,High,Milliseconds to minutes with aggregation for usage reporting,BR-004,—,"SUM(INBOUND_PHONE_MS) / 1000.0 / 60.0 GROUP BY DATE, ACCOUNT_ID",Aggregate and convert units
INBOUND_PHONE_MS,NUMBER,WEEKLY_PHONE_USAGE,SLV_ROLL_29_DAY_USAGE,—,—,UNIT_CHANGE,Medium,Milliseconds to minutes - requires weekly aggregation logic,BR-004,—,SUM(INBOUND_PHONE_MS) / 1000.0 / 60.0 GROUP BY WEEK,[ASSUMPTION] Weekly window aggregation needed
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_CONSOLIDATED_USAGE,—,—,RENAME,Medium,Engagement-level activity mapped to account-level active flag,BR-007,—,IS_ACTIVE AS IS_ACTIVE_ACCOUNT,[ASSUMPTION] Engagement implies account active
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_DAILY_METRICS,—,—,RENAME,Medium,Engagement-level activity mapped to account-level active flag,BR-007,—,IS_ACTIVE AS IS_ACTIVE_ACCOUNT,[ASSUMPTION] Engagement implies account active
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_MONTHLY_METRICS,—,—,RENAME,Medium,Engagement-level activity mapped to account-level active flag,BR-007,—,IS_ACTIVE AS IS_ACTIVE_ACCOUNT,[ASSUMPTION] Engagement implies account active
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_WEEKLY_METRICS,—,—,RENAME,Medium,Engagement-level activity mapped to account-level active flag,BR-007,—,IS_ACTIVE AS IS_ACTIVE_ACCOUNT,[ASSUMPTION] Engagement implies account active
CLUSTER,TEXT,—,—,REGION,GLD_AGGREGATE,SEMANTIC_CHANGE,Medium,AWS cluster regions mapped to business regions via lookup,BR-010,—,"CASE WHEN CLUSTER = 'us-east-1' THEN 'NAMER' WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' ELSE 'UNKNOWN' END",[LOW CONFIDENCE] LATAM mapping unclear
CLIENT_TYPE,TEXT,—,—,—,—,NEW_CAPABILITY,N/A,Device/platform dimension not present in PI schema - new FTL capability,—,—,Available for Silver extension,Recommend add to SLV_COMBINED_CHANNELS
OS,TEXT,—,—,—,—,NEW_CAPABILITY,N/A,Operating system dimension not present in PI schema - new FTL capability,—,—,Available for Silver extension,Consider adding to SLV_COMBINED_CHANNELS
ZCC_ACCOUNT_ID,TEXT,—,—,—,—,NEW_CAPABILITY,N/A,ZCC-specific account ID not present in PI schema - relationship to ACCOUNT_ID unclear,—,—,Available for Silver extension,Clarify business purpose before use
—,—,ACCOUNT_FIRST_ACTIVE,SLV_ACCT_FIRST_ACTIVE,—,—,GAP,High,No historical first active date in FTL - requires MIN(DATA_DATE) or lookup table,—,GAP-008,NULL AS ACCOUNT_FIRST_ACTIVE -- Requires historical aggregation,Build dimension table from history
—,—,ACCOUNT_FIRST_ACTIVE,SLV_USAGE_MASTER,—,—,GAP,High,No historical first active date in FTL - requires lookup table,—,GAP-008,NULL AS ACCOUNT_FIRST_ACTIVE -- Requires historical aggregation,Build dimension table from history
—,—,USER_FIRST_ACTIVE,SLV_USER_FIRST_ACTIVE,—,—,GAP,High,No historical first active date in FTL - requires MIN(DATA_DATE) or lookup table,—,GAP-009,NULL AS USER_FIRST_ACTIVE -- Requires historical aggregation,Build dimension table from history
—,—,USER_FIRST_ACTIVE,SLV_USAGE_MASTER,—,—,GAP,High,No historical first active date in FTL - requires lookup table,—,GAP-009,NULL AS USER_FIRST_ACTIVE -- Requires historical aggregation,Build dimension table from history
—,—,REFRESH_TIMESTAMP,SLV_ACCT_FIRST_ACTIVE,—,—,GAP,High,No refresh timestamp in source - use system time,BR-012,—,CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP,Standard metadata field
—,—,REFRESH_TIMESTAMP,SLV_USER_FIRST_ACTIVE,—,—,GAP,High,No refresh timestamp in source - use system time,BR-012,—,CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP,Standard metadata field
—,—,ENGAGEMENT_STATUS,SLV_COMBINED_CHANNELS,—,—,GAP,High,No engagement outcome status in FTL source,—,GAP-007,NULL AS ENGAGEMENT_STATUS -- No FTL source available,Confirm if exists in separate system
—,—,SLA_ACHIEVED,SLV_COMBINED_CHANNELS,—,—,GAP,High,No SLA achievement tracking in FTL source,—,GAP-006,NULL AS SLA_ACHIEVED -- No FTL source available,Confirm if exists in separate system
—,—,SLA_ACHIEVED_SESSIONS,SLV_USAGE_MASTER,—,—,GAP,High,No SLA session count in FTL source,—,GAP-006,NULL AS SLA_ACHIEVED_SESSIONS -- No FTL source available,Confirm if exists in separate system
—,—,SOURCE_TABLE,SLV_COMBINED_CHANNELS,—,—,GAP,High,No source table metadata in FTL - hardcode source name,—,—,'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE,Hardcoded metadata
—,—,PRODUCT_NAME,SLV_CONSOLIDATED_USAGE,—,—,GAP,Medium,No product dimension in FTL source,—,GAP-014,'ZCC Platform' AS PRODUCT_NAME -- Hardcoded default,Default or derive from metadata
—,—,WINDOW,SLV_CONSOLIDATED_USAGE,—,—,GAP,Medium,No temporal window dimension in FTL - hardcode based on table purpose,BR-011,—,'DAILY' AS WINDOW,[ASSUMPTION] Based on table granularity
—,—,WINDOW,SLV_DAILY_METRICS,—,—,GAP,Medium,No temporal window dimension in FTL - hardcode based on table purpose,BR-011,—,'DAILY' AS WINDOW,[ASSUMPTION] Based on table granularity
—,—,WINDOW,SLV_MONTHLY_METRICS,—,—,GAP,Medium,No temporal window dimension in FTL - hardcode based on table purpose,BR-011,—,'MONTHLY' AS WINDOW,[ASSUMPTION] Based on table granularity
—,—,WINDOW,SLV_WEEKLY_METRICS,—,—,GAP,Medium,No temporal window dimension in FTL - hardcode based on table purpose,BR-011,—,'WEEKLY' AS WINDOW,[ASSUMPTION] Based on table granularity
—,—,ACTIVE_USERS,SLV_CONSOLIDATED_USAGE,—,—,GAP,Medium,Count distinct agents as active users - requires aggregation,BR-008,—,COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true,[ASSUMPTION] Agents = users
—,—,ACTIVE_USERS,SLV_DAILY_METRICS,—,—,GAP,Medium,Count distinct agents as active user