# ============================================================
# FILE: view_saved_runs.py
# PURPOSE: Standalone "View Saved Runs" page
#          Shows all saved pipeline runs with their
#          mapping CSV, DBT code, test suite, and comments
# DEPLOY: Add as a second page in Streamlit in Snowflake
#         Save as: pages/view_saved_runs.py
# ============================================================

import streamlit as st
import json
import csv
import io

DATABASE      = "ZOOM_AI_POC"
SCHEMA        = "CORTEX_AGENT"
PERSIST_TABLE = f"{DATABASE}.{SCHEMA}.PIPELINE_RUN_HISTORY"

session = st.connection("snowflake").session()


def parse_csv_content(csv_text: str) -> list:
    try:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        return list(reader)
    except Exception:
        return []


def get_all_runs() -> list:
    try:
        rows = session.sql(f"""
            SELECT RUN_ID, CREATED_AT, UPDATED_AT,
                   FTL_TABLES, PI_TABLES, PIPELINE_STATUS
            FROM {PERSIST_TABLE}
            ORDER BY UPDATED_AT DESC
            LIMIT 50
        """).collect()
        return rows
    except Exception:
        return []


def load_run_data(run_id: str):
    rows = session.sql(f"""
        SELECT * FROM {PERSIST_TABLE}
        WHERE RUN_ID = '{run_id}'
    """).collect()
    return rows[0] if rows else None


def get_col(row, col: str):
    val = row[col]
    return val if val and str(val) != "None" else None


# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Saved Pipeline Runs",
    layout="wide"
)

st.title("📂 Saved Pipeline Runs")
st.markdown(
    "View all saved pipeline runs — mapping CSV, "
    "DBT models, test suite, and review comments."
)

# ── Navigation banner ──────────────────────────────────────────
st.info(
    "📌 This page shows **saved runs only**. "
    "To run a fresh mapping analysis, go to the "
    "**🚀 streamlit_app** page from the left sidebar."
)

# ── Get all runs ───────────────────────────────────────────────
all_runs = get_all_runs()

if not all_runs:
    st.info(
        "No saved runs yet. "
        "Run the pipeline first from the main page."
    )
    st.stop()

# ── Run selector ───────────────────────────────────────────────
run_options = {}
for run in all_runs:
    run_id  = run["RUN_ID"]
    status  = run["PIPELINE_STATUS"]
    updated = str(run["UPDATED_AT"])[:16]
    try:
        ftl_list  = json.loads(run["FTL_TABLES"] or "[]")
        ftl_label = ", ".join(
            t.split(".")[-1] for t in ftl_list
        ) if ftl_list else "—"
    except Exception:
        ftl_label = "—"

    status_icon = {
        "COMPLETE":         "✅",
        "TESTS_PENDING":    "🧪",
        "DBT_PENDING":      "⚙️",
        "MAPPING_COMPLETE": "📋",
        "IN_PROGRESS":      "⏳"
    }.get(status, "⏳")

    label = (
        f"{status_icon} {ftl_label} — "
        f"{updated} — {run_id}"
    )
    run_options[label] = run_id

selected_label  = st.selectbox(
    "Select a run to view",
    options=list(run_options.keys())
)
selected_run_id = run_options[selected_label]

# ── Load selected run ──────────────────────────────────────────
run_data = load_run_data(selected_run_id)
if not run_data:
    st.error("Could not load this run.")
    st.stop()

# ── Run summary ────────────────────────────────────────────────
st.divider()
col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.metric("Run ID", selected_run_id)
with col_i2:
    st.metric("Status", run_data["PIPELINE_STATUS"])
with col_i3:
    st.metric("Last Updated", str(run_data["UPDATED_AT"])[:16])

try:
    ftl = json.loads(get_col(run_data, "FTL_TABLES") or "[]")
    pi  = json.loads(get_col(run_data, "PI_TABLES")  or "[]")
    ct1, ct2 = st.columns(2)
    with ct1:
        st.markdown("**FTL Source Tables:**")
        for t in ftl:
            st.markdown(f"• `{t}`")
    with ct2:
        st.markdown("**PI Target Tables:**")
        for t in pi:
            st.markdown(f"• `{t}`")
except Exception:
    pass

# ── Tabs for each output ───────────────────────────────────────
st.divider()
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Mapping CSV",
    "📋 Full Report",
    "⚙️ DBT Models",
    "🧪 Test Suite",
    "💬 Comments Log"
])

