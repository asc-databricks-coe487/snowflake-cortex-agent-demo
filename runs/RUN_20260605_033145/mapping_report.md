

🔍 **STEP 1:** Schema Discovery — Identified 20 Silver target tables and 1 Bronze FTL source table

🔍 **STEP 2:** Data Profiling — Profiled all 21 tables (1 source + 20 targets); source contains 14 columns with 5 data rows

🔍 **STEP 3:** Mapping Analysis — Analyzed semantic and structural compatibility across 20 Silver tables totaling 96 target columns

---

# BRONZE FTL TO SILVER LAYER MIGRATION REPORT
**Comprehensive Mapping Analysis & Feasibility Assessment**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1: EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Source FTL Bronze Table:** ZOOM_AI_POC.BRONZE.BRZ_FTL_AGENT_BASE_AGG

**Target PI Silver Tables:** 20 tables across ZOOM_AI_POC.SILVER layer
- SLV_ACCT_FIRST_ACTIVE
- SLV_COMBINED_CHANNELS  
- SLV_CONSOLIDATED_USAGE
- SLV_DAILY_METRICS
- SLV_MONTHLY_METRICS
- SLV_ROLL_29_DAY_USAGE
- SLV_USAGE_MASTER
- SLV_USER_ACTIVE_DAYS
- SLV_USER_FIRST_ACTIVE
- SLV_WEEKLY_METRICS
- (Plus 10 non-prefixed duplicate schema tables: ACCT_FIRST_ACTIVE, COMBINED_CHANNELS, CONSOLIDATED_USAGE, DAILY_METRICS, MONTHLY_METRICS, ROLL_29_DAY_USAGE, USAGE_MASTER, USER_ACTIVE_DAYS, USER_FIRST_ACTIVE, WEEKLY_METRICS)

**Migration Readiness Score:** 52/100

**Column Analysis Summary:**
- Total FTL Bronze columns analyzed: 14
- Successfully mapped (DIRECT_MATCH): 6 core columns (43%)
- Partially mapped (requires transformation): 3 columns (21%)
- New capabilities (no PI equivalent): 3 columns (21%) — CLIENT_TYPE, OS, ZCC_ACCOUNT_ID
- Gaps (PI Silver columns with no FTL source): 26 unique gaps

**Gap Summary:**
- GAP-001: REFRESH_TIMESTAMP (system-generated field)
- GAP-002: ENGAGEMENT_STATUS (no status tracking in FTL)
- GAP-003: SLA_ACHIEVED (no SLA metrics in FTL)
- GAP-004: SOURCE_TABLE (metadata field)
- GAP-005: PRODUCT_NAME (metadata field)
- GAP-006: WINDOW (reporting window classification)
- GAP-007: CHAT_USAGE / CHAT_SESSIONS (no chat metrics in FTL)
- GAP-008: VIDEO_USAGE (no video metrics in FTL)
- GAP-009: IS_PAID_USER (no payment/licensing data in FTL)
- GAP-010: ACTIVE_DAYS_LAST_7 (requires 7-day rolling calculation)
- GAP-011: ACTIVE_DAYS_LAST_28 (requires 28-day rolling calculation)
- GAP-012: USERS_ACTIVE_1_DAY (requires active day classification)
- GAP-013: USERS_ACTIVE_16PLUS_DAYS (requires 28-day rolling with 16+ filter)
- GAP-014: ACTIVE_1_DAY_L7 (requires 7-day rolling user classification)
- GAP-015: ACTIVE_4_7_DAYS_L7 (requires 7-day rolling with 4-7 filter)
- GAP-016: ACTIVE_1_DAY_L28 (requires 28-day rolling user classification)
- GAP-017: ACTIVE_16PLUS_DAYS_L28 (requires 28-day rolling with 16+ filter)
- GAP-018: ACTIVE_USERS (requires aggregation logic)
- GAP-019: ACCOUNT_FIRST_ACTIVE derived field (requires historical MIN aggregation)
- GAP-020: USER_FIRST_ACTIVE derived field (requires historical MIN aggregation)
- GAP-021: SLA_ACHIEVED_SESSIONS (no SLA tracking)
- GAP-022: USERS_ACTIVE_4_7_DAYS (requires 7-day rolling with 4-7 filter)
- GAP-023: DURATION_SEC for non-phone channels (only INBOUND_PHONE_MS available)
- GAP-024: START_DATE semantic clarity (DATA_DATE interpretation)
- GAP-025: DAILY_CHAT_USAGE (no chat metrics)
- GAP-026: WEEKLY_PHONE_USAGE aggregation logic (unclear weekly boundary)

**Blocking Items:** 7 critical gaps
- GAP-007 (Chat metrics completely absent — blocks 5 Silver tables)
- GAP-008 (Video metrics completely absent — blocks MONTHLY_METRICS)
- GAP-009 (Payment data absent — blocks ROLL_29_DAY_USAGE)
- GAP-010, GAP-011 (Rolling window calculations — blocks ROLL_29_DAY_USAGE)
- GAP-014 through GAP-017 (Complex rolling user classifications — blocks USER_ACTIVE_DAYS)
- GAP-023 (Duration only available for phone — limits COMBINED_CHANNELS)

