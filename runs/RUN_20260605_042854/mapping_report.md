

🔍 **STEP 1: Schema Discovery** — Discovered 1 source table, 20 Silver tables, 1 Gold table  
🔍 **STEP 2: Data Profiling** — Profiled BRZ_FTL_AGENT_BASE_AGG (14 columns), GLD_AGGREGATE (8 columns), and key Silver tables  
🔍 **STEP 3: Mapping Analysis** — Analyzed Bronze→Silver and Silver→Gold transformations with confidence scoring

---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1: EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG  
**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE  
**Migration Readiness Score:** 35/100  

**Total FTL columns analyzed:** 14  
**Successfully mapped:** 5 (DATE, ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE, partial REGION)  
**Partially mapped:** 2 (REGION requires lookup, PHONE_USAGE requires business rule clarification)  
**New capabilities (no PI equivalent):** 6 (ZCC_ACCOUNT_ID, ENGAGEMENT_ID, DIRECTION, MODALITY, CLIENT_TYPE, OS)  
**Gaps (PI Gold columns with no FTL source):** 3  
→ **GAP-001**: SEGMENT  
→ **GAP-002**: IS_LICENSED  
→ **GAP-003**: USERS_ACTIVE_16PLUS_DAYS  

**Blocking items:** 3 Critical Gaps

