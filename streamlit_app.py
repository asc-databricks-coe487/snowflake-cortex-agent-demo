# ============================================================
# FILE: streamlit_app.py
# PURPOSE: 3-Agent Pipeline with Human-in-the-Loop
#          + Selective re-run from any step
#          + Snowflake persistence
#          + GitHub push for every run output
#          + Cost summary after pipeline completes
# DEPLOY: Streamlit in Snowflake
# ============================================================

import streamlit as st
import json
import csv
import io
from datetime import datetime

DATABASE      = "ZOOM_AI_POC"
SCHEMA        = "CORTEX_AGENT"
AGENT_1       = "MAPPING_ANALYSIS_AGENT"
AGENT_2       = "DBT_CODE_GENERATOR_AGENT"
AGENT_3       = "TEST_CASE_GENERATOR_AGENT"
PERSIST_TABLE = f"{DATABASE}.{SCHEMA}.PIPELINE_RUN_HISTORY"

session = st.connection("snowflake").session()


# ══════════════════════════════════════════════════════════════
# PERSISTENCE
# ══════════════════════════════════════════════════════════════

def ensure_persist_table():
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {PERSIST_TABLE} (
            RUN_ID          VARCHAR(50)       NOT NULL,
            CREATED_AT      TIMESTAMP_NTZ     DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT      TIMESTAMP_NTZ     DEFAULT CURRENT_TIMESTAMP(),
            FTL_TABLES      VARCHAR(2000),
            PI_TABLES       VARCHAR(2000),
            MAPPING_REPORT  VARCHAR(16777216),
            MAPPING_CSV     VARCHAR(16777216),
            APPROVED_CSV    VARCHAR(16777216),
            SILVER_OUTPUT   VARCHAR(16777216),
            GOLD_OUTPUT     VARCHAR(16777216),
            DBT_OUTPUT      VARCHAR(16777216),
            APPROVED_DBT    VARCHAR(16777216),
            TEST_OUTPUT     VARCHAR(16777216),
            APPROVED_TESTS  VARCHAR(16777216),
            PIPELINE_STATUS VARCHAR(50)       DEFAULT 'IN_PROGRESS',
            COMMENTS_LOG    VARCHAR(16777216),
            AGENT_CALL_LOG  VARCHAR(16777216),
            PRIMARY KEY (RUN_ID)
        )
    """).collect()


def save_run(run_id: str):
    s         = st.session_state
    confirmed = s.get("confirmed_tables", {})
    ftl       = json.dumps(confirmed.get("ftl", []))
    pi        = json.dumps(confirmed.get("pi",  []))

    if s.get("approved_tests"):   status = "COMPLETE"
    elif s.get("approved_dbt"):   status = "TESTS_PENDING"
    elif s.get("approved_csv"):   status = "DBT_PENDING"
    elif s.get("mapping_report"): status = "MAPPING_COMPLETE"
    else:                         status = "IN_PROGRESS"

    comments = {
        "review1": s.get("review1_comment_history", []),
        "review2": s.get("review2_comment_history", []),
        "review3": s.get("review3_comment_history", [])
    }

    def e(v):
        return "'" + str(v or "").replace("'", "''") + "'"

    session.sql(f"""
        MERGE INTO {PERSIST_TABLE} AS t
        USING (SELECT
            {e(run_id)}                        AS RUN_ID,
            {e(ftl)}                           AS FTL_TABLES,
            {e(pi)}                            AS PI_TABLES,
            {e(s.get('mapping_report'))}       AS MAPPING_REPORT,
            {e(s.get('mapping_csv'))}          AS MAPPING_CSV,
            {e(s.get('approved_csv'))}         AS APPROVED_CSV,
            {e(s.get('silver_output'))}        AS SILVER_OUTPUT,
            {e(s.get('gold_output'))}          AS GOLD_OUTPUT,
            {e(s.get('dbt_output'))}           AS DBT_OUTPUT,
            {e(s.get('approved_dbt'))}         AS APPROVED_DBT,
            {e(s.get('test_output'))}          AS TEST_OUTPUT,
            {e(s.get('approved_tests'))}       AS APPROVED_TESTS,
            {e(status)}                        AS PIPELINE_STATUS,
            {e(json.dumps(comments))}          AS COMMENTS_LOG,
            {e(json.dumps(s.get('agent_call_log', [])))} AS AGENT_CALL_LOG
        ) AS s ON t.RUN_ID = s.RUN_ID
        WHEN MATCHED THEN UPDATE SET
            t.UPDATED_AT      = CURRENT_TIMESTAMP(),
            t.FTL_TABLES      = s.FTL_TABLES,
            t.PI_TABLES       = s.PI_TABLES,
            t.MAPPING_REPORT  = s.MAPPING_REPORT,
            t.MAPPING_CSV     = s.MAPPING_CSV,
            t.APPROVED_CSV    = s.APPROVED_CSV,
            t.SILVER_OUTPUT   = s.SILVER_OUTPUT,
            t.GOLD_OUTPUT     = s.GOLD_OUTPUT,
            t.DBT_OUTPUT      = s.DBT_OUTPUT,
            t.APPROVED_DBT    = s.APPROVED_DBT,
            t.TEST_OUTPUT     = s.TEST_OUTPUT,
            t.APPROVED_TESTS  = s.APPROVED_TESTS,
            t.PIPELINE_STATUS = s.PIPELINE_STATUS,
            t.COMMENTS_LOG    = s.COMMENTS_LOG,
            t.AGENT_CALL_LOG  = s.AGENT_CALL_LOG
        WHEN NOT MATCHED THEN INSERT (
            RUN_ID, FTL_TABLES, PI_TABLES,
            MAPPING_REPORT, MAPPING_CSV, APPROVED_CSV,
            SILVER_OUTPUT, GOLD_OUTPUT, DBT_OUTPUT,
            APPROVED_DBT, TEST_OUTPUT, APPROVED_TESTS,
            PIPELINE_STATUS, COMMENTS_LOG, AGENT_CALL_LOG
        ) VALUES (
            s.RUN_ID, s.FTL_TABLES, s.PI_TABLES,
            s.MAPPING_REPORT, s.MAPPING_CSV, s.APPROVED_CSV,
            s.SILVER_OUTPUT, s.GOLD_OUTPUT, s.DBT_OUTPUT,
            s.APPROVED_DBT, s.TEST_OUTPUT, s.APPROVED_TESTS,
            s.PIPELINE_STATUS, s.COMMENTS_LOG, s.AGENT_CALL_LOG
        )
    """).collect()


def load_run(run_id: str):
    rows = session.sql(f"""
        SELECT * FROM {PERSIST_TABLE}
        WHERE RUN_ID = '{run_id}'
    """).collect()
    if not rows:
        return False
    row = rows[0]
    def v(col):
        val = row[col]
        return val if val and str(val) != "None" else None
    ftl = json.loads(v("FTL_TABLES") or "[]")
    pi  = json.loads(v("PI_TABLES")  or "[]")
    if ftl and pi:
        st.session_state["confirmed_tables"] = {"ftl": ftl, "pi": pi}
        st.session_state["ftl_source_tables"] = ftl
        st.session_state["pi_target_tables"]  = pi
    for key, col in [
        ("mapping_report", "MAPPING_REPORT"),
        ("mapping_csv",    "MAPPING_CSV"),
        ("approved_csv",   "APPROVED_CSV"),
        ("silver_output",  "SILVER_OUTPUT"),
        ("gold_output",    "GOLD_OUTPUT"),
        ("dbt_output",     "DBT_OUTPUT"),
        ("approved_dbt",   "APPROVED_DBT"),
        ("test_output",    "TEST_OUTPUT"),
        ("approved_tests", "APPROVED_TESTS"),
    ]:
        val = v(col)
        if val:
            st.session_state[key] = val
    try:
        c = json.loads(v("COMMENTS_LOG") or "{}")
        for stage in ["review1", "review2", "review3"]:
            h = c.get(stage, [])
            if h:
                st.session_state[f"{stage}_comment_history"] = h
    except Exception:
        pass
    # Restore agent call log so cost summary stays accurate
    try:
        call_log_raw = v("AGENT_CALL_LOG")
        if call_log_raw:
            st.session_state["agent_call_log"] =                 json.loads(call_log_raw)
    except Exception:
        pass
    st.session_state["active_run_id"] = run_id
    return True


def get_all_runs() -> list:
    try:
        return session.sql(f"""
            SELECT RUN_ID, CREATED_AT, UPDATED_AT,
                   FTL_TABLES, PI_TABLES, PIPELINE_STATUS
            FROM {PERSIST_TABLE}
            ORDER BY UPDATED_AT DESC LIMIT 20
        """).collect()
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════
# GITHUB PUSH
# ══════════════════════════════════════════════════════════════

def push_output_to_github(
    run_id: str,
    filename: str,
    content: str,
    commit_message: str
):
    """Push a run output file to GitHub under runs/RUN_ID/."""
    safe_content = content.replace("'", "''")
    safe_msg     = commit_message.replace("'", "''")
    file_path    = f"runs/{run_id}/{filename}"

    try:
        result = session.sql(f"""
            CALL {DATABASE}.{SCHEMA}.SP_PUSH_TO_GITHUB(
                '{file_path}',
                '{safe_content[:50000]}',
                '{safe_msg}'
            )
        """).collect()

        response = result[0][0] if result else ""
        if "SUCCESS" in str(response):
            return True
        else:
            st.warning(
                f"⚠️ GitHub push warning: {response}. "
                f"Output still saved to Snowflake."
            )
            return False
    except Exception as e:
        st.warning(
            f"⚠️ Could not push to GitHub: {str(e)[:100]}. "
            f"Output saved to Snowflake only."
        )
        return False


def push_run_summary(run_id: str):
    """Push a summary file when pipeline completes."""
    s         = st.session_state
    confirmed = s.get("confirmed_tables", {})

    ftl = "\n".join(
        f"- `{t}`" for t in confirmed.get("ftl", [])
    )
    pi = "\n".join(
        f"- `{t}`" for t in confirmed.get("pi", [])
    )

    summary = f"""# Run: {run_id}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Tables
