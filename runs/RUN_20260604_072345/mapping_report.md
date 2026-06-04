

🔍 **STEP 1: Schema Discovery** — Discovered 1 source table (BRZ_FTL_AGENT_BASE_AGG with 14 columns), 20 Silver tables, and 1 Gold table (GLD_AGGREGATE with 8 columns)

🔍 **STEP 2: Data Profiling** — Profiled source Bronze table, all active Silver tables (SLV_ prefix), and Gold target to understand column distributions, data types, and sample values

🔍 **STEP 3: Silver Layer Mapping Analysis** — Analyzed column-level lineage from FTL Bronze to Silver tables, identified 11 critical gaps including missing historical dates, SLA metrics, and usage windows

🔍 **STEP 4: Gold Layer Mapping Analysis** — Analyzed Bronze to Gold direct mapping, identified 3 blocking gaps (SEGMENT, USERS_ACTIVE_16PLUS_DAYS, REGION derivation) with 45% overall confidence

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1: EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG  
**Target PI Gold Table:** ZOOM_AI_POC.GOLD.GLD_AGGREGATE  
**Migration Readiness Score:** 42/100  

**Total FTL columns analyzed:** 14  
**Successfully mapped:** 5 (35.7%)  
**Partially mapped:** 3 (21.4%)  
**New capabilities (no PI equivalent):** 3 (21.4%)  
**Gaps (PI Gold columns with no FTL source):** 3  
→ **GAP-001**: SEGMENT (customer segmentation dimension)  
→ **GAP-002**: USERS_ACTIVE_16PLUS_DAYS (temporal activity metric)  
→ **GAP-003**: REGION (geographic dimension - derivable from CLUSTER with mapping)  

**Blocking items:** 2 (GAP-001, GAP-002)