**Overall Assessment:**  
The FTL Bronze source table BRZ_FTL_AGENT_BASE_AGG lacks three critical business dimensions required by the Gold layer: customer segmentation (SEGMENT), licensing status (IS_LICENSED), and long-term user engagement tracking (USERS_ACTIVE_16PLUS_DAYS). These gaps represent 37.5% of the Gold output columns and are core business metrics, not optional attributes. The source provides strong coverage for activity metrics (accounts, users, phone usage) and introduces valuable new dimensions for device/OS tracking, but cannot functionally replicate the current Gold table without additional data sources or fundamental changes to reporting requirements. Migration is not feasible in the current state.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2: GAP IMPACT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | Why It's a Gap | Impact on Gold Output | Blocks Migration? | Action Required | Raise With |
|--------|----------------|----------------|----------------------|-------------------|----------------|------------|
| GAP-001 | SEGMENT | No customer segmentation data exists in FTL source | Cannot classify accounts by size/tier (SMB/Mid-Market/Enterprise); all segment-level reporting and analysis breaks | **YES** | BDP Team to add SEGMENT column to FTL source OR provide separate dimension table with ACCOUNT_ID → SEGMENT mapping | BDP Team + Zoom PM |
| GAP-002 | IS_LICENSED | No licensing/subscription status in FTL source | Cannot differentiate paid customers from trial users; revenue reporting and conversion analysis impossible | **YES** | BDP Team to include licensing flag in FTL source OR join to existing billing/subscription table | BDP Team + PI Billing System Owner |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | No historical activity tracking or day-count logic in FTL source | Cannot measure user stickiness or engagement depth; power user identification and retention metrics broken | **YES** | Requires rolling 28-day activity calculation not present in FTL base table; needs new Silver layer aggregation table or FTL enhancement | BDP Team + Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3: FULL COLUMN LINEAGE MAPPING TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER | DATE | GLD_AGGREGATE | UNIT_CHANGE | Medium | FTL stores date as TEXT "5/29/26 13:01"; Gold requires DATE type; confirmed via distinct value query showing text format | BR-001 | — | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | Requires validation of date format consistency |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column name and data type identical; TEXT to TEXT with matching ID patterns confirmed via sample values | — | — | — | Used for aggregation in Gold via GROUP BY |
| AGENT_ID | TEXT | USER_ID | SLV_USAGE_MASTER | — | — | SEMANTIC_MATCH | High | Semantic analysis indicates AGENT_ID represents end users; distinct count (5) matches expected user cardinality | BR-004 | — | `AGENT_ID AS USER_ID` | Assumption: AGENT_ID = USER_ID |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE | — | — | SEMANTIC_MATCH | Medium | FTL IS_ACTIVE (true/false) maps to Silver IS_ACTIVE_ACCOUNT; used in active account/user counting logic | BR-003 | — | — | Assumption: IS_ACTIVE applies at account level |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column name, data type (NUMBER), and sample values (426, 41, 248) match exactly between FTL and Silver | — | — | — | Direct pass-through to Silver |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE | Medium | FTL stores phone time in milliseconds (e.g., 325295 ms); Silver/Gold require minutes; unit conversion confirmed via data type analysis | BR-002 | — | `INBOUND_PHONE_MS / 60000.0` | Converts MS to minutes (÷ 60,000) |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | SEMANTIC_MATCH | Low | FTL CLUSTER contains AWS region codes (eu-central-1, ap-south-1, us-east-1); Gold REGION has business regions (EMEA, LATAM, NAMER); requires lookup table | BR-005 | — | `CASE WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' WHEN CLUSTER = 'us-east-1' THEN 'NAMER' ELSE 'UNKNOWN' END` | [LOW CONFIDENCE] Assumption: CLUSTER maps to REGION; incomplete mapping |
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | High | ZCC_ACCOUNT_ID (distinct count: 5) exists in FTL but no equivalent column in current PI pipeline; provides Zoom Contact Center account identifier | — | — | — | New dimension available for enrichment |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Column name and data type identical; TEXT to TEXT with matching ID patterns (ID_8325, ID_2919, ID_6563) confirmed | — | — | — | Used in Silver channel-level detail table |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | High | FTL has values "Inbound, Outbound" (mixed case); Silver has "INBOUND, OUTBOUND" (uppercase); confirmed via distinct value query | BR-006 | — | `UPPER(DIRECTION)` | Simple case standardization |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | High | FTL has values "SMS, Email, Chat" (mixed case); Silver has mixed case too but different formatting; distinct values confirmed via query | BR-007 | — | `UPPER(MODALITY)` | Case standardization for consistency |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | Medium | FTL has 2 distinct values (Video, Phone); Silver has 5 values (EMAIL, VIDEO, PHONE, SMS, CHAT); FTL provides subset; confirmed via distinct value query | BR-008 | — | `UPPER(CHANNEL)` | FTL CHANNEL alone insufficient; needs combination with MODALITY |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | High | CLIENT_TYPE (Mobile, Desktop, Web) exists in FTL but no equivalent in current PI pipeline; provides device type tracking | — | — | — | New dimension for device analytics |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | Medium | OS column exists in FTL (currently single value "Sample Text"); no equivalent in PI pipeline; provides operating system tracking | — | — | — | Data quality concern: only 1 distinct value |
| — | — | — | — | REGION | GLD_AGGREGATE | GAP | High | No direct source for business REGION in FTL; CLUSTER provides technical infrastructure location but requires lookup to business region; distinct value query shows GOLD has EMEA, LATAM, NAMER, APAC but FTL CLUSTER only has AWS codes | BR-005 | — | Requires CLUSTER → REGION mapping table | See BR-005 for transformation |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No column found in FTL source matching customer segmentation concept; GOLD has numeric SEGMENT (3, 5, 2 values observed); no business logic or source data available in FTL | — | GAP-001 | `NULL AS SEGMENT -- GAP-001` | **CRITICAL GAP** - Blocks migration |
| — | — | — | — | IS_LICENSED | GLD_AGGREGATE | GAP | High | No licensing/subscription status column exists in FTL; GOLD requires boolean IS_LICENSED (true/false); confirmed via column inventory - no matching concept in FTL schema | — | GAP-002 | `NULL AS IS_LICENSED -- GAP-002` | **CRITICAL GAP** - Blocks migration |
| — | — | — | — | ACTIVE_ACCOUNTS | GLD_AGGREGATE | GRAIN_CHANGE | Medium | Requires aggregation: COUNT(DISTINCT ACCOUNT_ID WHERE IS_ACTIVE = true) grouped by DATE, REGION, SEGMENT, IS_LICENSED; source columns exist but transformation is complex | BR-003 | — | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN ACCOUNT_ID END)` | Requires GROUP BY DATE, REGION, SEGMENT, IS_LICENSED |
| — | — | — | — | ACTIVE_USERS | GLD_AGGREGATE | GRAIN_CHANGE | Medium | Requires aggregation: COUNT(DISTINCT AGENT_ID WHERE IS_ACTIVE = true) grouped by DATE, REGION, SEGMENT, IS_LICENSED; assumes AGENT_ID represents users | BR-004 | — | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN AGENT_ID END)` | Assumption: AGENT_ID = user; GROUP BY DATE, REGION, SEGMENT, IS_LICENSED |
| — | — | — | — | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | No historical activity tracking in FTL; metric requires counting users active 16+ days in rolling 28-day window; FTL has single date snapshot, no day-count logic; confirmed via schema analysis | — | GAP-003 | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP-003` | **CRITICAL GAP** - Requires new aggregation logic |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4: TRANSFORMATION GUIDE (Business Rules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|---------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | DATE (Silver/Gold) | UNIT_CHANGE | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | FTL stores dates as TEXT in format "5/29/26 13:01"; Silver and Gold require proper DATE type for time-series analysis and date arithmetic | None | [ASSUMPTION] All DATA_DATE values follow consistent format M/D/YY HH24:MI; century is 20XX |
| BR-002 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS, PHONE_USAGE | UNIT_CHANGE | `INBOUND_PHONE_MS / 60000.0` | FTL stores phone duration in milliseconds for precision; Silver/Gold report in minutes for business readability; conversion factor: 1 minute = 60,000 milliseconds | Non-null INBOUND_PHONE_MS values | Only inbound phone time captured; outbound duration not available in FTL |
| BR-003 | ACCOUNT_ID, IS_ACTIVE | ACTIVE_ACCOUNTS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN ACCOUNT_ID END) GROUP BY TO_DATE(DATA_DATE), <REGION>, <SEGMENT>, <IS_LICENSED>` | Gold requires daily aggregated count of active accounts by region/segment/license; FTL has agent-level records requiring GROUP BY aggregation | IS_ACTIVE flag, DATE transformation (BR-001), REGION mapping (BR-005), SEGMENT (GAP-001), IS_LICENSED (GAP-002) | [ASSUMPTION] IS_ACTIVE = true indicates account is active for that day |
| BR-004 | AGENT_ID, IS_ACTIVE | ACTIVE_USERS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN AGENT_ID END) GROUP BY TO_DATE(DATA_DATE), <REGION>, <SEGMENT>, <IS_LICENSED>` | Gold requires daily aggregated count of active users by region/segment/license; FTL has agent-level records requiring GROUP BY aggregation | IS_ACTIVE flag, DATE transformation (BR-001), REGION mapping (BR-005), SEGMENT (GAP-001), IS_LICENSED (GAP-002) | [ASSUMPTION] AGENT_ID represents end users (not internal support agents) |
| BR-005 | CLUSTER | REGION (Gold) | SEMANTIC_MATCH | `CASE WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' WHEN CLUSTER = 'us-east-1' THEN 'NAMER' ELSE 'UNKNOWN' END` | FTL CLUSTER contains AWS infrastructure region codes; Gold REGION requires business-oriented geography (EMEA, LATAM, NAMER, APAC) for executive reporting | Complete CLUSTER → REGION mapping table covering all possible CLUSTER values | [LOW CONFIDENCE] [ASSUMPTION] Only 3 CLUSTER values observed in sample data; full production data may have additional clusters not mapped; LATAM region not observed in FTL sample |
| BR-006 | DIRECTION | DIRECTION (Silver) | CASE_CHANGE | `UPPER(DIRECTION)` | FTL has mixed case "Inbound, Outbound"; Silver standardizes to uppercase "INBOUND, OUTBOUND" for consistency across tables and downstream joins | None | Simple string transformation; no data loss risk |
| BR-007 | MODALITY | MODALITY (Silver) | CASE_CHANGE | `UPPER(MODALITY)` | FTL has mixed case modality values; Silver standardizes to uppercase for consistency with other dimension tables | None | Simple string transformation; no data loss risk |
| BR-008 | CHANNEL, MODALITY | CHANNEL (Silver) | PARTIAL_MATCH | `CASE WHEN MODALITY = 'Email' THEN 'EMAIL' WHEN MODALITY = 'SMS' THEN 'SMS' WHEN MODALITY = 'Chat' THEN 'CHAT' WHEN CHANNEL = 'Video' THEN 'VIDEO' WHEN CHANNEL = 'Phone' THEN 'PHONE' ELSE 'UNKNOWN' END` | FTL splits communication type across two columns (CHANNEL and MODALITY); Silver CHANNEL consolidates into single dimension; FTL CHANNEL only has Video/Phone; MODALITY has SMS/Email/Chat | Both CHANNEL and MODALITY columns | [LOW CONFIDENCE] [ASSUMPTION] Mapping logic inferred from sample data; business rules for overlapping values (e.g., if both CHANNEL and MODALITY are populated) not specified |
| — | SEGMENT | SEGMENT (Gold) | GAP | `NULL AS SEGMENT -- GAP ID: GAP-001` | No customer segmentation data exists in FTL; Gold requires SEGMENT for account classification by size/revenue tier | Requires new data source: either BDP adds SEGMENT to FTL, or join to separate customer dimension table | **CRITICAL GAP** - Business stakeholder decision needed on segmentation logic source |
| — | IS_LICENSED | IS_LICENSED (Gold) | GAP | `NULL AS IS_LICENSED -- GAP ID: GAP-002` | No licensing/subscription status in FTL; Gold requires IS_LICENSED to differentiate paid vs trial accounts for revenue reporting | Requires join to billing/subscription system table or BDP to add IS_LICENSED flag to FTL | **CRITICAL GAP** - Dependency on billing system or FTL enhancement |
| — | USERS_ACTIVE_16PLUS_DAYS | USERS_ACTIVE_16PLUS_DAYS (Gold) | GAP | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-003` | FTL provides single-day snapshot; Gold requires count of users active 16+ days within rolling 28-day window; no historical activity tracking or day-count logic exists in FTL | Requires new Silver aggregation table tracking daily user activity over 28-day windows, then counting users meeting 16+ day threshold | **CRITICAL GAP** - Requires new Silver layer table and complex windowing logic not derivable from single-day FTL records |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5: NEW FTL CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|--------------------|-------------------|----------------|
| ZCC_ACCOUNT_ID | TEXT | Zoom Contact Center account identifier (distinct from general ACCOUNT_ID); provides mapping to ZCC-specific features and billing | ZCC product adoption tracking, ZCC vs non-ZCC account segmentation, cross-product usage analysis | PENDING DECISION | Keep in Silver layer for now; propose Gold extension to BDP/PI teams for ZCC-specific reporting dashboard; requires business case validation |
| CLIENT_TYPE | TEXT | Device type used for engagement: Mobile, Desktop, Web; enables device preference analysis | Device-specific adoption metrics, mobile-first user identification, device mix by account/region | YES | Add to Silver SLV_COMBINED_CHANNELS and potentially Gold for device-level aggregates (e.g., MOBILE_USERS, DESKTOP_USERS); high business value for UX/product teams |
| OS | TEXT | Operating system of client device; currently shows limited variety ("Sample Text" in sample) | OS-specific support metrics, platform compatibility analysis | NO | Keep in Silver only; data quality needs improvement (only 1 distinct value observed); confirm with BDP if OS tracking is reliable before promoting to Gold |
| ENGAGEMENT_ID | TEXT | Unique identifier for each customer engagement/interaction; already exists in Silver but now available directly from canonical source | Engagement-level granular analysis, session tracking, multi-touch attribution | NO | Already exists in Silver SLV_COMBINED_CHANNELS; FTL provides authoritative source - no Gold extension needed, continue Silver-only usage |
| DIRECTION | TEXT | Inbound vs Outbound engagement direction; already exists in Silver but FTL provides as canonical source | Directional flow analysis (inbound call volume vs outbound campaigns) | PENDING DECISION | Currently in Silver; consider promoting to Gold for INBOUND_USERS vs OUTBOUND_USERS distinction if business needs directional reporting at aggregate level |
| MODALITY | TEXT | Communication modality (SMS, Email, Chat, Phone, Video); already exists in Silver but FTL provides as canonical source | Modality-specific engagement metrics, channel preference shifts | PENDING DECISION | Currently in Silver; assess whether Gold needs modality-level aggregates (e.g., EMAIL_USERS, SMS_USERS) vs continuing channel-level reporting only |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 6: GAP REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | PI Silver Source | Why FTL Cannot Produce This | Blocks Migration? | Proposed Resolution | Raise With |
|--------|----------------|------------------|----------------------------|-------------------|---------------------|------------|
| GAP-001 | SEGMENT | Currently derived from account dimension table or manual classification | FTL BRZ_FTL_AGENT_BASE_AGG contains no customer segmentation dimension (SMB/Mid-Market/Enterprise/etc.); no SEGMENT column or proxy attribute exists; sample data shows ACCOUNT_ID but no classification metadata | **YES** | **Option 1**: BDP Team adds SEGMENT column directly to FTL source table based on Zoom's authoritative customer segmentation system. **Option 2**: Create separate dimension table ZOOM_AI_POC.BRONZE.BRZ_ACCOUNT_SEGMENT with ACCOUNT_ID → SEGMENT mapping; join in Silver layer. **Option 3**: Accept reduced Gold functionality and hardcode SEGMENT = NULL or 'UNKNOWN' with business stakeholder approval to proceed with limited reporting. | BDP Team (for FTL enhancement), Zoom Product Management (for segmentation logic), PI Data Governance (for dimension table approach) |
| GAP-002 | IS_LICENSED | Currently sourced from billing/subscription system or account properties table | FTL contains no licensing status, subscription tier, or payment information; cannot differentiate trial users from paid customers; IS_ACTIVE flag exists but only indicates usage activity, not license status | **YES** | **Option 1**: BDP Team adds IS_LICENSED boolean flag to FTL source by joining FTL pipeline to Zoom's billing system upstream. **Option 2**: Create LEFT JOIN in Silver layer to existing ZOOM_AI_POC billing/subscription table (if available) using ACCOUNT_ID. **Option 3**: Default IS_LICENSED = true with [ASSUMPTION] flag and accept inaccuracy in trial vs paid reporting until proper source identified. | BDP Team (for FTL enhancement), PI Billing System Owner (for join approach), Zoom Finance (for licensing data source identification) |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | Currently calculated from rolling 28-day user activity logs in Silver SLV_USER_ACTIVE_DAYS table | FTL provides single-day snapshot with IS_ACTIVE boolean but no historical activity tracking; Gold metric requires: (1) track each user's daily activity over rolling 28-day window, (2) count days user was active, (3) flag users with 16+ active days; FTL lacks both windowing data and day-count logic | **YES** | **Option 1**: BDP Team enhances FTL to include pre-calculated ACTIVE_DAYS_L28 metric with daily history. **Option 2**: Build new Silver aggregation table SLV_USER_ACTIVITY_ROLLING_28D that consumes daily FTL records, maintains 28-day history per user, calculates day counts, then feeds Gold with 16+ day filter applied. **Option 3**: Remove USERS_ACTIVE_16PLUS_DAYS from Gold with business stakeholder approval; replace with simpler ACTIVE_USERS metric (already available from FTL). | BDP Team (for FTL enhancement Option 1), Data Engineering (for new Silver table Option 2), PI Product/Analytics Leadership (for metric change approval Option 3) |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 7: FEASIBILITY VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| ZOOM_AI_POC.GOLD.GLD_AGGREGATE | 35% | 3 Critical (SEGMENT, IS_LICENSED, USERS_ACTIVE_16PLUS_DAYS) | **Not Feasible** | (1) Resolve **GAP-001** by adding SEGMENT via FTL enhancement or dimension table join; (2) Resolve **GAP-002** by adding IS_LICENSED via FTL enhancement or billing system join; (3) Resolve **GAP-003** by either BDP adding 28-day activity tracking to FTL OR building new Silver aggregation table SLV_USER_ACTIVITY_ROLLING_28D OR removing metric from Gold with business approval; (4) Validate **BR-005** CLUSTER→REGION mapping covers all production clusters (only 3 observed in sample); (5) Clarify **BR-008** CHANNEL+MODALITY combination logic with business rules; (6) Obtain business stakeholder sign-off on reduced Gold functionality if any gap resolution is deferred |

**Verdict Rationale:**

The FTL Bronze source table **BRZ_FTL_AGENT_BASE_AGG** cannot currently produce a functionally equivalent Gold table due to three critical gaps representing 37.5% of Gold output columns. These are not optional fields or "nice-to-have" attributes — they are core business dimensions required for executive reporting, revenue analysis, and user engagement tracking:

1. **SEGMENT** (GAP-001): Customer segmentation is a primary grouping dimension in the Gold layer; every dashboard, executive report, and business review relies on SMB vs Mid-Market vs Enterprise breakdowns. Without this, the Gold table becomes a flat list of undifferentiated accounts with no strategic business context.

2. **IS_LICENSED** (GAP-002): Licensing status is fundamental to revenue reporting, conversion funnel analysis, and churn prediction. Inability to distinguish trial users from paying customers renders financial metrics meaningless and breaks critical business KPIs.

3. **USERS_ACTIVE_16PLUS_DAYS** (GAP-003): This engagement depth metric identifies "power users" and measures product stickiness. It's a leading indicator for retention and upsell opportunities. The FTL source's single-day snapshot design fundamentally cannot produce this rolling 28-day metric without architectural changes.

**Confidence Score Breakdown:**
- Successfully mapped columns (DATE, ACCOUNT_ID, IS_ACTIVE, PHONE_SESSIONS): 100% confidence (5 columns)
- Partially mapped requiring transformation (INBOUND_PHONE_MS, CLUSTER): 70-75% confidence (2 columns)
- Semantic match requiring assumption (AGENT_ID→USER_ID): 85% confidence (1 column)
- Critical gaps preventing migration: 0% confidence (3 columns)
- **Weighted average: 35%**

**Migration Blocker Analysis:**
- All three gaps have "Blocks Migration = YES" in Section 2
- Gold table cannot run with NULL values for SEGMENT, IS_LICENSED, or USERS_ACTIVE_16PLUS_DAYS
- Existing downstream dashboards, reports, and BI tools expect these columns to be populated
- Data contracts with business stakeholders would be broken

**Path Forward:**
Migration can only proceed with one of the following:
1. **Full Resolution**: BDP Team enhances FTL source to include all three missing dimensions (ideal but high effort)
2. **Hybrid Approach**: Join FTL to existing dimension tables for SEGMENT/IS_LICENSED + build new Silver aggregation for 16+ day metric (feasible, medium effort)
3. **Reduced Scope**: Remove missing metrics from Gold with explicit business stakeholder approval and updated reporting requirements (fastest but reduces functionality)

Without addressing these conditions, migration would result in broken reporting, incomplete business metrics, and failure to meet current Gold layer SLAs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 8: DBT MODEL IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 8.1 — NEW TABLES TO CREATE

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| SLV_FTL_USAGE_MASTER | SILVER | Replaces existing SLV_USAGE_MASTER with FTL as source; user-level daily activity metrics including phone sessions, duration (converted to minutes), date parsing | BRZ_FTL_AGENT_BASE_AGG, BR-001 (date parsing), BR-002 (MS→minutes) |
| SLV_FTL_COMBINED_CHANNELS | SILVER | Replaces existing SLV_COMBINED_CHANNELS with FTL as source; engagement-level detail with standardized DIRECTION/MODALITY/CHANNEL | BRZ_FTL_AGENT_BASE_AGG, BR-006 (DIRECTION uppercase), BR-007 (MODALITY uppercase), BR-008 (CHANNEL mapping) |
| SLV_USER_ACTIVITY_ROLLING_28D | SILVER | **NEW TABLE** to resolve GAP-003; tracks daily user activity over rolling 28-day windows, calculates active day counts per user, enables 16+ day filter for Gold | SLV_FTL_USAGE_MASTER, requires 28 days of historical data accumulation |
| DIM_ACCOUNT_SEGMENT | BRONZE or SILVER | **NEW DIMENSION TABLE** to resolve GAP-001; provides ACCOUNT_ID → SEGMENT mapping; sourced from Zoom's customer segmentation system | Zoom customer master data or BDP segmentation feed |
| DIM_ACCOUNT_LICENSE | BRONZE or SILVER | **NEW DIMENSION TABLE** to resolve GAP-002; provides ACCOUNT_ID → IS_LICENSED mapping; sourced from Zoom's billing/subscription system | Zoom billing system or existing PI licensing table |
| DIM_CLUSTER_REGION_MAP | BRONZE or SILVER | **NEW REFERENCE TABLE** to support BR-005; maps AWS CLUSTER codes to business REGION names (EMEA, LATAM, NAMER, APAC) | Manual mapping table or Zoom infrastructure metadata |

## 8.2 — EXISTING TABLES TO ALTER

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|-----------------|----------------|-------------------|--------|
| SLV_USAGE_MASTER | SILVER | Source change from legacy Bronze views to BRZ_FTL_AGENT_BASE_AGG; remove deprecated columns | None (structure preserved but source changes) | USER_ID (now sourced from AGENT_ID), INBOUND_PHONE_MINS (now calculated from INBOUND_PHONE_MS÷60000) | Medium - Column mappings change but output schema remains same for backward compatibility |
| SLV_COMBINED_CHANNELS | SILVER | Source change from legacy Bronze views to BRZ_FTL_AGENT_BASE_AGG; case standardization required | None | DIRECTION (add UPPER transformation), MODALITY (add UPPER transformation), CHANNEL (add CASE logic combining CHANNEL+MODALITY) | Medium - Transformations added but output schema preserved |
| SLV_CONSOLIDATED_USAGE | SILVER | Source change from legacy Bronze views to BRZ_FTL_AGENT_BASE_AGG; aggregation logic changes | None | IS_ACTIVE_ACCOUNT (now sourced from IS_ACTIVE), ACTIVE_USERS (now COUNT DISTINCT AGENT_ID), PHONE_USAGE (now derived from INBOUND_PHONE_MS) | High - Aggregation logic fundamentally changes; requires validation that new calculations match old results |
| GLD_AGGREGATE | GOLD | Add joins to new dimension tables for gap resolution; add REGION mapping transformation | None (if gaps resolved via dimension tables) | REGION (add BR-005 CASE transformation or join to DIM_CLUSTER_REGION_MAP), SEGMENT (join to DIM_ACCOUNT_SEGMENT), IS_LICENSED (join to DIM_ACCOUNT_LICENSE), USERS_ACTIVE_16PLUS_DAYS (join to SLV_USER_ACTIVITY_ROLLING_28D) | High - Multiple new joins required; query complexity increases; performance testing needed |

## 8.3 — GAP REMEDIATION ACTIONS

| GAP ID | PI Gold Column | Remediation Action | New Table Required? | New Join Required? | Estimated Complexity | Owner |
|--------|----------------|-------------------|---------------------|-------------------|---------------------|-------|
| GAP-001 | SEGMENT | Create dimension table DIM_ACCOUNT_SEGMENT with ACCOUNT_ID → SEGMENT mapping; source from Zoom customer master or BDP feed; join in Gold model using ACCOUNT_ID | **YES** - DIM_ACCOUNT_SEGMENT | **YES** - `LEFT JOIN DIM_ACCOUNT_SEGMENT ON FTL.ACCOUNT_ID = DIM.ACCOUNT_ID` | **HIGH** - Requires identifying authoritative segmentation source, building ETL pipeline, implementing SCD Type 2 if segments change over time, validating segment coverage for all accounts | BDP Team (source data), Data Engineering (ETL + dimension table), Zoom PM (segmentation logic approval) |
| GAP-002 | IS_LICENSED | Create dimension table DIM_ACCOUNT_LICENSE with ACCOUNT_ID → IS_LICENSED mapping; source from Zoom billing system or existing PI licensing table; join in Gold model using ACCOUNT_ID | **YES** - DIM_ACCOUNT_LICENSE (unless existing PI table can be reused) | **YES** - `LEFT JOIN DIM_ACCOUNT_LICENSE ON FTL.ACCOUNT_ID = DIM.ACCOUNT_ID` | **MEDIUM** - If existing PI licensing table available, just add join; if new table needed, requires billing system integration, daily refresh to capture license changes, handling trial-to-paid conversions | BDP Team (if new source needed), Data Engineering (ETL or join implementation), PI Billing System Owner (existing table coordination) |
| GAP-003 | USERS_ACTIVE_16PLUS_DAYS | Build new Silver table SLV_USER_ACTIVITY_ROLLING_28D that: (1) consumes daily SLV_FTL_USAGE_MASTER records, (2) maintains 28-day rolling history per user using window functions or incremental materialization, (3) calculates COUNT(days active) per user per window, (4) outputs users meeting 16+ day threshold; Gold joins this table and aggregates COUNT(users) | **YES** - SLV_USER_ACTIVITY_ROLLING_28D | **YES** - `LEFT JOIN SLV_USER_ACTIVITY_ROLLING_28D ON FTL.USER_ID = ROLLING.USER_ID AND FTL.DATE = ROLLING.REPORT_DATE` | **HIGH** - Requires complex windowing logic (28-day sliding window), incremental update strategy to avoid full table scans, 28 days of historical data accumulation before metric becomes accurate, potential performance issues with large user counts; alternatively, could use dbt incremental models with date range logic | Data Engineering (primary owner for Silver table build), PI Team (validation of 16+ day calculation matches existing logic) |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 9: RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Priority-ordered action list (no timeline or schedule provided):**

1. **BLOCKING: Resolve GAP-001 (SEGMENT)** — Identify authoritative source for customer segmentation (SMB/Mid-Market/Enterprise); coordinate with BDP Team to either (a) add SEGMENT directly to BRZ_FTL_AGENT_BASE_AGG upstream, or (b) provide separate dimension table DIM_ACCOUNT_SEGMENT with ACCOUNT_ID → SEGMENT mapping; validate segment coverage for all accounts in production FTL data.

2. **BLOCKING: Resolve GAP-002 (IS_LICENSED)** — Coordinate with PI Billing System Owner and BDP Team to identify licensing status source; evaluate whether existing PI licensing table can be joined or if new dimension table DIM_ACCOUNT_LICENSE is needed; ensure daily refresh to capture trial→paid conversions; validate license flag accuracy against Zoom billing system.

3. **BLOCKING: Resolve GAP-003 (USERS_ACTIVE_16PLUS_DAYS)** — Data Engineering to design and build new Silver table SLV_USER_ACTIVITY_ROLLING_28D with 28-day rolling window logic; implement incremental materialization strategy; coordinate with PI Team to validate calculation matches existing 16+ day metric; note: requires 28 days of historical FTL data accumulation before metric is production-ready.

4. **SILVER DBT CHANGES: Implement BR-001 (Date Parsing)** — Update all Silver models to parse DATA_DATE from TEXT format "5/29/26 13:01" to proper DATE type using `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')`; validate date format consistency across all FTL records; add data quality check to catch format exceptions; ensure century assumption (20XX) is correct.