# ── TAB 1: Mapping CSV ─────────────────────────────────────────
with tab1:
    st.subheader("📊 Mapping CSV")

    approved_csv = get_col(run_data, "APPROVED_CSV")
    mapping_csv  = get_col(run_data, "MAPPING_CSV")
    csv_to_show  = approved_csv or mapping_csv

    if csv_to_show:
        if approved_csv:
            st.success("✅ Showing approved version")
        else:
            st.warning("⚠️ Showing original — not yet approved")

        rows = parse_csv_content(csv_to_show)
        if rows:
            # Summary metrics
            total    = len(rows)
            gaps     = sum(
                1 for r in rows
                if r.get("Classification", "") == "GAP"
            )
            high_conf = sum(
                1 for r in rows
                if r.get("Confidence", "") == "High"
            )

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Total Columns", total)
            with m2:
                st.metric("Gaps", gaps)
            with m3:
                st.metric("High Confidence", high_conf)

            st.divider()

            # Filter by classification
            all_classes = list({
                r.get("Classification", "") for r in rows
            })
            selected_class = st.multiselect(
                "Filter by Classification",
                options=sorted(all_classes),
                default=sorted(all_classes),
                key="class_filter"
            )
            filtered = [
                r for r in rows
                if r.get("Classification", "")
                in selected_class
            ]
            st.dataframe(filtered, use_container_width=True)

        # Download
        st.download_button(
            label="⬇️ Download Mapping CSV",
            data=csv_to_show.encode("utf-8"),
            file_name=f"mapping_{selected_run_id}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No mapping CSV saved for this run.")

# ── TAB 2: Full Mapping Report ─────────────────────────────────
with tab2:
    st.subheader("📋 Full Mapping Report")
    mapping_report = get_col(run_data, "MAPPING_REPORT")
    if mapping_report:
        st.markdown(mapping_report)
        st.download_button(
            label="⬇️ Download Mapping Report (.md)",
            data=mapping_report.encode("utf-8"),
            file_name=f"mapping_report_{selected_run_id}.md",
            mime="text/markdown"
        )
    else:
        st.info("No mapping report saved for this run.")

# ── TAB 3: DBT Models ─────────────────────────────────────────
with tab3:
    st.subheader("⚙️ DBT Models")
    approved_dbt = get_col(run_data, "APPROVED_DBT")
    dbt_output   = get_col(run_data, "DBT_OUTPUT")
    dbt_to_show  = approved_dbt or dbt_output

    if dbt_to_show:
        if approved_dbt:
            st.success("✅ Showing approved version")
        else:
            st.warning("⚠️ Showing original — not yet approved")
        st.markdown(dbt_to_show)
        st.download_button(
            label="⬇️ Download DBT Models (.md)",
            data=dbt_to_show.encode("utf-8"),
            file_name=f"dbt_{selected_run_id}.md",
            mime="text/markdown"
        )
    else:
        st.info("No DBT models saved for this run.")

# ── TAB 4: Test Suite ─────────────────────────────────────────
with tab4:
    st.subheader("🧪 Test Suite")
    approved_tests = get_col(run_data, "APPROVED_TESTS")
    test_output    = get_col(run_data, "TEST_OUTPUT")
    tests_to_show  = approved_tests or test_output

    if tests_to_show:
        if approved_tests:
            st.success("✅ Showing approved version")
        else:
            st.warning("⚠️ Showing original — not yet approved")
        st.markdown(tests_to_show)
        st.download_button(
            label="⬇️ Download Test Suite (.md)",
            data=tests_to_show.encode("utf-8"),
            file_name=f"tests_{selected_run_id}.md",
            mime="text/markdown"
        )
    else:
        st.info("No test suite saved for this run.")

# ── TAB 5: Comments Log ────────────────────────────────────────
with tab5:
    st.subheader("💬 Review Comments Log")
    comments_raw = get_col(run_data, "COMMENTS_LOG")
    if comments_raw:
        try:
            comments = json.loads(comments_raw)
            has_any  = any(
                comments.get(s)
                for s in ["review1", "review2", "review3"]
            )
            if has_any:
                for stage, label in [
                    ("review1", "Review 1 — Mapping CSV"),
                    ("review2", "Review 2 — DBT Code"),
                    ("review3", "Review 3 — Test Suite")
                ]:
                    hist = comments.get(stage, [])
                    if hist:
                        st.markdown(f"**{label}:**")
                        for i, c in enumerate(hist):
                            st.info(f"Round {i+1}: {c}")
                        st.divider()
            else:
                st.info("No comments were left for this run.")
        except Exception:
            st.info("Could not parse comments log.")
    else:
        st.info("No comments were left for this run.")