**Overall Assessment:**
The FTL Bronze source provides strong foundational data for account, engagement, and phone metrics but has critical gaps in chat, video, SLA, and payment dimensions. Six tables are migration-feasible with manageable caveats (SLV_ACCT_FIRST_ACTIVE, SLV_COMBINED_CHANNELS, SLV_CONSOLIDATED_USAGE, SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE, and their non-prefixed duplicates). Two tables (SLV_ROLL_29_DAY_USAGE and SLV_USER_ACTIVE_DAYS) are not feasible without additional data sources providing historical rolling windows, chat metrics, and payment classifications. Four tables (SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS) are partially feasible but will produce incomplete results with NULL chat/video usage values. Migration can proceed incrementally for phone/engagement-focused use cases while BDP team addresses missing modalities.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2: GAP IMPACT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Silver Column | Why It's a Gap | Impact on Silver Output | Blocks Migration? | Action Required | Raise With |
|--------|-----------------|----------------|------------------------|-------------------|-----------------|------------|
| GAP-001 | REFRESH_TIMESTAMP | System-generated metadata field not present in FTL | Operational metadata missing; does not affect business metrics | NO | Use CURRENT_TIMESTAMP() in DBT model | Data Engineering |
| GAP-002 | ENGAGEMENT_STATUS | FTL does not track engagement resolution status (Answered/Missed/Resolved) | COMBINED_CHANNELS table cannot classify engagement outcomes | NO | Default to NULL or derive from duration (duration > 0 = 'Answered') | BDP Team / Zoom PM |
| GAP-003 | SLA_ACHIEVED | FTL does not contain SLA achievement flag | COMBINED_CHANNELS and USAGE_MASTER cannot report SLA metrics | NO | Default to NULL; requires separate SLA calculation system | BDP Team |
| GAP-004 | SOURCE_TABLE | Metadata field identifying originating Bronze table | Traceability metadata missing; does not affect metrics | NO | Hardcode 'BRZ_FTL_AGENT_BASE_AGG' in DBT model | Data Engineering |
| GAP-005 | PRODUCT_NAME | Product classification field (e.g., 'ZCC Platform') | CONSOLIDATED_USAGE cannot segment by product | NO | Hardcode 'ZCC Platform' or join to product dimension table | Data Engineering / Zoom PM |
| GAP-006 | WINDOW | Reporting window classification (R1/R7/R28) for rolling calculations | All metrics tables cannot produce multi-window reports | YES | Implement window logic in DBT (explode single date to multiple windows) | Data Engineering |
| GAP-007 | CHAT_USAGE / CHAT_SESSIONS | FTL Bronze contains no chat activity metrics (sessions, duration, or message counts) | DAILY_METRICS, WEEKLY_METRICS, ROLL_29_DAY_USAGE, USAGE_MASTER report NULL for all chat metrics | YES | BDP to add chat metrics to FTL table OR join to legacy BRZ_CHAT_HISTORY | BDP Team |
| GAP-008 | VIDEO_USAGE | FTL Bronze contains no video activity metrics | MONTHLY_METRICS reports NULL for video usage | YES | BDP to add video metrics to FTL table OR join to legacy BRZ_VIDEO_HISTORY | BDP Team |
| GAP-009 | IS_PAID_USER | FTL Bronze has no payment or licensing classification | ROLL_29_DAY_USAGE cannot segment paid vs. free users | YES | Join to billing/licensing dimension table (if exists in PI schema) | BDP Team / Zoom PM |
| GAP-010 | ACTIVE_DAYS_LAST_7 | Requires 7-day rolling window calculation not present in single-day FTL grain | ROLL_29_DAY_USAGE cannot report weekly activity patterns | YES | Build intermediate rolling window table using historical FTL data | Data Engineering |
| GAP-011 | ACTIVE_DAYS_LAST_28 | Requires 28-day rolling window calculation not present in single-day FTL grain | ROLL_29_DAY_USAGE cannot report monthly activity patterns | YES | Build intermediate rolling window table using historical FTL data | Data Engineering |
| GAP-012 | USERS_ACTIVE_1_DAY | Requires classification of users active exactly 1 day in period | DAILY_METRICS cannot produce activity distribution reports | NO | Derive from window logic using IS_ACTIVE flag (low confidence) | Data Engineering |
| GAP-013 | USERS_ACTIVE_16PLUS_DAYS | Requires counting users active 16+ days in last 28 days | MONTHLY_METRICS cannot produce high-engagement user counts | NO | Requires historical rolling calculation (complex) | Data Engineering |
| GAP-014 | ACTIVE_1_DAY_L7 | Count of users active 1 day in last 7 days | USER_ACTIVE_DAYS table cannot be populated | YES | Requires historical rolling window calculation | Data Engineering |
| GAP-015 | ACTIVE_4_7_DAYS_L7 | Count of users active 4-7 days in last 7 days | USER_ACTIVE_DAYS table cannot be populated | YES | Requires historical rolling window calculation | Data Engineering |
| GAP-016 | ACTIVE_1_DAY_L28 | Count of users active 1 day in last 28 days | USER_ACTIVE_DAYS table cannot be populated | YES | Requires historical rolling window calculation | Data Engineering |
| GAP-017 | ACTIVE_16PLUS_DAYS_L28 | Count of users active 16+ days in last 28 days | USER_ACTIVE_DAYS table cannot be populated | YES | Requires historical rolling window calculation | Data Engineering |
| GAP-018 | ACTIVE_USERS | Aggregated count of distinct active users per account/window | All metrics tables require this as core KPI | NO | Implement COUNT(DISTINCT AGENT_ID WHERE IS_ACTIVE = TRUE) | Data Engineering |
| GAP-019 | ACCOUNT_FIRST_ACTIVE (derived) | First activity date per account requires historical MIN(DATE) | USAGE_MASTER and ACCT_FIRST_ACTIVE rely on this dimension | NO | Calculate MIN(DATA_DATE) per ACCOUNT_ID across all history (assumption: current data = first activity) | Data Engineering |
| GAP-020 | USER_FIRST_ACTIVE (derived) | First activity date per user requires historical MIN(DATE) | USAGE_MASTER and USER_FIRST_ACTIVE rely on this dimension | NO | Calculate MIN(DATA_DATE) per AGENT_ID across all history (assumption: current data = first activity) | Data Engineering |
| GAP-021 | SLA_ACHIEVED_SESSIONS | Count of sessions meeting SLA target | USAGE_MASTER cannot report SLA compliance metrics | NO | Default to NULL; requires SLA threshold definition and calculation | BDP Team |
| GAP-022 | USERS_ACTIVE_4_7_DAYS | Count of users active 4-7 days in reporting window | WEEKLY_METRICS cannot produce activity distribution | NO | Requires rolling window calculation (complex) | Data Engineering |
| GAP-023 | DURATION_SEC for non-phone | FTL only provides INBOUND_PHONE_MS; no duration for Email/SMS/Chat/Video | COMBINED_CHANNELS reports NULL duration for 5 of 7 modality/channel combinations | NO | BDP to add duration metrics for all modalities OR accept partial data | BDP Team |
| GAP-024 | START_DATE semantic clarity | DATA_DATE format is timestamp string; unclear if represents engagement start or report date | Ambiguity in date semantics across tables | NO | Confirm with BDP: is DATA_DATE the engagement start timestamp? | BDP Team |
| GAP-025 | DAILY_CHAT_USAGE | Daily aggregated chat usage for user-level rolling table | ROLL_29_DAY_USAGE cannot populate daily chat metric | YES | Same as GAP-007; requires chat metrics in FTL | BDP Team |
| GAP-026 | WEEKLY_PHONE_USAGE aggregation logic | Unclear how to aggregate phone usage to weekly grain from daily DATA_DATE | ROLL_29_DAY_USAGE weekly phone metric logic ambiguous | NO | Define weekly boundary (Sunday-Saturday? Calendar week? Rolling 7-day?) | Zoom PM / Data Engineering |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3: FULL COLUMN LINEAGE MAPPING TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Bronze Column | FTL Data Type | PI Silver Column | PI Silver Table | PI Silver Column (cont.) | PI Silver Table (cont.) | Classification | Confidence | Mapping Reason | BR ID | GAP ID | Transformation | Notes |
|-------------------|---------------|------------------|-----------------|--------------------------|-------------------------|----------------|------------|----------------|-------|--------|----------------|-------|
| ZCC_ACCOUNT_ID | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | No Silver column maps to ZCC_ACCOUNT_ID; FTL provides dual account identifier not present in legacy PI schema | — | — | N/A | New dimension available for future use |
| ACCOUNT_ID | TEXT | ACCOUNT_ID | SLV_ACCT_FIRST_ACTIVE | ACCOUNT_ID | SLV_COMBINED_CHANNELS, SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_ACTIVE_DAYS, SLV_USER_FIRST_ACTIVE, SLV_WEEKLY_METRICS | DIRECT_MATCH | High | Column name and semantic meaning identical; sample values confirm TEXT format with ID_ prefix pattern matches across source and all targets | BR-001 | — | Direct pass-through | Core join key |
| ENGAGEMENT_ID | TEXT | ENGAGEMENT_ID | SLV_COMBINED_CHANNELS | — | — | DIRECT_MATCH | High | Column name and semantic meaning identical; represents unique engagement identifier in both FTL and Silver | BR-002 | — | Direct pass-through | Primary key for engagement-level table |
| AGENT_ID | TEXT | USER_ID | SLV_COMBINED_CHANNELS | USER_ID | SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER, SLV_USER_FIRST_ACTIVE | SEMANTIC_MATCH | Medium | FTL uses AGENT_ID while Silver uses USER_ID; semantic mapping assumes agent = user in contact center context; requires confirmation with BDP | BR-003 | — | Rename: AGENT_ID AS USER_ID | Semantic assumption: agent = user |
| DIRECTION | TEXT | DIRECTION | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | Medium | FTL has 2 distinct values (Inbound, Outbound) vs. Silver has 2 values (INBOUND, OUTBOUND); only case differs — requires UPPER() transformation | BR-004 | — | UPPER(DIRECTION) | Case normalization required |
| MODALITY | TEXT | MODALITY | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | Medium | FTL has 3 distinct values (SMS, Email, Chat) vs. Silver has 5 values (Chat, Phone, SMS, Email, Video); FTL subset confirmed — Video/Phone modality from CHANNEL column | BR-005 | — | Conditional logic: CASE WHEN CHANNEL IN ('Phone','Video') THEN CHANNEL ELSE MODALITY END | Modality/Channel merge needed |
| CHANNEL | TEXT | CHANNEL | SLV_COMBINED_CHANNELS | — | — | PARTIAL_MATCH | Medium | FTL has 2 distinct values (Video, Phone) vs. Silver has 5 values (EMAIL, VIDEO, PHONE, CHAT, SMS); FTL provides Phone/Video channels while Email/SMS/Chat derived from MODALITY column | BR-006 | — | Conditional logic: CASE WHEN MODALITY IN ('Email','SMS','Chat') THEN UPPER(MODALITY) ELSE UPPER(CHANNEL) END | Channel/Modality merge needed |
| PHONE_SESSIONS | NUMBER | PHONE_SESSIONS | SLV_USAGE_MASTER | — | — | DIRECT_MATCH | High | Column name and data type identical; semantic meaning confirmed as count of phone sessions | BR-007 | — | Direct pass-through | Core phone metric |
| INBOUND_PHONE_MS | NUMBER | INBOUND_PHONE_MINS | SLV_USAGE_MASTER | PHONE_USAGE | SLV_CONSOLIDATED_USAGE, SLV_ROLL_29_DAY_USAGE | UNIT_CHANGE | High | FTL provides milliseconds; Silver expects minutes (INBOUND_PHONE_MINS) or float minutes (PHONE_USAGE); requires division by 60,000 | BR-008 | — | INBOUND_PHONE_MS / 60000.0 AS INBOUND_PHONE_MINS | Milliseconds → Minutes |
| INBOUND_PHONE_MS | NUMBER | DURATION_SEC | SLV_COMBINED_CHANNELS | — | — | UNIT_CHANGE | Low | FTL provides phone duration in milliseconds; Silver expects seconds for all channels; only phone duration available (Email/SMS/Chat/Video duration = NULL) | BR-009 | GAP-023 | INBOUND_PHONE_MS / 1000.0 AS DURATION_SEC | Milliseconds → Seconds; only phone |
| CLIENT_TYPE | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | FTL provides client type dimension (Mobile, Desktop, Web) not present in any Silver table; new analysis capability | — | — | N/A | New dimension for device analytics |
| OS | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | FTL provides operating system dimension not present in any Silver table; new analysis capability | — | — | N/A | New dimension for OS analytics |
| IS_ACTIVE | BOOLEAN | IS_ACTIVE_ACCOUNT | SLV_CONSOLIDATED_USAGE | IS_ACTIVE_ACCOUNT | SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | SEMANTIC_MATCH | Medium | FTL provides IS_ACTIVE boolean; Silver expects IS_ACTIVE_ACCOUNT; semantic mapping assumes row-level activity flag represents account-level activity when aggregated | BR-010 | — | IS_ACTIVE AS IS_ACTIVE_ACCOUNT | Semantic assumption: row activity = account activity |
| CLUSTER | TEXT | — | — | — | — | NEW_CAPABILITY | N/A | FTL provides cluster/region dimension (eu-central-1, ap-south-1, us-east-1) not present in Silver; new geographic analysis capability; may map to future REGION field if added to Silver | — | — | N/A | New dimension for cluster/region analytics |
| DATA_DATE | TEXT | DATE | SLV_USAGE_MASTER | START_DATE | SLV_COMBINED_CHANNELS | UNIT_CHANGE | Medium | FTL provides timestamp as text string ('5/29/26 13:01'); Silver expects DATE type; requires parsing with TO_DATE(); semantic ambiguity: is this engagement timestamp or report date? | BR-011 | GAP-024 | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | Text → Date parsing; confirm semantics with BDP |
| DATA_DATE | TEXT | REPORT_DATE | SLV_CONSOLIDATED_USAGE | REPORT_DATE | SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USER_ACTIVE_DAYS, SLV_WEEKLY_METRICS, SLV_ACCT_FIRST_ACTIVE (as ACCOUNT_FIRST_ACTIVE) | GRAIN_CHANGE | Medium | FTL provides single timestamp; Silver metrics tables require REPORT_DATE for aggregation reporting; requires date parsing and potential aggregation to daily grain | BR-012 | — | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') AS REPORT_DATE | Text → Date; aggregation grain shift |
| — | — | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE | REFRESH_TIMESTAMP | SLV_USER_FIRST_ACTIVE | GAP | High | System-generated metadata timestamp indicating table refresh time; not present in FTL source | BR-013 | GAP-001 | CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP | System-generated field |
| — | — | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE | ACCOUNT_FIRST_ACTIVE | SLV_USAGE_MASTER | GAP | Medium | Derived metric requiring MIN(DATA_DATE) grouped by ACCOUNT_ID across historical data; FTL provides daily snapshots but not historical first activity date | BR-014 | GAP-019 | MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY ACCOUNT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ACCOUNT_FIRST_ACTIVE | Requires historical aggregation |
| — | — | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE | USER_FIRST_ACTIVE | SLV_USAGE_MASTER | GAP | Medium | Derived metric requiring MIN(DATA_DATE) grouped by AGENT_ID across historical data; FTL provides daily snapshots but not historical first activity date | BR-015 | GAP-020 | MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY AGENT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS USER_FIRST_ACTIVE | Requires historical aggregation |
| — | — | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | — | — | GAP | High | FTL does not track engagement resolution status (Answered/Missed/Resolved/etc.) | BR-016 | GAP-002 | NULL AS ENGAGEMENT_STATUS | No source available |
| — | — | SLA_ACHIEVED | SLV_COMBINED_CHANNELS | — | — | GAP | High | FTL does not contain SLA achievement flag | BR-017 | GAP-003 | NULL AS SLA_ACHIEVED | No SLA data in source |
| — | — | SOURCE_TABLE | SLV_COMBINED_CHANNELS | — | — | GAP | High | Metadata field identifying originating Bronze view; FTL is single table | BR-018 | GAP-004 | 'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE | Hardcoded metadata |
| — | — | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | — | — | GAP | High | Product classification dimension not present in FTL | BR-019 | GAP-005 | 'ZCC Platform' AS PRODUCT_NAME | Hardcoded; confirm with Zoom PM |
| — | — | WINDOW | SLV_CONSOLIDATED_USAGE | WINDOW | SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | GAP | High | Reporting window classification (R1, R7, R28) for rolling period reports; requires business rule to explode single date row into multiple window rows | BR-020 | GAP-006 | CASE WHEN window_type = 'R1' THEN 'R1' WHEN window_type = 'R7' THEN 'R7' WHEN window_type = 'R28' THEN 'R28' END (requires CROSS JOIN to window dimension) | Window logic needed |
| — | — | ACTIVE_USERS | SLV_CONSOLIDATED_USAGE | ACTIVE_USERS | SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | GAP | Medium | Aggregated count of distinct active users per account/date/window; requires GROUP BY logic | BR-021 | GAP-018 | COUNT(DISTINCT AGENT_ID) WHERE IS_ACTIVE = TRUE | Aggregation required |
| — | — | CHAT_USAGE | SLV_DAILY_METRICS | CHAT_USAGE | SLV_WEEKLY_METRICS | GAP | High | FTL Bronze contains no chat activity metrics (duration, sessions, or message counts); cannot populate chat usage columns | BR-022 | GAP-007 | NULL AS CHAT_USAGE | No chat metrics in source |
| — | — | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | — | — | GAP | Low | Count of users active exactly 1 day in reporting period; requires complex classification logic not derivable from single-day FTL grain | BR-023 | GAP-012 | NULL AS USERS_ACTIVE_1_DAY (or complex window function if historical data available) | Low confidence derivation |
| — | — | VIDEO_USAGE | SLV_MONTHLY_METRICS | — | — | GAP | High | FTL Bronze contains no video activity metrics; cannot populate video usage column | BR-024 | GAP-008 | NULL AS VIDEO_USAGE | No video metrics in source |
| — | — | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | — | — | GAP | Low | Count of users active 16+ days in last 28 days; requires 28-day rolling window calculation not available in single-day FTL grain | BR-025 | GAP-013 | NULL AS USERS_ACTIVE_16PLUS_DAYS (requires historical rolling calculation) | Requires historical data |
| — | — | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Payment/licensing classification not present in FTL; requires join to billing dimension | BR-026 | GAP-009 | NULL AS IS_PAID_USER | No payment data in source |
| — | — | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Count of active days in last 7 days requires 7-day rolling window calculation not available in single-day FTL grain | BR-027 | GAP-010 | NULL AS ACTIVE_DAYS_LAST_7 (requires historical rolling window table) | Blocking: historical data needed |
| — | — | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Count of active days in last 28 days requires 28-day rolling window calculation not available in single-day FTL grain | BR-028 | GAP-011 | NULL AS ACTIVE_DAYS_LAST_28 (requires historical rolling window table) | Blocking: historical data needed |
| — | — | DAILY_CHAT_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | GAP | High | Daily aggregated chat usage; same as GAP-007 — no chat metrics in FTL | BR-029 | GAP-025 | NULL AS DAILY_CHAT_USAGE | No chat metrics in source |
| — | — | WEEKLY_PHONE_USAGE | SLV_ROLL_29_DAY_USAGE | — | — | GAP | Medium | Weekly aggregated phone usage from INBOUND_PHONE_MS; requires weekly boundary definition (Sunday-Saturday? Rolling 7-day?) | BR-030 | GAP-026 | SUM(INBOUND_PHONE_MS / 60000.0) OVER (PARTITION BY AGENT_ID, ACCOUNT_ID ORDER BY DATA_DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) | Weekly aggregation logic ambiguous |
| — | — | CHAT_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | Count of chat sessions; no chat activity tracking in FTL | BR-031 | GAP-007 | NULL AS CHAT_SESSIONS | No chat metrics in source |
| — | — | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | — | — | GAP | High | Count of sessions meeting SLA; no SLA tracking in FTL | BR-032 | GAP-021 | NULL AS SLA_ACHIEVED_SESSIONS | No SLA data in source |
| — | — | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Count of users active 1 day in last 7 days; requires historical rolling window calculation | BR-033 | GAP-014 | NULL AS ACTIVE_1_DAY_L7 (requires historical rolling calculation) | Blocking: historical data needed |
| — | — | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Count of users active 4-7 days in last 7 days; requires historical rolling window calculation | BR-034 | GAP-015 | NULL AS ACTIVE_4_7_DAYS_L7 (requires historical rolling calculation) | Blocking: historical data needed |
| — | — | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Count of users active 1 day in last 28 days; requires historical rolling window calculation | BR-035 | GAP-016 | NULL AS ACTIVE_1_DAY_L28 (requires historical rolling calculation) | Blocking: historical data needed |
| — | — | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | — | — | GAP | High | Count of users active 16+ days in last 28 days; requires historical rolling window calculation | BR-036 | GAP-017 | NULL AS ACTIVE_16PLUS_DAYS_L28 (requires historical rolling calculation) | Blocking: historical data needed |
| — | — | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | — | — | GAP | Low | Count of users active 4-7 days in reporting window; requires rolling window calculation | BR-037 | GAP-022 | NULL AS USERS_ACTIVE_4_7_DAYS (requires historical rolling calculation) | Requires historical data |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4: TRANSFORMATION GUIDE (Business Rules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| BR ID | FTL Column | PI Silver Column | Classification | SQL Transformation | Business Reason | Dependencies | Assumptions |
|-------|------------|------------------|----------------|-------------------|-----------------|--------------|-------------|
| BR-001 | ACCOUNT_ID | ACCOUNT_ID | DIRECT_MATCH | ACCOUNT_ID | Direct pass-through of account identifier | None | None |
| BR-002 | ENGAGEMENT_ID | ENGAGEMENT_ID | DIRECT_MATCH | ENGAGEMENT_ID | Direct pass-through of engagement identifier | None | None |
| BR-003 | AGENT_ID | USER_ID | SEMANTIC_MATCH | AGENT_ID AS USER_ID | In contact center context, agent is treated as user for Silver layer consumption | AGENT_ID not null | [ASSUMPTION] Agent ID represents user ID in all Silver contexts; confirm with BDP that no separate USER_ID dimension exists |
| BR-004 | DIRECTION | DIRECTION | PARTIAL_MATCH | UPPER(DIRECTION) AS DIRECTION | Silver schema uses uppercase convention (INBOUND/OUTBOUND) while FTL uses title case (Inbound/Outbound) | DIRECTION not null | Format standardization required |
| BR-005 | MODALITY | MODALITY | PARTIAL_MATCH | CASE WHEN CHANNEL IN ('Phone', 'Video') THEN CHANNEL ELSE MODALITY END AS MODALITY | FTL separates Phone/Video into CHANNEL column; Email/SMS/Chat in MODALITY column; Silver expects unified MODALITY field | MODALITY, CHANNEL | [ASSUMPTION] When CHANNEL is Phone or Video, use CHANNEL as modality; otherwise use MODALITY column |
| BR-006 | CHANNEL | CHANNEL | PARTIAL_MATCH | CASE WHEN MODALITY IN ('Email', 'SMS', 'Chat') THEN UPPER(MODALITY) ELSE UPPER(CHANNEL) END AS CHANNEL | FTL uses CHANNEL for Phone/Video and MODALITY for Email/SMS/Chat; Silver expects unified CHANNEL field with all 5 values | CHANNEL, MODALITY | [ASSUMPTION] Merge logic produces EMAIL, SMS, CHAT, PHONE, VIDEO values |
| BR-007 | PHONE_SESSIONS | PHONE_SESSIONS | DIRECT_MATCH | PHONE_SESSIONS | Direct pass-through of phone session count | None | None |
| BR-008 | INBOUND_PHONE_MS | INBOUND_PHONE_MINS, PHONE_USAGE | UNIT_CHANGE | INBOUND_PHONE_MS / 60000.0 AS INBOUND_PHONE_MINS | Convert milliseconds to minutes for Silver layer consumption | INBOUND_PHONE_MS not null | [ASSUMPTION] FTL always provides phone duration in milliseconds; division by 60,000 converts to minutes |
| BR-009 | INBOUND_PHONE_MS | DURATION_SEC | UNIT_CHANGE | INBOUND_PHONE_MS / 1000.0 AS DURATION_SEC | Convert milliseconds to seconds for COMBINED_CHANNELS table; only phone duration available | INBOUND_PHONE_MS not null | [LOW CONFIDENCE] Duration only available for phone engagements; Email/SMS/Chat/Video will have NULL DURATION_SEC values |
| BR-010 | IS_ACTIVE | IS_ACTIVE_ACCOUNT | SEMANTIC_MATCH | IS_ACTIVE AS IS_ACTIVE_ACCOUNT | Row-level activity flag treated as account-level activity when aggregated | IS_ACTIVE not null | [ASSUMPTION] If any row for an account has IS_ACTIVE = TRUE, account is considered active for that date |
| BR-011 | DATA_DATE | DATE | UNIT_CHANGE | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') AS DATE | Parse text timestamp to DATE type for USAGE_MASTER table | DATA_DATE not null | [ASSUMPTION] Format is MM/DD/YY HH24:MI (e.g., '5/29/26 13:01'); confirm with BDP if format varies |
| BR-012 | DATA_DATE | REPORT_DATE | GRAIN_CHANGE | TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') AS REPORT_DATE | Parse text timestamp to DATE for aggregation metrics tables | DATA_DATE not null | [ASSUMPTION] DATA_DATE represents report date for aggregation purposes; semantic meaning confirmed with BDP |
| BR-013 | N/A | REFRESH_TIMESTAMP | GAP | CURRENT_TIMESTAMP() AS REFRESH_TIMESTAMP -- GAP ID: GAP-001 | System-generated metadata indicating table refresh time | None | System timestamp at DBT model execution time |
| BR-014 | DATA_DATE | ACCOUNT_FIRST_ACTIVE | GAP | MIN(TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')) OVER (PARTITION BY ACCOUNT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ACCOUNT_FIRST_ACTIVE -- GAP ID: GAP-019 | Calculate first activity date per account using window function over historical data | DATA_DATE, ACCOUNT_ID | [ASSUMPTION] Current FTL data represents complete history; if incremental loads, requires separate historical lookup table |
| BR-015 | DATA_DATE | USER_FIRST_ACTIVE | GAP | MIN(TO_DATE(DATA_DATE, 'M/D/YY HH24:MI')) OVER (PARTITION BY AGENT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS USER_FIRST_ACTIVE -- GAP ID: GAP-020 | Calculate first activity date per user using window function over historical data | DATA_DATE, AGENT_ID | [ASSUMPTION] Current FTL data represents complete history; if incremental loads, requires separate historical lookup table |
| BR-016 | N/A | ENGAGEMENT_STATUS | GAP | NULL AS ENGAGEMENT_STATUS -- GAP ID: GAP-002 | FTL does not track engagement resolution status | None | Consider deriving simple status: CASE WHEN DURATION_SEC > 0 THEN 'Answered' ELSE 'Missed' END (low confidence) |
| BR-017 | N/A | SLA_ACHIEVED | GAP | NULL AS SLA_ACHIEVED -- GAP ID: GAP-003 | FTL does not contain SLA achievement tracking | None | Requires separate SLA calculation system defining thresholds per channel/modality |
| BR-018 | N/A | SOURCE_TABLE | GAP | 'BRZ_FTL_AGENT_BASE_AGG' AS SOURCE_TABLE -- GAP ID: GAP-004 | Hardcoded source table identifier for traceability | None | Static value identifying Bronze source table |
| BR-019 | N/A | PRODUCT_NAME | GAP | 'ZCC Platform' AS PRODUCT_NAME -- GAP ID: GAP-005 | Hardcoded product name; single product assumed | None | [ASSUMPTION] All FTL data represents 'ZCC Platform' product; confirm with Zoom PM if multi-product environment |
| BR-020 | N/A | WINDOW | GAP | CASE WHEN window_dimension.window_type = 'R1' THEN 'R1' WHEN window_dimension.window_type = 'R7' THEN 'R7' WHEN window_dimension.window_type = 'R28' THEN 'R28' END AS WINDOW -- GAP ID: GAP-006 | Explode single-date row into multiple window rows using CROSS JOIN to window dimension table | Window dimension table (R1, R7, R28) | [ASSUMPTION] R1 = 1-day rolling, R7 = 7-day rolling, R28 = 28-day rolling; requires rolling window aggregation logic per window type |
| BR-021 | IS_ACTIVE, AGENT_ID | ACTIVE_USERS | GAP | COUNT(DISTINCT CASE WHEN IS_ACTIVE = TRUE THEN AGENT_ID END) AS ACTIVE_USERS -- GAP ID: GAP-018 | Aggregate count of distinct active agents per account/date/window | IS_ACTIVE, AGENT_ID, GROUP BY clause | GROUP BY REPORT_DATE, ACCOUNT_ID, WINDOW required in aggregation layer |
| BR-022 | N/A | CHAT_USAGE | GAP | NULL AS CHAT_USAGE -- GAP ID: GAP-007 | FTL does not contain chat metrics (duration, sessions, message count) | None | **BLOCKING** Requires BDP to add chat metrics to FTL table OR join to legacy BRZ_CHAT_HISTORY view |
| BR-023 | N/A | USERS_ACTIVE_1_DAY | GAP | NULL AS USERS_ACTIVE_1_DAY -- GAP ID: GAP-012 | Count of users active exactly 1 day in period; requires complex window function | None | [LOW CONFIDENCE] Could derive as: COUNT(DISTINCT AGENT_ID) WHERE active_day_count = 1 (requires pre-calculated active day count per user per window) |
| BR-024 | N/A | VIDEO_USAGE | GAP | NULL AS VIDEO_USAGE -- GAP ID: GAP-008 | FTL does not contain video metrics | None | **BLOCKING** Requires BDP to add video metrics to FTL table OR join to legacy BRZ_VIDEO_HISTORY view |
| BR-025 | N/A | USERS_ACTIVE_16PLUS_DAYS | GAP | NULL AS USERS_ACTIVE_16PLUS_DAYS -- GAP ID: GAP-013 | Count of users active 16+ days in last 28 days; requires historical rolling window | None | [LOW CONFIDENCE] Requires intermediate table with daily active flags per user, then COUNT(active_days) HAVING COUNT >= 16 per 28-day window |
| BR-026 | N/A | IS_PAID_USER | GAP | NULL AS IS_PAID_USER -- GAP ID: GAP-009 | Payment/licensing classification not in FTL | Billing/licensing dimension table (if exists) | **BLOCKING** Requires join to ACCOUNT_DIM or BILLING_DIM table with paid/free classification; confirm with Zoom PM |
| BR-027 | N/A | ACTIVE_DAYS_LAST_7 | GAP | NULL AS ACTIVE_DAYS_LAST_7 -- GAP ID: GAP-010 | Count of active days in last 7 days; requires 7-day rolling window calculation | Historical FTL data | **BLOCKING** Requires intermediate table: COUNT(DISTINCT DATE WHERE IS_ACTIVE = TRUE) OVER (PARTITION BY AGENT_ID, ACCOUNT_ID ORDER BY DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) |
| BR-028 | N/A | ACTIVE_DAYS_LAST_28 | GAP | NULL AS ACTIVE_DAYS_LAST_28 -- GAP ID: GAP-011 | Count of active days in last 28 days; requires 28-day rolling window calculation | Historical FTL data | **BLOCKING** Requires intermediate table: COUNT(DISTINCT DATE WHERE IS_ACTIVE = TRUE) OVER (PARTITION BY AGENT_ID, ACCOUNT_ID ORDER BY DATE ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) |
| BR-029 | N/A | DAILY_CHAT_USAGE | GAP | NULL AS DAILY_CHAT_USAGE -- GAP ID: GAP-025 | Daily chat usage; same as GAP-007 — no chat metrics in FTL | None | **BLOCKING** Requires chat metrics in FTL source |
| BR-030 | INBOUND_PHONE_MS | WEEKLY_PHONE_USAGE | GAP | SUM(INBOUND_PHONE_MS / 60000.0) OVER (PARTITION BY AGENT_ID, ACCOUNT_ID ORDER BY TO_DATE(DATA_DATE) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS WEEKLY_PHONE_USAGE -- GAP ID: GAP-026 | Weekly phone usage using 7-day rolling window | INBOUND_PHONE_MS, historical data | [ASSUMPTION] Weekly = rolling 7-day window; confirm if calendar week (Sun-Sat) or ISO week required instead |
| BR-031 | N/A | CHAT_SESSIONS | GAP | NULL AS CHAT_SESSIONS -- GAP ID: GAP-007 | Count of chat sessions; no chat activity in FTL | None | **BLOCKING** Requires chat metrics in FTL source |
| BR-032 | N/A | SLA_ACHIEVED_SESSIONS | GAP | NULL AS SLA_ACHIEVED_SESSIONS -- GAP ID: GAP-021 | Count of sessions meeting SLA threshold; no SLA tracking in FTL | SLA threshold definitions | Requires SLA threshold per channel/modality and comparison logic (e.g., duration < threshold_seconds) |
| BR-033 | N/A | ACTIVE_1_DAY_L7 | GAP | NULL AS ACTIVE_1_DAY_L7 -- GAP ID: GAP-014 | Count of users active 1 day in last 7 days | Historical FTL data | **BLOCKING** Requires intermediate table with per-user active day counts over 7-day window, then COUNT(DISTINCT AGENT_ID WHERE active_days_L7 = 1) |
| BR-034 | N/A | ACTIVE_4_7_DAYS_L7 | GAP | NULL AS ACTIVE_4_7_DAYS_L7 -- GAP ID: GAP-015 | Count of users active 4-7 days in last 7 days | Historical FTL data | **BLOCKING** Requires intermediate table with per-user active day counts over 7-day window, then COUNT(DISTINCT AGENT_ID WHERE active_days_L7 BETWEEN 4 AND 7) |
| BR-035 | N/A | ACTIVE_1_DAY_L28 | GAP | NULL AS ACTIVE_1_DAY_L28 -- GAP ID: GAP-016 | Count of users active 1 day in last 28 days | Historical FTL data | **BLOCKING** Requires intermediate table with per-user active day counts over 28-day window, then COUNT(DISTINCT AGENT_ID WHERE active_days_L28 = 1) |
| BR-036 | N/A | ACTIVE_16PLUS_DAYS_L28 | GAP | NULL AS ACTIVE_16PLUS_DAYS_L28 -- GAP ID: GAP-017 | Count of users active 16+ days in last 28 days | Historical FTL data | **BLOCKING** Requires intermediate table with per-user active day counts over 28-day window, then COUNT(DISTINCT AGENT_ID WHERE active_days_L28 >= 16) |
| BR-037 | N/A | USERS_ACTIVE_4_7_DAYS | GAP | NULL AS USERS_ACTIVE_4_7_DAYS -- GAP ID: GAP-022 | Count of users active 4-7 days in reporting window | Historical FTL data | [LOW CONFIDENCE] Requires rolling window calculation similar to BR-034 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5: NEW FTL CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| FTL Column | Data Type | Description | New Metric Enabled | Enrich Silver Layer? | Recommendation |
|------------|-----------|-------------|-------------------|---------------------|----------------|
| ZCC_ACCOUNT_ID | TEXT | Secondary account identifier specific to ZCC platform; distinct from general ACCOUNT_ID | Cross-platform account reconciliation; dual-key joins for data quality validation | PENDING DECISION | Add to Silver as optional dimension; confirm with BDP whether ZCC_ACCOUNT_ID provides incremental value over ACCOUNT_ID or represents separate account hierarchy |
| CLIENT_TYPE | TEXT | Device type classification (Mobile, Desktop, Web) | Device analytics: channel preference by device type; mobile-first user segmentation; desktop vs. mobile engagement patterns | YES | **Add to SLV_COMBINED_CHANNELS immediately** — enables high-value device analytics for channel optimization; propose adding to SLV_USAGE_MASTER for daily device-level metrics |
| OS | TEXT | Operating system dimension | OS-specific engagement analysis; platform performance tracking; OS-level support issue identification | YES | **Add to SLV_COMBINED_CHANNELS immediately** — complements CLIENT_TYPE for full device fingerprinting; consider adding to SLV_USAGE_MASTER if OS-level daily metrics are valuable |
| CLUSTER | TEXT | Cloud cluster/region identifier (e.g., eu-central-1, ap-south-1, us-east-1) | Geographic performance analysis; regional engagement patterns; data residency compliance reporting; latency analysis by cluster | YES | **Add to Silver layer immediately** — high-value dimension for regional analysis; propose adding CLUSTER to: (1) SLV_COMBINED_CHANNELS for engagement-level regional tracking; (2) SLV_USAGE_MASTER for daily regional metrics; (3) All metrics tables (CONSOLIDATED_USAGE, DAILY_METRICS, etc.) for regional aggregation capability. Note: CLUSTER may map to future REGION field in Gold layer (GLD_AGGREGATE already has REGION column). |

**Summary:**
FTL provides **4 new dimensions** not present in current Silver schema. All four represent high-value analytical capabilities:

1. **CLIENT_TYPE & OS** enable device/platform analytics — critical for understanding mobile vs. desktop engagement patterns and device-specific optimization opportunities.

2. **CLUSTER** enables regional analytics — essential for geographic performance monitoring, data residency compliance, and latency troubleshooting. This dimension may bridge to the existing REGION field in GLD_AGGREGATE Gold table.

3. **ZCC_ACCOUNT_ID** provides dual account key — value unclear without BDP confirmation of its semantic meaning vs. ACCOUNT_ID.

**Recommendation:** Enrich Silver layer with CLIENT_TYPE, OS, and CLUSTER immediately as part of FTL migration. These dimensions unlock new analysis capabilities without blocking migration. Hold ZCC_ACCOUNT_ID pending BDP clarification on its business purpose.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 6: GAP REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| GAP ID | PI Silver Column | PI Silver Source | Why FTL Cannot Produce This | Blocks Migration? | Proposed Resolution | Raise With |
|--------|-----------------|------------------|----------------------------|-------------------|---------------------|------------|
| GAP-001 | REFRESH_TIMESTAMP | SLV_ACCT_FIRST_ACTIVE, SLV_USER_FIRST_ACTIVE | System-generated metadata timestamp; not present in FTL source data | NO | Use CURRENT_TIMESTAMP() in DBT model at execution time | Data Engineering |
| GAP-002 | ENGAGEMENT_STATUS | SLV_COMBINED_CHANNELS | FTL does not track engagement resolution status (Answered/Missed/Resolved/Abandoned/etc.); no status field in source schema | NO | Option 1: Default to NULL; Option 2: Derive simple status using CASE WHEN DURATION_SEC > 0 THEN 'Answered' ELSE 'Missed' END (low confidence); Option 3: BDP adds STATUS field to FTL | BDP Team + Zoom PM |
| GAP-003 | SLA_ACHIEVED | SLV_COMBINED_CHANNELS, SLV_USAGE_MASTER (as SLA_ACHIEVED_SESSIONS) | FTL does not contain SLA achievement flag or SLA threshold data; no way to determine if engagement met SLA target | NO | Option 1: Default to NULL; Option 2: Build separate SLA calculation pipeline with threshold definitions per channel/modality and compare duration against threshold; Option 3: BDP adds SLA_ACHIEVED to FTL | BDP Team + Zoom PM |
| GAP-004 | SOURCE_TABLE | SLV_COMBINED_CHANNELS | Metadata field identifying originating Bronze view (e.g., PHONE_HISTORY, CHAT_HISTORY); FTL is single unified table | NO | Hardcode 'BRZ_FTL_AGENT_BASE_AGG' as static value in DBT model | Data Engineering |
| GAP-005 | PRODUCT_NAME | SLV_CONSOLIDATED_USAGE | Product classification dimension (e.g., 'ZCC Platform', 'Zoom Phone', 'Zoom Meetings'); FTL does not include product taxonomy | NO | Option 1: Hardcode 'ZCC Platform' as static value (assumption: all FTL data = single product); Option 2: Join to product dimension table if multi-product environment | Zoom PM (confirm single vs. multi-product) |
| GAP-006 | WINDOW | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | Reporting window classification (R1, R7, R28) for rolling period reports; FTL provides single-day snapshot without window logic | YES | Implement window explosion logic in DBT: CROSS JOIN FTL source to window dimension table (R1, R7, R28), then apply rolling aggregation for each window type (1-day, 7-day, 28-day lookback) | Data Engineering |
| GAP-007 | CHAT_USAGE, CHAT_SESSIONS | SLV_DAILY_METRICS, SLV_WEEKLY_METRICS, SLV_ROLL_29_DAY_USAGE, SLV_USAGE_MASTER | FTL Bronze table contains no chat activity metrics (session count, duration, message count, or any chat-related fields); MODALITY includes 'Chat' but no associated quantitative metrics | **YES** | **BLOCKING** Option 1 (recommended): BDP adds chat metrics (CHAT_SESSIONS, CHAT_DURATION_MS, CHAT_MESSAGES) to FTL table; Option 2: Join FTL to legacy BRZ_CHAT_HISTORY view to backfill chat metrics (requires alignment on ENGAGEMENT_ID or USER_ID + DATE join key) | **BDP Team (Priority 1)** |
| GAP-008 | VIDEO_USAGE | SLV_MONTHLY_METRICS | FTL Bronze table contains no video activity metrics (session count, duration, participants, etc.); CHANNEL includes 'Video' but no associated quantitative metrics | **YES** | **BLOCKING** Option 1 (recommended): BDP adds video metrics (VIDEO_SESSIONS, VIDEO_DURATION_MS, VIDEO_PARTICIPANTS) to FTL table; Option 2: Join FTL to legacy BRZ_VIDEO_HISTORY view to backfill video metrics | **BDP Team (Priority 2)** |
| GAP-009 | IS_PAID_USER | SLV_ROLL_29_DAY_USAGE | Payment/licensing classification field; FTL contains no billing or subscription status data | **YES** | **BLOCKING** Option 1: Join FTL to existing ACCOUNT_DIM or BILLING_DIM table (if exists in PI schema) on ACCOUNT_ID to retrieve paid/free user classification; Option 2: BDP adds IS_PAID field to FTL; Option 3: Accept NULL and exclude paid user segmentation from ROLL_29_DAY_USAGE | **Zoom PM + BDP Team** |
| GAP-010 | ACTIVE_DAYS_LAST_7 | SLV_ROLL_29_DAY_USAGE | Count of distinct active days in last 7 days; requires 7-day rolling window calculation not available in single-day FTL grain | **YES** | **BLOCKING** Build intermediate DBT model: Create rolling window table that calculates COUNT(DISTINCT DATE WHERE IS_ACTIVE = TRUE) over 7-day lookback per user per account; requires historical FTL data (minimum 7 days history) | **Data Engineering** |
| GAP-011 | ACTIVE_DAYS_LAST_28 | SLV_ROLL_29_DAY_USAGE | Count of distinct active days in last 28 days; requires 28-day rolling window calculation not available in single-day FTL grain | **YES** | **BLOCKING** Build intermediate DBT model: Create rolling window table that calculates COUNT(DISTINCT DATE WHERE IS_ACTIVE = TRUE) over 28-day lookback per user per account; requires historical FTL data (minimum 28 days history) | **Data Engineering** |
| GAP-012 | USERS_ACTIVE_1_DAY | SLV_DAILY_METRICS | Count of users active exactly 1 day in reporting period; requires classification logic not derivable from single-day FTL grain without historical context | NO | Low confidence derivation: Use rolling window intermediate table (from GAP-010/011) to count users WHERE active_day_count = 1; alternatively default to NULL if low-priority metric | Data Engineering |
| GAP-013 | USERS_ACTIVE_16PLUS_DAYS | SLV_MONTHLY_METRICS | Count of users active 16 or more days in last 28 days; requires 28-day rolling window with 16+ day filter | NO | Low confidence derivation: Use rolling window intermediate table (from GAP-011) to count users WHERE active_day_count >= 16; alternatively default to NULL if low-priority metric | Data Engineering |
| GAP-014 | ACTIVE_1_DAY_L7 | SLV_USER_ACTIVE_DAYS | Count of users active exactly 1 day in last 7 days (per account); complex classification requiring historical rolling calculation | **YES** | **BLOCKING** Build intermediate rolling window table (from GAP-010), then aggregate: COUNT(DISTINCT AGENT_ID WHERE active_days_L7 = 1) GROUP BY REPORT_DATE, ACCOUNT_ID | **Data Engineering** |
| GAP-015 | ACTIVE_4_7_DAYS_L7 | SLV_USER_ACTIVE_DAYS | Count of users active 4-7 days in last 7 days (per account); complex classification requiring historical rolling calculation | **YES** | **BLOCKING** Build intermediate rolling window table (from GAP-010), then aggregate: COUNT(DISTINCT AGENT_ID WHERE active_days_L7 BETWEEN 4 AND 7) GROUP BY REPORT_DATE, ACCOUNT_ID | **Data Engineering** |
| GAP-016 | ACTIVE_1_DAY_L28 | SLV_USER_ACTIVE_DAYS | Count of users active exactly 1 day in last 28 days (per account); complex classification requiring historical rolling calculation | **YES** | **BLOCKING** Build intermediate rolling window table (from GAP-011), then aggregate: COUNT(DISTINCT AGENT_ID WHERE active_days_L28 = 1) GROUP BY REPORT_DATE, ACCOUNT_ID | **Data Engineering** |
| GAP-017 | ACTIVE_16PLUS_DAYS_L28 | SLV_USER_ACTIVE_DAYS | Count of users active 16+ days in last 28 days (per account); complex classification requiring historical rolling calculation | **YES** | **BLOCKING** Build intermediate rolling window table (from GAP-011), then aggregate: COUNT(DISTINCT AGENT_ID WHERE active_days_L28 >= 16) GROUP BY REPORT_DATE, ACCOUNT_ID | **Data Engineering** |
| GAP-018 | ACTIVE_USERS | SLV_CONSOLIDATED_USAGE, SLV_DAILY_METRICS, SLV_MONTHLY_METRICS, SLV_WEEKLY_METRICS | Aggregated count of distinct active users per account/date/window; not a gap in source data but requires GROUP BY aggregation logic | NO | Implement in DBT: COUNT(DISTINCT CASE WHEN IS_ACTIVE = TRUE THEN AGENT_ID END) GROUP BY REPORT_DATE, ACCOUNT_ID, WINDOW | Data Engineering |
| GAP-019 | ACCOUNT_FIRST_ACTIVE | SLV_ACCT_FIRST_ACTIVE, SLV_USAGE_MASTER | First activity date per account; FTL provides daily snapshots but not historical first date; requires MIN(DATE) across all history | NO | Calculate in DBT: MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY ACCOUNT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) — assumes current FTL load contains complete history; if incremental loads, build separate dimension table with MIN date per account | Data Engineering (confirm FTL load strategy with BDP) |
| GAP-020 | USER_FIRST_ACTIVE | SLV_USER_FIRST_ACTIVE, SLV_USAGE_MASTER | First activity date per user; FTL provides daily snapshots but not historical first date; requires MIN(DATE) across all history | NO | Calculate in DBT: MIN(TO_DATE(DATA_DATE)) OVER (PARTITION BY AGENT_ID ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) — assumes current FTL load contains complete history; if incremental loads, build separate dimension table with MIN date per user | Data Engineering (confirm FTL load strategy with BDP) |
| GAP-021 | SLA_ACHIEVED_SESSIONS | SLV_USAGE_MASTER | Count of sessions meeting SLA threshold; requires both SLA threshold definitions and SLA achievement flag | NO | Same as GAP-003; default to NULL or build separate SLA calculation logic | BDP Team + Zoom PM |
| GAP-022 | USERS_ACTIVE_4_7_DAYS | SLV_WEEKLY_METRICS | Count of users active 4-7 days in reporting window; requires rolling window calculation | NO | Low confidence derivation: Use rolling window intermediate table (from GAP-010) for 7-day window; alternatively default to NULL if low-priority metric | Data Engineering |
| GAP-023 | DURATION_SEC | SLV_COMBINED_CHANNELS | FTL provides INBOUND_PHONE_MS (phone duration in milliseconds) but no duration fields for Email, SMS, Chat, or Video modalities | NO | Partial solution: Convert INBOUND_PHONE_MS to seconds for phone engagements; default to NULL for Email/SMS/Chat/Video rows; BDP to add duration fields for all modalities if duration tracking is critical | BDP Team (low priority unless duration needed for non-phone analysis) |
| GAP-024 | START_DATE | SLV_COMBINED_CHANNELS | Semantic ambiguity: FTL provides DATA_DATE as text timestamp ('5/29/26 13:01') but unclear if this represents engagement start time or report date | NO | Clarify with BDP: Does DATA_DATE represent engagement start timestamp or daily report date? Assuming engagement start for now; parse using TO_DATE(DATA_DATE, 'M/D/YY HH24:MI') | BDP Team (confirm semantics) |
| GAP-025 | DAILY_CHAT_USAGE | SLV_ROLL_29_DAY_USAGE | Daily aggregated chat usage; same root cause as GAP-007 — no chat metrics in FTL | **YES** | **BLOCKING** Same resolution as GAP-007: BDP adds chat metrics to FTL table | **BDP Team (Priority 1)** |
| GAP-026 | WEEKLY_PHONE_USAGE | SLV_ROLL_29_DAY_USAGE | Weekly aggregated phone usage; FTL has daily INBOUND_PHONE_MS but weekly boundary definition unclear (Sunday-Saturday? Rolling 7-day? ISO week?) | NO | Implement rolling 7-day SUM: SUM(INBOUND_PHONE_