**FTL Source:**
{ftl}

**PI Target:**
{pi}

## Outputs
| Output | Status |
|--------|--------|
| Mapping Report | {'✅' if s.get('mapping_report') else '—'} |
| Mapping CSV    | {'✅' if s.get('mapping_csv')    else '—'} |
| Silver Model   | {'✅' if s.get('silver_output')  else '—'} |
| Gold Model     | {'✅' if s.get('gold_output')    else '—'} |
| Test Suite     | {'✅' if s.get('test_output')    else '—'} |

## Approvals
| Stage | Status |
|-------|--------|
| Mapping | {'✅ Approved' if s.get('approved_csv')   else '⏳ Pending'} |
| DBT     | {'✅ Approved' if s.get('approved_dbt')   else '⏳ Pending'} |
| Tests   | {'✅ Approved' if s.get('approved_tests') else '⏳ Pending'} |
"""
    push_output_to_github(
        run_id,
        "run_summary.md",
        summary,
        f"run({run_id}): pipeline complete"
    )


# ══════════════════════════════════════════════════════════════
# COST SUMMARY
# ══════════════════════════════════════════════════════════════

def show_cost_summary():
    """
    Show real-time per-run cost summary using:
    1. Agent call log tracked during this session (immediate)
    2. QUERY_HISTORY for Snowflake credit usage (near real-time, ~minutes)
    3. ACCOUNT_USAGE as fallback (up to 3hr latency)
    """
    st.divider()
    st.header("💰 Run Cost Summary")

    call_log  = st.session_state.get("agent_call_log", [])
    run_start = st.session_state.get("run_start_time", datetime.now())
    run_id    = st.session_state.get("active_run_id", "UNKNOWN")

    # ── Section 1: Per-call cost (immediate, no delay) ──────────
    if call_log:
        import pandas as pd

        st.subheader("📋 Per-Call Cost Breakdown")
        st.caption(
            "Estimated using Snowflake Cortex "
            "claude-sonnet-4-5 pricing. "
            "Input: 0.000003 credits/token · "
            "Output: 0.000015 credits/token · "
            "1 credit ≈ $2 USD"
        )

        # ── Top-level summary metrics ──────────────────────────
        total_calls    = len(call_log)
        total_duration = sum(c.get("duration_s",   0) for c in call_log)
        total_tokens   = sum(c.get("total_tokens", 0) for c in call_log)
        total_credits  = sum(c.get("total_credits",0) for c in call_log)
        total_usd      = sum(c.get("total_usd",    0) for c in call_log)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Agent Calls",  total_calls)
        with m2:
            st.metric(
                "Total Time",
                f"{total_duration:.0f}s "
                f"({total_duration/60:.1f} min)"
            )
        with m3:
            st.metric(
                "Total Tokens",
                f"{total_tokens:,}"
            )
        with m4:
            st.metric(
                "Est. Credits",
                f"{total_credits:.4f}",
                help=f"≈ ${total_usd:.4f} USD"
            )

        st.caption(f"💵 Estimated total cost: **${total_usd:.4f} USD**")

        # ── Per-call table ─────────────────────────────────────
        df_log = pd.DataFrame([{
            "Step":            c.get("step",         "—"),
            "Agent":           c.get("agent",        "—"),
            "Start":           c.get("start",        "—"),
            "Duration (s)":    c.get("duration_s",    0),
            "Input Tokens":    c.get("input_tokens",  0),
            "Output Tokens":   c.get("output_tokens", 0),
            "Total Tokens":    c.get("total_tokens",  0),
            "Credits":         c.get("total_credits", 0),
            "Est. USD":        c.get("total_usd",     0)
        } for c in call_log])

        st.dataframe(df_log, use_container_width=True)

        # ── Per-agent summary ──────────────────────────────────
        st.markdown("**Summary by Agent:**")
        summary_df = df_log.groupby("Agent").agg(
            Calls         = ("Duration (s)",  "count"),
            Total_Dur_s   = ("Duration (s)",  "sum"),
            Total_Tokens  = ("Total Tokens",  "sum"),
            Total_Credits = ("Credits",       "sum"),
            Total_USD     = ("Est. USD",      "sum")
        ).reset_index()
        st.dataframe(summary_df, use_container_width=True)

    else:
        st.info("No agent calls recorded for this run yet.")

    st.divider()

    # ── Section 2: Snowflake credits from QUERY_HISTORY ─────────
    st.subheader("🔢 Snowflake Credit Usage")
    st.caption(
        "From `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` — "
        "near real-time (few minutes delay)"
    )

    try:
        run_start_str = run_start.strftime("%Y-%m-%d %H:%M:%S")

        qh_df = session.sql(f"""
            SELECT
                QUERY_TEXT,
                START_TIME,
                END_TIME,
                TOTAL_ELAPSED_TIME / 1000        AS DURATION_SEC,
                CREDITS_USED_CLOUD_SERVICES      AS CREDITS,
                EXECUTION_STATUS
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= '{run_start_str}'::TIMESTAMP_NTZ
              AND EXECUTION_STATUS = 'SUCCESS'
              AND (
                  QUERY_TEXT ILIKE '%DATA_AGENT_RUN%'
                  OR QUERY_TEXT ILIKE '%{AGENT_1}%'
                  OR QUERY_TEXT ILIKE '%{AGENT_2}%'
                  OR QUERY_TEXT ILIKE '%{AGENT_3}%'
              )
            ORDER BY START_TIME
        """).to_pandas()

        if not qh_df.empty:
            total_credits = qh_df["CREDITS"].sum()
            total_dur     = qh_df["DURATION_SEC"].sum()

            m1, m2 = st.columns(2)
            with m1:
                st.metric(
                    "Total Credits Used",
                    f"{total_credits:.6f}"
                )
            with m2:
                st.metric(
                    "Total Query Time",
                    f"{total_dur:.1f}s"
                )

            with st.expander(
                "📋 Query-level breakdown", expanded=False
            ):
                st.dataframe(
                    qh_df[[
                        "START_TIME", "DURATION_SEC",
                        "CREDITS", "QUERY_TEXT"
                    ]].assign(
                        QUERY_TEXT=qh_df["QUERY_TEXT"].str[:80]
                    ),
                    use_container_width=True
                )

            # Build cost summary for GitHub push
            if call_log:
                import pandas as pd
                df_c = pd.DataFrame([{
                    "Step":    c.get("step", "—"),
                    "Agent":   c.get("agent", "—"),
                    "Dur(s)":  c.get("duration_s", 0),
                    "Tokens":  c.get("total_tokens", 0),
                    "Credits": c.get("total_credits", 0),
                    "USD":     c.get("total_usd", 0)
                } for c in call_log])
                t_tok  = df_c["Tokens"].sum()
                t_cred = df_c["Credits"].sum()
                t_usd  = df_c["USD"].sum()
                t_dur  = df_c["Dur(s)"].sum()
            else:
                df_c   = None
                t_tok  = t_cred = t_usd = t_dur = 0

            cost_md = f"""# Cost Summary: {run_id}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Total Cost
