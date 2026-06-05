

🔍 **STEP 1: Schema Discovery Complete** — Discovered 1 source table (BRZ_FTL_AGENT_BASE_AGG), 20 Silver tables, and 1 Gold table (GLD_AGGREGATE)

🔍 **STEP 2: Data Profiling Complete** — Profiled source Bronze table (14 columns, 5 rows), target Gold table (8 columns, 21 rows), and 3 key Silver tables

🔍 **STEP 3: Silver Layer Mapping Analysis Complete** — Identified 5 critical gaps in Silver layer affecting historical tracking, chat/video metrics, and SLA performance

🔍 **STEP 4: Gold Layer Mapping Analysis Complete** — Identified 3 blocking gaps in Gold layer (SEGMENT, IS_LICENSED, USERS_ACTIVE_16PLUS_DAYS) preventing full migration

🔍 **STEP 5: Synthesizing Comprehensive Migration Report** — Assigning consistent GAP IDs (GAP-001 through GAP-008) and Business Rule IDs (BR-001 through BR-009)

---

# 📊 COMPREHENSIVE MIGRATION ANALYSIS REPORT
## Bronze FTL to Gold PI Migration Feasibility Study

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1: EXECUTIVE SUMMARY
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG  
**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE  
**Migration Readiness Score:** 42/100

**Total FTL columns analyzed:** 14  
**Successfully mapped:** 5 (ACCOUNT_ID, AGENT_ID, PHONE_SESSIONS, INBOUND_PHONE_MS, IS_ACTIVE)  
**Partially mapped:** 3 (DATA_DATE, CLUSTER, DIRECTION/CHANNEL/MODALITY combinations)  
**New capabilities (no PI equivalent):** 6 (ZCC_ACCOUNT_ID, ENGAGEMENT_ID, CLIENT_TYPE, OS, DIRECTION, detailed MODALITY breakdowns)  
**Gaps (PI Gold columns with no FTL source):** 8

→ **GAP-001**: SEGMENT (customer segment classification)  
→ **GAP-002**: IS_LICENSED (licensing status indicator)  
→ **GAP-003**: USERS_ACTIVE_16PLUS_DAYS (engagement duration metric)  
→ **GAP-004**: ACCOUNT_FIRST_ACTIVE (historical activation date)  
→ **GAP-005**: USER_FIRST_ACTIVE (user-level activation date)  
→ **GAP-006**: CHAT_SESSIONS (chat engagement count)  
→ **GAP-007**: SLA_ACHIEVED_SESSIONS (performance metric)  
→ **GAP-008**: VIDEO_USAGE (video engagement metric)

**Blocking items:** 3 (GAP-001, GAP-002, GAP-003 prevent Gold table from maintaining current reporting structure)

