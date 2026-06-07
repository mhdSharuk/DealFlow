import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st

from config import API_BASE_URL

log = logging.getLogger("dealflow.ui")
logging.basicConfig(level=logging.INFO)

hide_elements = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }
    </style>
"""
st.markdown(hide_elements, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DealFlow",
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

/* ── Drop zone notice ── */
.drop-zone {
    background: #0D1117;
    border: 1.5px dashed #30363D;
    border-radius: 12px;
    padding: 1.1rem 2rem;
    margin-bottom: 1.75rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.drop-zone .dz-icon {
    font-size: 1.4rem;
}
.drop-zone .dz-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #58A6FF;
    letter-spacing: 0.08em;
}
.drop-zone .dz-path {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #3FB950;
    background: #3FB95011;
    border: 1px solid #3FB95033;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    letter-spacing: 0.06em;
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

/* ── Job queue panel ── */
.job-queue-panel {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 0;
    overflow: hidden;
}
.jq-header {
    background: #161B22;
    padding: 0.65rem 1rem;
    border-bottom: 1px solid #21262D;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #484F58;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.job-row {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #21262D;
    cursor: pointer;
    transition: background .2s;
}
.job-row:last-child { border-bottom: none; }
.job-row:hover { background: #161B22; }
.job-row.selected { background: #58A6FF11; border-left: 3px solid #58A6FF; }
.jr-top {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.2rem;
}
.jr-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.15rem 0.45rem;
    border-radius: 20px;
    flex-shrink: 0;
}
.badge-pending    { background: #D2992220; color: #D29922; border: 1px solid #D2992244; }
.badge-processing { background: #58A6FF20; color: #58A6FF; border: 1px solid #58A6FF44; animation: pulse-badge 1.4s infinite; }
.badge-complete   { background: #3FB95020; color: #3FB950; border: 1px solid #3FB95044; }
.badge-failed     { background: #F8514920; color: #F85149; border: 1px solid #F8514944; }
.jr-name {
    font-size: 0.82rem;
    color: #C9D1D9;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
}
.jr-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #484F58;
}

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
.metric-chip .mc-value.accent  { color: #58A6FF; }
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
@keyframes pulse-badge {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.55; }
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
_DEFAULTS: Dict[str, Any] = {
    "selected_job_id": None,   # job_id currently shown in detail panel
}


def init_session_state() -> None:
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
#  API helpers
# ─────────────────────────────────────────────────────────────────────────────
def fetch_all_jobs() -> List[Dict[str, Any]]:
    try:
        r = httpx.get(f"{API_BASE_URL}/jobs", timeout=5.0)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return []
    except httpx.HTTPError:
        return []


def fetch_job(job_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = httpx.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=5.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def api_online() -> bool:
    try:
        r = httpx.get(f"{API_BASE_URL}/health", timeout=3.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False
    except httpx.ConnectError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  Elapsed time helper
# ─────────────────────────────────────────────────────────────────────────────
def _elapsed_seconds(job: Dict[str, Any]) -> Optional[float]:
    try:
        start = job.get("started_at")
        end   = job.get("completed_at")
        if start and end:
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            return (datetime.strptime(end, fmt) - datetime.strptime(start, fmt)).total_seconds()
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────────────────────────────────────
def render_header() -> None:
    st.markdown(
        """
        <div class="sc-header">
            <span class="wordmark">DealFlow</span>
            <span class="tagline">Multi-Agent Intelligence</span>
            <span class="version">v2.0 · Pipeline Mode</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Drop-zone notice (replaces the old upload widget)
