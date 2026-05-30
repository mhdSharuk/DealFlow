import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime

import streamlit as st

from orchestrator import DealFlowOrchestrator

# ─────────────────────────────────────────────────────────────────────────────
#  Logging — writes to BOTH terminal (stderr) and a session-state log buffer
# ─────────────────────────────────────────────────────────────────────────────
class UILogHandler(logging.Handler):
    """Push log records into st.session_state.logs so the UI can render them."""
    def emit(self, record: logging.LogRecord) -> None:
        if "logs" not in st.session_state:
            st.session_state.logs = []
        ts = datetime.now().strftime("%H:%M:%S")
        level = record.levelname
        msg   = self.format(record)
        st.session_state.logs.append({"ts": ts, "level": level, "msg": msg})


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("sales_copilot")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Terminal handler (colour-coded via ANSI)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(
            logging.Formatter(
                "\033[90m%(asctime)s\033[0m  %(levelname)-8s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(ch)

        # UI handler
        ui_handler = UILogHandler()
        ui_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(ui_handler)

    return logger


log = _setup_logger()


# ─────────────────────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS — dark terminal / command-centre aesthetic
# ─────────────────────────────────────────────────────────────────────────────
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Bebas+Neue&family=Barlow:wght@400;500;600&display=swap');

/* ── Reset / Shell ── */
html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0A0C10 !important;
    color: #C9D1D9 !important;
}
.block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1280px;
    background: transparent !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0A0C10; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 4px; }

/* ── Top header ── */
.sc-header {
    display: flex;
    align-items: baseline;
    gap: 1.2rem;
    margin-bottom: 2.5rem;
    border-bottom: 1px solid #21262D;
    padding-bottom: 1.25rem;
}
.sc-header .wordmark {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    letter-spacing: 3px;
    color: #58A6FF;
    line-height: 1;
    text-shadow: 0 0 40px rgba(88,166,255,.35);
}
.sc-header .tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #3FB950;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.25rem 0.6rem;
    border: 1px solid #3FB95044;
    border-radius: 4px;
    background: #3FB95011;
}
.sc-header .version {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #484F58;
    margin-left: auto;
}

/* ── Upload zone ── */
.upload-zone {
    background: #0D1117;
    border: 1.5px dashed #30363D;
    border-radius: 12px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.75rem;
    transition: border-color .25s;
}
.upload-zone:hover { border-color: #58A6FF55; }
.upload-zone .uz-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #58A6FF;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.75rem;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.25rem !important;
    transition: all .2s ease !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #58A6FF !important;
    color: #0A0C10 !important;
    border: none !important;
    box-shadow: 0 0 20px rgba(88,166,255,.25) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #79BAFF !important;
    box-shadow: 0 0 30px rgba(88,166,255,.45) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background: transparent !important;
    color: #8B949E !important;
    border: 1px solid #30363D !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: #58A6FF !important;
    color: #58A6FF !important;
}