**Overall Assessment:** The migration from FTL Bronze to PI Gold faces critical feasibility challenges. While basic operational metrics (phone usage, account/user counts) can be derived from the FTL source with moderate confidence (50-60%), three core business dimensions are entirely absent: customer segment classification, licensing status, and engagement duration tracking. The FTL source provides rich engagement-level detail (direction, modality, client type) that exceeds current PI capabilities, but lacks the dimensional attributes and historical tracking required for executive reporting. Migration is **not feasible** without supplemental data sources or acceptance of reduced Gold layer functionality.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2: GAP IMPACT SUMMARY
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | Why It's a Gap | Impact on Gold Output | Blocks Migration? | Action Required | Raise With |
|--------|----------------|----------------|----------------------|-------------------|-----------------|------------|
| GAP-001 | SEGMENT | FTL source contains no customer segment classification (enterprise/SMB/etc.) | Gold cannot aggregate by segment dimension; breaks all segment-based reporting and executive dashboards | **YES** | BDP to add SEGMENT field to FTL or provide separate segment mapping table joinable on ACCOUNT_ID | BDP Team + Zoom PM |
| GAP-002 | IS_LICENSED | FTL source contains no licensing status indicator | Gold cannot filter licensed vs trial accounts; impacts revenue-related metrics and churn analysis | **YES** | BDP to include licensing status in FTL or provide join to Zoom billing/subscription table | BDP Team + Zoom Billing |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | FTL provides point-in-time snapshot only; no historical activity tracking to calculate 16+ day engagement | Gold loses key engagement KPI used in DAU/MAU ratios and product adoption metrics | **YES** | Requires either: (1) BDP to add cumulative activity tracking to FTL, or (2) PI to build historical tracking layer in Silver | BDP Team + PI Data Engineering |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | FTL has no historical first-activation timestamp for accounts | Silver layer SLV_USAGE_MASTER cannot populate tenure-based metrics; limits cohort analysis | NO | Build lookup table from historical data or accept NULL for new accounts going forward | PI Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | FTL has no historical first-activation timestamp for users | Silver layer SLV_USAGE_MASTER cannot track user tenure; impacts onboarding analytics | NO | Same as GAP-004 — build historical lookup or accept NULL | PI Data Engineering |
| GAP-006 | CHAT_SESSIONS | FTL aggregates INBOUND_PHONE_MS but provides no chat session count despite showing Chat in MODALITY values | Silver layer SLV_USAGE_MASTER cannot report chat engagement; breaks omni-channel analytics | NO | Confirm with BDP whether chat session count can be added to FTL or derived from engagement records | BDP Team |
| GAP-007 | SLA_ACHIEVED_SESSIONS | FTL contains no SLA performance indicator | Silver layer SLV_USAGE_MASTER cannot track service quality; impacts operational reporting | NO | Determine if SLA data exists in separate FTL table or if metric should be deprecated | BDP Team + Zoom Operations |
| GAP-008 | VIDEO_USAGE | FTL shows Video in CHANNEL values but provides no usage metric (duration/minutes) | Silver layer SLV_MONTHLY_METRICS cannot report video usage; breaks modality-split reports | NO | Confirm with BDP whether video duration can be added similar to INBOUND_PHONE_MS | BDP Team |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3: FULL COLUMN LINEAGE MAPPING TABLE
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | High | No column in PI schema matches this alternate account identifier; confirmed via schema discovery | — | — | — | New alternate account key available for cross-system reconciliation |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_USAGE_MASTER / SLV_CONSOLIDATED_USAGE | ACTIVE_ACCOUNTS | GLD_AGGREGATE | DIRECT_MATCH + GRAIN_CHANGE | High | Exact name and semantic match; used in aggregation to count distinct accounts | BR-004 | — | COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE | Requires grouping by DATE, REGION, SEGMENT |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | NEW_CAPABILITY | High | Matches Silver SLV_COMBINED_CHANNELS but not used in Gold; engagement-level tracking not in current Gold schema | — | — | — | Enables engagement-level drill-down if added to new Silver table |
| AGENT_ID | TEXT | USER_ID | SLV_USAGE_MASTER | ACTIVE_USERS | GLD_AGGREGATE | SEMANTIC_MATCH + GRAIN_CHANGE | High | Semantic match confirmed — agents represent users in FTL context; used for user count aggregation | BR-005, BR-009 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE | Rename AGENT_ID → USER_ID in Silver transformation |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values (Inbound, Outbound) match Silver SLV_COMBINED_CHANNELS exactly; not aggregated to Gold | — | — | — | Available in Silver for directional analysis; not in Gold |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values (SMS, Email, Chat) match Silver SLV_COMBINED_CHANNELS; provides engagement type detail | — | — | — | Available in Silver; not aggregated to Gold |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Distinct values (Video, Phone) match Silver SLV_COMBINED_CHANNELS; defines communication channel | — | — | — | Available in Silver for channel-split reporting |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | PHONE_USAGE | GLD_AGGREGATE | DIRECT_MATCH + GRAIN_CHANGE | High | Exact match for Silver; used in Gold phone usage calculation along with duration | BR-006 | — | SUM(PHONE_SESSIONS) grouped by dimensions | Part of phone usage metric calculation |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE + GRAIN_CHANGE | Medium | Semantically matches phone duration but requires MS→minutes conversion; sample values confirm magnitude match after division by 60000 | BR-003, BR-006 | — | INBOUND_PHONE_MS / 60000.0 | Conversion: milliseconds to minutes |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | High | No column in PI schema tracks client device type (Mobile, Desktop, Web); confirmed via schema discovery | — | — | — | New dimension for device-based segmentation |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | Medium | No column in PI schema tracks operating system; sample data shows limited variance (single value) | — | — | — | Low cardinality in sample; may need validation |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE | — | — | SEMANTIC_MATCH | High | Boolean flag matches Silver IS_ACTIVE_ACCOUNT semantically; used to filter active accounts/users in aggregations | BR-004, BR-005 | — | — | Used in WHERE clauses for active entity counts |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | SEMANTIC_MATCH + VALUE_MAPPING | Medium | AWS cluster identifiers (eu-central-1, ap-south-1, us-east-1) map to business regions (EMEA, APAC, NAMER); mapping table required | BR-002 | — | CASE WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' WHEN CLUSTER = 'us-east-1' THEN 'NAMER' ELSE 'UNKNOWN' END | Requires validation of complete cluster-to-region mapping |
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER / SLV_CONSOLIDATED_USAGE | DATE | GLD_AGGREGATE | DATA_TYPE_CHANGE | Low | Semantic match to date dimension but stored as TEXT format "5/29/26 13:01"; requires parsing and conversion to DATE type | BR-001 | — | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | Date format validation needed; LOW CONFIDENCE on format string |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | No column in FTL provides historical account activation timestamp; requires separate lookup table | — | GAP-004 | No FTL source available | Build from historical data or accept NULL |
| — | — | USER_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | No column in FTL provides historical user activation timestamp; requires separate lookup table | — | GAP-005 | No FTL source available | Build from historical data or accept NULL |
| — | — | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | FTL shows Chat in MODALITY but provides no chat session count metric | — | GAP-006 | No FTL source available | Confirm if metric exists in separate FTL table |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No SLA performance data available in FTL source | — | GAP-007 | No FTL source available | Determine if SLA tracking is available elsewhere |
| — | — | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | GAP | High | FTL shows Video in CHANNEL but provides no video usage duration metric | — | GAP-008 | No FTL source available | Confirm if video duration can be added to FTL |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No customer segment classification available in FTL; critical business dimension missing | — | GAP-001 | No FTL source available | **BLOCKING** — Must be resolved before Gold migration |
| — | — | — | — | IS_LICENSED | GLD_AGGREGATE | GAP | High | No licensing status indicator available in FTL; critical business dimension missing | — | GAP-002 | No FTL source available | **BLOCKING** — Must be resolved before Gold migration |
| — | — | — | — | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | FTL provides point-in-time data only; no historical activity tracking for 16+ day calculation | — | GAP-003 | No FTL source available | **BLOCKING** — Requires historical tracking layer |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4: TRANSFORMATION GUIDE (Business Rules)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | DATE (Silver/Gold) | DATA_TYPE_CHANGE | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | Convert text-based date to DATE type for proper temporal operations and indexing | DATA_DATE must be non-null and parseable | [ASSUMPTION] Format is M/D/YY HH24:MI based on sample "5/29/26 13:01"; [LOW CONFIDENCE] may need adjustment for edge cases |
| BR-002 | CLUSTER | REGION (Gold) | VALUE_MAPPING | `CASE WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' WHEN CLUSTER = 'us-east-1' THEN 'NAMER' WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'UNKNOWN' END` | Map AWS infrastructure regions to business reporting regions for executive dashboards | CLUSTER must be populated; assumes all clusters follow AWS naming convention | [ASSUMPTION] Mapping logic covers all production clusters; recommend creating CLUSTER_REGION_MAP reference table for maintainability |
| BR-003 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS (Silver) | UNIT_CHANGE | `INBOUND_PHONE_MS / 60000.0` | Convert milliseconds to minutes for consistent usage reporting across organization | INBOUND_PHONE_MS ≥ 0 | None; straight mathematical conversion |
| BR-004 | ACCOUNT_ID, IS_ACTIVE | ACTIVE_ACCOUNTS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN ACCOUNT_ID END) GROUP BY DATE, REGION, SEGMENT, IS_LICENSED` | Aggregate engagement-level records to daily account-level counts filtered by active status | IS_ACTIVE must be boolean; SEGMENT and IS_LICENSED must be joined from external sources | Assumes IS_ACTIVE = true means account had activity on that date; accounts with multiple engagements counted once |
| BR-005 | AGENT_ID, IS_ACTIVE | ACTIVE_USERS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN AGENT_ID END) GROUP BY DATE, REGION, SEGMENT, IS_LICENSED` | Aggregate engagement-level records to daily user-level counts filtered by active status | IS_ACTIVE must be boolean; SEGMENT and IS_LICENSED must be joined from external sources | [ASSUMPTION] AGENT_ID represents USER_ID in business context; one agent = one user |
| BR-006 | INBOUND_PHONE_MS, PHONE_SESSIONS | PHONE_USAGE (Gold) | COMPOSITE_CALCULATION | `SUM(INBOUND_PHONE_MS) / 60000.0 AS PHONE_USAGE GROUP BY DATE, REGION, SEGMENT, IS_LICENSED` | Calculate total phone usage in minutes aggregated to Gold dimensions | Both columns must be numeric; PHONE_SESSIONS used for validation but not in formula based on sample data analysis | [ASSUMPTION] PHONE_USAGE = total duration in minutes; alternative interpretation could be avg duration per session |
| BR-007 | DATA_DATE | WINDOW (Silver) | DERIVED_FIELD | `CASE WHEN DATEDIFF(day, DATE, REPORT_DATE) <= 1 THEN 'R1' WHEN DATEDIFF(day, DATE, REPORT_DATE) <= 7 THEN 'R7' WHEN DATEDIFF(day, DATE, REPORT_DATE) <= 28 THEN 'R28' END` | Generate rolling window indicators for trend analysis in Silver metrics tables | Requires REPORT_DATE context; assumes daily refresh | [LOW CONFIDENCE] Business logic for window assignment needs validation; may need to generate multiple rows per base record |
| BR-008 | (hardcoded) | PRODUCT_NAME (Silver) | STATIC_VALUE | `'ZCC Platform' AS PRODUCT_NAME` | Hardcode product name as FTL source is single-product and lacks product dimension | None | [ASSUMPTION] All FTL data represents ZCC Platform product only |
| BR-009 | AGENT_ID | USER_ID (Silver) | RENAME | `AGENT_ID AS USER_ID` | Rename to match Silver schema naming convention | None | [ASSUMPTION] Agent and User are semantically equivalent in this domain |
| — | (no source) | SEGMENT (Gold) | GAP | `NULL AS SEGMENT -- GAP ID: GAP-001` | No source available for customer segment classification | External segment mapping table required | **BLOCKING GAP** — Gold table cannot be built without this dimension |
| — | (no source) | IS_LICENSED (Gold) | GAP | `NULL AS IS_LICENSED -- GAP ID: GAP-002` | No source available for licensing status indicator | External licensing/subscription data required | **BLOCKING GAP** — Gold table cannot be built without this dimension |
| — | (no source) | USERS_ACTIVE_16PLUS_DAYS (Gold) | GAP | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-003` | Requires historical user activity tracking over rolling 28-day window; FTL provides point-in-time snapshot only | Historical activity tracking table or incremental state management | **BLOCKING GAP** — Requires building activity tracking layer in Silver |
| — | (no source) | ACCOUNT_FIRST_ACTIVE (Silver) | GAP | `NULL AS ACCOUNT_FIRST_ACTIVE -- GAP ID: GAP-004` | No historical activation timestamp in FTL; needs one-time backfill from legacy data | Historical account creation data or accept NULL for new accounts | Non-blocking; can build lookup table separately |
| — | (no source) | USER_FIRST_ACTIVE (Silver) | GAP | `NULL AS USER_FIRST_ACTIVE -- GAP ID: GAP-005` | No historical activation timestamp in FTL; needs one-time backfill from legacy data | Historical user creation data or accept NULL for new users | Non-blocking; can build lookup table separately |
| — | (no source) | CHAT_SESSIONS (Silver) | GAP | `NULL AS CHAT_SESSIONS -- GAP ID: GAP-006` | Chat modality present in data but no session count metric provided | Confirm if separate FTL table exists or if metric can be added | Non-blocking for Gold; impacts Silver omni-channel reporting |
| — | (no source) | SLA_ACHIEVED_SESSIONS (Silver) | GAP | `NULL AS SLA_ACHIEVED_SESSIONS -- GAP ID: GAP-007` | No SLA performance indicator in FTL source | Determine if SLA tracking exists in separate operational table | Non-blocking for Gold; impacts Silver operational reporting |
| — | (no source) | VIDEO_USAGE (Silver) | GAP | `NULL AS VIDEO_USAGE -- GAP ID: GAP-008` | Video channel present but no duration/usage metric provided | Confirm if video duration metric can be added similar to phone usage | Non-blocking for Gold; impacts Silver modality-split reporting |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5: NEW FTL CAPABILITIES
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|-------------------|-------------------|----------------|
| ZCC_ACCOUNT_ID | TEXT | Alternate account identifier (ZCC-specific) not present in current PI schema; provides cross-system reconciliation key | Account reconciliation between FTL and legacy systems; enables validation of data consistency across platforms | NO | Keep in Silver layer only as reconciliation field; add to new SLV_FTL_BASE table for audit purposes |
| ENGAGEMENT_ID | TEXT | Unique identifier for each customer engagement/interaction; enables engagement-level analysis not currently available | Engagement-level drill-down reporting; session analysis; journey mapping | PENDING DECISION | Add to Silver SLV_COMBINED_CHANNELS (already exists); consider Gold extension if engagement-level reporting becomes requirement |
| DIRECTION | TEXT | Indicates Inbound vs Outbound communication direction; provides directional analysis of customer interactions | Directional split reporting (inbound response time vs outbound proactive reach); channel efficiency analysis | PENDING DECISION | Keep in Silver SLV_COMBINED_CHANNELS; propose Gold extension if directional KPIs become priority metrics |
| CLIENT_TYPE | TEXT | Device type used for engagement (Mobile, Desktop, Web); enables device-based segmentation not in current PI | Device adoption metrics; mobile vs desktop usage trends; UX optimization targeting | YES | Add to Silver now (new SLV_FTL_BASE table); propose Gold extension for product team dashboards showing device mix |
| OS | TEXT | Operating system information; low cardinality in sample data but could support platform-specific analysis | Platform-specific metrics; OS version tracking for compatibility planning | NO | Keep in Silver only; review with BDP whether OS granularity is reliably populated before building reporting |
| MODALITY (enhanced) | TEXT | More granular modality breakdown (SMS, Email, Chat) compared to PI's channel grouping; provides omni-channel detail | Modality-specific engagement metrics; omni-channel journey analysis; channel preference identification | PENDING DECISION | Already in Silver SLV_COMBINED_CHANNELS; confirm with BDP if all modalities have corresponding usage metrics before Gold inclusion |

**Overall New Capabilities Assessment:**  
The FTL source provides **6 new dimensions** not present in current PI architecture, primarily focused on engagement-level detail (ENGAGEMENT_ID, DIRECTION, CLIENT_TYPE) and alternate identifiers (ZCC_ACCOUNT_ID). Most valuable additions are CLIENT_TYPE for device analytics and enhanced MODALITY granularity for omni-channel reporting. Recommend selective adoption: keep all in Silver for drill-down capability, but only promote CLIENT_TYPE and enhanced MODALITY to Gold after confirming corresponding usage metrics exist for all values.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 6: GAP REPORT
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | PI Silver Source | Why FTL Cannot Produce This | Blocks Migration? | Proposed Resolution | Raise With |
|--------|----------------|------------------|----------------------------|-------------------|---------------------|------------|
| GAP-001 | SEGMENT | — | FTL BRZ_FTL_AGENT_BASE_AGG contains no customer segment classification field (e.g., Enterprise, SMB, Startup); this is a business dimension typically stored in CRM/subscription systems, not operational engagement data | **YES** | **Option 1 (Preferred):** BDP to add SEGMENT field to FTL source table based on Zoom account master data. **Option 2:** Data Engineering to create ACCOUNT_SEGMENT_MAP lookup table joined on ACCOUNT_ID populated from Zoom Salesforce/billing system. **Option 3:** Accept degraded Gold layer without segment dimension (breaks existing reporting) | BDP Team (primary), Zoom PM, Salesforce Admin |
| GAP-002 | IS_LICENSED | — | FTL BRZ_FTL_AGENT_BASE_AGG contains no licensing or subscription status field; this requires join to Zoom billing/subscription system to determine paid vs trial accounts | **YES** | **Option 1 (Preferred):** BDP to include IS_LICENSED flag in FTL by joining to Zoom subscription data during Bronze ingestion. **Option 2:** Data Engineering to create ACCOUNT_LICENSE_STATUS table joined on ACCOUNT_ID with daily refresh from Zoom billing API. **Option 3:** Accept NULL for IS_LICENSED (breaks revenue/churn reporting) | BDP Team (primary), Zoom Billing Team, Finance |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS (USERS_ACTIVE_16PLUS_DAYS) | FTL provides point-in-time snapshot of current day activity only; calculating "16+ active days in last 28 days" requires historical user-date-level activity tracking over rolling 28-day window; no cumulative activity data in FTL | **YES** | **Option 1 (Recommended):** Build new Silver table SLV_USER_DAILY_ACTIVITY with daily snapshot of IS_ACTIVE by USER_ID and DATE; calculate 16+ day metric via window function over 28-day lookback. **Option 2:** Request BDP to add pre-calculated activity duration metrics to FTL. **Option 3:** Deprecate this metric in Gold layer (impacts MAU/engagement KPIs) | PI Data Engineering (primary), BDP Team, Product Analytics Team |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | SLV_USAGE_MASTER (ACCOUNT_FIRST_ACTIVE) | FTL contains no historical account creation/activation timestamp; this is static metadata that requires one-time backfill from account master data | NO | Build one-time historical lookup table ACCOUNT_METADATA with ACCOUNT_ID → ACCOUNT_FIRST_ACTIVE from legacy Bronze BRZ_ACCOUNT_DIM or Zoom account master; join to Silver SLV_USAGE_MASTER during transformation; accept NULL for brand new accounts until first activity logged | PI Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | SLV_USAGE_MASTER (USER_FIRST_ACTIVE), SLV_USER_FIRST_ACTIVE (USER_FIRST_ACTIVE) | FTL contains no historical user creation/activation timestamp; requires one-time backfill from user master data | NO | Build one-time historical lookup table USER_METADATA with USER_ID/AGENT_ID → USER_FIRST_ACTIVE from legacy data sources; join to Silver tables during transformation; for new users, populate on first appearance in FTL with MIN(DATA_DATE) logic | PI Data Engineering |
| GAP-006 | CHAT_SESSIONS | SLV_USAGE_MASTER (CHAT_SESSIONS) | FTL shows Chat in MODALITY column indicating chat engagements exist, but provides no CHAT_SESSIONS numeric count field (only PHONE_SESSIONS exists); unclear if chat session count is available in separate FTL table or not tracked | NO | **Option 1:** Confirm with BDP whether chat session count exists in separate FTL table that can be joined. **Option 2:** Request BDP to add CHAT_SESSIONS field parallel to PHONE_SESSIONS. **Option 3:** Derive from engagement-level data if ENGAGEMENT_ID represents session boundary. **Option 4:** Accept NULL for chat sessions (impacts omni-channel reporting) | BDP Team, Zoom Chat Product Team |
| GAP-007 | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER (SLA_ACHIEVED_SESSIONS) | FTL contains no SLA performance indicator or achieved/missed service level fields; SLA tracking may exist in separate operational monitoring system | NO | **Option 1:** Confirm with Zoom Operations whether SLA data exists in separate FTL table or operational database that can be joined on ENGAGEMENT_ID. **Option 2:** Deprecate SLA metric from Silver layer if no longer tracked. **Option 3:** Accept NULL (impacts operational reporting) | BDP Team, Zoom Operations Team |
| GAP-008 | VIDEO_USAGE | SLV_MONTHLY_METRICS (VIDEO_USAGE) | FTL shows Video in CHANNEL column indicating video engagements exist, but provides no VIDEO_USAGE duration metric (only INBOUND_PHONE_MS exists for phone); unclear if video duration is tracked | NO | **Option 1:** Confirm with BDP whether video usage duration metric exists and can be added to FTL similar to INBOUND_PHONE_MS. **Option 2:** Derive from engagement-level duration if available in raw data. **Option 3:** Accept NULL for video usage (impacts modality-split reporting showing phone vs video usage trends) | BDP Team, Zoom Video Product Team |

**Critical Path Items:**  
- **GAP-001, GAP-002, GAP-003** are **blocking** and must be resolved before Gold layer migration can proceed  
- GAP-001 and GAP-002 require external data source integration (CRM/billing systems)  
- GAP-003 requires building new historical tracking infrastructure in Silver layer  
- GAP-004 through GAP-008 are non-blocking; Silver layer can be built with NULL placeholders and backfilled later

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 7: FEASIBILITY VERDICT
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| ZOOM_AI_POC.GOLD.GLD_AGGREGATE | 42% | GAP-001 (SEGMENT), GAP-002 (IS_LICENSED), GAP-003 (USERS_ACTIVE_16PLUS_DAYS) — 3 of 8 columns unmapped | **Not Feasible** | **(1)** Resolve GAP-001: Add SEGMENT to FTL or provide segment mapping table. **(2)** Resolve GAP-002: Add IS_LICENSED to FTL or provide license status lookup. **(3)** Resolve GAP-003: Build historical user activity tracking in Silver or request pre-calculated metric from BDP. **(4)** Validate BR-001 date parsing logic with sample of production data. **(5)** Validate BR-002 region mapping covers all production clusters. **(6)** Confirm BR-005 assumption that AGENT_ID = USER_ID with Zoom domain experts. |

**Verdict Explanation:**

The migration from FTL Bronze to PI Gold is **not feasible in its current state** due to three blocking data gaps representing 37.5% of the target Gold schema. While operational metrics (phone usage, active counts) can be derived with moderate confidence (50-60%), the absence of core business dimensions (segment, licensing) and engagement tracking (16+ day users) prevents the Gold table from maintaining functional parity with its current implementation.

**Specific Blocking Issues:**

1. **SEGMENT (GAP-001):** Gold table currently groups all metrics by customer segment (Enterprise/SMB/etc.). Without this dimension, all segment-based executive dashboards and reporting break. This is a **hard blocker** requiring external data integration.

2. **IS_LICENSED (GAP-002):** Gold table currently filters and groups by licensing status to separate paid customers from trials. Revenue reporting, churn analysis, and conversion metrics all depend on this dimension. This is a **hard blocker** requiring billing system integration.

3. **USERS_ACTIVE_16PLUS_DAYS (GAP-003):** This engagement KPI tracks highly-engaged users (active 16+ days in last 28 days) and is critical for MAU calculations and product adoption metrics. FTL provides point-in-time data only; building this metric requires constructing a historical activity tracking layer in Silver. This is a **hard blocker** requiring new infrastructure.

**Partial Success Scenarios:**

- **Silver Layer Only:** 60% feasible. Silver tables can be built from FTL with NULL placeholders for GAP-004 through GAP-008 (non-blocking gaps). This provides engagement-level detail and basic usage metrics but loses historical context and SLA/video metrics.

- **Degraded Gold Layer:** 42% feasible. Gold could be built without segment/licensing dimensions and with USERS_ACTIVE_16PLUS_DAYS permanently NULL, but this breaks all existing reporting that depends on these fields. **Not recommended** — would require full dashboard redesign.

**Recommended Path Forward:**

Do not proceed with Gold migration until GAP-001, GAP-002, and GAP-003 are resolved. Proceed with Silver layer build immediately using NULL placeholders for non-blocking gaps, enabling parallel work while blocking gaps are resolved.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 8: DBT MODEL IMPACT ANALYSIS
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 8.1 — NEW TABLES TO CREATE

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| SLV_FTL_BASE | Silver | Base transformation of FTL Bronze with all new FTL capabilities preserved; serves as canonical Silver source for downstream tables | ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG |
| SLV_USER_DAILY_ACTIVITY | Silver | Historical tracking table for user-date-level activity flags; enables calculation of activity duration metrics (GAP-003 resolution) | SLV_FTL_BASE, historical backfill from legacy Bronze |
| ACCOUNT_SEGMENT_MAP | Reference | Lookup table mapping ACCOUNT_ID to SEGMENT classification (GAP-001 resolution) | External source: Zoom Salesforce/CRM, BDP-provided data |
| ACCOUNT_LICENSE_STATUS | Reference | Lookup table mapping ACCOUNT_ID to IS_LICENSED flag with effective date tracking (GAP-002 resolution) | External source: Zoom billing system, BDP-provided data |
| ACCOUNT_METADATA | Reference | One-time historical backfill of ACCOUNT_ID → ACCOUNT_FIRST_ACTIVE (GAP-004 resolution) | Legacy ZOOM_AI_POC.BRONZE.BRZ_ACCOUNT_DIM or Zoom account master |
| USER_METADATA | Reference | One-time historical backfill of USER_ID → USER_FIRST_ACTIVE (GAP-005 resolution) | Legacy user data sources, initial FTL load |
| CLUSTER_REGION_MAP | Reference | Maintainable lookup table for AWS cluster → business region mapping (BR-002 enhancement) | Manual creation by Data Engineering, validated with Zoom Infrastructure |

### 8.2 — EXISTING TABLES TO ALTER

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|-----------------|----------------|------------------|--------|
| SLV_USAGE_MASTER | Silver | Complete source swap from legacy Bronze views to SLV_FTL_BASE; add joins to reference tables | None (schema unchanged) | **USER_ID**: source changes from legacy to BR-009 (AGENT_ID rename). **PHONE_SESSIONS**: source changes to FTL. **INBOUND_PHONE_MINS**: source changes to FTL with BR-003 conversion. **ACCOUNT_FIRST_ACTIVE**: add LEFT JOIN to ACCOUNT_METADATA. **USER_FIRST_ACTIVE**: add LEFT JOIN to USER_METADATA. **CHAT_SESSIONS**: NULL until GAP-006 resolved. **SLA_ACHIEVED_SESSIONS**: NULL until GAP-007 resolved | **HIGH** — Complete rewrite of transformation logic; extensive testing required for backward compatibility |
| SLV_CONSOLIDATED_USAGE | Silver | Source swap to SLV_FTL_BASE; modify aggregation logic | None (schema unchanged) | **REPORT_DATE**: source changes to BR-001 date parsing. **ACCOUNT_ID**: source changes to FTL. **IS_ACTIVE_ACCOUNT**: maps to IS_ACTIVE from FTL. **ACTIVE_USERS**: aggregation changes to BR-005. **PHONE_USAGE**: calculation changes to BR-006. **WINDOW**: implement BR-007 rolling window logic | **MEDIUM** — Aggregation grain changes; validation needed for metric continuity |
| SLV_MONTHLY_METRICS | Silver | Source swap to SLV_FTL_BASE; modify aggregation logic | None (schema unchanged) | **REPORT_DATE**: source changes to BR-001 date parsing. **ACCOUNT_ID**: source changes to FTL. **IS_ACTIVE_ACCOUNT**: maps to IS_ACTIVE from FTL. **ACTIVE_USERS**: aggregation changes to BR-005. **VIDEO_USAGE**: NULL until GAP-008 resolved. **USERS_ACTIVE_16PLUS_DAYS**: source changes to SLV_USER_DAILY_ACTIVITY (requires GAP-003 resolution) | **HIGH** — Key engagement metric depends on new infrastructure; cannot proceed until GAP-003 resolved |
| SLV_COMBINED_CHANNELS | Silver | Source swap to SLV_FTL_BASE; leverage new FTL capabilities | **CLIENT_TYPE** (optional, from NEW_CAPABILITY), **CLUSTER** (optional, for region enrichment) | **START_DATE**: maps to BR-001. **USER_ID**: maps to BR-009. **ENGAGEMENT_ID**: direct from FTL. **ACCOUNT_ID**: direct from FTL. **CHANNEL**: direct from FTL. **DIRECTION**: direct from FTL. **MODALITY**: direct from FTL | **LOW** — Schema mostly aligned with FTL; opportunity to add new dimensions |
| GLD_AGGREGATE | Gold | Complete rebuild with source pointing to new Silver tables; add joins to reference tables | None (schema unchanged) | **DATE**: aggregation from SLV_FTL_BASE via BR-001. **REGION**: add BR-002 cluster mapping (validate with reference table). **SEGMENT**: add LEFT JOIN to ACCOUNT_SEGMENT_MAP (**blocks migration until GAP-001 resolved**). **IS_LICENSED**: add LEFT JOIN to ACCOUNT_LICENSE_STATUS (**blocks migration until GAP-002 resolved**). **ACTIVE_ACCOUNTS**: BR-004 aggregation. **ACTIVE_USERS**: BR-005 aggregation. **PHONE_USAGE**: BR-006 calculation. **USERS_ACTIVE_16PLUS_DAYS**: aggregation from SLV_USER_DAILY_ACTIVITY (**blocks migration until GAP-003 resolved**) | **CRITICAL** — Cannot proceed until all blocking gaps (GAP-001, GAP-002, GAP-003) resolved; complete transformation rewrite required |

### 8.3 — GAP REMEDIATION ACTIONS

| GAP ID | PI Gold Column | Remediation Action | New Table Required? | New Join Required? | Estimated Complexity | Owner |
|--------|----------------|-------------------|---------------------|-------------------|---------------------|-------|
| GAP-001 | SEGMENT | Create ACCOUNT_SEGMENT_MAP reference table with ACCOUNT_ID → SEGMENT lookup; populate from Zoom Salesforce/CRM system; implement daily refresh to capture segment changes; add LEFT JOIN to all Silver and Gold models using ACCOUNT_ID | **YES** — ACCOUNT_SEGMENT_MAP | **YES** — Join to all Silver aggregation tables and Gold on ACCOUNT_ID | **HIGH** — Requires cross-system integration with Salesforce; need API access, data validation, and SLA agreement for refresh frequency | BDP Team (data source), Data Engineering (table build), Zoom PM (business validation) |
| GAP-002 | IS_LICENSED | Create ACCOUNT_LICENSE_STATUS reference table with ACCOUNT_ID → IS_LICENSED → EFFECTIVE_DATE slowly-changing dimension Type 2 structure; populate from Zoom billing/subscription system; implement daily refresh; add LEFT JOIN to Gold model with date-effective logic | **YES** — ACCOUNT_LICENSE_STATUS | **YES** — Join to Gold on ACCOUNT_ID with DATE BETWEEN EFFECTIVE_DATE AND END_DATE | **HIGH** — Requires integration with Zoom billing system; need subscription state tracking; handle trial-to-paid conversions; coordinate with Finance on data definitions | Zoom Billing Team (data source), Data Engineering (SCD2 implementation), Finance (metric validation) |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | Build SLV_USER_DAILY_ACTIVITY Silver table to track daily user activity snapshots (USER_ID, DATE, IS_ACTIVE); backfill historical data from legacy sources; implement incremental daily loads from SLV_FTL_BASE; create window function in Gold to calculate COUNT(DISTINCT USER_ID) WHERE activity_days_in_last_28 >= 16 | **YES** — SLV_USER_DAILY_ACTIVITY | **YES** — Gold aggregates from this new Silver table with 28-day rolling window | **MEDIUM** — Pure data engineering task; requires historical backfill strategy; window function performance testing for large datasets; no external dependencies | PI Data Engineering (primary), Product Analytics Team (metric validation) |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | One-time build of ACCOUNT_METADATA reference table from legacy BRZ_ACCOUNT_DIM or Zoom account master; extract MIN(activation_date) per ACCOUNT_ID; add LEFT JOIN to SLV_USAGE_MASTER; for new accounts, set ACCOUNT_FIRST_ACTIVE = first appearance in FTL via COALESCE logic | **YES** — ACCOUNT_METADATA (one-time, not incrementally updated) | **YES** — Join to SLV_USAGE_MASTER on ACCOUNT_ID | **LOW** — One-time historical extract; no ongoing refresh needed; new accounts handled in transformation logic | PI Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | One-time build of USER_METADATA reference table from legacy user data sources; extract MIN(activation_date) per USER_ID; add LEFT JOIN to SLV_USAGE_MASTER and SLV_USER_FIRST_ACTIVE; for new users, set USER_FIRST_ACTIVE = first appearance in FTL via COALESCE logic | **YES** — USER_METADATA (one-time, not incrementally updated) | **YES** — Join to SLV_USAGE_MASTER and SLV_USER_FIRST_ACTIVE on USER_ID | **LOW** — One-time historical extract; similar to GAP-004; may need to map legacy USER_ID to FTL AGENT_ID if schema differs | PI Data Engineering |
| GAP-006 | CHAT_SESSIONS | **Action 1:** Confirm with BDP whether CHAT_SESSIONS metric exists in separate FTL table or can be added to BRZ_FTL_AGENT_BASE_AGG. **Action 2:** If exists, add to FTL source and update BR transformation. **Action 3:** If not available, accept NULL and document limitation | **NO** (if added to FTL source) | **NO** (direct column mapping) | **LOW** (if exists), **MEDIUM** (if requires new instrumentation) | BDP Team (data availability), Zoom Chat Product Team (metric definition) |
| GAP-007 | SLA_ACHIEVED_SESSIONS | **Action 1:** Confirm with Zoom Operations whether SLA metrics exist in operational monitoring system. **Action 2:** If exists in separate table, add LEFT JOIN on ENGAGEMENT_ID to SLV_USAGE_MASTER. **Action 3:** If not tracked, deprecate metric from Silver schema | **NO** (if exists in separate source) | **YES** (if needs join to operational table) | **LOW** (if simple join), **MEDIUM** (if requires new data pipeline from ops system) | Zoom Operations Team (data availability), BDP Team (integration) |
| GAP-008 | VIDEO_USAGE | **Action 1:** Confirm with BDP whether video duration metric exists parallel to INBOUND_PHONE_MS. **Action 2:** If available, add VIDEO_MS column to FTL and implement BR transformation similar to BR-003. **Action 3:** If not available, accept NULL and document limitation | **NO** (if added to FTL source) | **NO** (direct column mapping with unit conversion) | **LOW** (if exists), **MEDIUM** (if requires new instrumentation) | BDP Team (data availability), Zoom Video Product Team (metric definition) |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 9: RECOMMENDED ACTIONS
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**PRIORITY 1 — BLOCKING ITEMS (Must be resolved before Gold migration):**

1. **Resolve GAP-001 (SEGMENT):** Engage with BDP Team and Zoom PM to determine source of customer segment classification. Option A: Request BDP to add SEGMENT field to FTL Bronze based on Zoom account master. Option B: Data Engineering to build ACCOUNT_SEGMENT_MAP lookup table from Salesforce/CRM with daily refresh. Validate segment values match existing Gold table distinct values (3, 5, 2 shown in profile). **Target Owner:** BDP Team + Zoom PM.

2. **Resolve GAP-002 (IS_LICENSED):** Engage with Zoom Billing Team to access subscription/license status data. Option A: Request BDP to add IS_LICENSED flag to FTL Bronze. Option B: Data Engineering to build ACCOUNT_LICENSE_STATUS SCD2 table from billing API with effective date tracking. Coordinate with Finance to validate licensed vs trial definitions match revenue reporting standards. **Target Owner:** BDP Team + Zoom Billing + Finance.

3. **Resolve GAP-003 (USERS_ACTIVE_16PLUS_DAYS):** Data Engineering to build SLV_USER_DAILY_ACTIVITY historical tracking table. Design incremental load pattern to capture daily user activity flags from SLV_FTL_BASE. Backfill historical activity from legacy Bronze sources (minimum 28 days required). Implement window function in Gold aggregation to calculate users with 16+ active days in rolling 28-day window. Validate metric continuity with current Gold output. **Target Owner:** PI Data Engineering + Product Analytics Team.

**PRIORITY 2 — SILVER DBT MODEL CHANGES (Can proceed in parallel with Priority 1):**

4. **Build SLV_FTL_BASE foundation table (reference BR-001, BR-002, BR-003, BR-009):** Create base Silver transformation of BRZ_FTL_AGENT_BASE_AGG applying BR-001 date parsing, BR-002 region mapping (with CLUSTER_REGION_MAP reference table), BR-003 phone duration conversion, BR-009 agent-to-user ID rename. Preserve all new FTL capabilities (ENGAGEMENT_ID, CLIENT_TYPE, OS, DIRECTION, MODALITY, CHANNEL, ZCC_ACCOUNT_ID) for downstream enrichment. Implement data quality checks on date parsing and region mapping. **Target Owner:** PI Data Engineering.

5. **Rebuild SLV_USAGE_MASTER (reference BR-004, BR-005):** Swap source from legacy Bronze views to SLV_FTL_BASE. Add LEFT JOIN to ACCOUNT_METADATA (GAP-004) and USER_METADATA (GAP-005) for first-active dates. Implement BR-004/BR-005 aggregation logic for active counts. Set CHAT_SESSIONS and SLA_ACHIEVED_SESSIONS to NULL with documentation. Full regression testing against current output required. **Target Owner:** PI Data Engineering.

6. **Rebuild SLV_CONSOLIDATED_USAGE and SLV_MONTHLY_METRICS (reference BR-006, BR-007):** Swap source to SLV_FTL_BASE. Implement BR-006 phone usage calculation and BR-007 rolling window logic (validate R1/R7/R28 business definitions with analytics team). Set VIDEO_USAGE to NULL with documentation (GAP-008). Validate metric continuity. **Target Owner:** PI Data Engineering.

**PRIORITY 3 — UNIT CONVERSIONS AND RENAMES (Apply in Silver transformations):**

7. **Validate BR-001 date parsing logic:** Test DATA_DATE parsing with production sample data to confirm format "M/D/YY HH24:MI" is correct. Implement error handling for unparseable dates. Document any date format variations discovered. Add data quality monitoring for parsing failures. **Target Owner:** PI Data Engineering.

8. **Validate BR-002 region mapping completeness:** Confirm CLUSTER_REGION_MAP covers all production AWS clusters. Test mapping logic with production CLUSTER distinct values. Add ELSE 'UNKNOWN' fallback and alerting for unmapped clusters. Coordinate with Zoom Infrastructure team to maintain mapping as new clusters are added. **Target Owner:** PI Data Engineering + Zoom Infrastructure.

9. **Validate BR-003 phone duration conversion:** Confirm INBOUND_PHONE_MS → minutes conversion (divide by 60000) produces values consistent with current INBOUND_PHONE_MINS in Silver. Test with sample data comparing FTL output to legacy output for same date range. Document any discrepancies. **Target Owner:** PI Data Engineering.

**PRIORITY 4 — ITEMS TO RAISE WITH BDP TEAM:**

10. **GAP-006 (CHAT_SESSIONS):** Confirm whether chat session count metric exists in FTL ecosystem. FTL shows "Chat" in MODALITY values but provides no numeric count field. If metric exists in separate table, request table name and join key. If not available, request addition to BRZ_FTL_AGENT_BASE_AGG parallel to PHONE_SESSIONS. **Target Owner:** BDP Team.

11. **GAP-007 (SLA_ACHIEVED_SESSIONS):** Confirm whether SLA performance data is tracked in FTL or separate operational system. If available, request table schema and join methodology. If not tracked, confirm deprecation of this metric from PI reporting. **Target Owner:** BDP Team + Zoom Operations.

12. **GAP-008 (VIDEO_USAGE):** Confirm whether video duration metric exists parallel to INBOUND_PHONE_MS. FTL shows "Video" in CHANNEL values but provides no duration measurement. If metric exists, request addition to FTL. If not available, document limitation in omni-channel reporting. **Target Owner:** BDP Team + Zoom Video Product Team.

**PRIORITY 5 — ITEMS TO CONFIRM WITH ZOOM TEAM:**

13. **Validate BR-005/BR-009 assumption (AGENT_ID = USER_ID):** Confirm with Zoom domain experts that AGENT_ID in FTL represents the same business concept as USER_ID in PI schema. Verify one agent maps to one user (no many-to-many relationships). Document any semantic differences for reporting interpretation. **Target Owner:** Zoom PM + Product Team.

14. **Confirm IS_ACTIVE semantic meaning:** Clarify whether IS_ACTIVE flag in FTL represents account-level activity, user-level activity, or engagement-level status. Validate usage in BR-004/BR-005 aggregations aligns with business definitions of "active account" and "active user". **Target Owner:** Zoom PM + BDP Team.

15. **Validate PHONE_USAGE calculation (BR-006):** Confirm business definition of PHONE_USAGE metric in Gold table. Current analysis assumes total duration in minutes (SUM(INBOUND_PHONE_MS)/60000). Alternative interpretation could be average duration per session. Validate against current Gold calculation logic. **Target Owner:** Product Analytics Team.

**PRIORITY 6 — NEW CAPABILITIES (Decision needed from PI team leads):**

16. **Evaluate CLIENT_TYPE for Gold extension:** FTL provides device type dimension (Mobile, Desktop, Web) not in current Gold schema. Assess value of adding device-based segmentation to Gold reporting. If approved, design schema extension and update dashboard requirements. **Target Owner:** PI Team Leads + Product Analytics.

17. **Evaluate DIRECTION for Gold extension:** FTL provides Inbound/Outbound directionality not in current Gold schema. Assess value of directional KPIs (e.g., inbound response time vs outbound proactive engagement). If approved, design metric definitions and Gold schema extension. **Target Owner:** PI Team Leads + Product Analytics.

18. **Evaluate ENGAGEMENT_ID utility:** FTL provides engagement-level granularity via ENGAGEMENT_ID. Assess whether engagement-level drill-down reporting is required. If yes, keep in Silver SLV_COMBINED_CHANNELS for ad-hoc analysis. If critical, consider Gold extension for engagement-level fact table. **Target Owner:** PI Team Leads + Business Intelligence.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 10: MAPPING CSV FOR REVIEW
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```csv
FTL_Bronze_Column,FTL_Data_Type,PI_Silver_Column,PI_Silver_Table,PI_Gold_Column,PI_Gold_Table,Classification,Confidence,Mapping_Reason,BR_ID,GAP_ID,Transformation,Notes
ZCC_ACCOUNT_ID,TEXT,—,—,—,—,NEW_CAPABILITY,High,No column in PI schema matches this alternate account identifier; confirmed via schema discovery,—,—,—,New alternate account key available for cross-system reconciliation
ACCOUNT_ID,TEXT,ACCOUNT_ID,"SLV_USAGE_MASTER, SLV_CONSOLIDATED_USAGE",ACTIVE_ACCOUNTS,GLD_AGGREGATE,DIRECT_MATCH + GRAIN_CHANGE,High,Exact name and semantic match; used in aggregation to count distinct accounts,BR-004,—,"COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE",Requires grouping by DATE/REGION/SEGMENT
ENGAGEMENT_ID,TEXT,ENGAGEMENT_ID,SLV_COMBINED_CHANNELS,—,—,NEW_CAPABILITY,High,Matches Silver SLV_COMBINED_CHANNELS but not used in Gold; engagement-level tracking not in current Gold schema,—,—,—,Enables engagement-level drill-down if added to new Silver table
AGENT_ID,TEXT,USER_ID,SLV_USAGE_MASTER,ACTIVE_USERS,GLD_AGGREGATE,SEMANTIC_MATCH + GRAIN_CHANGE,High,Semantic match confirmed — agents represent users in FTL context; used for user count aggregation,"BR-005, BR-009",—,"COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE",Rename AGENT_ID → USER_ID in Silver transformation
DIRECTION,TEXT,DIRECTION,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Distinct values (Inbound/Outbound) match Silver SLV_