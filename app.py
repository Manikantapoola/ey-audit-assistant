import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agents.agent1_ingestion import Agent1Ingestion
from agents.agent2_anomaly import Agent2Anomaly
from agents.agent3_summary import Agent3Summary
from agents.agent4_report import Agent4Report

load_dotenv()

# ── HTML compaction helper ─────────────────────────────────────────────────────
# Strips leading whitespace per line and removes blank lines so that Markdown
# never interprets indented content as a <code> block (CommonMark 4-space rule).
def _h(html: str) -> str:
    return "".join(
        line.strip() for line in html.splitlines() if line.strip()
    )

# ── Color palette ──────────────────────────────────────────────────────────────
RISK_COLORS = {
    "Critical": "#FF4C4C",
    "High":     "#FF9F43",
    "Medium":   "#FFE600",
    "Low":      "#2ECC71",
}
SEV_COLORS = {
    "Critical": "#FF4C4C",
    "High":     "#FF9F43",
    "Medium":   "#FFE600",
    "Low":      "#2ECC71",
}

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EY Audit Intelligence",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injection ───────────────────────────────────────────────────────
st.markdown("""<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0A0F1E !important;
    color: #E8EEFF !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}
[data-testid="stMain"], .main, .block-container {
    background-color: #0A0F1E !important;
}
[data-testid="stSidebar"] {
    background-color: #0F1729 !important;
    border-right: 1px solid #1E3055 !important;
}
[data-testid="stSidebar"] * { color: #8BA4D4 !important; }
[data-testid="stHeader"] {
    background-color: #0A0F1E !important;
    border-bottom: 1px solid #1E3055 !important;
}
[data-testid="stToolbar"] { background-color: #0A0F1E !important; }
input, textarea, [data-testid="stTextInput"] input {
    background-color: #141F38 !important;
    border: 1px solid #1E3055 !important;
    color: #E8EEFF !important;
    border-radius: 6px !important;
}
input:focus {
    border-color: #3B7FE8 !important;
    box-shadow: 0 0 0 2px rgba(59,127,232,0.2) !important;
}
[data-testid="stButton"] button {
    background-color: #3B7FE8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: background 0.15s !important;
}
[data-testid="stButton"] button:hover { background-color: #5A96F0 !important; }
[data-testid="stDownloadButton"] button {
    background-color: #141F38 !important;
    color: #6B9FFF !important;
    border: 1px solid #3B7FE8 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover { background-color: #1A2B4A !important; }
[data-testid="stFileUploader"] {
    background-color: #141F38 !important;
    border: 1px dashed #2A4A80 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"] * { color: #8BA4D4 !important; }
[data-testid="stFileUploaderDropzone"] { background-color: #141F38 !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background-color: #0F1729 !important;
    border-bottom: 1px solid #1E3055 !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #4A6090 !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 16px !important;
    font-size: 13px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background-color: #141F38 !important;
    color: #6B9FFF !important;
    border-bottom: 2px solid #3B7FE8 !important;
}
[data-testid="stTabsContent"] {
    background-color: #0A0F1E !important;
    border: none !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid #1E3055 !important;
    border-radius: 8px !important;
}
[data-testid="stProgressBar"] > div {
    background-color: #1E3055 !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background-color: #3B7FE8 !important;
    border-radius: 4px !important;
}
[data-testid="stMetric"] {
    background-color: #141F38 !important;
    border: 1px solid #1E3055 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] p {
    color: #8BA4D4 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stMetricValue"] {
    color: #E8EEFF !important;
    font-size: 24px !important;
    font-weight: 500 !important;
}
[data-testid="stAlert"] {
    background-color: #141F38 !important;
    border-left: 3px solid #3B7FE8 !important;
    border-radius: 0 6px 6px 0 !important;
    color: #8BA4D4 !important;
}
[data-testid="stVegaLiteChart"] { background-color: #141F38 !important; }
hr { border-color: #1E3055 !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0A0F1E; }
::-webkit-scrollbar-thumb { background: #1E3055; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2A4A80; }
code, pre {
    background-color: #0A0F1E !important;
    color: #6B9FFF !important;
    border: 1px solid #1E3055 !important;
    border-radius: 4px !important;
}
[data-testid="stCaptionContainer"] p { color: #4A6090 !important; }
.stSpinner > div { border-top-color: #3B7FE8 !important; }
</style>""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
_defaults = {
    "api_key":        os.getenv("ANTHROPIC_API_KEY", ""),
    "ing_result":     None,
    "anom_result":    None,
    "summ_result":    None,
    "rep_result":     None,
    "pipeline_ran":   False,
    "agent_1_status": "waiting",
    "agent_2_status": "waiting",
    "agent_3_status": "waiting",
    "agent_4_status": "waiting",
    "total_rows":     "—",
    "flagged_count":  "—",
    "critical_count": "—",
    "pipeline_pct":   "—",
    "risk_score":     0,
    "risk_label":     "—",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(_h("""
    <div style="padding:16px 0 24px;">
    <div style="font-size:11px;font-weight:500;color:#4A6090;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Ernst &amp; Young LLP</div>
    <div style="font-size:20px;font-weight:500;color:#E8EEFF;line-height:1.2;">Audit <span style="color:#3B7FE8;">Intelligence</span></div>
    <div style="font-size:11px;color:#4A6090;margin-top:4px;">Multi-Agent AI Platform</div>
    </div>
    <div style="border-top:1px solid #1E3055;margin-bottom:20px;"></div>
    """), unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">API Configuration</div>', unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Anthropic API key",
        type="password",
        value=st.session_state["api_key"],
        placeholder="sk-ant-...",
        label_visibility="collapsed",
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.markdown('<div style="font-size:11px;color:#2ECC71;margin-top:4px;">&#9679; Connected</div>', unsafe_allow_html=True)
    else:
        st.session_state["api_key"] = ""
        st.markdown('<div style="font-size:11px;color:#4A6090;margin-top:4px;">&#9675; Not connected</div>', unsafe_allow_html=True)

    st.markdown('<div style="border-top:1px solid #1E3055;margin:20px 0;"></div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload journal entries",
        type=["csv"],
        label_visibility="collapsed",
    )

    st.markdown('<div style="border-top:1px solid #1E3055;margin:20px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px;">Agent Pipeline</div>', unsafe_allow_html=True)

    for num, label in [(1,"Data ingestion"),(2,"Anomaly detection"),(3,"AI audit summary"),(4,"PDF risk report")]:
        status = st.session_state.get(f"agent_{num}_status", "waiting")
        dot    = "&#9679;" if status in ("done","running") else "&#9675;"
        color  = "#2ECC71" if status == "done" else ("#3B7FE8" if status == "running" else "#4A6090")
        tc     = "#E8EEFF" if status != "waiting" else "#4A6090"
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0;"><span style="color:{color};font-size:12px;">{dot}</span><span style="font-size:12px;color:{tc};">Agent {num} &mdash; {label}</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="border-top:1px solid #1E3055;margin:20px 0;"></div>', unsafe_allow_html=True)

    run_btn = st.button("Run audit pipeline", use_container_width=True)

    try:
        with open("data/sample_journal_entries.csv", "rb") as _f:
            st.download_button("Download sample CSV", _f, "sample_journal_entries.csv", "text/csv", use_container_width=True)
    except FileNotFoundError:
        pass

    st.markdown('<div style="margin-top:40px;font-size:10px;color:#4A6090;line-height:1.6;">Powered by Claude AI (Anthropic)<br>EY.ai &mdash; Multi-Agent Assurance<br>&copy; 2026 Portfolio Project</div>', unsafe_allow_html=True)

# ── Pipeline execution ─────────────────────────────────────────────────────────
if run_btn:
    if uploaded_file is None:
        st.warning("Upload a CSV file first, then click Run audit pipeline.")
    else:
        file_bytes = uploaded_file.read()
        for n in range(1, 5):
            st.session_state[f"agent_{n}_status"] = "waiting"

        progress_bar = st.progress(0)
        status_box   = st.empty()

        def _status(msg, color="#8BA4D4", border="#3B7FE8"):
            status_box.markdown(
                f'<div style="background:#141F38;border:1px solid #1E3055;border-left:3px solid {border};border-radius:0 6px 6px 0;padding:10px 16px;font-size:13px;color:{color};margin-bottom:8px;"><span style="color:{border};">&#9679;</span> &nbsp; {msg}</div>',
                unsafe_allow_html=True,
            )

        # Agent 1
        st.session_state["agent_1_status"] = "running"
        _status("Agent 1 — Ingesting and validating data&hellip;")
        progress_bar.progress(5)
        ing = Agent1Ingestion().run(file_bytes)
        st.session_state["ing_result"] = ing

        if not ing.success:
            st.session_state["agent_1_status"] = "waiting"
            _status(f"Agent 1 failed: {ing.error_message}", "#FF4C4C", "#FF4C4C")
            progress_bar.empty()
        else:
            st.session_state["agent_1_status"] = "done"
            st.session_state["total_rows"] = ing.row_count
            progress_bar.progress(25)

            # Agent 2
            st.session_state["agent_2_status"] = "running"
            _status("Agent 2 — Scanning for anomalies&hellip;")
            anom = Agent2Anomaly().run(ing.df)
            st.session_state["anom_result"]    = anom
            st.session_state["agent_2_status"] = "done"
            st.session_state["flagged_count"]  = anom.total_flags
            st.session_state["critical_count"] = anom.severity_counts.get("Critical", 0)
            progress_bar.progress(50)

            # Agent 3
            st.session_state["agent_3_status"] = "running"
            _status("Agent 3 — Generating AI audit summary&hellip;")
            api_key = st.session_state.get("api_key", "")
            summ = Agent3Summary().run(anom.flagged_df, anom.severity_counts, anom.rule_summary, api_key)
            st.session_state["summ_result"]    = summ
            st.session_state["agent_3_status"] = "done"
            progress_bar.progress(75)

            # Agent 4
            st.session_state["agent_4_status"] = "running"
            _status("Agent 4 — Compiling PDF risk report&hellip;")
            rep = Agent4Report().run(ing, anom, summ)
            st.session_state["rep_result"]     = rep
            st.session_state["agent_4_status"] = "done"
            if rep.success:
                st.session_state["risk_score"] = rep.risk_score
                st.session_state["risk_label"] = rep.risk_label
            st.session_state["pipeline_pct"] = 100
            progress_bar.progress(100)

            _status("Audit pipeline complete &mdash; all 4 agents finished", "#2ECC71", "#2ECC71")
            st.session_state["pipeline_ran"] = True
            st.rerun()

# ── Main header ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])

with col_left:
    st.markdown(_h("""
    <div style="padding:8px 0 20px;">
    <div style="font-size:22px;font-weight:500;color:#E8EEFF;">Audit Intelligence Platform</div>
    <div style="font-size:13px;color:#8BA4D4;margin-top:4px;">
    EY Canvas &mdash; Multi-Agent Assurance Framework &nbsp;
    <span style="color:#3B7FE8;font-size:11px;border:1px solid #1E3055;padding:2px 8px;border-radius:4px;">April 2026 Launch</span>
    </div>
    </div>
    """), unsafe_allow_html=True)

with col_right:
    risk       = st.session_state.get("risk_score", 0)
    risk_label = st.session_state.get("risk_label", "—")
    risk_color = RISK_COLORS.get(risk_label, "#4A6090")
    st.markdown(_h(f"""
    <div style="text-align:right;padding:8px 0 20px;">
    <div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Risk score</div>
    <div style="font-size:32px;font-weight:500;color:{risk_color};">{risk}</div>
    <div style="font-size:12px;color:{risk_color};">{risk_label} risk</div>
    </div>
    """), unsafe_allow_html=True)

st.markdown('<div style="border-top:1px solid #1E3055;margin-bottom:20px;"></div>', unsafe_allow_html=True)

# ── Metric cards ──────────────────────────────────────────────────────────────
def cyber_metric(label, value, value_color="#E8EEFF", sublabel=""):
    return _h(f"""
    <div style="background:#141F38;border:1px solid #1E3055;border-radius:8px;padding:14px 16px;height:100%;">
    <div style="font-size:10px;color:#4A6090;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px;">{label}</div>
    <div style="font-size:26px;font-weight:500;color:{value_color};line-height:1;">{value}</div>
    <div style="font-size:11px;color:#4A6090;margin-top:4px;">{sublabel}</div>
    </div>
    """)

mc1, mc2, mc3, mc4 = st.columns(4)
total    = st.session_state.get("total_rows", "—")
flagged  = st.session_state.get("flagged_count", "—")
critical = st.session_state.get("critical_count", "—")
complete = st.session_state.get("pipeline_pct", "—")
pct_str  = f"{complete}%" if isinstance(complete, int) else complete

with mc1: st.markdown(cyber_metric("Transactions", total, "#E8EEFF", "loaded"), unsafe_allow_html=True)
with mc2: st.markdown(cyber_metric("Anomalies", flagged, "#FF9F43", "flagged"), unsafe_allow_html=True)
with mc3: st.markdown(cyber_metric("Critical flags", critical, "#FF4C4C", "require action"), unsafe_allow_html=True)
with mc4: st.markdown(cyber_metric("Pipeline", pct_str, "#3B7FE8", "complete"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "01 — Data ingestion",
    "02 — Anomaly detection",
    "03 — AI audit summary",
    "04 — Risk report",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    ing = st.session_state.get("ing_result")
    if ing is None:
        st.markdown(_h("""
        <div style="background:#141F38;border:1px dashed #1E3055;border-radius:8px;padding:40px;text-align:center;margin-top:20px;">
        <div style="font-size:32px;color:#1E3055;margin-bottom:12px;">&#8593;</div>
        <div style="font-size:14px;color:#4A6090;">Upload a CSV and click Run audit pipeline</div>
        <div style="font-size:12px;color:#4A6090;margin-top:4px;">Agent 1 will validate and clean your journal entry data</div>
        </div>
        """), unsafe_allow_html=True)
    elif not ing.success:
        st.markdown(f'<div style="background:#141F38;border-left:3px solid #FF4C4C;border-radius:0 6px 6px 0;padding:12px 16px;font-size:13px;color:#FF4C4C;">Ingestion failed: {ing.error_message}</div>', unsafe_allow_html=True)
    else:
        mc = "#FF4C4C" if ing.rows_with_nulls > 0 else "#2ECC71"
        ic = "#FF9F43" if ing.validation_issues else "#2ECC71"
        st.markdown(_h(f"""
        <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
        <div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;padding:8px 14px;font-size:12px;color:#8BA4D4;"><span style="color:#2ECC71;">&#9679;</span> &nbsp; {ing.row_count} rows loaded</div>
        <div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;padding:8px 14px;font-size:12px;color:#8BA4D4;"><span style="color:#3B7FE8;">&#9679;</span> &nbsp; {ing.column_count} columns detected</div>
        <div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;padding:8px 14px;font-size:12px;color:{mc};"><span style="color:{mc};">&#9679;</span> &nbsp; {ing.rows_with_nulls} missing values</div>
        <div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;padding:8px 14px;font-size:12px;color:{ic};"><span style="color:{ic};">&#9679;</span> &nbsp; {len(ing.validation_issues)} validation issues</div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Data preview</div>', unsafe_allow_html=True)
        st.dataframe(ing.df.head(20), use_container_width=True, height=280)

        if ing.validation_issues:
            st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin:16px 0 8px;">Validation issues</div>', unsafe_allow_html=True)
            for issue in ing.validation_issues:
                st.markdown(f'<div style="background:#141F38;border-left:3px solid #FF9F43;border-radius:0 6px 6px 0;padding:8px 12px;font-size:12px;color:#8BA4D4;margin-bottom:6px;">{issue}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    anom = st.session_state.get("anom_result")
    if anom is None:
        st.markdown(_h("""
        <div style="background:#141F38;border:1px dashed #1E3055;border-radius:8px;padding:40px;text-align:center;margin-top:20px;">
        <div style="font-size:14px;color:#4A6090;">Waiting for Agent 1 to complete data ingestion</div>
        </div>
        """), unsafe_allow_html=True)
    elif not anom.success:
        st.markdown(f'<div style="background:#141F38;border-left:3px solid #FF4C4C;border-radius:0 6px 6px 0;padding:12px 16px;font-size:13px;color:#FF4C4C;">Anomaly detection failed: {anom.error_message}</div>', unsafe_allow_html=True)
    else:
        # Build all four severity badges as a single compact HTML string
        badges_html = '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">'
        for sev in ["Critical", "High", "Medium", "Low"]:
            count = anom.severity_counts.get(sev, 0)
            color = SEV_COLORS[sev]
            badges_html += (
                f'<div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;'
                f'padding:8px 16px;text-align:center;min-width:80px;">'
                f'<div style="font-size:20px;font-weight:500;color:{color};">{count}</div>'
                f'<div style="font-size:10px;color:#4A6090;text-transform:uppercase;letter-spacing:0.05em;">{sev}</div>'
                f'</div>'
            )
        badges_html += '</div>'
        st.markdown(badges_html, unsafe_allow_html=True)

        if anom.rule_summary:
            st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Flags by detection rule</div>', unsafe_allow_html=True)
            rule_df = (
                pd.DataFrame(list(anom.rule_summary.items()), columns=["Rule", "Count"])
                .sort_values("Count", ascending=False)
            )
            st.bar_chart(rule_df.set_index("Rule"), height=180)

        st.markdown('<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.06em;margin:16px 0 8px;">Flagged transactions</div>', unsafe_allow_html=True)
        if anom.flagged_df.empty:
            st.markdown('<div style="background:#141F38;border-left:3px solid #2ECC71;border-radius:0 6px 6px 0;padding:10px 16px;font-size:13px;color:#2ECC71;">No anomalies detected &mdash; dataset appears clean.</div>', unsafe_allow_html=True)
        else:
            def _color_sev(val):
                return f"color:{SEV_COLORS.get(val,'#8BA4D4')};font-weight:500;"
            styled_df = anom.flagged_df.style.map(_color_sev, subset=["severity"])
            st.dataframe(styled_df, use_container_width=True, height=340)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    summ    = st.session_state.get("summ_result")
    api_key = st.session_state.get("api_key", "")

    if summ is None and not st.session_state.get("pipeline_ran"):
        st.markdown(_h("""
        <div style="background:#141F38;border:1px dashed #1E3055;border-radius:8px;padding:40px;text-align:center;margin-top:20px;">
        <div style="font-size:14px;color:#4A6090;">Waiting for anomaly detection to complete</div>
        </div>
        """), unsafe_allow_html=True)
    elif summ and summ.skipped:
        st.markdown(_h("""
        <div style="background:#141F38;border:1px solid #1E3055;border-left:3px solid #FF9F43;border-radius:0 8px 8px 0;padding:20px;font-size:13px;color:#8BA4D4;">
        No API key provided. Enter your Anthropic API key in the sidebar to enable AI-generated audit summaries. Agents 1, 2 and 4 still run without it.
        </div>
        """), unsafe_allow_html=True)
    elif summ and not summ.success:
        st.markdown(f'<div style="background:#141F38;border-left:3px solid #FF4C4C;border-radius:0 6px 6px 0;padding:12px 16px;font-size:13px;color:#FF4C4C;">Agent 3 error: {summ.error_message}</div>', unsafe_allow_html=True)
    elif summ and summ.success:
        st.markdown(_h("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="width:32px;height:32px;border-radius:50%;background:#141F38;border:1px solid #3B7FE8;display:flex;align-items:center;justify-content:center;font-size:14px;color:#3B7FE8;flex-shrink:0;">AI</div>
        <div>
        <div style="font-size:13px;font-weight:500;color:#E8EEFF;">Senior EY Audit AI &mdash; Claude Sonnet</div>
        <div style="font-size:11px;color:#4A6090;">Anthropic Claude API &mdash; Audit analysis complete</div>
        </div>
        </div>
        """), unsafe_allow_html=True)

        safe = (
            summ.summary_text
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        st.markdown(
            f'<div style="background:#141F38;border:1px solid #1E3055;border-left:3px solid #3B7FE8;border-radius:0 8px 8px 0;padding:20px 24px;font-size:13px;color:#8BA4D4;line-height:1.8;">{safe}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(_h("""
        <div style="background:#141F38;border:1px dashed #1E3055;border-radius:8px;padding:40px;text-align:center;margin-top:20px;">
        <div style="font-size:14px;color:#4A6090;">Waiting for anomaly detection to complete</div>
        </div>
        """), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    rep = st.session_state.get("rep_result")
    if rep is None:
        st.markdown(_h("""
        <div style="background:#141F38;border:1px dashed #1E3055;border-radius:8px;padding:40px;text-align:center;margin-top:20px;">
        <div style="font-size:14px;color:#4A6090;">Run the full pipeline to generate your risk report</div>
        </div>
        """), unsafe_allow_html=True)
    elif not rep.success:
        st.markdown(f'<div style="background:#141F38;border-left:3px solid #FF4C4C;border-radius:0 6px 6px 0;padding:12px 16px;font-size:13px;color:#FF4C4C;">Report generation failed: {rep.error_message}</div>', unsafe_allow_html=True)
    else:
        score      = rep.risk_score
        label      = rep.risk_label
        risk_color = RISK_COLORS.get(label, "#4A6090")

        st.markdown(
            f'<div style="background:#141F38;border:1px solid #1E3055;border-radius:8px;padding:24px;text-align:center;margin-bottom:20px;">'
            f'<div style="font-size:11px;color:#4A6090;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Overall risk score</div>'
            f'<div style="font-size:64px;font-weight:500;color:{risk_color};line-height:1;">{score}</div>'
            f'<div style="font-size:18px;color:{risk_color};margin-top:4px;font-weight:500;">{label.upper()} RISK</div>'
            f'<div style="font-size:12px;color:#4A6090;margin-top:8px;">Score formula: Critical&times;4 + High&times;3 + Medium&times;2 + Low&times;1</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        anom_res = st.session_state.get("anom_result")
        if anom_res:
            r1, r2, r3, r4 = st.columns(4)
            for col, (sev, color) in zip(
                [r1, r2, r3, r4],
                [("Critical","#FF4C4C"),("High","#FF9F43"),("Medium","#FFE600"),("Low","#2ECC71")]
            ):
                cnt = anom_res.severity_counts.get(sev, 0)
                with col:
                    st.markdown(
                        f'<div style="background:#141F38;border:1px solid #1E3055;border-radius:6px;padding:12px;text-align:center;">'
                        f'<div style="font-size:22px;font-weight:500;color:{color};">{cnt}</div>'
                        f'<div style="font-size:10px;color:#4A6090;text-transform:uppercase;letter-spacing:0.05em;">{sev}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="Download PDF risk report",
            data=rep.pdf_bytes,
            file_name="EY_Audit_Risk_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.markdown('<div style="font-size:11px;color:#4A6090;text-align:center;margin-top:8px;">Professional PDF report &mdash; ready to attach to your EY application</div>', unsafe_allow_html=True)