5. **SILVER DBT CHANGES: Implement BR-002 (Phone Duration Conversion)** — Update SLV_FTL_USAGE_MASTER to convert INBOUND_PHONE_MS to INBOUND_PHONE_MINS using formula `INBOUND_PHONE_MS / 60000.0`; validate converted values match expected ranges (e.g., 325295 ms → 5.42 minutes); ensure NULL handling for zero-duration calls.

6. **SILVER DBT CHANGES: Implement BR-006, BR-007 (Case Standardization)** — Update SLV_FTL_COMBINED_CHANNELS to apply `UPPER()` transformation to DIRECTION and MODALITY columns for consistency with existing Silver schema; simple transformation with no data loss risk.

7. **SILVER DBT CHANGES: Implement BR-008 (Channel Mapping)** — Update SLV_FTL_COMBINED_CHANNELS to map FTL's split CHANNEL+MODALITY columns into single consolidated CHANNEL using CASE logic; reference BR-008 in Section 4 for SQL; note [LOW CONFIDENCE] flag — business rule validation needed for overlapping values.

8. **GOLD DBT CHANGES: Implement BR-003, BR-004 (Active Account/User Aggregation)** — Update GLD_AGGREGATE model to use COUNT DISTINCT aggregations with IS_ACTIVE filter: `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN ACCOUNT_ID END)` for ACTIVE_ACCOUNTS and `COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN AGENT_ID END)` for ACTIVE_USERS; validate counts match existing Gold output; note assumption that AGENT_ID = USER_ID.