**Overall Assessment:**  
The FTL Bronze source provides foundational engagement-level data with strong coverage for account/user identifiers and phone usage metrics. However, critical dimensional attributes (SEGMENT) and temporal activity metrics (16+ day active users) are completely absent from the source, creating blocking gaps that prevent a complete Gold layer migration. Additionally, the source operates at engagement-level grain while Gold requires date/region/segment aggregation, introducing complexity in transformation logic. REGION can be derived from CLUSTER with a mapping table (60% confidence), but SEGMENT has no identifiable source and USERS_ACTIVE_16PLUS_DAYS requires historical activity tracking data not present in BRZ_FTL_AGENT_BASE_AGG.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2: GAP IMPACT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | Why It's a Gap | Impact on Gold Output | Blocks Migration? | Action Required | Raise With |
|--------|----------------|----------------|----------------------|-------------------|-----------------|------------|
| GAP-001 | SEGMENT | No customer segmentation data in FTL Bronze source; requires external dimension table or business logic | All Gold rows will have NULL for SEGMENT dimension; breaks core reporting structure by segment cohorts | **YES** | BDP team must provide SEGMENT mapping table (ACCOUNT_ID → SEGMENT) or expose in new FTL column | BDP Team & Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | FTL source is single-date snapshot without historical user activity tracking over 28-day windows | Cannot calculate power user engagement metric; breaks MAU cohort analysis and retention dashboards | **YES** | Requires historical daily user activity table from BDP OR calculation logic in new Silver intermediate table using historical FTL data | BDP Team & Data Engineering |
| GAP-003 | REGION | FTL has CLUSTER (aws regions) but no direct REGION business dimension | Can derive from CLUSTER using mapping logic, but requires assumption validation | **NO** | Create CLUSTER → REGION mapping table; validate with business stakeholders that CLUSTER mapping is accurate | Data Engineering & Zoom PM |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | No historical account creation/first activity date in FTL Bronze | Silver table SLV_ACCT_FIRST_ACTIVE cannot be populated; breaks account lifecycle analysis | NO | Requires historical MIN(DATA_DATE) calculation per account from all historical FTL records OR separate account dimension table | BDP Team & Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | No historical user/agent creation/first activity date in FTL Bronze | Silver table SLV_USER_FIRST_ACTIVE cannot be populated; breaks user onboarding funnel analysis | NO | Requires historical MIN(DATA_DATE) calculation per user from all historical FTL records OR separate user dimension table | BDP Team & Data Engineering |
| GAP-006 | CHAT_SESSIONS | FTL source only has PHONE_SESSIONS count; no chat session count metric despite MODALITY='Chat' | Silver SLV_USAGE_MASTER will have NULL for CHAT_SESSIONS; breaks multi-channel usage reporting | NO | BDP must add CHAT_SESSIONS column to FTL Bronze OR derive from engagement count WHERE MODALITY='Chat' | BDP Team |
| GAP-007 | SLA_ACHIEVED_SESSIONS | No SLA achievement indicator in FTL Bronze for any engagement type | Silver tables cannot calculate SLA compliance metrics; breaks QoS reporting | NO | BDP must add SLA_ACHIEVED flag/timestamp to FTL Bronze based on engagement resolution time | BDP Team |
| GAP-008 | ENGAGEMENT_STATUS | No engagement outcome/status field (e.g., Resolved, Missed, Abandoned) in FTL Bronze | Silver SLV_COMBINED_CHANNELS cannot track engagement funnel stages; breaks conversion analysis | NO | BDP must add ENGAGEMENT_STATUS column to FTL Bronze | BDP Team |
| GAP-009 | WINDOW (R1/R7/R28) | FTL Bronze is daily snapshot without rolling window calculations | Silver metric tables (DAILY_METRICS, WEEKLY_METRICS, MONTHLY_METRICS) cannot populate WINDOW dimension | NO | Build rolling window calculation logic in Silver DBT models using historical FTL data with LAG/WINDOW functions | Data Engineering |
| GAP-010 | IS_PAID_USER | No subscription/licensing status per user in FTL Bronze | Silver SLV_ROLL_29_DAY_USAGE cannot filter by paid status; breaks revenue cohort analysis | NO | Join to existing PI billing/subscription table OR request BDP add to FTL Bronze | BDP Team / Data Engineering |
| GAP-011 | ACTIVE_DAYS_LAST_7/28 | FTL Bronze is single-date snapshot without daily activity tracking per user | Silver tables cannot calculate rolling active day counts; breaks engagement intensity metrics | NO | Build rolling calculation logic in Silver DBT models using historical FTL data with COUNTIF(DISTINCT DATE) | Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3: FULL COLUMN LINEAGE MAPPING TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Gold Column | PI Gold Table | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|----------------|---------------|----------------|------------|----------------|-------|--------|----------------|-------|
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER | DATE | GLD_AGGREGATE | UNIT_CHANGE | Medium | FTL has text format "5/29/26 13:01" confirmed via distinct value query; PI expects DATE type - requires parsing | BR-001 | — | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | Format validation needed |
| DATA_DATE | TEXT | START_DATE | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Medium | Same text-to-date conversion as above for engagement start tracking | BR-001 | — | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | Reuse BR-001 |
| DATA_DATE | TEXT | REPORT_DATE | SLV_CONSOLIDATED_USAGE | — | — | UNIT_CHANGE | Medium | Same text-to-date conversion for metrics reporting date dimension | BR-001 | — | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | Reuse BR-001 |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Exact column name and TEXT data type match confirmed via schema | — | — | None | — |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_ACCT_FIRST_ACTIVE | — | — | DIRECT_MATCH | High | Exact column name and TEXT data type match | — | — | None | — |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Exact column name and TEXT data type match | — | — | None | — |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_CONSOLIDATED_USAGE | — | — | DIRECT_MATCH | High | Exact column name and TEXT data type match | — | — | None | — |
| ACCOUNT_ID | TEXT | — | — | ACTIVE_ACCOUNTS | GLD_AGGREGATE | GRAIN_CHANGE | Medium | Requires aggregation COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE=true grouped by DATE, REGION, SEGMENT | BR-002 | — | COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT | Aggregation logic |
| AGENT_ID | TEXT | USER_ID | SLV_USAGE_MASTER | — | — | SEMANTIC_MATCH | High | FTL calls it AGENT_ID, PI calls it USER_ID - both represent agent/user entity confirmed via cardinality (25 distinct in both) | BR-003 | — | AGENT_ID AS USER_ID | Semantic rename |
| AGENT_ID | TEXT | USER_ID | SLV_USER_FIRST_ACTIVE | — | — | SEMANTIC_MATCH | High | Same agent-to-user semantic mapping | BR-003 | — | AGENT_ID AS USER_ID | Semantic rename |
| AGENT_ID | TEXT | USER_ID | SLV_COMBINED_CHANNELS | — | — | SEMANTIC_MATCH | High | Same agent-to-user semantic mapping | BR-003 | — | AGENT_ID AS USER_ID | Semantic rename |
| AGENT_ID | TEXT | — | — | ACTIVE_USERS | GLD_AGGREGATE | GRAIN_CHANGE | Medium | Requires aggregation COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE=true grouped by DATE, REGION, SEGMENT | BR-004 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT | Aggregation logic |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Exact column name and TEXT data type match confirmed via schema | — | — | None | — |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | High | FTL has "Inbound"/"Outbound" (2 distinct), PI has "INBOUND"/"OUTBOUND" - case differs but values match confirmed via query | BR-005 | — | UPPER(DIRECTION) | Case standardization |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | FTL has "Chat"/"Email"/"SMS" (3 distinct), PI has "Phone"/"SMS"/"Chat" (5 distinct) - overlapping values confirmed via query | — | — | None | Subset match acceptable |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | CASE_CHANGE | Medium | FTL has "Phone"/"Video" (2 distinct), PI has "VIDEO"/"CHAT"/"PHONE"/"EMAIL"/"SMS" (5 distinct) - partial overlap requires case change | BR-006 | — | UPPER(CHANNEL) | FTL subset of PI values |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Exact column name and NUMBER data type match confirmed via schema | — | — | None | — |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | — | — | UNIT_CHANGE | High | FTL in milliseconds (3784798 sample), PI in minutes (4.94 sample) - 3784798ms ÷ 60000 = 63.08min vs 4.94min indicates aggregation needed | BR-007 | — | INBOUND_PHONE_MS / 60000.0 | Milliseconds to minutes |
| INBOUND_PHONE_MS | NUMBER | DURATION_SEC | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Low | FTL milliseconds to PI seconds, but only phone duration available (no chat/video duration) | BR-008 | — | INBOUND_PHONE_MS / 1000.0 WHERE CHANNEL='Phone' | Low confidence - incomplete |
| INBOUND_PHONE_MS | NUMBER | — | — | PHONE_USAGE | GLD_AGGREGATE | UNIT_CHANGE | Medium | Aggregation and unit conversion needed; FTL milliseconds to PI minutes (float) | BR-009 | — | SUM(INBOUND_PHONE_MS) / 60000.0 GROUP BY DATE, REGION, SEGMENT | Minutes aggregated |
| INBOUND_PHONE_MS | NUMBER | PHONE_USAGE | SLV_CONSOLIDATED_USAGE | — | — | UNIT_CHANGE | Medium | Same conversion as above for Silver usage table | BR-009 | — | SUM(INBOUND_PHONE_MS) / 60000.0 GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID | Rolling window context |
| INBOUND_PHONE_MS | NUMBER | WEEKLY_PHONE_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | UNIT_CHANGE | Medium | Same conversion with 7-day rolling window | BR-010 | — | SUM(INBOUND_PHONE_MS) OVER (PARTITION BY USER_ID ORDER BY DATE ROWS 6 PRECEDING) / 60000.0 | 7-day rolling sum |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE | IS_LICENSED | GLD_AGGREGATE | SEMANTIC_MATCH | Medium | FTL IS_ACTIVE (boolean) maps to PI IS_ACTIVE_ACCOUNT and Gold IS_LICENSED - assumes active = licensed [ASSUMPTION] | BR-011 | — | IS_ACTIVE AS IS_LICENSED | Validate business assumption |
| CLUSTER | TEXT | — | — | REGION | GLD_AGGREGATE | GRAIN_CHANGE | Medium | FTL has AWS clusters (ap-south-1, eu-central-1, us-east-1), PI has business regions (NAMER, LATAM, EMEA, APAC) - requires mapping table | BR-012 | GAP-003 | CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' ELSE 'UNKNOWN' END | Needs validation |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | High | FTL provides Desktop/Mobile/Web breakdown (3 distinct values) not present in any PI table | — | — | None | Available for enrichment |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | Medium | FTL provides OS dimension but only 1 sample value observed | — | — | None | Low cardinality in sample |
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | High | FTL provides secondary account identifier (5 distinct) not used in PI schema | — | — | None | Additional join key |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE | — | — | GAP | High | No column found in FTL matching first account activity date concept - requires historical MIN(DATA_DATE) calculation | BR-013 | GAP-004 | No FTL source available | Historical aggregation needed |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | Same gap as above | BR-013 | GAP-004 | No FTL source available | Reuse GAP-004 logic |
| — | — | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE | — | — | GAP | High | No column found in FTL matching first user activity date concept - requires historical MIN(DATA_DATE) calculation per AGENT_ID | BR-014 | GAP-005 | No FTL source available | Historical aggregation needed |
| — | — | USER_FIRST_ACTIVE | SLV_USAGE_MASTER | — | — | GAP | High | Same gap as above | BR-014 | GAP-005 | No FTL source available | Reuse GAP-005 logic |
| — | — | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | FTL has PHONE_SESSIONS but no CHAT_SESSIONS count despite MODALITY='Chat' being present | BR-015 | GAP-006 | No FTL source available | Needs BDP to add column |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | No SLA achievement indicator in FTL Bronze | BR-016 | GAP-007 | No FTL source available | Needs BDP to add column |
| — | — | SLA_ACHIEVED | SLV_COMBINED_CHANNELS | — | — | GAP | High | Same SLA gap as above | BR-016 | GAP-007 | No FTL source available | Reuse GAP-007 |
| — | — | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | — | — | GAP | High | No engagement outcome/status in FTL Bronze | BR-017 | GAP-008 | No FTL source available | Needs BDP to add column |
| — | — | SOURCE_TABLE | SLV_COMBINED_CHANNELS | — | — | GAP | Low | Metadata field not in FTL; can hardcode as 'BRZ_FTL_AGENT_BASE_AGG' | BR-018 | — | 'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE | System-generated |
| — | — | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE | — | — | GAP | Low | System timestamp not in FTL; can use CURRENT_TIMESTAMP() at load time | BR-019 | — | CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP | System-generated |
| — | — | REFRESH_TIMESTAMP | SLV_USER_FIRST_ACTIVE | — | — | GAP | Low | Same system timestamp as above | BR-019 | — | CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP | Reuse BR-019 |
| — | — | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | — | — | GAP | Low | Static dimension not in FTL; hardcode as 'ZCC Platform' | BR-020 | — | 'ZCC Platform' AS PRODUCT_NAME | Hardcoded value |
| — | — | WINDOW | SLV_CONSOLIDATED_USAGE | — | — | GAP | High | Rolling window indicator (R1/R7/R28) not in FTL; requires calculation logic based on lookback period | BR-021 | GAP-009 | No FTL source available | Build in Silver DBT |
| — | — | WINDOW | SLV_DAILY_METRICS | — | — | GAP | High | Same window gap as above | BR-021 | GAP-009 | No FTL source available | Reuse GAP-009 logic |
| — | — | WINDOW | SLV_WEEKLY_METRICS | — | — | GAP | High | Same window gap as above | BR-021 | GAP-009 | No FTL source available | Reuse GAP-009 logic |
| — | — | WINDOW | SLV_MONTHLY_METRICS | — | — | GAP | High | Same window gap as above | BR-021 | GAP-009 | No FTL source available | Reuse GAP-009 logic |
| — | — | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No subscription/licensing status per user in FTL | BR-022 | GAP-010 | No FTL source available | Join to billing table |
| — | — | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | FTL is single-date snapshot; requires historical calculation | BR-023 | GAP-011 | No FTL source available | Build windowing logic |
| — | — | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Same active days gap as above | BR-023 | GAP-011 | No FTL source available | Reuse GAP-011 logic |
| — | — | DAILY_CHAT_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | No chat usage metric in FTL (only phone) | BR-024 | GAP-006 | No FTL source available | Blocked by GAP-006 |
| — | — | CHAT_USAGE | SLV_DAILY_METRICS | — | — | GAP | High | Same chat usage gap | BR-024 | GAP-006 | No FTL source available | Reuse GAP-006 |
| — | — | CHAT_USAGE | SLV_WEEKLY_METRICS | — | — | GAP | High | Same chat usage gap | BR-024 | GAP-006 | No FTL source available | Reuse GAP-006 |
| — | — | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | GAP | High | FTL has CHANNEL='Video' but no VIDEO_USAGE metric | BR-025 | — | Derive from engagement counts WHERE CHANNEL='Video' | Derivable from FTL |
| — | — | ACTIVE_USERS | SLV_CONSOLIDATED_USAGE | — | — | GAP | Medium | Requires COUNT(DISTINCT AGENT_ID) aggregation per account/date/window | BR-026 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID | Aggregation logic |
| — | — | ACTIVE_USERS | SLV_DAILY_METRICS | — | — | GAP | Medium | Same active users aggregation | BR-026 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID | Reuse BR-026 |
| — | — | ACTIVE_USERS | SLV_WEEKLY_METRICS | — | — | GAP | Medium | Same active users aggregation | BR-026 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID | Reuse BR-026 |
| — | — | ACTIVE_USERS | SLV_MONTHLY_METRICS | — | — | GAP | Medium | Same active users aggregation | BR-026 | — | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID | Reuse BR-026 |
| — | — | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | — | — | GAP | High | Requires historical daily activity calculation per user | BR-027 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | — | — | GAP | High | Same as above for 4-7 day cohort | BR-028 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | — | — | GAP | High | Same as above for 16+ day cohort | BR-029 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | — | — | USERS_ACTIVE_16PLUS_DAYS | GLD_AGGREGATE | GAP | High | No temporal activity tracking in FTL Bronze - requires historical user activity over 28-day windows | BR-029 | GAP-002 | No FTL source available | **BLOCKING** |
| — | — | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Requires historical daily activity calculation | BR-030 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Same as above for 4-7 day cohort in 7-day window | BR-030 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Same as above for 28-day window | BR-030 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Same as above for 16+ day cohort in 28-day window | BR-030 | GAP-011 | No FTL source available | Blocked by GAP-011 |
| — | — | — | — | SEGMENT | GLD_AGGREGATE | GAP | High | No customer segmentation data in FTL Bronze - no columns match this concept confirmed via schema scan | — | GAP-001 | No FTL source available | **BLOCKING** |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4: TRANSFORMATION GUIDE (Business Rules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|-----------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | DATA_DATE | DATE / START_DATE / REPORT_DATE | UNIT_CHANGE | `TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')` | FTL stores date as TEXT "5/29/26 13:01"; PI expects DATE type for all date dimensions and partitioning | DATA_DATE format consistency | [ASSUMPTION] All DATA_DATE values follow M/D/YY HH24:MI format |
| BR-002 | ACCOUNT_ID | ACTIVE_ACCOUNTS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT ACCOUNT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT` | Gold requires account count metric aggregated at date/region/segment grain; FTL is engagement-level | IS_ACTIVE field, SEGMENT derivation (GAP-001), REGION mapping (BR-012) | [ASSUMPTION] IS_ACTIVE indicates account is active for counting purposes |
| BR-003 | AGENT_ID | USER_ID | SEMANTIC_MATCH | `AGENT_ID AS USER_ID` | FTL uses AGENT_ID terminology; PI uses USER_ID - both represent the same agent/user entity | None | [ASSUMPTION] Agent and User are semantically equivalent entities in PI schema |
| BR-004 | AGENT_ID | ACTIVE_USERS (Gold) | GRAIN_CHANGE | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY DATE, REGION, SEGMENT` | Gold requires user count metric aggregated at date/region/segment grain; FTL is engagement-level | IS_ACTIVE field, SEGMENT derivation (GAP-001), REGION mapping (BR-012) | [ASSUMPTION] IS_ACTIVE applies to user activity for counting purposes |
| BR-005 | DIRECTION | DIRECTION | CASE_CHANGE | `UPPER(DIRECTION)` | FTL has "Inbound"/"Outbound" (mixed case); PI standardizes to "INBOUND"/"OUTBOUND" (uppercase) | None | None |
| BR-006 | CHANNEL | CHANNEL | CASE_CHANGE | `UPPER(CHANNEL)` | FTL has "Phone"/"Video" (mixed case); PI standardizes to uppercase; note FTL has 2 of 5 PI values | None | [ASSUMPTION] FTL CHANNEL is subset of PI CHANNEL domain; missing EMAIL/CHAT/SMS may appear in MODALITY |
| BR-007 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS | UNIT_CHANGE | `INBOUND_PHONE_MS / 60000.0` | FTL stores phone duration in milliseconds; PI expects minutes (FLOAT) | INBOUND_PHONE_MS > 0 | None |
| BR-008 | INBOUND_PHONE_MS | DURATION_SEC | UNIT_CHANGE | `CASE WHEN CHANNEL = 'Phone' THEN INBOUND_PHONE_MS / 1000.0 ELSE NULL END` | FTL only has phone duration; PI expects duration in seconds for all channels | CHANNEL field populated | [LOW CONFIDENCE] Only phone duration available; chat/video/email durations missing |
| BR-009 | INBOUND_PHONE_MS | PHONE_USAGE (Gold & Silver) | UNIT_CHANGE | `SUM(INBOUND_PHONE_MS) / 60000.0 GROUP BY DATE, REGION, SEGMENT` (Gold) or `SUM(INBOUND_PHONE_MS) / 60000.0 GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID` (Silver) | Aggregate phone usage from milliseconds to minutes; Gold grouped by dimensions, Silver by rolling windows | WINDOW calculation logic (GAP-009 for Silver) | None |
| BR-010 | INBOUND_PHONE_MS | WEEKLY_PHONE_USAGE | UNIT_CHANGE | `SUM(INBOUND_PHONE_MS) OVER (PARTITION BY USER_ID ORDER BY DATE ROWS 6 PRECEDING) / 60000.0` | 7-day rolling window sum of phone usage in minutes per user | Historical 7 days of FTL data available | None |
| BR-011 | IS_ACTIVE | IS_LICENSED / IS_ACTIVE_ACCOUNT | SEMANTIC_MATCH | `IS_ACTIVE AS IS_LICENSED` (Gold) or `IS_ACTIVE AS IS_ACTIVE_ACCOUNT` (Silver) | FTL IS_ACTIVE boolean maps to PI account licensing/activity status | None | [ASSUMPTION] IS_ACTIVE in FTL represents licensed/active status - MUST be validated with BDP team |
| BR-012 | CLUSTER | REGION | GRAIN_CHANGE | `CASE WHEN CLUSTER LIKE 'us-%' THEN 'NAMER' WHEN CLUSTER LIKE 'eu-%' THEN 'EMEA' WHEN CLUSTER LIKE 'ap-%' THEN 'APAC' WHEN CLUSTER LIKE 'sa-%' THEN 'LATAM' ELSE 'UNKNOWN' END` | Map AWS cluster regions to business regions; FTL has infrastructure dimension, PI needs business geography | Complete CLUSTER → REGION mapping table/logic | [ASSUMPTION] AWS region prefixes map to business regions; requires validation with Zoom PM - **relates to GAP-003** |
| BR-013 | — | ACCOUNT_FIRST_ACTIVE | GAP | `NULL AS ACCOUNT_FIRST_ACTIVE -- GAP ID: GAP-004` | No source for first account activity date; requires historical MIN(DATA_DATE) per ACCOUNT_ID from all FTL records | Historical FTL data from inception | Need BDP to provide account dimension table OR calculate from historical FTL Bronze snapshots |
| BR-014 | — | USER_FIRST_ACTIVE | GAP | `NULL AS USER_FIRST_ACTIVE -- GAP ID: GAP-005` | No source for first user activity date; requires historical MIN(DATA_DATE) per AGENT_ID from all FTL records | Historical FTL data from inception | Need BDP to provide user dimension table OR calculate from historical FTL Bronze snapshots |
| BR-015 | — | CHAT_SESSIONS | GAP | `NULL AS CHAT_SESSIONS -- GAP ID: GAP-006` | FTL only has PHONE_SESSIONS; no chat session count despite MODALITY='Chat' present | BDP to add CHAT_SESSIONS column to FTL | Could derive as COUNT(DISTINCT ENGAGEMENT_ID WHERE MODALITY='Chat') if engagement grain is per-session |
| BR-016 | — | SLA_ACHIEVED / SLA_ACHIEVED_SESSIONS | GAP | `NULL AS SLA_ACHIEVED_SESSIONS -- GAP ID: GAP-007` | No SLA achievement indicator in FTL Bronze for any engagement type | BDP to add SLA timestamp/flag to FTL | Requires SLA resolution time tracking in source system |
| BR-017 | — | ENGAGEMENT_STATUS | GAP | `NULL AS ENGAGEMENT_STATUS -- GAP ID: GAP-008` | No engagement outcome/status field (Resolved, Missed, Abandoned, etc.) | BDP to add ENGAGEMENT_STATUS to FTL | Requires engagement lifecycle tracking in source system |
| BR-018 | — | SOURCE_TABLE | GAP | `'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE` | Metadata field to track data lineage in combined channel view | None | Hardcoded constant - no gap impact |
| BR-019 | — | REFRESH_TIMESTAMP | GAP | `CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP` | System timestamp to track ETL load time for incremental processing | None | System-generated at load time - no gap impact |
| BR-020 | — | PRODUCT_NAME | GAP | `'ZCC Platform' AS PRODUCT_NAME` | Static product dimension for multi-product reporting | None | Hardcoded constant - no gap impact |
| BR-021 | — | WINDOW | GAP | `NULL AS WINDOW -- GAP ID: GAP-009` | Rolling window indicator (R1=1day, R7=7day, R28=28day) not in FTL; requires calculation logic based on lookback period | Historical FTL data for windowing | Build window calculation in Silver DBT models using DATE-based partitioning |
| BR-022 | — | IS_PAID_USER | GAP | `NULL AS IS_PAID_USER -- GAP ID: GAP-010` | No subscription/licensing status per user in FTL | BDP to add to FTL OR join to existing PI billing table | Join to billing dimension table OR derive from account licensing status |
| BR-023 | — | ACTIVE_DAYS_LAST_7 / ACTIVE_DAYS_LAST_28 | GAP | `NULL AS ACTIVE_DAYS_LAST_7 -- GAP ID: GAP-011` | FTL is single-date snapshot; requires COUNT(DISTINCT DATE) per user over rolling window | Historical FTL data for 28+ days | Build using window function: `COUNT(DISTINCT DATE) OVER (PARTITION BY USER_ID ORDER BY DATE ROWS 27 PRECEDING)` |
| BR-024 | — | CHAT_USAGE / DAILY_CHAT_USAGE | GAP | `NULL AS CHAT_USAGE -- GAP ID: GAP-006` | No chat usage metric in FTL (only INBOUND_PHONE_MS for phone) | BDP to add CHAT_DURATION_MS or similar to FTL | Blocked by GAP-006 - need chat session duration measurement |
| BR-025 | CHANNEL | VIDEO_USAGE | GAP | `COUNT(DISTINCT ENGAGEMENT_ID) WHERE CHANNEL = 'Video'` | FTL has CHANNEL='Video' but no VIDEO_USAGE metric; can derive from engagement counts | None | [LOW CONFIDENCE] Assumes 1 engagement = 1 video session; need duration metric for true usage |
| BR-026 | AGENT_ID | ACTIVE_USERS (Silver metrics) | GAP | `COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = true GROUP BY REPORT_DATE, WINDOW, ACCOUNT_ID` | Silver metrics tables require active user count per account/date/window | WINDOW calculation (BR-021) | Aggregation logic needed in Silver DBT models |
| BR-027 | — | USERS_ACTIVE_1_DAY | GAP | `NULL AS USERS_ACTIVE_1_DAY -- GAP ID: GAP-011` | Requires COUNT of users with exactly 1 active day in 7-day window | Historical user-date activity tracking | Blocked by GAP-011 - need daily user activity history |
| BR-028 | — | USERS_ACTIVE_4_7_DAYS | GAP | `NULL AS USERS_ACTIVE_4_7_DAYS -- GAP ID: GAP-011` | Requires COUNT of users with 4-7 active days in 7-day window | Historical user-date activity tracking | Blocked by GAP-011 - need daily user activity history |
| BR-029 | — | USERS_ACTIVE_16PLUS_DAYS | GAP | `NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-002` | Requires COUNT of power users with 16+ active days in 28-day window | Historical user-date activity tracking over 28 days | **BLOCKING GAP** - Gold metric cannot be NULL |
| BR-030 | — | ACTIVE_1_DAY_L7 / ACTIVE_4_7_DAYS_L7 / ACTIVE_1_DAY_L28 / ACTIVE_16PLUS_DAYS_L28 | GAP | `NULL AS ACTIVE_1_DAY_L7 -- GAP ID: GAP-011` | Account-level active day cohort counts; requires aggregating user-level activity over rolling windows | Historical user-date activity tracking | Blocked by GAP-011 - need daily user activity history |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5: NEW FTL CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Gold Layer? | Recommendation |
|------------|-----------|-------------|-------------------|-------------------|----------------|
| CLIENT_TYPE | TEXT | Device category for user engagement (Desktop, Mobile, Web) - 3 distinct values observed | Multi-device usage analysis; channel affinity by device type; mobile-first user segmentation | PENDING DECISION | Add to Silver SLV_COMBINED_CHANNELS now; propose Gold extension for device-segmented metrics after validating business value with Zoom PM |
| OS | TEXT | Operating system dimension (1 sample value observed - low cardinality in current data) | OS-level engagement patterns; platform compatibility analysis | NO | Keep in Silver only until data quality improves; low cardinality suggests incomplete data |
| ZCC_ACCOUNT_ID | TEXT | Secondary account identifier (5 distinct values matching ACCOUNT_ID cardinality) | Additional join key for external systems; account reconciliation across platforms | NO | Keep in Silver SLV_COMBINED_CHANNELS for lineage tracking; not needed in Gold aggregations - serves as technical join key only |

**Summary:**  
CLIENT_TYPE offers the most immediate analytical value for understanding device-driven engagement patterns and should be prioritized for Silver layer enrichment with potential Gold layer extension pending business validation. OS field appears to have data quality issues (only 1 value in sample) and should remain Silver-only until confirmed complete. ZCC_ACCOUNT_ID serves as a technical reconciliation field with no direct analytical value for Gold aggregations but maintains important lineage in Silver.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 6: GAP REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Gold Column | PI Silver Source | Why FTL Cannot Produce This | Blocks Migration? | Proposed Resolution | Raise With |
|--------|----------------|------------------|----------------------------|-------------------|---------------------|------------|
| GAP-001 | SEGMENT | N/A (dimension) | FTL Bronze has no customer segmentation attribute; no columns match segment concept (numeric 1-5 scale); likely external dimension from CRM/billing system | **YES** | BDP team to provide SEGMENT dimension table with ACCOUNT_ID → SEGMENT mapping OR add SEGMENT column to FTL Bronze source table; validate segment definition with Zoom PM | BDP Team & Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS, SLV_USER_ACTIVE_DAYS | FTL Bronze is daily snapshot with no historical user activity tracking; calculating 16+ active days requires MIN 28 days of historical daily user-level activity data; current FTL design does not support temporal analysis | **YES** | BDP to create historical user activity tracking table OR data engineering to build intermediate Silver table aggregating historical FTL Bronze daily snapshots with 28-day rolling window calculations | BDP Team & Data Engineering |
| GAP-003 | REGION | N/A (dimension) | FTL has technical CLUSTER dimension (AWS regions) but no business REGION dimension (NAMER/EMEA/APAC/LATAM); requires mapping logic | **NO** | Create CLUSTER → REGION mapping table in Silver layer; validate with Zoom PM that mapping logic (us-*→NAMER, eu-*→EMEA, ap-*→APAC) is accurate; handle edge cases (sa-* for LATAM) | Data Engineering & Zoom PM |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE, SLV_USAGE_MASTER | FTL Bronze lacks account creation/onboarding date; requires historical analysis of MIN(DATA_DATE) per ACCOUNT_ID across all FTL records from inception | NO | Data engineering to build one-time backfill query: `SELECT ACCOUNT_ID, MIN(DATA_DATE) as ACCOUNT_FIRST_ACTIVE FROM historical_FTL_snapshots GROUP BY ACCOUNT_ID`; store in dimension table; OR BDP to add to FTL source | BDP Team & Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE, SLV_USAGE_MASTER | FTL Bronze lacks user/agent onboarding date; requires historical analysis of MIN(DATA_DATE) per AGENT_ID across all FTL records from inception | NO | Data engineering to build one-time backfill query: `SELECT AGENT_ID, MIN(DATA_DATE) as USER_FIRST_ACTIVE FROM historical_FTL_snapshots GROUP BY AGENT_ID`; store in dimension table; OR BDP to add to FTL source | BDP Team & Data Engineering |
| GAP-006 | CHAT_SESSIONS, CHAT_USAGE | SLV_USAGE_MASTER, SLV_DAILY_METRICS, SLV_WEEKLY_METRICS, SLV_ROLL_29_DAY_USAGE | FTL Bronze only has PHONE_SESSIONS count and INBOUND_PHONE_MS duration; no chat session count or duration despite MODALITY='Chat' being present; missing dimension breakdown for multi-channel reporting | NO | BDP to add CHAT_SESSIONS (count) and CHAT_DURATION_MS columns to FTL Bronze; OR derive CHAT_SESSIONS as `COUNT(DISTINCT ENGAGEMENT_ID WHERE MODALITY='Chat')` if engagement grain is per-session [requires grain validation] | BDP Team |
| GAP-007 | SLA_ACHIEVED, SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER, SLV_COMBINED_CHANNELS | FTL Bronze has no SLA compliance indicator; no timestamp data to calculate resolution time vs SLA threshold; critical for QoS reporting | NO | BDP to add SLA_ACHIEVED boolean flag OR timestamps (engagement_start, engagement_resolved, sla_threshold) to FTL Bronze to enable SLA calculation in Silver layer | BDP Team |
| GAP-008 | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | FTL Bronze has no engagement outcome/lifecycle status (Resolved, Missed, Answered, Abandoned); prevents engagement funnel analysis and conversion tracking | NO | BDP to add ENGAGEMENT_STATUS column to FTL Bronze tracking engagement lifecycle from initiation to resolution | BDP Team |
| GAP-009 | WINDOW (R1/R7/R28) | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_WEEKLY_METRICS, SLV_MONTHLY_METRICS | FTL Bronze is daily snapshot; rolling window indicator not present; requires calculation logic to create R1 (1-day), R7 (7-day), R28 (28-day) views of same metrics | NO | Data engineering to build rolling window calculation in Silver DBT models using window functions: calculate metrics for each date with 1-day, 7-day, 28-day lookback periods; create UNION ALL with WINDOW dimension | Data Engineering |
| GAP-010 | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | FTL Bronze has no user-level subscription/licensing status; prevents paid vs free cohort analysis | NO | Data engineering to join to existing PI billing/subscription table on ACCOUNT_ID + USER_ID; OR BDP to add IS_PAID_USER to FTL Bronze if available in source system | BDP Team / Data Engineering |
| GAP-011 | ACTIVE_DAYS_LAST_7, ACTIVE_DAYS_LAST_28, USERS_ACTIVE_1_DAY, USERS_ACTIVE_4_7_DAYS, USERS_ACTIVE_16PLUS_DAYS, ACTIVE_1_DAY_L7, ACTIVE_4_7_DAYS_L7, ACTIVE_1_DAY_L28, ACTIVE_16PLUS_DAYS_L28 | SLV_ROLL_29_DAY_USAGE, SLV_DAILY_METRICS, SLV_WEEKLY_METRICS, SLV_MONTHLY_METRICS, SLV_USER_ACTIVE_DAYS | FTL Bronze is single-date snapshot; active day calculations require COUNT(DISTINCT DATE WHERE user_was_active) over rolling 7/28-day windows per user; lacks historical tracking mechanism | NO | Data engineering to build rolling window calculation in Silver DBT models using historical FTL Bronze snapshots: `COUNT(DISTINCT DATE) OVER (PARTITION BY USER_ID ORDER BY DATE ROWS N PRECEDING)` where N=6 for 7-day, N=27 for 28-day | Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 7: FEASIBILITY VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Table | Overall Confidence % | Critical Gaps | Verdict | Conditions to Proceed |
|-------|---------------------|---------------|---------|----------------------|
| ZOOM_AI_POC.GOLD.GLD_AGGREGATE | 42% | GAP-001 (SEGMENT), GAP-002 (USERS_ACTIVE_16PLUS_DAYS) | **Not Feasible** | 1. BDP must provide SEGMENT dimension table or add SEGMENT to FTL Bronze (GAP-001)<br>2. BDP must provide historical user activity tracking table OR data engineering must build 28-day rolling activity calculation using historical FTL snapshots (GAP-002)<br>3. Validate CLUSTER → REGION mapping logic with Zoom PM (GAP-003)<br>4. Validate IS_ACTIVE = IS_LICENSED business assumption with stakeholders<br>5. Once GAP-001 and GAP-002 resolved, Gold migration becomes Feasible with Caveats |

**Verdict Rationale:**

The FTL Bronze source lacks two **critical blocking dimensions/metrics** that prevent Gold layer migration:

1. **SEGMENT (GAP-001)** — This is a core dimensional attribute in Gold's grain structure (DATE × REGION × SEGMENT × IS_LICENSED). Without segment data, all Gold rows will have NULL for SEGMENT, breaking all segment-based reporting, cohort analysis, and business dashboards. This is a complete schema breakdown that prevents any meaningful Gold output. SEGMENT appears to be an external business dimension (customer size tier, product tier, or revenue band) not captured in operational FTL data.

2. **USERS_ACTIVE_16PLUS_DAYS (GAP-002)** — This metric requires counting users who were active on 16 or more days within a rolling 28-day window. FTL Bronze is a daily snapshot with no historical activity tracking, making this calculation impossible without access to 28+ days of historical daily user-level records. This metric is critical for MAU (Monthly Active User) power user analysis and retention reporting.

**Additional Critical Dependencies:**

- **REGION (GAP-003)** is derivable from CLUSTER but requires mapping validation (60% confidence) — can proceed with assumption but needs business confirmation
- **IS_ACTIVE → IS_LICENSED mapping** is an unvalidated assumption that could break licensing status reporting if incorrect

**Path to Feasibility:**

If BDP provides SEGMENT dimension table and historical user activity tracking (or confirms 28+ days of historical FTL Bronze snapshots exist for calculation), the migration moves to **Feasible with Caveats**. The remaining 9 gaps (GAP-003 through GAP-011) are Silver-layer enrichment gaps that do not block Gold aggregation — they can be addressed through Silver DBT model development, mapping tables, and hardcoded system values.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 8: DBT MODEL IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 8.1 — NEW TABLES TO CREATE

| Table Name | Layer | Purpose | Depends On |
|------------|-------|---------|------------|
| ZOOM_AI_POC.SILVER.SLV_CLUSTER_REGION_MAP | SILVER | Static dimension table mapping FTL CLUSTER values (AWS regions) to business REGION dimension (NAMER/EMEA/APAC/LATAM) | None - seed table from CSV |
| ZOOM_AI_POC.SILVER.SLV_ACCOUNT_SEGMENT_DIM | SILVER | Dimension table mapping ACCOUNT_ID to SEGMENT (numeric 1-5 scale) for Gold aggregation | External source from BDP OR CRM system (blocks migration until provided - GAP-001) |
| ZOOM_AI_POC.SILVER.SLV_USER_ACTIVITY_HISTORY | SILVER | Historical daily user activity tracking table to enable rolling window calculations; stores USER_ID, DATE, IS_ACTIVE per day | BRZ_FTL_AGENT_BASE_AGG historical snapshots OR BDP historical feed |
| ZOOM_AI_POC.SILVER.SLV_FTL_DAILY_GRAIN | SILVER | Intermediate table converting FTL engagement-level grain to daily user-account-date grain for rolling window calculations | BRZ_FTL_AGENT_BASE_AGG |
| ZOOM_AI_POC.SILVER.SLV_ROLLING_WINDOWS | SILVER | Intermediate table calculating R1/R7/R28 window metrics per account/date for usage metric tables | SLV_FTL_DAILY_GRAIN |

## 8.2 — EXISTING TABLES TO ALTER

| Table Name | Layer | Change Required | Columns to Add | Columns to Modify | Impact |
|------------|-------|----------------|----------------|-------------------|--------|
| ZOOM_AI_POC.SILVER.SLV_COMBINED_CHANNELS | SILVER | Add new FTL dimensions; modify source join logic | CLIENT_TYPE (TEXT), ZCC_ACCOUNT_ID (TEXT) | CHANNEL: add UPPER() case conversion (BR-006); DIRECTION: add UPPER() case conversion (BR-005); DURATION_SEC: modify to handle INBOUND_PHONE_MS conversion (BR-008) | Medium — new dimensions enable device analysis; case standardization ensures consistency |
| ZOOM_AI_POC.SILVER.SLV_USAGE_MASTER | SILVER | Change source from legacy Bronze views to FTL Bronze; add unit conversions | None | DATE: change from legacy source to TO_DATE(DATA_DATE) (BR-001); USER_ID: change source from legacy to AGENT_ID (BR-003); INBOUND_PHONE_MINS: change source to INBOUND_PHONE_MS / 60000.0 (BR-007) | High — fundamental source change; all downstream models affected |
| ZOOM_AI_POC.SILVER.SLV_CONSOLIDATED_USAGE | SILVER | Add rolling window calculation logic; change aggregation source | WINDOW (TEXT) - now calculated via BR-021 | PHONE_USAGE: change to SUM(INBOUND_PHONE_MS) / 60000.0 with window partitioning (BR-009); ACTIVE_USERS: add aggregation logic (BR-026) | High — introduces window function complexity |
| ZOOM_AI_POC.SILVER.SLV_DAILY_METRICS | SILVER | Add rolling window calculation logic; change aggregation source | WINDOW (TEXT) - now calculated via BR-021 | CHAT_USAGE: blocked by GAP-006 until BDP adds chat duration; USERS_ACTIVE_1_DAY: blocked by GAP-011 until historical activity available | High — blocked by upstream gaps |
| ZOOM_AI_POC.SILVER.SLV_WEEKLY_METRICS | SILVER | Add rolling window calculation logic; change aggregation source | WINDOW (TEXT) - now calculated via BR-021 | CHAT_USAGE: blocked by GAP-006; USERS_ACTIVE_4_7_DAYS: blocked by GAP-011 | High — blocked by upstream gaps |
| ZOOM_AI_POC.SILVER.SLV_MONTHLY_METRICS | SILVER | Add rolling window calculation logic; change aggregation source | WINDOW (TEXT) - now calculated via BR-021 | VIDEO_USAGE: can derive from COUNT WHERE CHANNEL='Video' (BR-025); USERS_ACTIVE_16PLUS_DAYS: blocked by GAP-011 | High — blocked by upstream gaps |
| ZOOM_AI_POC.SILVER.SLV_ROLL_29_DAY_USAGE | SILVER | Add rolling window calculation logic; change aggregation source | None | IS_PAID_USER: blocked by GAP-010 until billing join added; ACTIVE_DAYS_LAST_7/28: blocked by GAP-011; DAILY_CHAT_USAGE: blocked by GAP-006; WEEKLY_PHONE_USAGE: change to 7-day window function (BR-010) | High — majority of columns blocked |
| ZOOM_AI_POC.SILVER.SLV_USER_ACTIVE_DAYS | SILVER | Add rolling activity calculation logic | None | ACTIVE_1_DAY_L7, ACTIVE_4_7_DAYS_L7, ACTIVE_1_DAY_L28, ACTIVE_16PLUS_DAYS_L28: all blocked by GAP-011 | High — entire table blocked by historical activity gap |
| ZOOM_AI_POC.SILVER.SLV_ACCT_FIRST_ACTIVE | SILVER | Add historical MIN date calculation or lookup to new dimension table | None | ACCOUNT_FIRST_ACTIVE: blocked by GAP-004 until historical analysis completed | Medium — one-time backfill possible |
| ZOOM_AI_POC.SILVER.SLV_USER_FIRST_ACTIVE | SILVER | Add historical MIN date calculation or lookup to new dimension table | None | USER_FIRST_ACTIVE: blocked by GAP-005 until historical analysis completed | Medium — one-time backfill possible |
| ZOOM_AI_POC.GOLD.GLD_AGGREGATE | GOLD | Add SEGMENT join; modify REGION derivation; change aggregation source to FTL-based Silver | None | DATE: change to FTL DATA_DATE conversion; REGION: add CLUSTER → REGION mapping (BR-012 + GAP-003); SEGMENT: blocked by GAP-001 until dimension table provided; USERS_ACTIVE_16PLUS_DAYS: blocked by GAP-002; PHONE_USAGE: change to FTL INBOUND_PHONE_MS aggregation (BR-009) | **CRITICAL** — entire Gold table blocked by GAP-001 and GAP-002 |

## 8.3 — GAP REMEDIATION ACTIONS

| GAP ID | PI Gold Column | Remediation Action | New Table Required? | New Join Required? | Estimated Complexity | Owner |
|--------|----------------|-------------------|--------------------|--------------------|---------------------|-------|
| GAP-001 | SEGMENT | BDP must provide ACCOUNT_ID → SEGMENT dimension table OR add SEGMENT column to FTL Bronze; if dimension table provided, create SLV_ACCOUNT_SEGMENT_DIM and join in Gold aggregation | YES (SLV_ACCOUNT_SEGMENT_DIM) | YES (Gold LEFT JOIN on ACCOUNT_ID) | High — **BLOCKING** — requires external data source not in FTL | BDP Team / Zoom PM |
| GAP-002 | USERS_ACTIVE_16PLUS_DAYS | Build SLV_USER_ACTIVITY_HISTORY table aggregating daily user activity from historical FTL snapshots; create window function logic to calculate 16+ active days in 28-day rolling window; aggregate to Gold | YES (SLV_USER_ACTIVITY_HISTORY) | NO (aggregation from Silver) | High — **BLOCKING** — requires 28+ days historical FTL data and complex windowing logic | Data Engineering |
| GAP-003 | REGION | Create SLV_CLUSTER_REGION_MAP seed table with CLUSTER → REGION mappings; validate mappings with Zoom PM; join in Gold aggregation logic | YES (SLV_CLUSTER_REGION_MAP) | YES (Gold JOIN on CLUSTER) | Medium — mapping table creation straightforward but requires business validation | Data Engineering / Zoom PM |
| GAP-004 | ACCOUNT_FIRST_ACTIVE | One-time backfill: query historical FTL Bronze snapshots to calculate MIN(DATA_DATE) per ACCOUNT_ID; store in SLV_ACCT_FIRST_ACTIVE as dimension; OR wait for BDP to add to FTL source | NO (use existing SLV_ACCT_FIRST_ACTIVE) | NO | Medium — one-time calculation; ongoing incremental update logic needed | Data Engineering |
| GAP-005 | USER_FIRST_ACTIVE | One-time backfill: query historical FTL Bronze snapshots to calculate MIN(DATA_DATE) per AGENT_ID; store in SLV_USER_FIRST_ACTIVE as dimension; OR wait for BDP to add to FTL source | NO (use existing SLV_USER_FIRST_ACTIVE) | NO | Medium — one-time calculation; ongoing incremental update logic needed | Data Engineering |
| GAP-006 | CHAT_SESSIONS, CHAT_USAGE | BDP must add CHAT_SESSIONS (count) and CHAT_DURATION_MS columns to FTL Bronze; OR derive CHAT_SESSIONS as COUNT(DISTINCT ENGAGEMENT_ID WHERE MODALITY='Chat') if grain allows | NO | NO | Medium — requires BDP source enhancement OR grain validation + derivation logic | BDP Team |
| GAP-007 | SLA_ACHIEVED, SLA_ACHIEVED_SESSIONS | BDP must add SLA_ACHIEVED boolean OR engagement resolution timestamps to FTL Bronze; if timestamps provided, calculate SLA breach in Silver layer | NO | NO | Medium — requires BDP source enhancement; calculation logic in Silver if timestamps provided | BDP Team |
| GAP-008 | ENGAGEMENT_STATUS | BDP must add ENGAGEMENT_STATUS column to FTL Bronze tracking engagement lifecycle (Initiated, Answered, Resolved, Missed, Abandoned) | NO | NO | Medium — requires BDP source enhancement | BDP Team |
| GAP-009 | WINDOW (R1/R7/R28) | Build SLV_ROLLING_WINDOWS intermediate table with window function logic; create 3 rows per date/account (R1, R7, R28) using UNION ALL; join in metrics tables | YES (SLV_ROLLING_WINDOWS) | YES (Silver JOIN on DATE + ACCOUNT_ID + WINDOW) | High — complex windowing logic with 3x row explosion; performance implications | Data Engineering |
| GAP-010 | IS_PAID_USER | Join to existing PI billing/subscription table on ACCOUNT_ID + USER_ID; OR request BDP to add IS_PAID_USER to FTL Bronze if available | NO | YES (Silver LEFT JOIN to billing table) | Low — join to existing table; OR wait for BDP enhancement | Data Engineering / BDP Team |
| GAP-011 | Multiple active day metrics | Build SLV_USER_ACTIVITY_HISTORY table from historical FTL snapshots; create window functions to calculate active day counts over rolling 7/28-day windows; use in metrics tables | YES (SLV_USER_ACTIVITY_HISTORY shared with GAP-002) | NO | High — complex windowing logic; requires historical data processing; affects 9 Silver columns + 1 Gold column | Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 9: RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## **PRIORITY 1: BLOCKING ITEMS (Must Resolve Before Any Migration)**

1. **Resolve SEGMENT gap (GAP-001)** — BDP Team to provide ACCOUNT_ID → SEGMENT dimension mapping table OR add SEGMENT column to FTL Bronze source. Without this, Gold layer cannot be built. **Raise with:** BDP Team Lead + Zoom PM

2. **Resolve USERS_ACTIVE_16PLUS_DAYS gap (GAP-002)** — Confirm availability of historical FTL Bronze snapshots (minimum 28 days) for rolling activity calculations OR request BDP to provide historical user activity tracking table. Without this, Gold power user metric is NULL. **Raise with:** BDP Team Lead + Data Engineering Lead

3. **Validate IS_ACTIVE = IS_LICENSED assumption (BR-011)** — Confirm with business stakeholder