/* ── Pipeline strip ── */
.pipeline-strip {
    display: flex;
    align-items: center;
    gap: 0;
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1.5rem;
    overflow-x: auto;
}
.pipe-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 130px;
}
.pipe-step .ps-dot {
    width: 14px; height: 14px;
    border-radius: 50%;
    background: #21262D;
    border: 2px solid #30363D;
    margin-bottom: 0.45rem;
    transition: all .4s ease;
}
.pipe-step.running .ps-dot  { background: #58A6FF; border-color: #58A6FF; box-shadow: 0 0 12px #58A6FF88; animation: pulse 1.2s infinite; }
.pipe-step.complete .ps-dot { background: #3FB950; border-color: #3FB950; box-shadow: 0 0 8px #3FB95055; }
.pipe-step.error .ps-dot    { background: #F85149; border-color: #F85149; }
.pipe-step .ps-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #484F58;
    text-align: center;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.pipe-step.running .ps-label  { color: #58A6FF; }
.pipe-step.complete .ps-label { color: #3FB950; }
.pipe-step.error .ps-label    { color: #F85149; }
.pipe-connector {
    flex: 1;
    height: 2px;
    background: #21262D;
    margin-bottom: 1.4rem;
    min-width: 20px;
    transition: background .4s ease;
}
.pipe-connector.lit { background: #3FB950; }

/* ── Live log console ── */
.log-console {
    background: #010409;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 0;
    margin-bottom: 1.5rem;
    overflow: hidden;
}
.log-console .lc-topbar {
    background: #161B22;
    padding: 0.55rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-bottom: 1px solid #21262D;
}
.log-console .lc-topbar .dot { width:10px;height:10px;border-radius:50%; }
.log-console .lc-topbar .d-red    { background:#F85149; }
.log-console .lc-topbar .d-yellow { background:#D29922; }
.log-console .lc-topbar .d-green  { background:#3FB950; }
.log-console .lc-topbar .lc-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #484F58;
    margin-left: 0.4rem;
    letter-spacing: 0.06em;
}
.log-console .lc-body {
    padding: 0.9rem 1.1rem;
    max-height: 280px;
    overflow-y: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.65;
}
.log-line { display: flex; gap: 0.75rem; margin-bottom: 0.15rem; }
.log-ts   { color: #484F58; flex-shrink: 0; }
.log-DEBUG   { color: #8B949E; }
.log-INFO    { color: #58A6FF; }
.log-WARNING { color: #D29922; }
.log-ERROR   { color: #F85149; }
.log-SUCCESS { color: #3FB950; }

/* ── Metric chips ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.metric-chip {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.6rem 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    min-width: 130px;
}
.metric-chip .mc-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: #484F58;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
.metric-chip .mc-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem;
    font-weight: 600;
    color: #C9D1D9;
}
.metric-chip .mc-value.accent { color: #58A6FF; }
.metric-chip .mc-value.success { color: #3FB950; }

/* ── Agent result card ── */
.agent-card {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
    transition: border-color .25s;
}
.agent-card:hover { border-color: #30363D; }
.agent-card .ac-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding-bottom: 0.85rem;
    border-bottom: 1px solid #21262D;
}
.agent-card .ac-icon {
    width: 36px; height: 36px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
}
.icon-blue   { background: #58A6FF18; border: 1px solid #58A6FF33; }
.icon-green  { background: #3FB95018; border: 1px solid #3FB95033; }
.icon-orange { background: #D2992218; border: 1px solid #D2992233; }
.icon-purple { background: #BC8CFF18; border: 1px solid #BC8CFF33; }
.agent-card .ac-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.25rem;
    letter-spacing: 1.5px;
    color: #E6EDF3;
}
.agent-card .ac-desc {
    font-size: 0.78rem;
    color: #484F58;
    margin-top: 0.1rem;
}
.ac-tag {
    margin-left: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #3FB950;
    background: #3FB95011;
    border: 1px solid #3FB95033;
    padding: 0.2rem 0.55rem;
    border-radius: 20px;
    letter-spacing: 0.06em;
}

/* ── Formatted content inside cards ── */
.fc-section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #484F58;
    margin: 1rem 0 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #21262D;
}
.fc-topic {
    background: #161B22;
    border-left: 3px solid #58A6FF;
    border-radius: 0 6px 6px 0;
    padding: 0.7rem 1rem;
    margin-bottom: 0.6rem;
}
.fc-topic .ft-name {
    font-weight: 600;
    color: #E6EDF3;
    font-size: 0.88rem;
}
.fc-topic .ft-body {
    font-size: 0.82rem;
    color: #8B949E;
    margin-top: 0.25rem;
}
.fc-pill {
    display: inline-block;
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.78rem;
    color: #8B949E;
    margin: 0.2rem 0.2rem 0 0;
}
.fc-task {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
}
.fc-task .ft-assignee {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #58A6FF;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}
.fc-task .ft-action { font-size: 0.85rem; color: #C9D1D9; }
.fc-task .ft-blocker {
    font-size: 0.78rem;
    color: #D29922;
    background: #D2992211;
    border: 1px solid #D2992233;
    border-radius: 5px;
    padding: 0.3rem 0.6rem;
    margin-top: 0.4rem;
}
.hs-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.hs-stat {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.75rem 1rem;
}
.hs-stat .hs-key {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #484F58;
    margin-bottom: 0.3rem;
}
.hs-stat .hs-val {
    font-size: 0.9rem;
    font-weight: 600;
    color: #E6EDF3;
}
.crm-notes {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    font-size: 0.83rem;
    color: #8B949E;
    line-height: 1.65;
}
.email-header-row {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
    margin-bottom: 0.35rem;
    font-size: 0.83rem;
}
.email-header-row .ehr-key {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #484F58;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    min-width: 55px;
}
.email-header-row .ehr-val { color: #C9D1D9; }

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.07em !important;
    color: #484F58 !important;
    text-transform: uppercase !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom-color: #58A6FF !important;
}

/* ── Code / JSON ── */
.stCodeBlock { font-size: 0.78rem !important; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.06em !important;
    background: transparent !important;
    color: #484F58 !important;
    border: 1px solid #21262D !important;
    padding: 0.3rem 0.75rem !important;
    border-radius: 5px !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: #58A6FF !important;
    color: #58A6FF !important;
}

/* ── Expander ── */
details {
    background: #0D1117 !important;
    border: 1px solid #21262D !important;
    border-radius: 8px !important;
}
summary { color: #8B949E !important; font-size: 0.85rem !important; }

/* ── Text area ── */
textarea {
    background: #010409 !important;
    color: #C9D1D9 !important;
    border: 1px solid #21262D !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
}

/* ── Divider ── */
hr { border-color: #21262D !important; }

/* ── Animations ── */
@keyframes pulse {
    0%,100% { box-shadow: 0 0 8px #58A6FF66; }
    50%      { box-shadow: 0 0 20px #58A6FFaa; }
}
@keyframes fadeIn {
    from { opacity:0; transform:translateY(6px); }
    to   { opacity:1; transform:translateY(0); }
}
.fade-in { animation: fadeIn .35s ease forwards; }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Session state
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "processing": False,
    "results": None,
    "processing_time": None,
    "uploaded_json": None,
    "logs": [],
    "pipe_status": {          # pending | running | complete | error
        "upload":    "pending",
        "extract":   "pending",
        "taskmage":  "pending",
        "hubspot":   "pending",
        "email":     "pending",
    },
}


def init_session_state() -> None:
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_state() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    log.info("State cleared — ready for new transcript.")


# ─────────────────────────────────────────────────────────────────────────────
#  HTML helpers
# ─────────────────────────────────────────────────────────────────────────────
def _pipe_step_html(label: str, status: str, connector: bool = True) -> str:
    lit = " lit" if status == "complete" else ""
    conn_html = f'<div class="pipe-connector{lit}"></div>' if connector else ""
    return (
        f'<div class="pipe-step {status}">'
        f'  <div class="ps-dot"></div>'
        f'  <div class="ps-label">{label}</div>'
        f"</div>"
        f"{conn_html}"
    )


def _log_line_html(ts: str, level: str, msg: str) -> str:
    css = f"log-{level}"
    return (
        f'<div class="log-line">'
        f'<span class="log-ts">{ts}</span>'
        f'<span class="{css}">{msg}</span>'
        f"</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  UI sections
# ─────────────────────────────────────────────────────────────────────────────
def render_header() -> None:
    st.markdown(
        """
        <div class="sc-header">
            <span class="wordmark">SALES COPILOT</span>
            <span class="tagline">Multi-Agent Intelligence</span>
            <span class="version">v2.0 · Fireflies AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_section() -> tuple[bool, bool]:
    """Returns (process_clicked, clear_clicked)."""
    st.markdown(
        '<div class="upload-zone"><div class="uz-label">⬆ Drop Transcript</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Fireflies JSON",
        type=["json"],
        help="Fireflies.ai transcript export (.json)",
        label_visibility="collapsed",
    )

    # Cache parsed JSON immediately — survives button-click rerun
    if uploaded_file is not None and st.session_state.uploaded_json is None:
        try:
            st.session_state.uploaded_json = json.load(uploaded_file)
            st.session_state.pipe_status["upload"] = "complete"
            log.info(f"Transcript loaded: {uploaded_file.name}  ({uploaded_file.size:,} bytes)")
        except json.JSONDecodeError:
            st.error("⚠️ Invalid JSON — please check the file.")
            st.session_state.uploaded_json = None
            log.error("JSON decode failed for uploaded file.")

    col1, col2, col3 = st.columns([1, 1, 7])
    with col1:
        process_clicked = st.button(
            "▶  ANALYZE",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True,
        )
    with col2:
        clear_clicked = st.button("↺  CLEAR", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    return process_clicked, clear_clicked


def render_pipeline_strip() -> None:
    ps = st.session_state.pipe_status
    steps = [
        ("UPLOAD",   ps["upload"]),
        ("EXTRACT",  ps["extract"]),
        ("TASKMAGE", ps["taskmage"]),
        ("HUBSPOT",  ps["hubspot"]),
        ("EMAIL",    ps["email"]),
    ]
    html = '<div class="pipeline-strip">'
    for i, (label, status) in enumerate(steps):
        connector = i < len(steps) - 1
        html += _pipe_step_html(label, status, connector)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_log_console(placeholder) -> None:
    logs = st.session_state.get("logs", [])
    lines_html = "".join(
        _log_line_html(e["ts"], e["level"], e["msg"]) for e in logs[-80:]
    )
    html = f"""
    <div class="log-console fade-in">
        <div class="lc-topbar">
            <span class="dot d-red"></span>
            <span class="dot d-yellow"></span>
            <span class="dot d-green"></span>
            <span class="lc-title">AGENT LOG STREAM — {len(logs)} entries</span>
        </div>
        <div class="lc-body" id="log-body">
            {lines_html if lines_html else '<span class="log-DEBUG">Waiting for events…</span>'}
        </div>
    </div>
    <script>
        // Auto-scroll log to bottom
        var lb = document.getElementById('log-body');
        if (lb) lb.scrollTop = lb.scrollHeight;
    </script>
    """
    placeholder.markdown(html, unsafe_allow_html=True)


def render_metrics() -> None:
    pt = st.session_state.processing_time
    results = st.session_state.results or {}
    n_agents = sum(1 for k in ["agent_1_extraction","agent_2_tickets","agent_3_hubspot","agent_4_email"] if results.get(k))

    topics = len((results.get("agent_1_extraction") or {}).get("topics", []))
    tasks  = len((results.get("agent_2_tickets") or {}).get("tasks", []))

    st.markdown(
        f"""
        <div class="metric-row fade-in">
            <div class="metric-chip">
                <span class="mc-label">Time</span>
                <span class="mc-value accent">{'%.1fs' % pt if pt else '—'}</span>
            </div>
            <div class="metric-chip">
                <span class="mc-label">Agents</span>
                <span class="mc-value success">{n_agents}/4</span>
            </div>
            <div class="metric-chip">
                <span class="mc-label">Topics</span>
                <span class="mc-value">{topics}</span>
            </div>
            <div class="metric-chip">
                <span class="mc-label">Tasks</span>
                <span class="mc-value">{tasks}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Formatted content renderers
# ─────────────────────────────────────────────────────────────────────────────
def _render_extractor(data: dict) -> None:
    topics = data.get("topics", [])
    if topics:
        st.markdown('<div class="fc-section-title">Topics Discussed</div>', unsafe_allow_html=True)
        for t in topics:
            st.markdown(
                f'<div class="fc-topic">'
                f'  <div class="ft-name">{t.get("topic_name","—")}</div>'
                f'  <div class="ft-body">{t.get("summary","")}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    pain_points = data.get("pain_points", [])
    if pain_points:
        st.markdown('<div class="fc-section-title">Pain Points</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="fc-pill">⚡ {p}</span>' for p in pain_points)
        st.markdown(pills, unsafe_allow_html=True)

    comps = data.get("competitors_mentioned", [])
    if comps:
        st.markdown('<div class="fc-section-title">Competitors Mentioned</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="fc-pill">⚔ {c}</span>' for c in comps)
        st.markdown(pills, unsafe_allow_html=True)


def _render_taskmage(data: dict) -> None:
    if isinstance(data, dict):
        tasks = data.get("tasks", [data])
    elif isinstance(data, list):
        tasks = data
    else:
        tasks = [data]

    st.markdown('<div class="fc-section-title">Action Items</div>', unsafe_allow_html=True)
    for i, task in enumerate(tasks, 1):
        blocker_html = ""
        if task.get("blocker"):
            blocker_html = f'<div class="ft-blocker">🚧 Blocker: {task["blocker"]}</div>'
        st.markdown(
            f'<div class="fc-task">'
            f'  <div class="ft-assignee">#{i} · {task.get("assignee","Unknown")}</div>'
            f'  <div class="ft-action">{task.get("action_item","No action specified")}</div>'
            f"  {blocker_html}"
            f"</div>",
            unsafe_allow_html=True,
        )


def _render_hubspot(data: dict) -> None:
    st.markdown(
        f"""
        <div class="hs-grid">
            <div class="hs-stat">
                <div class="hs-key">Deal Stage</div>
                <div class="hs-val">{data.get('deal_stage_recommendation','—')}</div>
            </div>
            <div class="hs-stat">
                <div class="hs-key">Sentiment</div>
                <div class="hs-val">{data.get('perceived_sentiment','—')}</div>
            </div>
            <div class="hs-stat">
                <div class="hs-key">Competitor Threat</div>
                <div class="hs-val">{data.get('competitor_threat_level','—')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="fc-section-title">CRM Notes</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crm-notes">{data.get("hubspot_notes_body","—")}</div>', unsafe_allow_html=True)


def _render_email(data: dict) -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:1rem;">
            <div class="email-header-row">
                <span class="ehr-key">TO</span>
                <span class="ehr-val">{data.get('recipient_email','—')}</span>
            </div>
            <div class="email-header-row">
                <span class="ehr-key">SUBJECT</span>
                <span class="ehr-val">{data.get('email_subject','—')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="fc-section-title">Body</div>', unsafe_allow_html=True)
    st.text_area(
        label="email_body",
        value=data.get("email_body", "—"),
        height=300,
        label_visibility="collapsed",
    )


_RENDERERS = {
    "agent_1_extraction": _render_extractor,
    "agent_2_tickets":    _render_taskmage,
    "agent_3_hubspot":    _render_hubspot,
    "agent_4_email":      _render_email,
}

_CARD_META = {
    "agent_1_extraction": ("🔍", "EXTRACTOR",     "icon-blue",   "Topics · Pain Points · Competitors",  "LAYER 1"),
    "agent_2_tickets":    ("📋", "TASKMAGE",      "icon-green",  "Action items & assignees",             "LAYER 1"),
    "agent_3_hubspot":    ("🏢", "HUBSPOT CRM",   "icon-orange", "Deal stage · Sentiment · CRM notes",  "LAYER 2"),
    "agent_4_email":      ("✉️", "EMAIL CLOSER",  "icon-purple", "Follow-up email draft",               "LAYER 2"),
}


def render_agent_card(key: str, data: dict) -> None:
    icon, name, icon_cls, desc, layer_tag = _CARD_META[key]

    header = (
        f'<div class="agent-card fade-in">'
        f'  <div class="ac-header">'
        f'    <div class="ac-icon {icon_cls}">{icon}</div>'
        f'    <div>'
        f'      <div class="ac-name">{name}</div>'
        f'      <div class="ac-desc">{desc}</div>'
        f'    </div>'
        f'    <span class="ac-tag">{layer_tag}</span>'
        f'  </div>'
    )
    st.markdown(header, unsafe_allow_html=True)

    col_dl, _ = st.columns([1, 7])
    with col_dl:
        st.download_button(
            "⬇ JSON",
            data=json.dumps(data, indent=2),
            file_name=f"{name.lower().replace(' ','_')}.json",
            mime="application/json",
            key=f"dl_{key}",
        )

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])
    with tab_fmt:
        renderer = _RENDERERS.get(key)
        if renderer:
            renderer(data)
    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)


def render_results(results: dict) -> None:
    render_metrics()
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍  EXTRACTOR", "📋  TASKMAGE", "🏢  HUBSPOT", "✉️  EMAIL"]
    )
    mapping = [
        (tab1, "agent_1_extraction"),
        (tab2, "agent_2_tickets"),
        (tab3, "agent_3_hubspot"),
        (tab4, "agent_4_email"),
    ]
    for tab, key in mapping:
        with tab:
            payload = results.get(key)
            if payload:
                render_agent_card(key, payload)
            else:
                st.markdown(
                    '<div style="color:#484F58;font-family:IBM Plex Mono,monospace;'
                    'font-size:.8rem;padding:1rem;">No data returned for this agent.</div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    with st.expander("🗂  FULL OUTPUT JSON"):
        st.code(json.dumps(results, indent=2), language="json")


# ─────────────────────────────────────────────────────────────────────────────
#  Analysis runner (updates pipe_status + logs as it progresses)
# ─────────────────────────────────────────────────────────────────────────────
def run_analysis(json_data: dict, log_placeholder) -> None:
    ps = st.session_state.pipe_status

    def _tick(key: str, status: str, msg: str, level: str = "INFO") -> None:
        ps[key] = status
        getattr(log, level.lower())(msg)
        render_log_console(log_placeholder)

    def _mark_running_as_error() -> None:
        for key in ps:
            if ps[key] == "running":
                ps[key] = "error"

    try:
        orchestrator = DealFlowOrchestrator()
        start = time.time()

        _tick("extract",  "running", "Layer 1 started — invoking Extractor agent…")
        _tick("taskmage", "running", "Layer 1 — Taskmage agent initialising…")

        result = asyncio.run(orchestrator.process_transcript(json_data))

        elapsed_l1 = time.time() - start
        _tick("extract",  "complete", f"Extractor finished  ({elapsed_l1:.1f}s)")
        _tick("taskmage", "complete", f"Taskmage finished   ({elapsed_l1:.1f}s)")

        _tick("hubspot", "running", "Layer 2 started — HubSpot CRM agent…")
        _tick("email",   "running", "Layer 2 — Email Closer agent…")

        elapsed_l2 = time.time() - start
        _tick("hubspot", "complete", f"HubSpot agent done  ({elapsed_l2:.1f}s)")
        _tick("email",   "complete", f"Email Closer done   ({elapsed_l2:.1f}s)")

        st.session_state.results = result
        st.session_state.processing_time = time.time() - start
        log.info(f"✅ All agents complete — total {st.session_state.processing_time:.2f}s")

    except Exception as exc:
        _mark_running_as_error()

        # ── Terminal: full traceback so you can actually debug ──
        full_tb = traceback.format_exc()
        print("\n" + "─" * 60, file=sys.stdout, flush=True)
        print("ANALYSIS FAILED — FULL TRACEBACK:", file=sys.stdout, flush=True)
        print(full_tb, file=sys.stdout, flush=True)
        print("─" * 60 + "\n", file=sys.stdout, flush=True)

        # ── Logger (terminal handler sees this too) ──
        log.error(f"Analysis failed: {type(exc).__name__}: {exc}")

        # ── UI: clean one-liner only, no stack trace ──
        st.error(f"❌ Analysis failed — **{type(exc).__name__}**: {exc}")

    finally:
        st.session_state.processing = False
        render_log_console(log_placeholder)


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    init_session_state()
    render_header()

    process_clicked, clear_clicked = render_upload_section()

    if clear_clicked:
        reset_state()
        st.rerun()

    # Always show pipeline + log console once triggered
    show_console = (
        st.session_state.processing
        or st.session_state.results
        or any(s != "pending" for s in st.session_state.pipe_status.values())
    )

    if show_console:
        render_pipeline_strip()
        log_placeholder = st.empty()
        render_log_console(log_placeholder)
    else:
        log_placeholder = st.empty()

    # Trigger analysis
    if process_clicked:
        json_data = st.session_state.get("uploaded_json")

        if json_data is None:
            st.warning("⚠️ Please upload a Fireflies JSON transcript first.")
            log.warning("Analyze clicked but no transcript loaded.")
        elif "meeting_id" not in json_data and "transcript" not in json_data:
            st.error("❌ Invalid format — expected Fireflies JSON with meeting_id or transcript.")
            log.error("Invalid transcript schema — missing meeting_id and transcript keys.")
        else:
            st.session_state.processing = True
            st.session_state.pipe_status = {k: "pending" for k in st.session_state.pipe_status}
            st.session_state.pipe_status["upload"] = "complete"
            st.session_state.logs = []
            log.info("═" * 55)
            log.info("ANALYSIS STARTED")
            log.info("═" * 55)
            render_pipeline_strip()
            log_placeholder = st.empty()
            run_analysis(json_data, log_placeholder)
            st.rerun()

    if st.session_state.results:
        render_results(st.session_state.results)


if __name__ == "__main__":
    main()