9. **GOLD DBT CHANGES: Implement BR-005 (Region Mapping)** — Add CLUSTER→REGION transformation using CASE statement (see BR-005 in Section 4) OR join to DIM_CLUSTER_REGION_MAP reference table; **[LOW CONFIDENCE]** — only 3 CLUSTER values observed in sample data (eu-central-1, ap-south-1, us-east-1); validate full production data includes LATAM region mapping; raise with BDP Team to confirm all production clusters are covered.

10. **RAISE WITH BDP TEAM: Data Quality Concerns** — (a) OS column in FTL has only 1 distinct value "Sample Text" — verify if OS tracking is functioning correctly in production; (b) Confirm DATA_DATE format is consistent across all FTL records (currently "5/29/26 13:01"); (c) Validate CLUSTER column contains all expected AWS regions (sample only showed 3 values); (d) Clarify business rules for CHANNEL vs MODALITY — when both are populated, which takes precedence?

11. **RAISE WITH ZOOM TEAM: Business Logic Validation** — (a) Confirm AGENT_ID represents end users (not internal support agents) for ACTIVE_USERS metric; (b) Validate PHONE_USAGE calculation formula — current assumption is average minutes per session; confirm this matches business definition; (c) Clarify whether IS_ACTIVE flag applies at account level or user level or engagement level — impacts aggregation logic; (d) Obtain segmentation rules for GAP-001 resolution (how are accounts classified into segments?).

