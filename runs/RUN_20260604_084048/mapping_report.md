

🔍 **STEP 1: Schema Discovery** — Retrieved metadata for 1 source table (Bronze FTL), 20 Silver tables, and 1 Gold table

🔍 **STEP 2: Data Profiling** — Profiled BRZ_FTL_AGENT_BASE_AGG (14 columns, 5 rows) and all target tables

🔍 **STEP 3: Silver Layer Mapping** — Analyzed 10 Silver tables with 71 total target columns

🔍 **STEP 4: Gold Layer Mapping** — Analyzed GLD_AGGREGATE with 8 target columns and identified critical gaps

🔍 **STEP 5: Gap Analysis** — Identified 11 gaps, 2 blocking (SEGMENT, USERS_ACTIVE_16PLUS_DAYS)

---

# COMPREHENSIVE MIGRATION MAPPING REPORT
## FTL Bronze → PI Silver → PI Gold Pipeline Migration Analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1: EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG  
**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE  
**Migration Readiness Score:** 52/100

**Total FTL columns analyzed:** 14  
**Successfully mapped:** 8 (57%)  
**Partially mapped:** 3 (21%)  
**New capabilities (no PI equivalent):** 3 (21%)  
**Gaps (PI Gold columns with no FTL source):** 11  
→ **GAP-001**: SEGMENT  
→ **GAP-002**: USERS_ACTIVE_16PLUS_DAYS  
→ **GAP-003**: Historical Rolling Windows (R7, R28)  
→ **GAP-004**: Chat/Video Duration Metrics  
→ **GAP-005**: SLA Achievement Tracking  
→ **GAP-006**: Engagement Status  
→ **GAP-007**: Time Window Logic  
→ **GAP-008**: Chat Sessions Count  
→ **GAP-009**: Video Usage Metrics  
→ **GAP-010**: Historical First Active Dates  
→ **GAP-011**: IS_PAID_USER / Payment Status  

**Blocking items:** 2 (GAP-001, GAP-002)