| Metric | Value |
|--------|-------|
| Total Agent Calls | {len(call_log)} |
| Total Duration    | {t_dur:.1f}s ({t_dur/60:.1f} min) |
| Total Tokens      | {int(t_tok):,} |
| Est. Credits      | {t_cred:.4f} |
| Est. USD          | ${t_usd:.4f} |

## Per-Call Breakdown
{df_c.to_markdown(index=False) if df_c is not None else "No data"}

## Snowflake Query Credits
| Total Credits | Total Time |
|---------------|------------|
| {total_credits:.6f} | {total_dur:.1f}s |
"""
            push_output_to_github(
                run_id,
                "cost_summary.md",
                cost_md,
                f"run({run_id}): cost summary"
            )

        else:
            st.info(
                "ℹ️ Query history not yet available. "
                "Try refreshing in a few minutes."
            )

    except Exception as e:
        st.warning(
            f"⚠️ Could not fetch query history: {str(e)[:200]}"
        )

    st.divider()

    # ── Section 3: ACCOUNT_USAGE fallback ───────────────────────
    with st.expander(
        "📊 Full Token Usage (ACCOUNT_USAGE — up to 3hr delay)",
        expanded=False
    ):
        st.caption(
            "If this is empty, check back in a few hours. "
            "This data is more detailed but has latency."
        )
        try:
            au_df = session.sql(f"""
                SELECT
                    AGENT_NAME,
                    START_TIME,
                    END_TIME,
                    TOKENS,
                    TOKEN_CREDITS
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
                WHERE AGENT_DATABASE_NAME = '{DATABASE}'
                  AND AGENT_SCHEMA_NAME   = '{SCHEMA}'
                  AND AGENT_NAME IN (
                      '{AGENT_1}', '{AGENT_2}', '{AGENT_3}'
                  )
                  AND START_TIME >= '{run_start_str}'::TIMESTAMP_NTZ
                ORDER BY START_TIME
            """).to_pandas()

            if not au_df.empty:
                st.dataframe(au_df, use_container_width=True)
                st.metric(
                    "Total Token Credits",
                    f"{au_df['TOKEN_CREDITS'].sum():.6f}"
                )
                st.metric(
                    "Total Tokens",
                    f"{int(au_df['TOKENS'].sum()):,}"
                )
            else:
                st.info("No data yet — check back in a few hours.")

        except Exception as e:
            st.warning(f"Could not fetch: {str(e)[:150]}")


# Cortex claude-sonnet-4-5 pricing (Snowflake credits per token)
# Source: Snowflake Cortex LLM pricing docs
# Input:  0.000003 credits per token  (~$0.003 / 1K tokens)
# Output: 0.000015 credits per token  (~$0.015 / 1K tokens)
# 1 credit ≈ $2 USD (Snowflake standard rate)
def show_comment_and_rerun(
    stage_key: str,
    agent_name: str,
    output_key: str,
    prompt_builder,
    rerun_label: str = "🔁 Submit Comment — Agent will revise"
):
    """
    Renders a comment box after any agent output.
    If user types a comment and clicks submit:
      - Comment is saved to history
      - Agent is re-called with the comment + previous output
      - Output is updated in session state + saved to Snowflake
      - GitHub push triggers automatically
    """
    st.markdown("---")
    st.markdown("### 💬 Leave a Comment")
    st.caption(
        "Type any correction or instruction below. "
        "The agent will revise its output based on your feedback. "
        "Leave blank and move on if you are satisfied."
    )

    comment = st.text_area(
        "Your comments / correction instructions",
        placeholder=(
            "e.g. 'Change MODALITY classification from "
            "DIRECT_MATCH to PARTIAL_MATCH' or "
            "'The Silver model is missing the CLUSTER_RAW column'"
        ),
        height=100,
        key=f"{stage_key}_comment_input"
    )

    # Show comment history if any previous rounds
    history_key = f"{stage_key}_comment_history"
    history     = st.session_state.get(history_key, [])
    if history:
        with st.expander(
            f"📝 Comment History ({len(history)} round(s))",
            expanded=False
        ):
            for i, h in enumerate(history):
                st.info(f"**Round {i + 1}:** {h}")

    if st.button(
        rerun_label,
        disabled=not comment.strip(),
        key=f"{stage_key}_comment_btn"
    ):
        # Save to history
        history.append(comment.strip())
        st.session_state[history_key] = history

        # Build revised prompt
        current_output = st.session_state.get(output_key, "")
        prompt         = prompt_builder(
            comment.strip(), current_output
        )

        with st.spinner(
            f"🤖 {agent_name} is revising based on "
            f"your comment..."
        ):
            st.session_state["current_step"] = (
                f"{stage_key} revision"
            )
            revised = call_agent(agent_name, prompt)

        # Update output
        st.session_state[output_key] = revised

        # If dbt — keep combined dbt_output in sync
        if output_key == "silver_output":
            st.session_state["dbt_output"] = (
                revised + "\n\n---\n\n"
                + st.session_state.get("gold_output", "")
            )
        if output_key == "gold_output":
            st.session_state["dbt_output"] = (
                st.session_state.get("silver_output", "")
                + "\n\n---\n\n" + revised
            )

        # Re-extract CSV if mapping report was revised
        if output_key == "mapping_report":
            csv_t = extract_csv(revised)
            if csv_t:
                st.session_state["mapping_csv"] = csv_t

        save_run(st.session_state.get("active_run_id", ""))
        st.success(
            "✅ Agent revised the output. "
            "Review below and approve or comment again."
        )
        st.rerun()


CREDITS_PER_INPUT_TOKEN  = 0.000003
CREDITS_PER_OUTPUT_TOKEN = 0.000015
CHARS_PER_TOKEN          = 4  # rough approximation


def estimate_tokens(text: str) -> int:
    """Estimate token count from character count."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_cost(input_tokens: int,
                  output_tokens: int) -> dict:
    """Calculate estimated Snowflake credits and USD cost."""
    input_credits  = input_tokens  * CREDITS_PER_INPUT_TOKEN
    output_credits = output_tokens * CREDITS_PER_OUTPUT_TOKEN
    total_credits  = input_credits + output_credits
    total_usd      = total_credits * 2.0  # $2 per credit
    return {
        "input_tokens":   input_tokens,
        "output_tokens":  output_tokens,
        "total_tokens":   input_tokens + output_tokens,
        "input_credits":  round(input_credits,  6),
        "output_credits": round(output_credits, 6),
        "total_credits":  round(total_credits,  6),
        "total_usd":      round(total_usd,       6)
    }