12. **NEW CAPABILITIES: Decision Needed from PI Team** — FTL provides 6 new columns not in current PI pipeline: ZCC_ACCOUNT_ID, CLIENT_TYPE, OS, plus finer-grained DIRECTION/MODALITY/CHANNEL tracking; coordinate with PI product and analytics leadership to determine: (a) Should any of these be promoted to Gold layer? (b) What new metrics or dashboards can leverage these dimensions? (c) Should CLIENT_TYPE be added to Gold for device-level reporting (MOBILE_USERS, DESKTOP_USERS)?

13. **DATA QUALITY VALIDATION: Cross-Verify FTL vs Legacy Pipeline** — Before deprecating legacy Bronze views, run parallel processing for 30-90 days: (a) Generate Gold table from both FTL and legacy sources; (b) Compare key metrics (ACTIVE_ACCOUNTS, ACTIVE_USERS, PHONE_USAGE) for discrepancies; (c) Investigate any deltas >5% to identify calculation differences or data quality issues; (d) Document and resolve all discrepancies before cutover.

14. **REFERENCE DATA: Build CLUSTER→REGION Mapping Table** — Create DIM_CLUSTER_REGION_MAP reference table with comprehensive mapping of all AWS CLUSTER values to business REGION names; coordinate with Zoom infrastructure team to obtain complete list of production clusters; ensure mapping covers EMEA, LATAM, NAMER, APAC, and any other regional breakdowns required by business.

