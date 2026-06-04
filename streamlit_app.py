# ============================================================
# FILE: streamlit_app.py
# PURPOSE: 3-Agent Pipeline with Human-in-the-Loop
#          + Selective re-run from any step
#          + Snowflake persistence
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
            {e(json.dumps(comments))}          AS COMMENTS_LOG
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
            t.COMMENTS_LOG    = s.COMMENTS_LOG
        WHEN NOT MATCHED THEN INSERT (
            RUN_ID, FTL_TABLES, PI_TABLES,
            MAPPING_REPORT, MAPPING_CSV, APPROVED_CSV,
            SILVER_OUTPUT, GOLD_OUTPUT, DBT_OUTPUT,
            APPROVED_DBT, TEST_OUTPUT, APPROVED_TESTS,
            PIPELINE_STATUS, COMMENTS_LOG
        ) VALUES (
            s.RUN_ID, s.FTL_TABLES, s.PI_TABLES,
            s.MAPPING_REPORT, s.MAPPING_CSV, s.APPROVED_CSV,
            s.SILVER_OUTPUT, s.GOLD_OUTPUT, s.DBT_OUTPUT,
            s.APPROVED_DBT, s.TEST_OUTPUT, s.APPROVED_TESTS,
            s.PIPELINE_STATUS, s.COMMENTS_LOG
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
# HELPERS
# ══════════════════════════════════════════════════════════════

def call_agent(agent_name: str, message: str) -> str:
    fqn = f"{DATABASE}.{SCHEMA}.{agent_name}"
    body = json.dumps({
        "messages": [{"role": "user",
                      "content": [{"type": "text",
                                   "text": message}]}],
        "stream": False
    })
    sql = (f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN("
           f"'{fqn}', $${body}$$) AS RESPONSE")
    result   = session.sql(sql).collect()
    response = json.loads(result[0]["RESPONSE"])
    return "".join(
        i.get("text", "") for i in response.get("content", [])
        if i.get("type") == "text"
    )


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
    Clear all outputs FROM a given step onwards.
    Earlier steps are preserved exactly as they were.

    step options:
      'step1'  — clears everything (full re-run)
      'step2a' — keeps mapping, re-runs Silver onwards
      'step2b' — keeps mapping + Silver, re-runs Gold onwards
      'step3'  — keeps mapping + DBT, re-runs Tests only
    """
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

    # ── Re-run from step ───────────────────────────────────────
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
            "step1": "⚠️ This will clear the mapping report, all DBT code, and all tests. The approved CSV, table selection, and run history are preserved.",
            "step2a": "ℹ️ This will clear the Silver model, Gold model, DBT approval, and tests. The approved mapping CSV is preserved and will be used again.",
            "step2b": "ℹ️ This will clear only the Gold model, DBT approval, and tests. The Silver model and approved mapping are preserved.",
            "step3": "ℹ️ This will clear only the test suite. The mapping, Silver model, and Gold model are all preserved."
        }

        selected_key = rerun_options.get(selected_rerun)
        if selected_key:
            st.info(step_descriptions[selected_key])
            if st.button(
                f"🔁 Confirm Re-run",
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

    # ── Run history ────────────────────────────────────────────
    st.header("📂 Run History")
    all_runs = get_all_runs()
    if all_runs:
        for run in all_runs:
            rid     = run["RUN_ID"]
            status  = run["PIPELINE_STATUS"]
            updated = str(run["UPDATED_AT"])[:16]
            try:
                ftl_l = json.loads(run["FTL_TABLES"] or "[]")
                label = ftl_l[0].split(".")[-1] if ftl_l else "—"
            except Exception:
                label = "—"
            icon = {"COMPLETE": "✅", "TESTS_PENDING": "🧪",
                    "DBT_PENDING": "⚙️",
                    "MAPPING_COMPLETE": "📋"}.get(status, "⏳")
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
            "review2_comment_history", "review3_comment_history"
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
    confirmed      = st.session_state["confirmed_tables"]
    ftl_str = "\n".join(f"  - {t}" for t in confirmed["ftl"])
    pi_str  = "\n".join(f"  - {t}" for t in confirmed["pi"])

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

        # ── auto-extract CSV ───────────────────────────────────
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
            f"Reload anytime from Run History in sidebar."
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