def call_agent(agent_name: str, message: str) -> str:
    """
    Call agent and track timing + token count + estimated cost.
    Cost is estimated using Cortex pricing for claude-sonnet-4-5.
    """
    fqn  = f"{DATABASE}.{SCHEMA}.{agent_name}"
    body = json.dumps({
        "messages": [{"role": "user",
                      "content": [{"type": "text",
                                   "text": message}]}],
        "stream": False
    })
    sql = (f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN("
           f"'{fqn}', $${body}$$) AS RESPONSE")

    call_start = datetime.now()
    result     = session.sql(sql).collect()
    call_end   = datetime.now()
    duration_s = (call_end - call_start).total_seconds()

    response  = json.loads(result[0]["RESPONSE"])
    full_text = "".join(
        i.get("text", "") for i in response.get("content", [])
        if i.get("type") == "text"
    )

    # Estimate tokens and cost
    input_tokens  = estimate_tokens(message)
    output_tokens = estimate_tokens(full_text)
    cost          = estimate_cost(input_tokens, output_tokens)

    # Accumulate call log — never replace, so re-runs add to total
    call_log = st.session_state.get("agent_call_log", [])
    call_log.append({
        "agent":          agent_name,
        "step":           st.session_state.get(
                              "current_step", "unknown"
                          ),
        "start":          call_start.strftime("%H:%M:%S"),
        "end":            call_end.strftime("%H:%M:%S"),
        "duration_s":     round(duration_s, 1),
        "input_tokens":   cost["input_tokens"],
        "output_tokens":  cost["output_tokens"],
        "total_tokens":   cost["total_tokens"],
        "total_credits":  cost["total_credits"],
        "total_usd":      cost["total_usd"]
    })
    st.session_state["agent_call_log"] = call_log

    # Persist immediately so page refresh keeps the log
    run_id = st.session_state.get("active_run_id", "")
    if run_id:
        try:
            save_run(run_id)
        except Exception:
            pass

    return full_text


def trim(text: str, limit: int = 8000) -> str:
    return text[:limit] if len(text) > limit else text


def extract_csv(text: str) -> str:
    lines, out, in_csv = text.split("\n"), [], False
    for line in lines:
        if "FTL_Bronze_Column" in line and "Classification" in line:
            in_csv = True
        if in_csv:
            if line.startswith("```") and out:
                break
            if not line.startswith("```"):
                out.append(line)
    return "\n".join(out) if out else ""


def parse_csv(text: str) -> list:
    try:
        return list(csv.DictReader(io.StringIO(text.strip())))
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_databases():
    try:
        return [r["DATABASE_NAME"] for r in session.sql(
            "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES "
            "ORDER BY DATABASE_NAME"
        ).collect()]
    except Exception:
        return [r["name"] for r in session.sql(
            "SHOW DATABASES"
        ).collect()]


@st.cache_data(ttl=300)
def get_schemas(db: str):
    try:
        return [r["SCHEMA_NAME"] for r in session.sql(f"""
            SELECT SCHEMA_NAME
            FROM {db}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA'
            ORDER BY SCHEMA_NAME
        """).collect()]
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_tables(db: str, schema: str):
    try:
        return [{"name": r["TABLE_NAME"], "type": r["TABLE_TYPE"],
                 "rows": r["ROW_COUNT"] or 0,
                 "comment": r["COMMENT"] or ""}
                for r in session.sql(f"""
                    SELECT TABLE_NAME, TABLE_TYPE,
                           ROW_COUNT, COMMENT
                    FROM {db}.INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = '{schema}'
                      AND TABLE_TYPE IN ('BASE TABLE','VIEW')
                    ORDER BY TABLE_NAME
                """).collect()]
    except Exception:
        return []


def fqn(db, schema, table):
    return f"{db}.{schema}.{table}"


# ══════════════════════════════════════════════════════════════
# RE-RUN FROM STEP helper
# ══════════════════════════════════════════════════════════════

def reset_from_step(step: str):
    """
    Clear outputs FROM a given step onwards.
    Earlier steps are preserved exactly as they were.
    Agent call log is filtered — keeps calls from
    preserved steps so total cost stays accurate.
    """
    # Which steps' agent calls to KEEP when re-running
    step_keep_map = {
        "step1":  [],
        "step2a": ["Step 1: Mapping"],
        "step2b": ["Step 1: Mapping", "Step 2a: Silver"],
        "step3":  [
            "Step 1: Mapping",
            "Step 2a: Silver",
            "Step 2b: Gold"
        ]
    }
    # Filter call log — keep only calls from preserved steps
    keep_steps   = step_keep_map.get(step, [])
    existing_log = st.session_state.get("agent_call_log", [])
    filtered_log = [
        c for c in existing_log
        if c.get("step", "") in keep_steps
    ]
    st.session_state["agent_call_log"] = filtered_log

    clear_map = {
        "step1": [
            "mapping_report", "mapping_csv", "approved_csv",
            "silver_output", "gold_output", "dbt_output",
            "approved_dbt", "test_output", "approved_tests",
            "review1_comment_history",
            "review2_comment_history",
            "review3_comment_history"
        ],
        "step2a": [
            "silver_output", "gold_output", "dbt_output",
            "approved_dbt", "test_output", "approved_tests",
            "review2_comment_history",
            "review3_comment_history"
        ],
        "step2b": [
            "gold_output", "dbt_output",
            "approved_dbt", "test_output", "approved_tests",
            "review2_comment_history",
            "review3_comment_history"
        ],
        "step3": [
            "test_output", "approved_tests",
            "review3_comment_history"
        ]
    }
    for key in clear_map.get(step, []):
        st.session_state.pop(key, None)


# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Medallion Pipeline Rebuild",
    layout="wide"
)

ensure_persist_table()