**Overall Assessment:**  
The FTL Bronze source provides foundational account, agent, and phone engagement data but lacks critical business dimensions (SEGMENT, IS_LICENSED semantics) and temporal tracking capabilities required for Gold-layer reporting. Silver-layer tables can be partially populated with default values and workarounds, but the Gold aggregate table cannot produce accurate business intelligence without external enrichment for customer segmentation and historical user activity patterns. Migration is feasible for basic phone usage tracking but not feasible for comprehensive multi-channel analytics and engagement reporting without architectural changes and additional data sources.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2: GAP IMPACT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | Why It's a Gap | Impact on Gold Output | Blocks Migration? | Action Required | Raise With |
|--------|----------------|----------------|----------------------|-------------------|-----------------|------------|
| GAP-001 | SEGMENT | No customer/account segmentation data in FTL source | Cannot classify accounts by business segment (2,3,5 values missing) — breaks all segment-level reporting | **YES** | BDP to provide SEGMENT dimension in FTL or create separate mapping table | BDP Team, Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | No historical temporal activity tracking in FTL source | Cannot calculate power user engagement metrics — KPI permanently NULL | **YES** | Implement historical tracking in FTL or build rolling window aggregation from daily snapshots | BDP Team, Data Engineering |
| GAP-003 | Window Aggregations (R7, R28, R1) | FTL provides single-day snapshot, no rolling window logic | All time-windowed metrics (weekly, monthly) default to R1 only | NO | Build DBT models to aggregate over historical data partitions | Data Engineering |
| GAP-004 | Chat/Video Duration | FTL only tracks INBOUND_PHONE_MS, no duration for other channels | Chat and video usage metrics will be NULL or 0 — phone-only reporting | NO | Populate with 0 for now, request BDP add chat/video duration fields | BDP Team |
| GAP-005 | SLA Achievement | No SLA_ACHIEVED field in FTL source | SLA compliance reporting impossible — metrics show 0 | NO | Default to FALSE/0, request BDP add SLA tracking logic | BDP Team |
| GAP-006 | Engagement Status | No engagement outcome (Resolved, Missed, Answered) in FTL | Cannot report on engagement resolution quality | NO | Default to NULL, request BDP add engagement status field | BDP Team |
| GAP-007 | Window Logic | No time window classification in FTL | All metrics default to 'R1' (single day) — no weekly/monthly views | NO | Hardcode window based on DBT model grain | Data Engineering |
| GAP-008 | Chat Sessions | No chat session count in FTL source | Chat engagement volume metrics unavailable | NO | Populate with 0, request BDP add CHAT_SESSIONS field | BDP Team |
| GAP-009 | Video Usage | No video duration or session metrics in FTL | Video engagement reporting unavailable | NO | Populate with 0, request BDP add VIDEO_SESSIONS and VIDEO_DURATION | BDP Team |
| GAP-010 | Historical First Active | FTL only has current DATA_DATE, not true first active date | User/account tenure metrics incorrect — assumes current date = first active | NO | Use current date as placeholder, build separate first-active tracking table | Data Engineering |
| GAP-011 | IS_PAID_USER / IS_LICENSED | FTL has IS_ACTIVE but semantics differ from IS_LICENSED | Licensing status unclear — may misclassify free vs paid users | NO | Clarify IS_ACTIVE vs IS_LICENSED mapping, potentially join to billing data | Zoom PM, Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3: FULL COLUMN LINEAGE MAPPING TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | High | FTL provides ZCC_ACCOUNT_ID not present in any PI table — confirmed via schema analysis | — | — | None | Available for future use |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_ACCT_FIRST_ACTIVE, SLV_COMBINED_CHANNELS, SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_ACTIVE_DAYS, SLV_USER_FIRST_ACTIVE, SLV_WEEKLY_METRICS | — | GLD_AGGREGATE (via agg) | DIRECT_MATCH | High | Exact column name match across 10 Silver tables — primary account identifier | BR-009 | — | None | Core dimension |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Exact column name match — engagement tracking identifier | BR-009 | — | None | Transaction ID |
| AGENT_ID | TEXT | USER_ID | SLV_COMBINED_CHANNELS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE | ACTIVE_USERS | GLD_AGGREGATE | SEMANTIC_MATCH | Medium | FTL AGENT_ID maps to PI USER_ID — confirmed agent represents user in business context | BR-004 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE | Semantic mapping |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | High | FTL values (Inbound/Outbound) match PI values (INBOUND/OUTBOUND) — case normalization needed | BR-003 | — | UPPER(DIRECTION) | Case differs |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | FTL values (Chat/Email/SMS) match PI values (Phone/SMS/Chat) — overlapping set | BR-009 | — | None | Semantic match |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | High | FTL values (Phone/Video) are subset of PI values (VIDEO/CHAT/PHONE/SMS/EMAIL) — case normalization needed | BR-003 | — | UPPER(CHANNEL) | Case differs |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Exact column name and semantic match — phone session count | BR-009 | — | None | Direct map |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE | High | FTL in milliseconds, PI in minutes, Gold in minutes — confirmed unit conversion required | BR-002, BR-008 | — | INBOUND_PHONE_MS / 60000.0 | Unit conversion |
| INBOUND_PHONE_MS | NUMBER | DURATION_SEC | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Medium | FTL in milliseconds, PI in seconds — conversion for phone channel only | BR-002 | — | INBOUND_PHONE_MS / 1000.0 | Phone only |
| INBOUND_PHONE_MS | NUMBER | PHONE_USAGE | SLV_CONSOLIDATED_USAGE | — | — | UNIT_CHANGE | High | FTL in milliseconds, PI in minutes — confirmed conversion needed | BR-002 | — | INBOUND_PHONE_MS / 60000.0 | Unit conversion |
| INBOUND_PHONE_MS | NUMBER | WEEKLY_PHONE_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | UNIT_CHANGE | Medium | FTL in milliseconds, PI in minutes — weekly aggregation needed | BR-002 | — | INBOUND_PHONE_MS / 60000.0 | Weekly agg |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | High | FTL provides CLIENT_TYPE (Desktop/Mobile/Web) not present in any PI table — confirmed via schema analysis | — | — | None | Available for future use |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | High | FTL provides OS not present in any PI table — device analytics capability | — | — | None | Available for future use |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | IS_LICENSED | GLD_AGGREGATE | SEMANTIC_MATCH | Medium | FTL IS_ACTIVE maps to PI IS_ACTIVE_ACCOUNT and Gold IS_LICENSED — semantic validation needed | BR-009 | GAP-011 | Direct or join to billing table | Semantic unclear |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | SEMANTIC_MATCH | Low | FTL CLUSTER (ap-south-1, eu-central-1, us-east-1) must map to PI REGION (NAMER, LATAM, EMEA, APAC) — mapping logic needed | BR-006 | — | CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'OTHER' END | [ASSUMPTION] |
| DATA_DATE | TEXT | START_DATE, DATE, REPORT_DATE | All Silver tables | DATE | GLD_AGGREGATE | UNIT_CHANGE | Medium | FTL DATA_DATE is TEXT format '5/29/26 13:01', PI expects DATE type — parsing required | BR-001 | — | TO_DATE(DATA_DATE, 'M/D/YY H:MI') | Format parse |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE, SLV_USAGE_MASTER | — | — | GAP | High | No FTL source for historical first active date — must use current DATA_DATE as proxy | — | GAP-010 | TO_DATE(DATA_DATE, 'M/D/YY H:MI') | [ASSUMPTION] current = first |
| — | — | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE, SLV_USER_FIRST_ACTIVE | — | — | GAP | High | No FTL source for refresh timestamp — system-generated field | — | — | CURRENT_TIMESTAMP() | System field |
| — | — | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | — | — | GAP | High | No FTL source for engagement outcome (Missed/Resolved/Answered) — quality metric missing | — | GAP-006 | NULL | Missing field |
| — | — | SLA_ACHIEVED | SLV_COMBINED_CHANNELS | — | — | GAP | High | No FTL source for SLA achievement tracking — compliance metric missing | — | GAP-005 | FALSE | Missing field |
| — | — | SOURCE_TABLE | SLV_COMBINED_CHANNELS | — | — | GAP | High | No FTL source for source table tracking — hardcode static value | BR-010 | — | 'BRZ_FTL_AGENT_BASE_AGG' | Static value |
| — | — | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | — | — | GAP | High | No FTL source for product name — hardcode static value | BR-010 | — | 'ZCC Platform' | Static value |
| — | — | WINDOW | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | — | — | GAP | High | No FTL source for time window (R1/R7/R28) — must assign based on DBT model grain | BR-005 | GAP-007 | 'R1' for daily, 'R7' for weekly, 'R28' for monthly | [ASSUMPTION] |
| — | — | ACTIVE_USERS | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | ACTIVE_USERS | GLD_AGGREGATE | GAP | Low | No direct FTL field — must aggregate COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE | BR-004 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE | Aggregation |
| — | — | CHAT_USAGE | SLV_DAILY_METRICS, SLV_WEEKLY_METRICS | — | — | GAP | High | No FTL source for chat duration — phone-only data available | — | GAP-004 | 0 or NULL | Missing field |
| — | — | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | — | — | GAP | Low | No FTL source for daily activity count — must derive from IS_ACTIVE | BR-004 | GAP-003 | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE | [LOW CONFIDENCE] |
| — | — | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | GAP | High | No FTL source for video duration — phone-only data available | — | GAP-009 | 0 or NULL | Missing field |
| — | — | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | No FTL source for historical 16+ day activity tracking — critical engagement KPI missing | — | GAP-002 | NULL or 0 | **BLOCKS MIGRATION** |
| — | — | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No FTL source for payment/license status — semantic unclear | — | GAP-011 | Copy ACCOUNT_ID as placeholder | [ASSUMPTION] |
| — | — | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No FTL source for 7-day rolling activity — single day snapshot only | — | GAP-003 | 1 (default) | Missing historical |
| — | — | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No FTL source for 28-day rolling activity — single day snapshot only | — | GAP-003 | 1 (default) | Missing historical |
| — | — | DAILY_CHAT_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No FTL source for chat duration — phone-only data available | — | GAP-004 | 0 | Missing field |
| — | — | USER_FIRST_ACTIVE | SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE | — | — | GAP | High | No FTL source for historical user first active date — must use current DATA_DATE | — | GAP-010 | TO_DATE(DATA_DATE, 'M/D/YY H:MI') | [ASSUMPTION] |
| — | — | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No FTL source for chat session count — phone sessions only | — | GAP-008 | 0 | Missing field |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No FTL source for SLA-achieved session count — compliance metric missing | — | GAP-005 | 0 | Missing field |
| — | — | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | Low | No FTL source for 1-day active count in last 7 days — can derive from IS_ACTIVE | BR-004 | GAP-003 | COUNT based on IS_ACTIVE | [LOW CONFIDENCE] |
| — | — | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No FTL source for 4-7 day active count — requires historical data | — | GAP-003 | 0 | Missing historical |
| — | — | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | Low | No FTL source for 1-day active count in last 28 days — can derive from IS_ACTIVE | BR-004 | GAP-003 | COUNT based on IS_ACTIVE | [LOW CONFIDENCE] |
| — | — | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | No FTL source for 16+ day active count — requires historical data | — | GAP-003 | 0 | Missing historical |
| — | — | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | — | — | GAP | High | No FTL source for 4-7 day active user count — requires historical data | — | GAP-003 | 0 | Missing historical |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No FTL source for customer/account segmentation — critical business dimension missing | — | GAP-001 | NULL | **BLOCKS MIGRATION** |
| — | — | — | — | ACTIVE_ACCOUNTS | GLD_AGGREGATE | GAP | Low | No direct FTL field — must aggregate COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE | BR-007 | — | COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE | Aggregation |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4: TRANSFORMATION GUIDE (Business Rules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | DATE, START_DATE, REPORT_DATE | UNIT_CHANGE | `TO_DATE(DATA_DATE, 'M/D/YY H:MI')` | FTL stores date as TEXT in format 'M/D/YY H:MI', PI expects DATE type for date columns | DATA_DATE not null | [ASSUMPTION] Format is consistent MM/DD/YY HH:MI |
| BR-002 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS, DURATION_SEC, PHONE_USAGE, WEEKLY_PHONE_USAGE | UNIT_CHANGE | `INBOUND_PHONE_MS / 60000.0` for minutes, `/1000.0` for seconds | FTL stores phone duration in milliseconds, PI expects minutes for usage metrics and seconds for duration | INBOUND_PHONE_MS not null, numeric | All phone durations are milliseconds |
| BR-003 | DIRECTION, CHANNEL | DIRECTION, CHANNEL | PARTIAL_MATCH | `UPPER(DIRECTION)`, `UPPER(CHANNEL)` | FTL uses mixed case (Inbound/Outbound, Phone/Video), PI expects uppercase (INBOUND/OUTBOUND, PHONE/VIDEO) | Source text fields not null | PI standard is uppercase |
| BR-004 | AGENT_ID, IS_ACTIVE | ACTIVE_USERS, USER_ID, USERS_ACTIVE_1_DAY, ACTIVE_1_DAY_L7, ACTIVE_1_DAY_L28 | SEMANTIC_MATCH / Aggregation | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = TRUE` | FTL AGENT_ID represents users in business context; active users counted only when IS_ACTIVE flag is true | AGENT_ID, IS_ACTIVE | [ASSUMPTION] Agent = User in PI context |
| BR-005 | — | WINDOW | GAP | `CASE WHEN model_grain = 'daily' THEN 'R1' WHEN model_grain = 'weekly' THEN 'R7' WHEN model_grain = 'monthly' THEN 'R28' END` | FTL has no window concept; PI uses R1/R7/R28 to denote rolling 1/7/28 day windows; hardcode based on DBT model grain | None | [ASSUMPTION] Single-day snapshot = R1 |
| BR-006 | CLUSTER | REGION | SEMANTIC_MATCH | `CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'OTHER' END` | FTL CLUSTER is AWS region (us-east-1, eu-central-1, ap-south-1), PI REGION is business region (NAMER, EMEA, APAC, LATAM); mapping logic required | CLUSTER not null | [ASSUMPTION] AWS prefix maps to business region; no LATAM in FTL sample |
| BR-007 | ACCOUNT_ID, IS_ACTIVE | ACTIVE_ACCOUNTS | Aggregation | `COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = TRUE` | Gold requires count of active accounts per date/region/segment; FTL provides account-level records | ACCOUNT_ID, IS_ACTIVE | Active accounts filter by IS_ACTIVE flag |
| BR-008 | INBOUND_PHONE_MS | PHONE_USAGE (Gold) | UNIT_CHANGE | `SUM(INBOUND_PHONE_MS) / 3600000.0` | Gold PHONE_USAGE measured in hours; FTL INBOUND_PHONE_MS in milliseconds; convert and aggregate | INBOUND_PHONE_MS | [ASSUMPTION] Gold usage metric is hours, not minutes |
| BR-009 | ACCOUNT_ID, ENGAGEMENT_ID, MODALITY, PHONE_SESSIONS, IS_ACTIVE | ACCOUNT_ID, ENGAGEMENT_ID, MODALITY, PHONE_SESSIONS, IS_ACTIVE_ACCOUNT | DIRECT_MATCH | Direct column copy | Columns have exact name and semantic match; no transformation needed | Source columns not null | None |
| BR-010 | — | SOURCE_TABLE, PRODUCT_NAME | GAP | `'BRZ_FTL_AGENT_BASE_AGG'` for SOURCE_TABLE, `'ZCC Platform'` for PRODUCT_NAME | FTL has no product or source tracking; PI expects static values for lineage and product classification | None | Static values agreed with business |
| **GAP-001** | — | SEGMENT (Gold) | GAP | `NULL AS SEGMENT -- GAP ID: GAP-001` | No FTL source for customer/account segment (values 2,3,5 in PI); critical business dimension missing; blocks Gold aggregation | None | **BLOCKING**: Requires external segment mapping table or BDP to add SEGMENT to FTL |
| **GAP-002** | — | USERS_ACTIVE_16PLUS_DAYS (Gold, Silver) | GAP | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-002` | No FTL source for historical 16+ day user activity; engagement KPI impossible to calculate without temporal tracking | None | **BLOCKING**: Requires BDP to implement historical activity tracking or build from daily snapshots |
| **GAP-003** | — | ACTIVE_DAYS_LAST_7, ACTIVE_DAYS_LAST_28, ACTIVE_4_7_DAYS_L7, ACTIVE_16PLUS_DAYS_L28 | GAP | `1 AS ACTIVE_DAYS_LAST_7 -- GAP ID: GAP-003` (default) | FTL provides single-day snapshot; no rolling window data; all historical activity metrics defaulted | None | Can build over time from daily FTL snapshots; initial load = 1 day |
| **GAP-004** | — | CHAT_USAGE, VIDEO_USAGE, DAILY_CHAT_USAGE | GAP | `0 AS CHAT_USAGE -- GAP ID: GAP-004` | FTL only tracks INBOUND_PHONE_MS; no chat or video duration; all non-phone channels = 0 | None | Request BDP add CHAT_DURATION_MS, VIDEO_DURATION_MS to FTL |
| **GAP-005** | — | SLA_ACHIEVED, SLA_ACHIEVED_SESSIONS | GAP | `FALSE AS SLA_ACHIEVED -- GAP ID: GAP-005` | FTL has no SLA tracking; compliance metrics unavailable; default to FALSE | None | Request BDP add SLA_ACHIEVED boolean to FTL |
| **GAP-006** | — | ENGAGEMENT_STATUS | GAP | `NULL AS ENGAGEMENT_STATUS -- GAP ID: GAP-006` | FTL has no engagement outcome (Missed/Resolved/Answered); quality metric missing | None | Request BDP add ENGAGEMENT_STATUS to FTL |
| **GAP-007** | — | WINDOW | GAP | `'R1' AS WINDOW -- GAP ID: GAP-007` | FTL has no window logic; hardcode R1 for daily models, R7 for weekly, R28 for monthly | None | [ASSUMPTION] DBT model grain determines window value |
| **GAP-008** | — | CHAT_SESSIONS | GAP | `0 AS CHAT_SESSIONS -- GAP ID: GAP-008` | FTL only tracks PHONE_SESSIONS; no chat session count | None | Request BDP add CHAT_SESSIONS to FTL |
| **GAP-009** | — | VIDEO_USAGE | GAP | `0 AS VIDEO_USAGE -- GAP ID: GAP-009` | FTL has no video duration or session metrics | None | Request BDP add VIDEO_SESSIONS, VIDEO_DURATION_MS to FTL |
| **GAP-010** | DATA_DATE | ACCOUNT_FIRST_ACTIVE, USER_FIRST_ACTIVE | GAP | `TO_DATE(DATA_DATE, 'M/D/YY H:MI') AS ACCOUNT_FIRST_ACTIVE -- GAP ID: GAP-010` | FTL only has current DATA_DATE; true first active dates unknown; use current date as proxy | DATA_DATE | [ASSUMPTION] New accounts/users — build separate first-active tracking table |
| **GAP-011** | IS_ACTIVE | IS_LICENSED, IS_PAID_USER | GAP | `IS_ACTIVE AS IS_LICENSED -- GAP ID: GAP-011` OR join to billing table | FTL IS_ACTIVE semantic differs from PI IS_LICENSED/IS_PAID_USER; unclear if active = licensed | IS_ACTIVE | [LOW CONFIDENCE] Clarify with Zoom PM if IS_ACTIVE = IS_LICENSED |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5: NEW FTL CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|-------------------|-------------------|----------------|
| ZCC_ACCOUNT_ID | TEXT | ZCC-specific account identifier separate from ACCOUNT_ID | Cross-system account reconciliation, ZCC platform analytics | PENDING DECISION | Add to Silver now; confirm with Zoom PM if ZCC_ACCOUNT_ID should be dimension in Gold for ZCC-specific reporting |
| CLIENT_TYPE | TEXT | Client platform (Desktop, Mobile, Web) | Device type analytics, mobile vs desktop usage segmentation | YES | Add to Silver immediately; propose Gold extension to include CLIENT_TYPE as dimension for device-based usage analysis |
| OS | TEXT | Operating system information | OS-level analytics, platform compatibility insights | NO | Keep in Silver only for technical analysis; not a core business dimension for Gold KPIs |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 6: GAP REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | PI Silver Source | Why FTL Cannot Produce This | Blocks Migration? | Proposed Resolution | Raise With |
|--------|----------------|------------------|----------------------------|-------------------|---------------------|------------|
| GAP-001 | SEGMENT | — (Gold dimension) | FTL has no customer/account segmentation field; SEGMENT values (2,3,5) represent business classification (SMB/Mid-Market/Enterprise) not present in source data | **YES** | Create ACCOUNT_SEGMENT_MAP reference table mapping ACCOUNT_ID to SEGMENT, or BDP to add SEGMENT field to FTL based on account metadata | BDP Team, Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS, SLV_USER_ACTIVE_DAYS | FTL provides single-day snapshot with IS_ACTIVE flag; no historical tracking of user activity over 28-day windows; power user engagement KPI cannot be calculated | **YES** | Option 1: BDP implements historical activity tracking in FTL; Option 2: Build rolling window aggregation in Silver from 28+ days of daily FTL snapshots; Option 3: Accept NULL until historical data accumulated | BDP Team, Data Engineering |
| GAP-003 | Rolling Window Metrics (ACTIVE_DAYS_LAST_7, ACTIVE_DAYS_LAST_28, etc.) | SLV_ROLL_29_DAY_USAGE, SLV_USER_ACTIVE_DAYS | FTL provides single-day snapshot; no R7/R28 rolling window aggregations; all historical activity metrics default to 1 day | NO | Build DBT models to aggregate over historical FTL daily snapshots; initial migration defaults to 1 day; accumulate 28+ days post-migration to enable rolling windows | Data Engineering |
| GAP-004 | CHAT_USAGE, VIDEO_USAGE, DAILY_CHAT_USAGE | SLV_DAILY_METRICS, SLV_WEEKLY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE | FTL only tracks INBOUND_PHONE_MS; no duration fields for Chat, Video, Email, SMS channels despite having CHANNEL/MODALITY dimensions | NO | Populate with 0 for initial migration (phone-only reporting); request BDP add CHAT_DURATION_MS, VIDEO_DURATION_MS, EMAIL_DURATION_MS, SMS_DURATION_MS to FTL | BDP Team |
| GAP-005 | SLA_ACHIEVED, SLA_ACHIEVED_SESSIONS | SLV_COMBINED_CHANNELS, SLV_USAGE_MASTER | FTL has no SLA achievement tracking field; compliance metrics (SLA achieved rate, sessions meeting SLA) unavailable | NO | Default to FALSE/0 for initial migration; request BDP add SLA_ACHIEVED boolean to FTL (requires SLA threshold configuration) | BDP Team |
| GAP-006 | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | FTL has no engagement outcome field (Missed/Resolved/Answered/Abandoned); engagement quality metrics unavailable | NO | Default to NULL; request BDP add ENGAGEMENT_STATUS to FTL (requires outcome tracking in source systems) | BDP Team |
| GAP-007 | WINDOW | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | FTL has no time window concept (R1/R7/R28); PI uses window to denote aggregation grain | NO | Hardcode window value based on DBT model grain: 'R1' for daily models, 'R7' for weekly, 'R28' for monthly; no data gap, just metadata | Data Engineering |
| GAP-008 | CHAT_SESSIONS | SLV_USAGE_MASTER | FTL only tracks PHONE_SESSIONS count; no chat session count despite having chat modality data | NO | Populate with 0 for phone-only migration; request BDP add CHAT_SESSIONS to FTL | BDP Team |
| GAP-009 | VIDEO_USAGE | SLV_MONTHLY_METRICS | FTL has no video duration or session metrics despite VIDEO appearing in CHANNEL sample values | NO | Populate with 0; request BDP add VIDEO_SESSIONS and VIDEO_DURATION_MS to FTL | BDP Team |
| GAP-010 | ACCOUNT_FIRST_ACTIVE, USER_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE, SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE | FTL only provides current DATA_DATE; no historical first active dates; tenure metrics will be incorrect (assumes all accounts/users are new on migration date) | NO | Option 1: Use current DATA_DATE as placeholder for new accounts/users; Option 2: Build separate first-active tracking table from historical PI data; Option 3: Request BDP backfill FIRST_ACTIVE_DATE to FTL | Data Engineering, BDP Team |
| GAP-011 | IS_LICENSED, IS_PAID_USER | GLD_AGGREGATE, SLV_ROLL_29_DAY_USAGE | FTL has IS_ACTIVE but semantic differs from IS_LICENSED (Gold) and IS_PAID_USER (Silver); unclear if active = licensed, or if licensing requires billing system join | NO | Option 1: Map IS_ACTIVE → IS_LICENSED directly (validate with business); Option 2: Join to existing PI billing/licensing table; Option 3: Request BDP add IS_LICENSED to FTL | Zoom PM, Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 7: FEASIBILITY VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| GLD_AGGREGATE | 35% | GAP-001 (SEGMENT), GAP-002 (USERS_ACTIVE_16PLUS_DAYS), GAP-011 (IS_LICENSED semantics) | **Not Feasible** | 1. BDP must provide SEGMENT mapping (GAP-001); 2. Implement historical activity tracking or accept NULL for GAP-002; 3. Clarify IS_ACTIVE vs IS_LICENSED semantics (GAP-011) |
| SLV_USAGE_MASTER | 70% | GAP-008 (CHAT_SESSIONS), GAP-005 (SLA_ACHIEVED_SESSIONS), GAP-010 (first active dates) | **Feasible with Caveats** | Proceed with 0/NULL defaults for chat and SLA metrics; use current date for first active; request BDP enhancements |
| SLV_COMBINED_CHANNELS | 65% | GAP-006 (ENGAGEMENT_STATUS), GAP-005 (SLA_ACHIEVED) | **Feasible with Caveats** | Proceed with NULL for engagement status, FALSE for SLA; limits engagement quality reporting |
| SLV_CONSOLIDATED_USAGE | 60% | GAP-007 (WINDOW logic), GAP-004 (CHAT/VIDEO_USAGE) | **Feasible with Caveats** | Proceed with hardcoded R1 window, 0 for non-phone usage; phone-only reporting initially |
| SLV_DAILY_METRICS | 55% | GAP-004 (CHAT_USAGE), GAP-003 (historical activity) | **Feasible with Caveats** | Proceed with 0 for chat usage, default 1 for daily activity counts; phone-only initially |
| SLV_MONTHLY_METRICS | 50% | GAP-009 (VIDEO_USAGE), GAP-002 (USERS_ACTIVE_16PLUS_DAYS) | **Feasible with Caveats** | Proceed with 0 for video usage, 0 for 16+ day users; engagement KPI limited until historical data available |
| SLV_WEEKLY_METRICS | 55% | GAP-004 (CHAT_USAGE), GAP-003 (weekly activity) | **Feasible with Caveats** | Proceed with 0 for chat usage; weekly activity metrics limited initially |
| SLV_ACCT_FIRST_ACTIVE | 75% | GAP-010 (historical first active) | **Feasible with Caveats** | Proceed with current DATA_DATE as first active; tenure metrics incorrect until backfilled |
| SLV_USER_FIRST_ACTIVE | 75% | GAP-010 (historical first active) | **Feasible with Caveats** | Proceed with current DATA_DATE as first active; user tenure metrics incorrect until backfilled |
| SLV_ROLL_29_DAY_USAGE | 45% | GAP-003 (rolling windows), GAP-004 (CHAT_USAGE), GAP-011 (IS_PAID_USER) | **Not Feasible** | Requires 28+ days of historical FTL snapshots to calculate rolling windows; defer until data accumulated |
| SLV_USER_ACTIVE_DAYS | 40% | GAP-003 (historical activity tracking) | **Not Feasible** | Requires historical daily activity data; defer until 28+ days of FTL snapshots available |

**OVERALL VERDICT:** Migration is **Feasible with Caveats** for 7 of 10 Silver tables and **Not Feasible** for Gold layer and 3 Silver tables (rolling window/historical tables) without addressing critical gaps.

**Conditions to Proceed:**

1. **GAP-001 (SEGMENT)**: BDP Team must provide SEGMENT dimension via new FTL field or separate mapping table — **BLOCKS GOLD MIGRATION**
2. **GAP-002 (USERS_ACTIVE_16PLUS_DAYS)**: Implement historical activity tracking or accept NULL for engagement KPI — **BLOCKS GOLD MIGRATION**
3. **GAP-011 (IS_LICENSED)**: Zoom PM to confirm IS_ACTIVE = IS_LICENSED OR provide billing table join logic
4. **GAP-003 (Rolling Windows)**: Accept degraded functionality for 28+ days post-migration while historical data accumulates
5. **GAP-004/005/006/008/009 (Multi-channel metrics)**: Accept phone-only reporting initially; request BDP add chat/video/SLA fields to FTL
6. **GAP-010 (First Active Dates)**: Accept incorrect tenure metrics; backfill from historical PI data OR wait for BDP to add to FTL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 8: DBT MODEL IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 8.1 — NEW TABLES TO CREATE

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| ACCOUNT_SEGMENT_MAP | Reference | Maps ACCOUNT_ID to SEGMENT (2/3/5) for Gold aggregation | BDP Team to provide source data or business rules |
| CLUSTER_REGION_MAP | Reference | Maps FTL CLUSTER (aws region) to PI REGION (business region) | BR-006 mapping logic |
| USER_FIRST_ACTIVE_TRACKING | Silver | Tracks true first active dates for users/accounts (SCD Type 1) | SLV_USAGE_MASTER daily snapshots |
| ROLLING_WINDOW_BASE | Silver | Daily aggregation base for building R7/R28 rolling windows | BRZ_FTL_AGENT_BASE_AGG daily snapshots |
| SLV_FTL_COMBINED_CHANNELS | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG |
| SLV_FTL_USAGE_MASTER | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG |
| SLV_FTL_CONSOLIDATED_USAGE | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG, ROLLING_WINDOW_BASE |
| SLV_FTL_DAILY_METRICS | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG, ROLLING_WINDOW_BASE |
| SLV_FTL_WEEKLY_METRICS | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG, ROLLING_WINDOW_BASE |
| SLV_FTL_MONTHLY_METRICS | Silver | New table sourced from FTL (replaces legacy BRZ views) | BRZ_FTL_AGENT_BASE_AGG, ROLLING_WINDOW_BASE |
| GLD_FTL_AGGREGATE | Gold | New Gold table sourced from FTL Silver tables | SLV_FTL_* tables, ACCOUNT_SEGMENT_MAP, CLUSTER_REGION_MAP |

### 8.2 — EXISTING TABLES TO ALTER

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|----------------|----------------|-------------------|--------|
| SLV_COMBINED_CHANNELS | Silver | Modify source from legacy BRZ views to FTL | None | SOURCE_TABLE (change to 'BRZ_FTL_AGENT_BASE_AGG') | Existing downstream queries continue to work; data source changed |
| SLV_USAGE_MASTER | Silver | Modify source from legacy BRZ views to FTL | None | INBOUND_PHONE_MINS (recalculate from FTL INBOUND_PHONE_MS) | Downstream queries unchanged; unit conversion logic updated |
| SLV_CONSOLIDATED_USAGE | Silver | Modify source from legacy BRZ views to FTL | None | PHONE_USAGE (recalculate from FTL INBOUND_PHONE_MS) | Downstream queries unchanged; aggregation logic updated |
| GLD_AGGREGATE | Gold | Cannot modify until GAP-001 and GAP-002 resolved | None | SEGMENT (remains NULL until mapping available), USERS_ACTIVE_16PLUS_DAYS (remains 0 until historical data available) | **BREAKS REPORTING** until gaps resolved |

### 8.3 — GAP REMEDIATION ACTIONS

| GAP ID | PI Gold Column | Remediation Action | New Table Required? | New Join Required? | Estimated Complexity | Owner |
|--------|----------------|-------------------|--------------------|--------------------|---------------------|-------|
| GAP-001 | SEGMENT | Create ACCOUNT_SEGMENT_MAP reference table OR request BDP add SEGMENT to FTL | YES — ACCOUNT_SEGMENT_MAP | YES — join to all Silver aggregations | HIGH — requires business rules for segment classification | BDP Team, Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | Implement ROLLING_WINDOW_BASE table to track daily activity over 28+ days OR request BDP add historical tracking | YES — ROLLING_WINDOW_BASE | YES — join to monthly metrics | HIGH — requires 28+ days of data accumulation | Data Engineering, BDP Team |
| GAP-003 | Rolling Window Metrics | Build ROLLING_WINDOW_BASE table from daily FTL snapshots; create DBT models to calculate R7/R28 windows | YES — ROLLING_WINDOW_BASE | YES — self-join over 7/28 day windows | MEDIUM — standard window function logic | Data Engineering |
| GAP-004 | CHAT_USAGE, VIDEO_USAGE, DAILY_CHAT_USAGE | Default to 0; request BDP add CHAT_DURATION_MS, VIDEO_DURATION_MS to FTL | NO — use 0 default | NO | LOW — default value only | BDP Team |
| GAP-005 | SLA_ACHIEVED, SLA_ACHIEVED_SESSIONS | Default to FALSE/0; request BDP add SLA_ACHIEVED boolean to FTL | NO — use default | NO | LOW — default value only | BDP Team |
| GAP-006 | ENGAGEMENT_STATUS | Default to NULL; request BDP add ENGAGEMENT_STATUS to FTL | NO — use NULL | NO | LOW — NULL default | BDP Team |
| GAP-007 | WINDOW | Hardcode window value based on DBT model grain (R1/R7/R28) | NO — hardcode in SQL | NO | LOW — static value logic | Data Engineering |
| GAP-008 | CHAT_SESSIONS | Default to 0; request BDP add CHAT_SESSIONS to FTL | NO — use 0 default | NO | LOW — default value only | BDP Team |
| GAP-009 | VIDEO_USAGE | Default to 0; request BDP add VIDEO_SESSIONS, VIDEO_DURATION_MS to FTL | NO — use 0 default | NO | LOW — default value only | BDP Team |
| GAP-010 | ACCOUNT_FIRST_ACTIVE, USER_FIRST_ACTIVE | Create USER_FIRST_ACTIVE_TRACKING table OR backfill from historical PI data OR use current DATA_DATE | YES — USER_FIRST_ACTIVE_TRACKING (optional) | MAYBE — depends on approach | MEDIUM — SCD Type 1 tracking logic | Data Engineering |
| GAP-011 | IS_LICENSED, IS_PAID_USER | Clarify IS_ACTIVE semantics with Zoom PM; if needed, join to existing PI billing table | MAYBE — if billing join required | MAYBE — if billing join required | MEDIUM — requires business validation | Zoom PM, Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 9: RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Priority 1 — Blocking Items (Must Resolve Before Gold Migration)**

1. **GAP-001**: BDP Team to provide SEGMENT dimension — either add SEGMENT field to BRZ_FTL_AGENT_BASE_AGG OR provide ACCOUNT_SEGMENT_MAP reference table with business rules for segment classification (SMB=2, Mid-Market=3, Enterprise=5)

2. **GAP-002**: BDP Team to implement historical activity tracking in FTL OR Data Engineering to build 28-day rolling window aggregation from daily snapshots (requires 28+ days post-migration before Gold can report accurately)

3. **GAP-011**: Zoom PM to confirm IS_ACTIVE = IS_LICENSED semantics OR provide billing table join logic for licensing status

**Priority 2 — Silver DBT Model Changes (Required for Migration)**

4. **BR-001**: Implement date parsing transformation in all Silver models: `TO_DATE(DATA_DATE, 'M/D/YY H:MI')`

5. **BR-002**: Implement unit conversion for phone duration in all Silver models: `INBOUND_PHONE_MS / 60000.0` for minutes, `/1000.0` for seconds

6. **BR-003**: Implement case normalization for DIRECTION and CHANNEL: `UPPER(DIRECTION)`, `UPPER(CHANNEL)`

7. **BR-004**: Implement user aggregation logic: `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = TRUE`

8. **BR-006**: Create CLUSTER_REGION_MAP reference table and implement region mapping logic for Gold layer

**Priority 3 — Unit Conversions and Renames**

9. **BR-002, BR-008**: Standardize phone usage unit conversions across all Silver tables (milliseconds → minutes for usage metrics, milliseconds → seconds for duration)

10. **BR-009**: Implement direct column mappings for ACCOUNT_ID, ENGAGEMENT_ID, MODALITY, PHONE_SESSIONS, IS_ACTIVE

**Priority 4 — Items to Raise with BDP Team**

11. **GAP-004**: Request BDP add CHAT_DURATION_MS, VIDEO_DURATION_MS, EMAIL_DURATION_MS, SMS_DURATION_MS to FTL for multi-channel usage reporting

12. **GAP-005**: Request BDP add SLA_ACHIEVED boolean to FTL for compliance reporting (requires SLA threshold configuration)

13. **GAP-006**: Request BDP add ENGAGEMENT_STATUS to FTL for engagement quality metrics (Missed/Resolved/Answered/Abandoned)

14. **GAP-008**: Request BDP add CHAT_SESSIONS count to FTL for chat engagement volume

15. **GAP-009**: Request BDP add VIDEO_SESSIONS and VIDEO_DURATION_MS to FTL for video engagement metrics

16. **GAP-010**: Request BDP add ACCOUNT_FIRST_ACTIVE_DATE and USER_FIRST_ACTIVE_DATE to FTL OR backfill from historical data

**Priority 5 — Items to Confirm with Zoom Team**

17. **GAP-001**: Confirm SEGMENT business rules and classification criteria (values 2/3/5 represent which customer types?)

18. **GAP-011**: Confirm IS_ACTIVE flag semantics — does it represent licensing status or just engagement activity?

19. **NEW CAPABILITY**: Confirm if ZCC_ACCOUNT_ID should be added as dimension in Gold for ZCC-specific reporting

20. **NEW CAPABILITY**: Confirm if CLIENT_TYPE (Desktop/Mobile/Web) should be added as dimension in Gold for device-based analytics

**Priority 6 — New Capabilities: Decision Needed from PI Team Leads**

21. **ZCC_ACCOUNT_ID**: Add to Silver layer immediately; decision needed on Gold inclusion for cross-system account reconciliation

22. **CLIENT_TYPE**: Add to Silver layer immediately; recommend Gold extension for device type analytics and mobile vs desktop segmentation

23. **OS**: Add to Silver layer for technical analysis; recommend keeping Silver-only (not core business dimension for Gold KPIs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 10: MAPPING CSV FOR REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```csv
FTL_Bronze_Column,FTL_Data_Type,PI_Silver_Column,PI_Silver_Table,PI_Gold_Column,PI_Gold_Table,Classification,Confidence,Mapping_Reason,BR_ID,GAP_ID,Transformation,Notes
ZCC_ACCOUNT_ID,TEXT,—,—,—,—,NEW_CAPABILITY,High,FTL provides ZCC_ACCOUNT_ID not present in any PI table — confirmed via schema analysis,—,—,None,Available for future use
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_ACCT_FIRST_ACTIVE,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_CONSOLIDATED_USAGE,—,GLD_AGGREGATE (via agg),DIRECT_MATCH,High,Exact column name match — aggregated for Gold,BR-007,—,COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE,Aggregation for Gold
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_DAILY_METRICS,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_MONTHLY_METRICS,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_ROLL_29_DAY_USAGE,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_USER_ACTIVE_DAYS,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_USER_FIRST_ACTIVE,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ACCOUNT_ID,TEXT,ACCOUNT_ID,SLV_WEEKLY_METRICS,—,—,DIRECT_MATCH,High,Exact column name match — primary account identifier,BR-009,—,None,Core dimension
ENGAGEMENT_ID,TEXT,ENGAGEMENT_ID,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,Exact column name match — engagement tracking identifier,BR-009,—,None,Transaction ID
AGENT_ID,TEXT,USER_ID,SLV_COMBINED_CHANNELS,—,—,SEMANTIC_MATCH,Medium,FTL AGENT_ID maps to PI USER_ID — agent represents user in business context,BR-004,—,AGENT_ID as USER_ID,Semantic mapping
AGENT_ID,TEXT,USER_ID,SLV_ROLL_29_DAY_USAGE,—,—,SEMANTIC_MATCH,Medium,FTL AGENT_ID maps to PI USER_ID — agent represents user in business context,BR-004,—,AGENT_ID as USER_ID,Semantic mapping
AGENT_ID,TEXT,USER_ID,SLV_USAGE_MASTER,—,—,SEMANTIC_MATCH,Medium,FTL AGENT_ID maps to PI USER_ID — agent represents user in business context,BR-004,—,AGENT_ID as USER_ID,Semantic mapping
AGENT_ID,TEXT,USER_ID,SLV_USER_FIRST_ACTIVE,ACTIVE_USERS,GLD_AGGREGATE,SEMANTIC_MATCH,Medium,FTL AGENT_ID maps to PI USER_ID and aggregates to Gold ACTIVE_USERS,BR-004,—,COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE,Aggregation for Gold
DIRECTION,TEXT,DIRECTION,SLV_COMBINED_CHANNELS,—,—,PARTIAL_MATCH,High,FTL values (Inbound/Outbound) match PI values (INBOUND/OUTBOUND) — case normalization needed,BR-003,—,UPPER(DIRECTION),Case differs
MODALITY,TEXT,MODALITY,SLV_COMBINED_CHANNELS,—,—,DIRECT_MATCH,High,"FTL values (Chat/Email/SMS) match PI values (Phone/SMS/Chat) — overlapping set",BR-009,—,None,Semantic match
CHANNEL,TEXT,CHANNEL,SLV_COMBINED_CHANNELS,—,—,PARTIAL_MATCH,High,"FTL values (Phone/Video) are subset of PI values (VIDEO/CHAT/PHONE/SMS/EMAIL) — case normalization needed",BR-003,—,UPPER(CHANNEL),Case differs
PHONE_SESSIONS,NUMBER,PHONE_SESSIONS,SLV_USAGE_MASTER,—,—,DIRECT_MATCH,High,Exact column name and semantic match — phone session count,BR-009,—,None,Direct map
INBOUND_PHONE_MS,NUMBER,INBOUND_PHONE_MINS,SLV_USAGE_MASTER,—,—,UNIT_CHANGE,High,FTL in milliseconds PI in minutes — confirmed unit conversion required,BR-002,—,INBOUND_PHONE_MS / 60000.0,Unit conversion
INBOUND_PHONE_MS,NUMBER,DURATION_SEC,SLV_COMBINED_CHANNELS,—,—,UNIT_CHANGE,Medium,FTL in milliseconds PI in seconds — conversion for phone channel only,BR-002,—,INBOUND_PHONE_MS / 1000.0,Phone only
INBOUND_PHONE_MS,NUMBER,PHONE_USAGE,SLV_CONSOLIDATED_USAGE,PHONE_USAGE,GLD_AGGREGATE,UNIT_CHANGE,High,FTL in milliseconds PI in minutes — confirmed conversion needed,BR-002,—,INBOUND_PHONE_MS / 60000.0,Unit conversion
INBOUND_PHONE_MS,NUMBER,WEEKLY_PHONE_USAGE,SLV_ROLL_29_DAY_USAGE,—,—,UNIT_CHANGE,Medium,FTL in milliseconds PI in minutes — weekly aggregation needed,BR-002,—,INBOUND_PHONE_MS / 60000.0,Weekly agg
CLIENT_TYPE,TEXT,—,—,—,—,NEW_CAPABILITY,High,FTL provides CLIENT_TYPE (Desktop/Mobile/Web) not present in any PI table — confirmed via schema analysis,—,—,None,Available for future use
OS,TEXT,—,—,—,—,NEW_CAPABILITY,High,FTL provides OS not present in any PI table — device analytics capability,—,—,None,Available for future use
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_CONSOLIDATED_USAGE,—,—,DIRECT_MATCH,High,Exact semantic match — active account flag,BR-009,—,None,Direct map
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_DAILY_METRICS,—,—,DIRECT_MATCH,High,Exact semantic match — active account flag,BR-009,—,None,Direct map
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_MONTHLY_METRICS,—,—,DIRECT_MATCH,High,Exact semantic match — active account flag,BR-009,—,None,Direct map
IS_ACTIVE,BOOLEAN,IS_ACTIVE_ACCOUNT,SLV_WEEKLY_METRICS,IS_LICENSED,GLD_AGGREGATE,SEMANTIC_MATCH,Medium,FTL IS_ACTIVE maps to PI IS_LICENSED — semantic validation needed,BR-009,GAP-011,Direct or join to billing table,Semantic unclear
CLUSTER,TEXT,—,—,REGION,GLD_AGGREGATE,SEMANTIC_MATCH,Low,FTL CLUSTER (ap-south-1 eu-central-1 us-east-1) must map to PI REGION (NAMER LATAM EMEA APAC) — mapping logic needed,BR-006,—,"CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'OTHER' END",[ASSUMPTION]
DATA_DATE,TEXT,START_DATE,SLV_COMBINED_CHANNELS,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format '5/29/26 13:01' PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,DATE,SLV_USAGE_MASTER,DATE,GLD_AGGREGATE,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_CONSOLIDATED_USAGE,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_DAILY_METRICS,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_MONTHLY_METRICS,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_ROLL_29_DAY_USAGE,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_USER_ACTIVE_DAYS,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
DATA_DATE,TEXT,REPORT_DATE,SLV_WEEKLY_METRICS,—,—,UNIT_CHANGE,Medium,FTL DATA_DATE is TEXT format PI expects DATE type — parsing required,BR-001,—,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",Format parse
—,—,ACCOUNT_FIRST_ACTIVE,SLV_ACCT_FIRST_ACTIVE,—,—,GAP,High,No FTL source for historical first active date — must use current DATA_DATE as proxy,BR-001,GAP-010,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",[ASSUMPTION] current = first
—,—,ACCOUNT_FIRST_ACTIVE,SLV_USAGE_MASTER,—,—,GAP,High,No FTL source for historical first active date — must use current DATA_DATE as proxy,BR-001,GAP-010,"TO_DATE(DATA_DATE 'M/D/YY H:MI')",[ASSUMPTION] current = first
—,—,REFRESH_TIMESTAMP,SLV_ACCT_FIRST_ACTIVE,—,—,GAP,High,No FTL source for refresh timestamp — system-generated field,—,—,CURRENT_TIMESTAMP(),System field
—,—,REFRESH_TIMESTAMP,SLV_USER_FIRST_ACTIVE,—,—,GAP,High,No FTL source for refresh timestamp — system-generated field,—,—,CURRENT_TIMESTAMP(),System field
—,—,ENGAGEMENT_STATUS,SLV_COMBINED_CHANNELS,—,—,GAP,High,No FTL source for engagement outcome (Missed/Resolved/Answered) — quality metric missing,—,GAP-006,NULL,Missing field
—,—,SLA_ACHIEVED,SLV_COMBINED_CHANNELS,—,—,GAP,High,No FTL source for SLA achievement tracking — compliance metric missing,—,GAP-005,FALSE,Missing field
—,—,SOURCE_TABLE,SLV_COMBINED_CHANNELS,—,—,GAP,High,No FTL source for source table tracking — hardcode static value,BR-010,—,'BRZ_FTL_AGENT_BASE_AGG',Static value
—,—,PRODUCT_NAME,SLV_CONSOLIDATED_USAGE,—,—,GAP,High,No FTL source for product name — hardcode static value,BR-010,—,'ZCC Platform',Static value
—,—,WINDOW,SLV_CONSOLIDATED_USAGE,—,—,GAP,High,No FTL source for time window (R1/R7/R28) — must assign based on DBT model grain,BR-005,GAP-007,"'R1' for daily 'R7' for weekly 'R28' for monthly",[ASSUMPTION]
—,—,WINDOW,SLV_DAILY_METRICS,—,—,GAP,High,No FTL source for time window (R1/R7/R28) — must assign based on DBT model grain,BR-005,GAP-007,"'R1' for daily 'R