# ─────────────────────────────────────────────────────────────────────────────
def render_drop_notice() -> None:
    st.markdown(
        """
        <div class="drop-zone">
            <span class="dz-icon">📂</span>
            <span class="dz-text">Drop Fireflies JSON transcripts into</span>
            <span class="dz-path">data/input/</span>
            <span class="dz-text">— they are picked up automatically every 3 s</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Job queue panel (left column)
# ─────────────────────────────────────────────────────────────────────────────
_STATUS_BADGE = {
    "pending":    ("pending",    "badge-pending"),
    "processing": ("processing", "badge-processing"),
    "complete":   ("complete",   "badge-complete"),
    "failed":     ("failed",     "badge-failed"),
}


def render_job_queue(jobs: List[Dict[str, Any]]) -> None:
    count = len(jobs)
    st.markdown(
        f'<div class="job-queue-panel">'
        f'  <div class="jq-header">▪ Job Queue &nbsp;·&nbsp; {count} job{"s" if count != 1 else ""}</div>',
        unsafe_allow_html=True,
    )

    if not jobs:
        st.markdown(
            '<div style="padding:1.2rem 1rem;font-family:IBM Plex Mono,monospace;'
            'font-size:.75rem;color:#484F58;">No jobs yet — drop a file to begin.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    selected = st.session_state.selected_job_id

    for job in jobs:
        job_id  = job["id"]
        status  = job.get("status", "pending")
        label, badge_cls = _STATUS_BADGE.get(status, (status, "badge-pending"))
        name    = job.get("source_file") or job.get("meeting_id") or job_id[:12]
        ts      = (job.get("created_at") or "")[:16].replace("T", " ")
        sel_cls = " selected" if job_id == selected else ""

        st.markdown(
            f'<div class="job-row{sel_cls}">'
            f'  <div class="jr-top">'
            f'    <span class="jr-badge {badge_cls}">{label}</span>'
            f'    <span class="jr-name" title="{name}">{name}</span>'
            f'  </div>'
            f'  <div class="jr-meta">{ts}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("View", key=f"view_{job_id}", use_container_width=True):
            st.session_state.selected_job_id = job_id
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Formatted content renderers (unchanged from original)
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

    comps = data.get("competitors", [])   # fixed: was "competitors_mentioned"
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
            f'  <div class="ft-action">{task.get("action_items","No action specified")}</div>'
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
    "agent_1_extraction": ("🔍", "EXTRACTOR",    "icon-blue",   "Topics · Pain Points · Competitors", "LAYER 1"),
    "agent_2_tickets":    ("📋", "TASKMAGE",     "icon-green",  "Action items & assignees",            "LAYER 1"),
    "agent_3_hubspot":    ("🏢", "HUBSPOT CRM",  "icon-orange", "Deal stage · Sentiment · CRM notes", "LAYER 2"),
    "agent_4_email":      ("✉️", "EMAIL CLOSER", "icon-purple", "Follow-up email draft",              "LAYER 2"),
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


# ─────────────────────────────────────────────────────────────────────────────
#  Job detail panel (right column)
# ─────────────────────────────────────────────────────────────────────────────
def render_job_detail(job: Dict[str, Any]) -> None:
    status  = job.get("status", "unknown")
    elapsed = _elapsed_seconds(job)

    # Metrics row
    result  = job.get("result") or {}
    topics  = len((result.get("agent_1_extraction") or {}).get("topics", []))
    tasks   = len((result.get("agent_2_tickets") or {}).get("tasks", []))
    n_agents = sum(
        1 for k in ["agent_1_extraction", "agent_2_tickets", "agent_3_hubspot", "agent_4_email"]
        if result.get(k) and not (result[k] or {}).get("error")
    )

    st.markdown(
        f"""
        <div class="metric-row fade-in">
            <div class="metric-chip">
                <span class="mc-label">Status</span>
                <span class="mc-value {'success' if status=='complete' else 'accent'}">{status.upper()}</span>
            </div>
            <div class="metric-chip">
                <span class="mc-label">Time</span>
                <span class="mc-value accent">{'%.1fs' % elapsed if elapsed else '—'}</span>
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

    if status == "failed":
        st.error(f"Job failed: {job.get('error_message', 'Unknown error')[:400]}")
        return

    if status in ("pending", "processing"):
        st.info(f"Job is **{status}** — results will appear here when complete.")
        return

    if not result:
        st.warning("Job completed but no result data found.")
        return

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
            payload = result.get(key)
            if payload and not (isinstance(payload, dict) and payload.get("error")):
                render_agent_card(key, payload)
            else:
                err = (payload or {}).get("error", "No data returned for this agent.")
                st.markdown(
                    f'<div style="color:#484F58;font-family:IBM Plex Mono,monospace;'
                    f'font-size:.8rem;padding:1rem;">{err}</div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    with st.expander("🗂  FULL OUTPUT JSON"):
        st.code(json.dumps(result, indent=2), language="json")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    init_session_state()
    render_header()
    render_drop_notice()

    # ── API connectivity check ────────────────────────────────────────────────
    if not api_online():
        st.warning(
            "API server is not reachable — start it with: "
            "`uvicorn api:app --host 0.0.0.0 --port 8000`"
        )

    # ── Fetch current job list ────────────────────────────────────────────────
    jobs = fetch_all_jobs()

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_queue, col_detail = st.columns([1, 2], gap="large")

    with col_queue:
        render_job_queue(jobs)

    with col_detail:
        selected_id = st.session_state.get("selected_job_id")
        if selected_id:
            job = fetch_job(selected_id)
            if job:
                render_job_detail(job)
            else:
                st.error(f"Could not load job `{selected_id[:12]}`.")
        else:
            st.markdown(
                '<div style="color:#484F58;font-family:IBM Plex Mono,monospace;'
                'font-size:.85rem;padding:2rem 1rem;">← Select a job from the queue to view results</div>',
                unsafe_allow_html=True,
            )

    # ── Auto-refresh while jobs are in flight ─────────────────────────────────
    active = any(j["status"] in ("pending", "processing") for j in jobs)
    if active:
        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    main()