if "active_run_id" not in st.session_state:
    st.session_state["active_run_id"] = (
        "RUN_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    # Record run start time for cost tracking
    st.session_state["run_start_time"] = datetime.now()

active_run_id = st.session_state["active_run_id"]

st.title("🔷 Medallion Pipeline Rebuild Orchestrator")
st.markdown(
    "**Pipeline:** FTL Bronze → New Silver → "
    "New Gold (PI Gold equivalent)"
)

# ── Session state shortcuts ────────────────────────────────────
tables_confirmed = "confirmed_tables" in st.session_state
step1_done       = "mapping_report"   in st.session_state
csv_approved     = "approved_csv"     in st.session_state
step2a_done      = "silver_output"    in st.session_state
step2b_done      = "gold_output"      in st.session_state
dbt_approved     = "approved_dbt"     in st.session_state
step3_done       = "test_output"      in st.session_state
tests_approved   = "approved_tests"   in st.session_state

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("📊 Pipeline Status")
    st.caption(f"Run: `{active_run_id}`")
    st.markdown(f"""
**Config** — Tables {'✅' if tables_confirmed else '⏳'}  
**Step 1** — Mapping {'✅' if step1_done else '⏳'}  
**Review 1** — {'✅ Approved' if csv_approved else ('⏳ Pending' if step1_done else '🔒')}  
**Step 2a** — Silver {'✅' if step2a_done else ('⏳' if csv_approved else '🔒')}  
**Step 2b** — Gold {'✅' if step2b_done else ('⏳' if step2a_done else '🔒')}  
**Review 2** — {'✅ Approved' if dbt_approved else ('⏳ Pending' if step2b_done else '🔒')}  
**Step 3** — Tests {'✅' if step3_done else ('⏳' if dbt_approved else '🔒')}  
**Review 3** — {'✅ Approved' if tests_approved else ('⏳ Pending' if step3_done else '🔒')}
    """)

    if step1_done:
        st.divider()
        st.markdown("**🔁 Re-run from Step**")
        st.caption(
            "Select which step to re-run. "
            "All steps before it are preserved."
        )

        rerun_options = {"— select —": None}
        rerun_options["Step 1 — Re-run Mapping Analysis"] = "step1"
        if csv_approved:
            rerun_options["Step 2a — Re-run Silver Model"] = "step2a"
        if step2a_done:
            rerun_options["Step 2b — Re-run Gold Model"] = "step2b"
        if dbt_approved:
            rerun_options["Step 3 — Re-run Test Cases"] = "step3"

        selected_rerun = st.selectbox(
            "Re-run from:",
            options=list(rerun_options.keys()),
            key="rerun_select"
        )

        step_descriptions = {
            "step1": "⚠️ Clears mapping, DBT, and tests. Table selection preserved.",
            "step2a": "ℹ️ Clears Silver, Gold, DBT approval, and tests. Approved mapping preserved.",
            "step2b": "ℹ️ Clears Gold, DBT approval, and tests. Silver and mapping preserved.",
            "step3": "ℹ️ Clears only the test suite. All other outputs preserved."
        }

        selected_key = rerun_options.get(selected_rerun)
        if selected_key:
            st.info(step_descriptions[selected_key])
            if st.button(
                "🔁 Confirm Re-run",
                type="primary",
                key="confirm_rerun"
            ):
                reset_from_step(selected_key)
                save_run(active_run_id)
                st.success(
                    f"✅ Reset from {selected_rerun}. "
                    f"Scroll down to re-run."
                )
                st.rerun()

    st.divider()

    st.header("📂 Run History")
    all_runs = get_all_runs()
    if all_runs:
        # ── Delete mode toggle ─────────────────────────────────
        delete_mode = st.toggle(
            "🗑️ Delete mode",
            value=st.session_state.get("delete_mode", False),
            key="delete_mode_toggle"
        )
        st.session_state["delete_mode"] = delete_mode

        if delete_mode:
            st.caption(
                "⚠️ Check boxes then click Delete Selected"
            )
            # Track which runs are checked for deletion
            to_delete = []
            for run in all_runs:
                rid     = run["RUN_ID"]
                status  = run["PIPELINE_STATUS"]
                updated = str(run["UPDATED_AT"])[:16]
                try:
                    ftl_l = json.loads(run["FTL_TABLES"] or "[]")
                    label = ftl_l[0].split(".")[-1] \
                        if ftl_l else "—"
                except Exception:
                    label = "—"
                icon = {
                    "COMPLETE":         "✅",
                    "TESTS_PENDING":    "🧪",
                    "DBT_PENDING":      "⚙️",
                    "MAPPING_COMPLETE": "📋"
                }.get(status, "⏳")

                checked = st.checkbox(
                    f"{icon} {label} — {updated}",
                    key=f"del_chk_{rid}",
                    help=rid
                )
                if checked:
                    to_delete.append(rid)

            if to_delete:
                st.caption(
                    f"{len(to_delete)} run(s) selected"
                )
                if st.button(
                    f"🗑️ Delete {len(to_delete)} Run(s)",
                    type="primary",
                    key="confirm_delete_btn"
                ):
                    # Confirm via session state flag
                    st.session_state[
                        "pending_delete"
                    ] = to_delete
                    st.rerun()

            # ── Confirm delete dialog ──────────────────────────
            pending = st.session_state.get(
                "pending_delete", []
            )
            if pending:
                st.warning(
                    f"⚠️ Permanently delete "
                    f"**{len(pending)} run(s)**? "
                    f"This cannot be undone."
                )
                cd1, cd2 = st.columns(2)
                with cd1:
                    if st.button(
                        "✅ Yes, Delete",
                        type="primary",
                        key="yes_delete"
                    ):
                        deleted = 0
                        for rid in pending:
                            try:
                                session.sql(f"""
                                    DELETE FROM {PERSIST_TABLE}
                                    WHERE RUN_ID = '{rid}'
                                """).collect()
                                deleted += 1
                                # If active run was deleted,
                                # clear session
                                if st.session_state.get(
                                    "active_run_id"
                                ) == rid:
                                    for k in [
                                        "confirmed_tables",
                                        "mapping_report",
                                        "mapping_csv",
                                        "approved_csv",
                                        "silver_output",
                                        "gold_output",
                                        "dbt_output",
                                        "approved_dbt",
                                        "test_output",
                                        "approved_tests",
                                        "active_run_id",
                                        "agent_call_log",
                                        "run_start_time"
                                    ]:
                                        st.session_state.pop(
                                            k, None
                                        )
                            except Exception as e:
                                st.error(
                                    f"Failed to delete "
                                    f"{rid}: {str(e)[:100]}"
                                )
                        st.session_state.pop(
                            "pending_delete", None
                        )
                        st.session_state[
                            "delete_mode"
                        ] = False
                        st.success(
                            f"✅ Deleted {deleted} run(s)"
                        )
                        st.rerun()
                with cd2:
                    if st.button(
                        "❌ Cancel",
                        key="cancel_delete"
                    ):
                        st.session_state.pop(
                            "pending_delete", None
                        )
                        st.rerun()

        else:
            # ── Normal mode — load runs ────────────────────────
            for run in all_runs:
                rid     = run["RUN_ID"]
                status  = run["PIPELINE_STATUS"]
                updated = str(run["UPDATED_AT"])[:16]
                try:
                    ftl_l = json.loads(run["FTL_TABLES"] or "[]")
                    label = ftl_l[0].split(".")[-1] \
                        if ftl_l else "—"
                except Exception:
                    label = "—"
                icon = {
                    "COMPLETE":         "✅",
                    "TESTS_PENDING":    "🧪",
                    "DBT_PENDING":      "⚙️",
                    "MAPPING_COMPLETE": "📋"
                }.get(status, "⏳")
                if st.button(
                    f"{icon} {label} — {updated}",
                    key=f"load_{rid}",
                    help=rid
                ):
                    for k in [
                        "confirmed_tables", "mapping_report",
                        "mapping_csv", "approved_csv",
                        "silver_output", "gold_output",
                        "dbt_output", "approved_dbt",
                        "test_output", "approved_tests",
                        "review1_comment_history",
                        "review2_comment_history",
                        "review3_comment_history"
                    ]:
                        st.session_state.pop(k, None)
                    if load_run(rid):
                        st.rerun()
    else:
        st.caption("No saved runs yet.")

    st.divider()
    if st.button("🆕 Start New Pipeline"):
        for k in [
            "confirmed_tables", "mapping_report",
            "mapping_csv", "approved_csv",
            "silver_output", "gold_output", "dbt_output",
            "approved_dbt", "test_output", "approved_tests",
            "active_run_id", "review1_comment_history",
            "review2_comment_history", "review3_comment_history",
            "agent_call_log", "run_start_time", "current_step"
        ]:
            st.session_state.pop(k, None)
        st.rerun()

    st.caption(f"Agent 1: `{AGENT_1}`")
    st.caption(f"Agent 2: `{AGENT_2}`")
    st.caption(f"Agent 3: `{AGENT_3}`")


# ══════════════════════════════════════════════════════════════
# STEP 0 — TABLE SELECTOR
# ══════════════════════════════════════════════════════════════
st.header("⚙️ Step 0: Select Tables")

if not tables_confirmed:
    databases = get_databases()

    st.subheader("📥 Source — FTL Bronze Tables")
    c1, c2 = st.columns(2)
    with c1:
        src_db = st.selectbox(
            "Database", ["— select —"] + databases, key="src_db"
        )
    with c2:
        src_schema = st.selectbox(
            "Schema",
            ["— select —"] + (
                get_schemas(src_db)
                if src_db != "— select —" else []
            ),
            key="src_schema"
        )

    if src_db != "— select —" and src_schema != "— select —":
        tlist = get_tables(src_db, src_schema)
        if tlist:
            st.markdown(
                f"**{len(tlist)} tables in "
                f"`{src_db}.{src_schema}` — check to include:**"
            )
            src_checked = []
            for t in tlist:
                lbl = f"`{t['name']}`"
                if t["rows"]:
                    lbl += f"  —  {t['rows']:,} rows"
                if t["comment"]:
                    lbl += f"  —  *{t['comment']}*"
                if st.checkbox(lbl, key=f"src_chk_{t['name']}"):
                    src_checked.append(
                        fqn(src_db, src_schema, t["name"])
                    )
            if src_checked:
                st.caption(f"{len(src_checked)} selected")
            if st.button(
                f"➕ Add {len(src_checked)} Source Table(s)",
                disabled=not src_checked, key="add_src"
            ):
                cur = st.session_state.get("ftl_source_tables", [])
                for t in src_checked:
                    if t not in cur:
                        cur.append(t)
                st.session_state["ftl_source_tables"] = cur
                st.rerun()

    ftl_added = st.session_state.get("ftl_source_tables", [])
    if ftl_added:
        st.markdown("**✅ Selected FTL Source Tables:**")
        to_rm = []
        for i, t in enumerate(ftl_added):
            ca, cb = st.columns([6, 1])
            with ca:
                st.markdown(f"• `{t}`")
            with cb:
                if st.button("✕", key=f"rm_src_{i}"):
                    to_rm.append(i)
        for idx in reversed(to_rm):
            ftl_added.pop(idx)
        if to_rm:
            st.session_state["ftl_source_tables"] = ftl_added
            st.rerun()

    st.divider()
    st.subheader("📤 Target — PI Silver & Gold Tables")
    c3, c4 = st.columns(2)
    with c3:
        tgt_db = st.selectbox(
            "Database", ["— select —"] + databases, key="tgt_db"
        )
    with c4:
        tgt_schema = st.selectbox(
            "Schema",
            ["— select —"] + (
                get_schemas(tgt_db)
                if tgt_db != "— select —" else []
            ),
            key="tgt_schema"
        )

    if tgt_db != "— select —" and tgt_schema != "— select —":
        tlist2 = get_tables(tgt_db, tgt_schema)
        if tlist2:
            st.markdown(
                f"**{len(tlist2)} tables in "
                f"`{tgt_db}.{tgt_schema}` — check to include:**"
            )
            tgt_checked = []
            for t in tlist2:
                lbl = f"`{t['name']}`"
                if t["rows"]:
                    lbl += f"  —  {t['rows']:,} rows"
                if t["comment"]:
                    lbl += f"  —  *{t['comment']}*"
                if st.checkbox(lbl, key=f"tgt_chk_{t['name']}"):
                    tgt_checked.append(
                        fqn(tgt_db, tgt_schema, t["name"])
                    )
            if tgt_checked:
                st.caption(f"{len(tgt_checked)} selected")
            if st.button(
                f"➕ Add {len(tgt_checked)} Target Table(s)",
                disabled=not tgt_checked, key="add_tgt"
            ):
                cur = st.session_state.get("pi_target_tables", [])
                for t in tgt_checked:
                    if t not in cur:
                        cur.append(t)
                st.session_state["pi_target_tables"] = cur
                st.rerun()

    pi_added = st.session_state.get("pi_target_tables", [])
    if pi_added:
        st.markdown("**✅ Selected PI Target Tables:**")
        to_rm2 = []
        for i, t in enumerate(pi_added):
            ca, cb = st.columns([6, 1])
            with ca:
                st.markdown(f"• `{t}`")
            with cb:
                if st.button("✕", key=f"rm_tgt_{i}"):
                    to_rm2.append(i)
        for idx in reversed(to_rm2):
            pi_added.pop(idx)
        if to_rm2:
            st.session_state["pi_target_tables"] = pi_added
            st.rerun()

    st.divider()
    ftl_ok = bool(st.session_state.get("ftl_source_tables"))
    pi_ok  = bool(st.session_state.get("pi_target_tables"))
    if not ftl_ok:
        st.warning("⚠️ Add at least one FTL Source table.")
    if not pi_ok:
        st.warning("⚠️ Add at least one PI Target table.")
    if ftl_ok and pi_ok:
        c5, c6 = st.columns(2)
        with c5:
            st.markdown("**FTL Source:**")
            for t in st.session_state["ftl_source_tables"]:
                st.markdown(f"• `{t}`")
        with c6:
            st.markdown("**PI Target:**")
            for t in st.session_state["pi_target_tables"]:
                st.markdown(f"• `{t}`")
        if st.button(
            "✅ Confirm Tables — Start Pipeline", type="primary"
        ):
            st.session_state["confirmed_tables"] = {
                "ftl": st.session_state["ftl_source_tables"],
                "pi":  st.session_state["pi_target_tables"]
            }
            save_run(active_run_id)
            st.rerun()

else:
    confirmed = st.session_state["confirmed_tables"]
    ftl_str   = "\n".join(f"  - {t}" for t in confirmed["ftl"])
    pi_str    = "\n".join(f"  - {t}" for t in confirmed["pi"])

    st.success("✅ Tables confirmed")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**FTL Source:**")
        for t in confirmed["ftl"]:
            st.markdown(f"• `{t}`")
    with c2:
        st.markdown("**PI Target:**")
        for t in confirmed["pi"]:
            st.markdown(f"• `{t}`")

    st.divider()

    # ══════════════════════════════════════════════════════════
    # STEP 1
    # ══════════════════════════════════════════════════════════
    st.header("Step 1: Mapping & Gap Analysis")

    if not step1_done:
        if st.button(
            "▶️ Run Mapping Analysis", type="primary"
        ):
            with st.spinner("🤖 Agent 1 running..."):
                st.session_state["current_step"] = "Step 1: Mapping"
                result = call_agent(AGENT_1, f"""
                    Comprehensive mapping analysis.
                    SOURCE: {ftl_str}
                    TARGET: {pi_str}
                    Show reasoning: 🔍 STEP X: [what] — [why]
                    Assign GAP IDs, BR IDs. No timeline.
                    Full report all sections.
                """)
                st.session_state["mapping_report"] = result
                csv_t = extract_csv(result)
                if csv_t:
                    st.session_state["mapping_csv"] = csv_t
                save_run(active_run_id)

                push_output_to_github(
                    active_run_id, "mapping_report.md",
                    result,
                    f"run({active_run_id}): mapping report"
                )
                if csv_t:
                    push_output_to_github(
                        active_run_id, "mapping_csv.csv",
                        csv_t,
                        f"run({active_run_id}): mapping CSV"
                    )
                st.rerun()
    else:
        st.success("✅ Mapping Analysis Complete")
        with st.expander("📋 View Mapping Report", expanded=True):
            st.markdown(st.session_state["mapping_report"])
        st.download_button(
            "⬇️ Download Mapping Report",
            st.session_state["mapping_report"].encode(),
            "ftl_mapping_report.md", "text/markdown"
        )

        # ── Comment section — Agent 1 ──────────────────────────
        show_comment_and_rerun(
            stage_key  = "agent1",
            agent_name = AGENT_1,
            output_key = "mapping_report",
            prompt_builder = lambda comment, current: f"""
                You previously produced a mapping analysis report.
                The reviewer has the following comments.
                Please revise accordingly.

                REVIEWER COMMENTS:
                {comment}

                YOUR PREVIOUS REPORT:
                {trim(current, 6000)}

                SOURCE FTL TABLES:
                {ftl_str}

                TARGET PI TABLES:
                {pi_str}

                Instructions:
                - Apply ONLY the changes in the comments
                - Keep everything else exactly as it was
                - Maintain all GAP IDs and BR IDs unless
                  the comment changes them
                - Reproduce the full revised report with
                  updated mapping CSV at the end
            """,
            rerun_label = (
                "🔁 Submit Comment — "
                "Agent 1 will revise mapping"
            )
        )

        if not st.session_state.get("mapping_csv"):
            csv_t = extract_csv(st.session_state["mapping_report"])
            if csv_t:
                st.session_state["mapping_csv"] = csv_t
                save_run(active_run_id)

        st.divider()

        # ══════════════════════════════════════════════════════
        # REVIEW 1
        # ══════════════════════════════════════════════════════
        st.header("🔍 Review 1: Mapping CSV")
        st.markdown("""
        1. Download CSV — review in Excel
        2. Approve as-is OR upload modified version
        3. Agent 2 uses the approved CSV as source of truth
        """)

        if st.session_state.get("mapping_csv"):
            st.success("✅ Mapping CSV ready")
            st.download_button(
                "⬇️ Download Mapping CSV",
                st.session_state["mapping_csv"].encode(),
                "ftl_mapping_review.csv", "text/csv",
                type="primary"
            )
            rows = parse_csv(st.session_state["mapping_csv"])
            if rows:
                with st.expander(
                    f"👁️ Preview ({len(rows)} rows)",
                    expanded=True
                ):
                    st.dataframe(rows, use_container_width=True)
        else:
            manual = st.text_area(
                "Paste mapping CSV here",
                height=150, key="manual_csv"
            )
            if manual and st.button("✅ Use This CSV"):
                st.session_state["mapping_csv"] = manual
                save_run(active_run_id)
                st.rerun()

        st.markdown("---")
        ca, cr = st.columns(2)
        with ca:
            st.markdown("**✅ Option 1 — Approve as-is**")
            if st.button(
                "✅ Approve Mapping", type="primary",
                disabled=csv_approved, key="approve_csv"
            ):
                st.session_state["approved_csv"] = \
                    st.session_state.get("mapping_csv", "")
                save_run(active_run_id)
                st.rerun()
        with cr:
            st.markdown("**🔄 Option 2 — Upload modified CSV**")
            up = st.file_uploader(
                "Upload modified CSV", type=["csv"],
                key="csv_upload"
            )
            if up:
                mod = up.read().decode("utf-8")
                rp  = parse_csv(mod)
                if rp:
                    st.dataframe(rp, use_container_width=True)
                if st.button(
                    "🔄 Submit", disabled=csv_approved,
                    key="submit_csv"
                ):
                    st.session_state["approved_csv"] = mod
                    st.session_state["mapping_csv"]  = mod
                    save_run(active_run_id)
                    st.rerun()

    if csv_approved:
        st.success("✅ Mapping approved — Agent 2 unlocked")
        ra = parse_csv(st.session_state["approved_csv"])
        if ra:
            st.dataframe(ra, use_container_width=True)
        st.divider()

        # ══════════════════════════════════════════════════════
        # STEP 2a — SILVER
        # ══════════════════════════════════════════════════════
        st.header("Step 2a: Generate Silver DBT Model")

        if not step2a_done:
            if st.button(
                "▶️ Generate Silver DBT Model", type="primary"
            ):
                with st.spinner("⚙️ Agent 2 — Silver model..."):
                    st.session_state["current_step"] = "Step 2a: Silver"
                    result = call_agent(AGENT_2, f"""
                        Generate dbt Silver model.
                        TARGET_LAYER = SILVER
                        Show reasoning: ⚙️ STEP X: [what] — [why]

                        ═══════════════════════════════════════
                        REPO NAMING CONVENTION — MANDATORY
                        NEVER use generic dbt-Labs house style
                        ═══════════════════════════════════════
                        File path : models/silver/slv_ftl_agent_base_agg.sql
                        Model name: slv_ftl_agent_base_agg
                        Config    : schema="SILVER", materialized="incremental"
                        Source ref: {{{{ source("zoom_ai_poc", "BRZ_FTL_AGENT_BASE_AGG") }}}}
                        YAML file : models/silver/slv_ftl_agent_base_agg.yml

                        NEVER USE:
                        ❌ stg_ prefix
                        ❌ models/staging/ path
                        ❌ fct_ prefix
                        ❌ models/marts/ path
                        ❌ zoom_ai_poc_bronze as source name

                        SOURCE: {ftl_str}
                        Use APPROVED MAPPING CSV exactly.
                        Apply every BR ID and GAP ID.

                        APPROVED MAPPING CSV:
                        {trim(st.session_state['approved_csv'], 6000)}

                        Generate these 4 files:
                        FILE 1: models/bronze/sources.yml
                                (source name: zoom_ai_poc, schema: BRONZE)
                        FILE 2: setup/CLUSTER_REGION_MAP.sql
                                (MERGE INTO syntax, never ON CONFLICT)
                        FILE 3: models/silver/slv_ftl_agent_base_agg.sql
                                (inline comment per column:
                                 -- SOURCE: col | CLASS: type | BR: br_id)
                        FILE 4: models/silver/slv_ftl_agent_base_agg.yml
                                (complete — never truncate)
                    """)
                    st.session_state["silver_output"] = result
                    save_run(active_run_id)

                    push_output_to_github(
                        active_run_id, "silver_model.md",
                        result,
                        f"run({active_run_id}): silver model"
                    )
                    st.rerun()
        else:
            st.success("✅ Silver Model Generated")
            with st.expander("View Silver Model", expanded=False):
                st.markdown(st.session_state["silver_output"])
            st.download_button(
                "⬇️ Download Silver Model",
                st.session_state["silver_output"].encode(),
                "ftl_silver_dbt_model.md", "text/markdown"
            )

            # ── Comment section — Agent 2 Silver ──────────────
            show_comment_and_rerun(
                stage_key  = "agent2_silver",
                agent_name = AGENT_2,
                output_key = "silver_output",
                prompt_builder = lambda comment, current: f"""
                    You previously generated a dbt Silver model.
                    The reviewer has the following comments.
                    Please revise accordingly.

                    REVIEWER COMMENTS:
                    {comment}

                    YOUR PREVIOUS SILVER MODEL:
                    {trim(current, 6000)}

                    APPROVED MAPPING CSV:
                    {trim(st.session_state.get('approved_csv',''), 3000)}

                    Instructions:
                    - Apply ONLY the changes in the comments
                    - Keep all BR IDs and GAP ID comments
                    - Maintain repo naming: slv_ prefix,
                      models/silver/ path, schema="SILVER"
                    - Reproduce all 4 files completely
                """,
                rerun_label = "🔁 Submit Comment — Agent 2 will revise Silver model"
            )

            st.divider()

            # ══════════════════════════════════════════════════
            # STEP 2b — GOLD
            # ══════════════════════════════════════════════════
            st.header("Step 2b: Generate Gold DBT Model")

            if not step2b_done:
                if st.button(
                    "▶️ Generate Gold DBT Model", type="primary"
                ):
                    with st.spinner("⚙️ Agent 2 — Gold model..."):
                        st.session_state["current_step"] = "Step 2b: Gold"
                        result = call_agent(AGENT_2, f"""
                            Generate dbt Gold model.
                            TARGET_LAYER = GOLD
                            Show reasoning: ⚙️ STEP X: [what] — [why]

                            ═══════════════════════════════════════
                            REPO NAMING CONVENTION — MANDATORY
                            NEVER use generic dbt-Labs house style
                            ═══════════════════════════════════════
                            File path : models/gold/gld_aggregate_new.sql
                            Model name: gld_aggregate_new
                                        (or gld_aggregate_p for parallel suffix)
                            Config    : schema="GOLD", materialized="table"
                            Silver ref: {{{{ ref("slv_ftl_agent_base_agg") }}}}
                            YAML file : models/gold/gld_aggregate_new.yml

                            NEVER USE:
                            ❌ fct_ prefix
                            ❌ fct_gld_aggregate_new as model name
                            ❌ models/marts/ path
                            ❌ stg_ prefix anywhere

                            SOURCE SILVER: {{{{ ref("slv_ftl_agent_base_agg") }}}}
                            TARGET: {pi_str}

                            Column order MUST match target Gold tables exactly.
                            For GAP columns: NULL AS col -- GAP: gap_id
                            Inline comment per column: BR ID and GAP ID.

                            APPROVED MAPPING:
                            {trim(st.session_state['approved_csv'], 3000)}

                            SILVER CONTEXT:
                            {trim(st.session_state['silver_output'], 3000)}

                            Generate these 2 files:
                            FILE 1: models/gold/gld_aggregate_new.sql
                            FILE 2: models/gold/gld_aggregate_new.yml
                                    (include functional equivalence test
                                     comparing gld_aggregate_new vs
                                     GLD_AGGREGATE)
                        """)
                        st.session_state["gold_output"] = result
                        st.session_state["dbt_output"]  = (
                            st.session_state["silver_output"]
                            + "\n\n---\n\n" + result
                        )
                        save_run(active_run_id)

                        push_output_to_github(
                            active_run_id, "gold_model.md",
                            result,
                            f"run({active_run_id}): gold model"
                        )
                        st.rerun()
            else:
                st.success("✅ Gold Model Generated")
                with st.expander("View Gold Model", expanded=False):
                    st.markdown(st.session_state["gold_output"])
                st.download_button(
                    "⬇️ Download Gold Model",
                    st.session_state["gold_output"].encode(),
                    "ftl_gold_dbt_model.md", "text/markdown"
                )

                # ── Comment section — Agent 2 Gold ────────────
                show_comment_and_rerun(
                    stage_key  = "agent2_gold",
                    agent_name = AGENT_2,
                    output_key = "gold_output",
                    prompt_builder = lambda comment, current: f"""
                        You previously generated a dbt Gold model.
                        The reviewer has the following comments.
                        Please revise accordingly.

                        REVIEWER COMMENTS:
                        {comment}

                        YOUR PREVIOUS GOLD MODEL:
                        {trim(current, 5000)}

                        APPROVED MAPPING CSV:
                        {trim(st.session_state.get('approved_csv',''), 2000)}

                        SILVER MODEL CONTEXT:
                        {trim(st.session_state.get('silver_output',''), 2000)}

                        Instructions:
                        - Apply ONLY the changes in the comments
                        - Keep all BR IDs and GAP ID comments
                        - Maintain repo naming: gld_ prefix,
                          models/gold/ path, schema="GOLD"
                        - Reproduce both files completely
                    """,
                    rerun_label = "🔁 Submit Comment — Agent 2 will revise Gold model"
                )

                st.divider()

                # ══════════════════════════════════════════════
                # REVIEW 2
                # ══════════════════════════════════════════════
                st.header("🔍 Review 2: DBT Code")
                st.markdown("""
                1. Download DBT code — review Silver and Gold
                2. Approve or upload modified version
                """)
                st.download_button(
                    "⬇️ Download DBT Code",
                    st.session_state["dbt_output"].encode(),
                    "ftl_dbt_review.md", "text/markdown"
                )
                st.markdown("---")
                ca2, cr2 = st.columns(2)
                with ca2:
                    st.markdown("**✅ Option 1 — Approve**")
                    if st.button(
                        "✅ Approve DBT", type="primary",
                        disabled=dbt_approved, key="approve_dbt"
                    ):
                        st.session_state["approved_dbt"] = \
                            st.session_state["dbt_output"]
                        save_run(active_run_id)
                        st.rerun()
                with cr2:
                    st.markdown("**🔄 Option 2 — Upload modified**")
                    up2 = st.file_uploader(
                        "Upload modified DBT",
                        type=["md", "sql", "txt"],
                        key="dbt_upload"
                    )
                    if up2:
                        mod2 = up2.read().decode("utf-8")
                        if st.button(
                            "🔄 Submit", disabled=dbt_approved,
                            key="submit_dbt"
                        ):
                            st.session_state["approved_dbt"] = mod2
                            st.session_state["dbt_output"]   = mod2
                            save_run(active_run_id)
                            st.rerun()

    if dbt_approved:
        st.success("✅ DBT approved — Agent 3 unlocked")
        st.divider()

        # ══════════════════════════════════════════════════════
        # STEP 3 — TESTS
        # ══════════════════════════════════════════════════════
        st.header("Step 3: Test Case Generation")

        if not step3_done:
            if st.button(
                "▶️ Generate Test Cases", type="primary"
            ):
                with st.spinner("🧪 Agent 3 generating tests..."):
                    st.session_state["current_step"] = "Step 3: Tests"
                    result = call_agent(AGENT_3, f"""
                        Generate complete test suite.
                        TARGET_LAYER = ALL
                        Show reasoning: 🧪 STEP X: [what] — [why]
                        SOURCE: {ftl_str}
                        TARGET: {pi_str}
                        Name unit tests: test_unit_<BR_ID>_<column>
                        Name gap tests: test_gap_<GAP_ID>_<col>_is_null

                        REPO MODEL NAMES — use these exactly:
                        Silver model: slv_ftl_agent_base_agg
                        Gold model  : gld_aggregate_new
                        Source name : zoom_ai_poc

                        APPROVED MAPPING:
                        {trim(st.session_state['approved_csv'], 3000)}
                        APPROVED DBT:
                        {trim(st.session_state['approved_dbt'], 3000)}

                        Generate all 6 files:
                        1. tests/unit/unit_tests.sql
                        2. tests/functional/functional_tests.sql
                        3. tests/functional/gold_equivalence_test.sql
                           (compare gld_aggregate_new vs GLD_AGGREGATE)
                        4. models/silver/slv_ftl_agent_base_agg.yml
                           (schema tests — not models/staging/)
                        5. tests/regression/regression_suite.sql
                        6. TEST_RUNBOOK.md
                    """)
                    st.session_state["test_output"] = result
                    save_run(active_run_id)

                    push_output_to_github(
                        active_run_id, "test_suite.md",
                        result,
                        f"run({active_run_id}): test suite"
                    )
                    st.rerun()
        else:
            st.success("✅ Test Suite Generated")
            with st.expander("🧪 View Tests", expanded=False):
                st.markdown(st.session_state["test_output"])
            st.download_button(
                "⬇️ Download Test Suite",
                st.session_state["test_output"].encode(),
                "ftl_test_suite.md", "text/markdown"
            )

            # ── Comment section — Agent 3 ──────────────────────
            show_comment_and_rerun(
                stage_key  = "agent3",
                agent_name = AGENT_3,
                output_key = "test_output",
                prompt_builder = lambda comment, current: f"""
                    You previously generated a test suite.
                    The reviewer has the following comments.
                    Please revise accordingly.

                    REVIEWER COMMENTS:
                    {comment}

                    YOUR PREVIOUS TEST SUITE:
                    {trim(current, 5000)}

                    APPROVED MAPPING CSV:
                    {trim(st.session_state.get('approved_csv',''), 2000)}

                    APPROVED DBT CODE:
                    {trim(st.session_state.get('approved_dbt',''), 2000)}

                    Instructions:
                    - Apply ONLY the changes in the comments
                    - Keep all BR IDs and GAP IDs consistent
                    - Maintain test naming:
                      test_unit_<BR_ID>_<column>
                      test_gap_<GAP_ID>_<col>_is_null
                    - Reproduce all 6 files completely
                """,
                rerun_label = "🔁 Submit Comment — Agent 3 will revise tests"
            )

            st.divider()

            # ══════════════════════════════════════════════════
            # REVIEW 3
            # ══════════════════════════════════════════════════
            st.header("🔍 Review 3: Test Suite")
            st.markdown("""
            1. Download test suite — review all files
            2. Approve or upload modified version
            """)
            st.download_button(
                "⬇️ Download Tests",
                st.session_state["test_output"].encode(),
                "ftl_tests_review.md", "text/markdown"
            )
            st.markdown("---")
            ca3, cr3 = st.columns(2)
            with ca3:
                st.markdown("**✅ Option 1 — Approve**")
                if st.button(
                    "✅ Approve Tests — Complete",
                    type="primary",
                    disabled=tests_approved,
                    key="approve_tests"
                ):
                    st.session_state["approved_tests"] = \
                        st.session_state["test_output"]
                    save_run(active_run_id)

                    push_run_summary(active_run_id)
                    st.rerun()
            with cr3:
                st.markdown("**🔄 Option 2 — Upload modified**")
                up3 = st.file_uploader(
                    "Upload modified tests",
                    type=["md", "sql", "txt"],
                    key="tests_upload"
                )
                if up3:
                    mod3 = up3.read().decode("utf-8")
                    if st.button(
                        "🔄 Submit", disabled=tests_approved,
                        key="submit_tests"
                    ):
                        st.session_state["approved_tests"] = mod3
                        st.session_state["test_output"]    = mod3
                        save_run(active_run_id)
                        st.rerun()

    # ══════════════════════════════════════════════════════════
    # PIPELINE COMPLETE + COST SUMMARY
    # ══════════════════════════════════════════════════════════
    if tests_approved:
        st.divider()
        st.success("🎉 Pipeline Complete — All Stages Approved")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Mapping", "✅")
        with c2: st.metric("Silver",  "✅")
        with c3: st.metric("Gold",    "✅")
        with c4: st.metric("Tests",   "✅")
        st.info(
            f"Saved as `{active_run_id}`. "
            f"Reload anytime from Run History in sidebar. "
            f"Outputs pushed to GitHub under "
            f"`runs/{active_run_id}/`."
        )
        st.markdown("""
**Next Steps:**
1. Run `setup/CLUSTER_REGION_MAP.sql` in Snowflake first
2. `models/bronze/sources.yml` ← register source
3. `models/silver/slv_ftl_agent_base_agg.sql` ← Silver model
4. `models/silver/slv_ftl_agent_base_agg.yml` ← Silver tests
5. `models/gold/gld_aggregate_new.sql` ← Gold model
6. `models/gold/gld_aggregate_new.yml` ← Gold tests
7. `dbt run --select slv_ftl_agent_base_agg`
8. `dbt test --select slv_ftl_agent_base_agg`
9. `dbt run --select gld_aggregate_new`
10. Run `gold_equivalence_test.sql` — verify vs GLD_AGGREGATE
11. Share GAP report with BDP
12. `regression_suite.sql` after every model change
        """)

        # ── Cost Summary ───────────────────────────────────────
        show_cost_summary()