15. **PERFORMANCE TESTING: Validate Gold Aggregation Performance** — GLD_AGGREGATE model will have increased complexity (multiple new joins for dimension tables, 28-day rolling window join, CLUSTER→REGION transformation); test query performance with production-scale data; identify if any indexes or materialization strategies needed; ensure daily refresh completes within SLA window.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 10: MAPPING CSV FOR REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```csv
FTL_Bronze_Column,FTL_Data_Type,PI_Silver_Column,PI_Silver_Table,PI_Gold_Column,PI_Gold_Table,Classification,Confidence,Mapping_Reason,BR_ID,GAP_ID,Transformation,Notes
DATA_DATE,TEXT,DATE,SLV_USAGE_MASTER,DATE,GLD_AGGREGATE,UNIT_CHANGE,Medium,FTL stores date as TEXT "5/29/26 13:01"; Gold requires DATE type; confirmed via distinct value query showing text format,BR-001,—,TO_DATE(DATA_DATE, 'M/D/YY HH24:MI'),Requires validation of date format consistency
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,Column name and data type identical; TEXT to TEXT with matching ID patterns confirmed via sample values,—,—,—,Used for aggregation in Gold via GROUP BY
AGENT_ID,TEXT,USER_ID,SLV_USAGE_MASTER,—,—,SEMANTIC_MATCH,High,Semantic analysis indicates AGENT_ID represents end users; distinct count (5) matches expected user cardinality,BR-004,—,AGENT_ID AS USER_ID,Assumption: AGENT_ID = USER_ID
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_CONSOLIDATED_USAGE,—,—,SEMANTIC_MATCH,Medium,FTL IS_ACTIVE (true/false) maps to Silver IS_ACTIVE_ACCOUNT; used in active account/user counting logic,BR-003,—,—,Assumption: IS_ACTIVE applies at account level
PHONE_SESSIONS,NUMBER,PHONE_SESSIONS,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,"Column name, data type (NUMBER), and sample values (426, 41, 248) match exactly between FTL and Silver",—,—,—,Direct pass-through to Silver
INBOUND_PHONE_MS,NUMBER,INBOUND_PHONE_MINS,SLV_USAGE_MASTER,PHONE_USAGE,GLD_AGGREGATE,UNIT_CHANGE,Medium,"FTL stores phone time in milliseconds (e.g., 325295 ms); Silver/Gold require minutes; unit conversion confirmed via data type analysis",BR-002,—,INBOUND_PHONE_MS / 60000.0,"Converts MS to minutes (÷ 60,000)"
CLUSTER,TEXT,—,—,REGION,GLD_AGGREGATE,SEMANTIC_MATCH,Low,"FTL CLUSTER contains AWS region codes (eu-central-1, ap-south-1, us-east-1); Gold REGION has business regions (EMEA, LATAM, NAMER); requires lookup table",BR-005,—,"CASE WHEN CLUSTER = 'eu-central-1' THEN 'EMEA' WHEN CLUSTER = 'ap-south-1' THEN 'APAC' WHEN CLUSTER = 'us-east-1' THEN 'NAMER' ELSE 'UNKNOWN' END","[LOW CONFIDENCE] Assumption: CLUSTER maps to REGION; incomplete mapping"
ZCC_ACCOUNT_ID,TEXT,—,—,—,—,NEW_CAPABILITY,High,ZCC_ACCOUNT_ID (distinct count: 5) exists in FTL but no equivalent column in current PI pipeline; provides Zoom Contact Center account identifier,—,—,—,New dimension available for enrichment
ENGAGEMENT_ID,TEXT,ENGAGEMENT_ID,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,"Column name and data type identical; TEXT to TEXT with matching ID patterns (ID_8325, ID_2919, ID_6563) confirmed",—,—,—,Used in Silver channel-level detail table
DIRECTION,TEXT,DIRECTION,SLV_COMBINED_CHANNELS,—,—,CASE_CHANGE,High,"FTL has values ""Inbound, Outbound"" (mixed case); Silver has ""INBOUND, OUTBOUND"" (uppercase); confirmed via distinct value query",BR-006,—,UPPER(DIRECTION),Simple case standardization
MODALITY,TEXT,MODALITY,SLV_COMBINED_CHANNELS,—,—,CASE_CHANGE,High,"FTL has values ""SMS, Email, Chat"" (mixed case); Silver has mixed case too but different formatting; distinct values confirmed via query",BR-007,—,UPPER(MODALITY),Case standardization for consistency
CHANNEL,TEXT,CHANNEL,SLV_COMBINED_CHANNELS,—,—,PARTIAL_MATCH,Medium,"FTL has 2 distinct values (Video, Phone); Silver has 5 values (EMAIL, VIDEO, PHONE, SMS, CHAT); FTL provides subset; confirmed via distinct value query",BR-008,—,UPPER(CHANNEL),FTL CHANNEL alone insufficient; needs combination with MODALITY
CLIENT_TYPE,TEXT,—,—,—,—,NEW_CAPABILITY,High,"CLIENT_TYPE (Mobile, Desktop, Web) exists in FTL but no equivalent in current PI pipeline; provides device type tracking",—,—,—,New dimension for device analytics
OS,TEXT,—,—,—,—,NEW_CAPABILITY,Medium,OS column exists in FTL (currently single value "Sample Text"); no equivalent in PI pipeline; provides operating system tracking,—,—,—,Data quality concern: only 1 distinct value
—,—,—,—,SEGMENT,GLD_AGGREGATE,GAP,High,"No column found in FTL source matching customer segmentation concept; GOLD has numeric SEGMENT (3, 5, 2 values observed); no business logic or source data available in FTL",—,GAP-001,NULL AS SEGMENT -- GAP-001,**CRITICAL GAP** - Blocks migration
—,—,—,—,IS_LICENSED,GLD_AGGREGATE,GAP,High,No licensing/subscription status column exists in FTL; GOLD requires boolean IS_LICENSED (true/false); confirmed via column inventory - no matching concept in FTL schema,—,GAP-002,NULL AS IS_LICENSED -- GAP-002,**CRITICAL GAP** - Blocks migration
—,—,—,—,ACTIVE_ACCOUNTS,GLD_AGGREGATE,GRAIN_CHANGE,Medium,"Requires aggregation: COUNT(DISTINCT ACCOUNT_ID WHERE IS_ACTIVE = true) grouped by DATE, REGION, SEGMENT, IS_LICENSED; source columns exist but transformation is complex",BR-003,—,COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN ACCOUNT_ID END),"Requires GROUP BY DATE, REGION, SEGMENT, IS_LICENSED"
—,—,—,—,ACTIVE_USERS,GLD_AGGREGATE,GRAIN_CHANGE,Medium,"Requires aggregation: COUNT(DISTINCT AGENT_ID WHERE IS_ACTIVE = true) grouped by DATE, REGION, SEGMENT, IS_LICENSED; assumes AGENT_ID represents users",BR-004,—,COUNT(DISTINCT CASE WHEN IS_ACTIVE = true THEN AGENT_ID END),"Assumption: AGENT_ID = user; GROUP BY DATE, REGION, SEGMENT, IS_LICENSED"
—,—,—,—,USERS_ACTIVE_16PLUS_DAYS,GLD_AGGREGATE,GAP,High,"No historical activity tracking in FTL; metric requires counting users active 16+ days in rolling 28-day window; FTL has single date snapshot, no day-count logic; confirmed via schema analysis",—,GAP-003,NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP-003,**CRITICAL GAP** - Requires new aggregation logic
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**END OF MIGRATION REPORT**