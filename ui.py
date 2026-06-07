import json
import logging
import time
from collections import defaultdict
from datetime import datetime
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
        .block-container { padding-top: 0rem; padding-bottom: 0rem; }
    </style>
"""
st.markdown(hide_elements, unsafe_allow_html=True)

st.set_page_config(
    page_title="DealFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Bebas+Neue&family=Barlow:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0A0C10 !important;
    color: #C9D1D9 !important;
}
.block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1400px;
    background: transparent !important;
}
section[data-testid="stSidebar"] { display: none !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0A0C10; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 4px; }

/* ── Header ── */
.sc-header {
    display: flex; align-items: baseline; gap: 1.2rem;
    margin-bottom: 2rem; border-bottom: 1px solid #21262D; padding-bottom: 1.25rem;
}
.sc-header .wordmark {
    font-family: 'Bebas Neue', sans-serif; font-size: 3rem;
    letter-spacing: 3px; color: #58A6FF; line-height: 1;
    text-shadow: 0 0 40px rgba(88,166,255,.35);
}
.sc-header .tagline {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #3FB950;
    letter-spacing: 0.12em; text-transform: uppercase; padding: 0.25rem 0.6rem;
    border: 1px solid #3FB95044; border-radius: 4px; background: #3FB95011;
}
.sc-header .version {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    color: #484F58; margin-left: auto;
}

/* ── Drop zone ── */
.drop-zone {
    background: #0D1117; border: 1.5px dashed #30363D; border-radius: 12px;
    padding: 1rem 2rem; margin-bottom: 1.5rem; display: flex;
    align-items: center; gap: 1rem;
}
.drop-zone .dz-icon { font-size: 1.4rem; }
.drop-zone .dz-text {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    color: #58A6FF; letter-spacing: 0.08em;
}
.drop-zone .dz-path {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #3FB950;
    background: #3FB95011; border: 1px solid #3FB95033; padding: 0.15rem 0.5rem;
    border-radius: 4px; letter-spacing: 0.06em;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
    font-weight: 600 !important; letter-spacing: 0.08em !important;
    border-radius: 6px !important; padding: 0.5rem 1.25rem !important;
    transition: all .2s ease !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background: transparent !important; color: #8B949E !important; border: 1px solid #30363D !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: #58A6FF !important; color: #58A6FF !important;
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.65rem !important;
    background: transparent !important; color: #484F58 !important;
    border: 1px solid #21262D !important; padding: 0.25rem 0.6rem !important;
    border-radius: 5px !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: #58A6FF !important; color: #58A6FF !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.7rem !important;
    letter-spacing: 0.07em !important; color: #484F58 !important;
    text-transform: uppercase !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58A6FF !important; border-bottom-color: #58A6FF !important;
}

/* ── Code / JSON ── */
.stCodeBlock { font-size: 0.76rem !important; }

/* ── Text area ── */
textarea {
    background: #010409 !important; color: #C9D1D9 !important;
    border: 1px solid #21262D !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important; border-radius: 8px !important;
}

/* ── Expander ── */
details { background: #0D1117 !important; border: 1px solid #21262D !important; border-radius: 8px !important; }
summary { color: #8B949E !important; font-size: 0.85rem !important; }

hr { border-color: #21262D !important; }

/* ── Job queue panel ── */
.job-queue-panel {
    background: #0D1117; border: 1px solid #21262D;
    border-radius: 12px; overflow: hidden;
}
.jq-header {
    background: #161B22; padding: 0.65rem 1rem; border-bottom: 1px solid #21262D;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #484F58;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.job-row {
    padding: 0.75rem 1rem; border-bottom: 1px solid #21262D;
    cursor: pointer; transition: background .2s;
}
.job-row:last-child { border-bottom: none; }
.job-row:hover { background: #161B22; }
.job-row.selected { background: #58A6FF11; border-left: 3px solid #58A6FF; }
.jr-top { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.2rem; }
.jr-badge {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; padding: 0.15rem 0.45rem;
    border-radius: 20px; flex-shrink: 0;
}
.badge-pending    { background: #D2992220; color: #D29922; border: 1px solid #D2992244; }
.badge-processing { background: #58A6FF20; color: #58A6FF; border: 1px solid #58A6FF44; animation: pulse-badge 1.4s infinite; }
.badge-complete   { background: #3FB95020; color: #3FB950; border: 1px solid #3FB95044; }
.badge-failed     { background: #F8514920; color: #F85149; border: 1px solid #F8514944; }
.jr-name {
    font-size: 0.82rem; color: #C9D1D9; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; max-width: 180px;
}
.jr-meta { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #484F58; }

/* ── Meeting header ── */
.meeting-header {
    background: #0D1117; border: 1px solid #21262D; border-radius: 12px;
    padding: 1.1rem 1.5rem; margin-bottom: 1.1rem;
    display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;
}
.mh-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.35rem;
    letter-spacing: 2px; color: #E6EDF3; flex: 1; min-width: 200px;
}
.mh-pill {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    color: #8B949E; background: #161B22; border: 1px solid #21262D;
    border-radius: 20px; padding: 0.2rem 0.65rem; white-space: nowrap;
}

/* ── Summary strip ── */
.summary-strip {
    display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1.25rem;
}
.ss-chip {
    background: #0D1117; border: 1px solid #21262D; border-radius: 8px;
    padding: 0.5rem 0.9rem; display: flex; flex-direction: column; gap: 0.1rem;
    min-width: 100px;
}
.ss-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem;
    color: #484F58; text-transform: uppercase; letter-spacing: 0.1em;
}
.ss-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem;
    font-weight: 600; color: #C9D1D9;
}
.ss-blue   { color: #58A6FF !important; }
.ss-green  { color: #3FB950 !important; }
.ss-yellow { color: #D29922 !important; }
.ss-red    { color: #F85149 !important; }

/* ── Agent section card ── */
.agent-section {
    background: #0D1117; border: 1px solid #21262D; border-radius: 12px;
    padding: 1.25rem 1.4rem; margin-bottom: 1rem;
}
.as-header {
    display: flex; align-items: center; gap: 0.7rem;
    margin-bottom: 0.9rem; padding-bottom: 0.75rem; border-bottom: 1px solid #21262D;
}
.as-icon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.icon-blue   { background: #58A6FF18; border: 1px solid #58A6FF33; }
.icon-green  { background: #3FB95018; border: 1px solid #3FB95033; }
.icon-orange { background: #D2992218; border: 1px solid #D2992233; }
.icon-purple { background: #BC8CFF18; border: 1px solid #BC8CFF33; }
.as-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem;
    letter-spacing: 1.5px; color: #E6EDF3;
}
.as-desc { font-size: 0.72rem; color: #484F58; margin-top: 0.05rem; }
.as-layer {
    margin-left: auto;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem;
    color: #3FB950; background: #3FB95011; border: 1px solid #3FB95033;
    padding: 0.18rem 0.5rem; border-radius: 20px;
}

/* ── Section sub-title ── */
.sub-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    text-transform: uppercase; letter-spacing: 0.12em; color: #484F58;
    margin: 0.85rem 0 0.45rem; padding-bottom: 0.25rem; border-bottom: 1px solid #21262D;
}

/* ── Extractor: topics ── */
.topic-row {
    display: flex; gap: 0.9rem;
    padding: 0.65rem 0; border-bottom: 1px solid #21262D1A;
}
.topic-row:last-child { border-bottom: none; }
.tr-num {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem;
    color: #484F58; padding-top: 0.1rem; min-width: 20px;
}
.tr-name { font-weight: 600; color: #E6EDF3; font-size: 0.86rem; margin-bottom: 0.15rem; }
.tr-summary { font-size: 0.79rem; color: #8B949E; line-height: 1.5; }

/* ── Extractor: pain points ── */
.pain-item {
    display: flex; align-items: flex-start; gap: 0.55rem;
    padding: 0.4rem 0; font-size: 0.82rem; color: #C9D1D9;
}
.pain-dot { color: #F85149; font-size: 0.55rem; margin-top: 0.35rem; flex-shrink: 0; }

/* ── Extractor: competitors ── */
.comp-chip {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #161B22; border: 1px solid #30363D; border-radius: 20px;
    padding: 0.22rem 0.65rem; font-size: 0.78rem; color: #8B949E;
    margin: 0.2rem 0.25rem 0 0;
}

/* ── Taskmage: assignee groups ── */
.assignee-header {
    display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;
}
.assignee-avatar {
    width: 26px; height: 26px; background: #58A6FF22; border: 1px solid #58A6FF44;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    color: #58A6FF; flex-shrink: 0;
}
.assignee-name {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
    font-weight: 600; color: #C9D1D9; text-transform: uppercase; letter-spacing: 0.06em;
}
.assignee-count {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: #484F58;
}
.task-card {
    background: #161B22; border: 1px solid #21262D; border-radius: 7px;
    padding: 0.65rem 0.85rem; margin-bottom: 0.35rem;
}
.task-action { font-size: 0.83rem; color: #C9D1D9; line-height: 1.45; }
.task-blocker {
    display: flex; align-items: flex-start; gap: 0.4rem; margin-top: 0.4rem;
    font-size: 0.75rem; color: #D29922; background: #D2992211;
    border: 1px solid #D2992233; border-radius: 5px; padding: 0.3rem 0.6rem;
}

/* ── HubSpot: deal pipeline ── */
.deal-pipeline {
    display: flex; align-items: center; margin: 0.6rem 0 1.1rem;
    overflow-x: auto; padding-bottom: 0.2rem;
}
.pipeline-node {
    display: flex; flex-direction: column; align-items: center;
    min-width: 72px; flex-shrink: 0;
}
.pd-dot {
    width: 10px; height: 10px; border-radius: 50%;
    margin-bottom: 0.3rem;
}
.pd-active   { background: #58A6FF; box-shadow: 0 0 10px #58A6FF88; border: 2px solid #79BAFF; }
.pd-passed   { background: #3FB950; border: 2px solid #3FB950; }
.pd-inactive { background: #21262D; border: 2px solid #30363D; }
.pn-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.56rem;
    text-align: center; letter-spacing: 0.03em; text-transform: uppercase;
}
.pn-active .pn-label   { color: #58A6FF; }
.pn-passed .pn-label   { color: #3FB950; }
.pn-inactive .pn-label { color: #484F58; }
.pc-line {
    flex: 1; height: 2px; min-width: 14px; margin-bottom: 1rem;
}
.pc-active   { background: #3FB950; }
.pc-inactive { background: #21262D; }

/* ── HubSpot: threat + sentiment ── */
.threat-badge {
    display: inline-block; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 0.2rem 0.65rem; border-radius: 20px;
}
.threat-low    { color: #3FB950; background: #3FB95018; border: 1px solid #3FB95044; }
.threat-medium { color: #D29922; background: #D2992218; border: 1px solid #D2992244; }
.threat-high   { color: #F85149; background: #F8514918; border: 1px solid #F8514944; }
.sentiment-box {
    background: #161B22; border: 1px solid #21262D; border-radius: 7px;
    padding: 0.65rem 0.9rem; font-size: 0.83rem; color: #C9D1D9; line-height: 1.5;
    margin-bottom: 0.75rem;
}
.crm-notes {
    background: #161B22; border: 1px solid #21262D; border-radius: 7px;
    padding: 0.75rem 0.9rem; font-size: 0.8rem; color: #8B949E; line-height: 1.65;
}

/* ── Email preview ── */
.email-preview { background: #161B22; border: 1px solid #21262D; border-radius: 8px; overflow: hidden; }
.ep-meta { background: #0D1117; padding: 0.7rem 1rem; border-bottom: 1px solid #21262D; }
.ep-field {
    display: flex; gap: 0.75rem; align-items: baseline;
    padding: 0.28rem 0; border-bottom: 1px solid #21262D22;
}
.ep-field:last-child { border-bottom: none; }
.ep-key {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: #484F58;
    text-transform: uppercase; letter-spacing: 0.08em; min-width: 60px; flex-shrink: 0;
}
.ep-val  { font-size: 0.83rem; color: #C9D1D9; }
.ep-subj { font-weight: 600; color: #E6EDF3; }

/* ── Animations ── */
@keyframes pulse-badge { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
.fade-in { animation: fadeIn .35s ease forwards; }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Session state
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS: Dict[str, Any] = {
    "selected_job_id": None,
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
    except Exception:
        return []


def fetch_job(job_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = httpx.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=5.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def api_online() -> bool:
    try:
        r = httpx.get(f"{API_BASE_URL}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _elapsed(job: Dict[str, Any]) -> Optional[float]:
    try:
        s, e = job.get("started_at"), job.get("completed_at")
        if s and e:
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            return (datetime.strptime(e, fmt) - datetime.strptime(s, fmt)).total_seconds()
    except Exception:
        pass
    return None


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


# ─────────────────────────────────────────────────────────────────────────────
#  Header & drop zone
# ─────────────────────────────────────────────────────────────────────────────
def render_header() -> None:
    st.markdown(
        '<div class="sc-header">'
        '  <span class="wordmark">DealFlow</span>'
        '  <span class="tagline">Multi-Agent Intelligence</span>'
        '  <span class="version">v2.0 · Pipeline Mode</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_drop_notice() -> None:
    st.markdown(
        '<div class="drop-zone">'
        '  <span class="dz-icon">📂</span>'
        '  <span class="dz-text">Drop Fireflies JSON transcripts into</span>'
        '  <span class="dz-path">data/input/</span>'
        '  <span class="dz-text">— picked up automatically every 3 s</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Job queue panel
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
        job_id = job["id"]
        status = job.get("status", "pending")
        label, badge_cls = _STATUS_BADGE.get(status, (status, "badge-pending"))
        name   = job.get("source_file") or job.get("meeting_id") or job_id[:12]
        ts     = (job.get("created_at") or "")[:16].replace("T", " ")
        sel    = " selected" if job_id == selected else ""
        st.markdown(
            f'<div class="job-row{sel}">'
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
#  Meeting header + summary strip
# ─────────────────────────────────────────────────────────────────────────────
def render_meeting_header(result: dict, job: dict) -> None:
    meta     = result.get("metadata") or {}
    title    = meta.get("title") or job.get("source_file") or "Untitled Meeting"
    date     = (meta.get("recording_at") or job.get("created_at") or "")[:10]
    duration = meta.get("duration_minutes")
    company  = meta.get("customer_company") or ""
    call_t   = meta.get("call_type") or ""

    pills = ""
    if date:
        pills += f'<span class="mh-pill">📅 {date}</span>'
    if duration:
        pills += f'<span class="mh-pill">⏱ {duration} min</span>'
    if company:
        pills += f'<span class="mh-pill">🏢 {company}</span>'
    if call_t:
        pills += f'<span class="mh-pill">📞 {call_t}</span>'

    st.markdown(
        f'<div class="meeting-header fade-in">'
        f'  <div class="mh-title">{title}</div>'
        f'  {pills}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_summary_strip(result: dict, job: dict) -> None:
    extraction = result.get("agent_1_extraction") or {}
    tickets    = result.get("agent_2_tickets") or {}
    hubspot    = result.get("agent_3_hubspot") or {}

    n_topics   = len(extraction.get("topics", []))
    n_pain     = len(extraction.get("pain_points", []))
    n_comps    = len(extraction.get("competitors", []))
    n_tasks    = len(tickets.get("tasks", []))
    deal_stage = hubspot.get("deal_stage_recommendation") or "—"
    threat     = hubspot.get("competitor_threat_level") or "—"
    elapsed    = _elapsed(job)

    threat_color = {"Low": "ss-green", "Medium": "ss-yellow", "High": "ss-red"}.get(threat, "")

    st.markdown(
        f"""
        <div class="summary-strip fade-in">
            <div class="ss-chip">
                <span class="ss-label">Topics</span>
                <span class="ss-value ss-blue">{n_topics}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Pain Points</span>
                <span class="ss-value">{n_pain}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Competitors</span>
                <span class="ss-value">{n_comps}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Tasks</span>
                <span class="ss-value ss-green">{n_tasks}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Deal Stage</span>
                <span class="ss-value ss-blue" style="font-size:0.78rem;">{deal_stage}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Threat Level</span>
                <span class="ss-value {threat_color}">{threat}</span>
            </div>
            <div class="ss-chip">
                <span class="ss-label">Process Time</span>
                <span class="ss-value">{'%.1fs' % elapsed if elapsed else '—'}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Agent section header helper
# ─────────────────────────────────────────────────────────────────────────────
def _section_header(icon: str, title: str, desc: str, icon_cls: str, layer: str) -> None:
    st.markdown(
        f'<div class="agent-section" style="padding-bottom:0; border:none; background:transparent;">'
        f'  <div class="as-header">'
        f'    <div class="as-icon {icon_cls}">{icon}</div>'
        f'    <div>'
        f'      <div class="as-title">{title}</div>'
        f'      <div class="as-desc">{desc}</div>'
        f'    </div>'
        f'    <span class="as-layer">{layer}</span>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Agent 1 — Extractor
# ─────────────────────────────────────────────────────────────────────────────
def render_extractor(data: dict) -> None:
    st.markdown('<div class="agent-section fade-in">', unsafe_allow_html=True)

    # Header
    st.markdown(
        '<div class="as-header">'
        '  <div class="as-icon icon-blue">🔍</div>'
        '  <div><div class="as-title">EXTRACTOR</div>'
        '  <div class="as-desc">Topics · Pain Points · Competitors</div></div>'
        '  <span class="as-layer">LAYER 1</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "extractor.json", "application/json", key="dl_extractor")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        # Topics
        topics = data.get("topics", [])
        if topics:
            st.markdown(f'<div class="sub-title">Topics Discussed &nbsp;({len(topics)})</div>', unsafe_allow_html=True)
            rows = "".join(
                f'<div class="topic-row">'
                f'  <div class="tr-num">0{i}</div>'
                f'  <div><div class="tr-name">{t.get("topic_name","—")}</div>'
                f'  <div class="tr-summary">{t.get("summary","")}</div></div>'
                f'</div>'
                for i, t in enumerate(topics, 1)
            )
            st.markdown(rows, unsafe_allow_html=True)

        # Pain points
        pain = data.get("pain_points", [])
        if pain:
            st.markdown(f'<div class="sub-title">Pain Points &nbsp;({len(pain)})</div>', unsafe_allow_html=True)
            items = "".join(
                f'<div class="pain-item"><span class="pain-dot">●</span><span>{p}</span></div>'
                for p in pain
            )
            st.markdown(items, unsafe_allow_html=True)

        # Competitors
        comps = data.get("competitors", [])
        if comps:
            st.markdown(f'<div class="sub-title">Competitors Mentioned &nbsp;({len(comps)})</div>', unsafe_allow_html=True)
            chips = "".join(f'<span class="comp-chip">⚔ {c}</span>' for c in comps)
            st.markdown(chips, unsafe_allow_html=True)

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Agent 2 — Taskmage (grouped by assignee)
# ─────────────────────────────────────────────────────────────────────────────
def render_taskmage(data: dict) -> None:
    st.markdown('<div class="agent-section fade-in">', unsafe_allow_html=True)

    tasks = data.get("tasks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    # Group by assignee
    grouped: Dict[str, list] = defaultdict(list)
    for task in tasks:
        grouped[task.get("assignee", "Unknown")].append(task)

    st.markdown(
        '<div class="as-header">'
        '  <div class="as-icon icon-green">📋</div>'
        '  <div><div class="as-title">TASKMAGE</div>'
        f'  <div class="as-desc">{len(tasks)} action item{"s" if len(tasks)!=1 else ""}'
        f' · {len(grouped)} assignee{"s" if len(grouped)!=1 else ""}</div></div>'
        '  <span class="as-layer">LAYER 1</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "taskmage.json", "application/json", key="dl_taskmage")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        if not tasks:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:.5rem 0;">No tasks generated.</div>', unsafe_allow_html=True)
        for assignee, atasks in grouped.items():
            initials = _initials(assignee)
            count    = len(atasks)
            st.markdown(
                f'<div style="margin-bottom:1rem;">'
                f'  <div class="assignee-header">'
                f'    <div class="assignee-avatar">{initials}</div>'
                f'    <span class="assignee-name">{assignee}</span>'
                f'    <span class="assignee-count">{count} task{"s" if count!=1 else ""}</span>'
                f'  </div>',
                unsafe_allow_html=True,
            )
            for task in atasks:
                blocker_html = (
                    f'<div class="task-blocker">🚧 {task["blocker"]}</div>'
                    if task.get("blocker") else ""
                )
                st.markdown(
                    f'<div class="task-card">'
                    f'  <div class="task-action">{task.get("action_items","—")}</div>'
                    f'  {blocker_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Agent 3 — HubSpot CRM (pipeline + threat + sentiment + notes)
# ─────────────────────────────────────────────────────────────────────────────
_DEAL_STAGES = ["Discovery", "Demo/Validation", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]


def _pipeline_html(current: str) -> str:
    current_lower = (current or "").lower()

    # Find the active index
    active_idx = next(
        (i for i, s in enumerate(_DEAL_STAGES) if s.lower() in current_lower or current_lower in s.lower()),
        -1,
    )

    nodes = []
    for i, stage in enumerate(_DEAL_STAGES):
        if i < active_idx:
            node_cls, dot_cls, line_cls = "pn-passed", "pd-passed", "pc-active"
        elif i == active_idx:
            node_cls, dot_cls, line_cls = "pn-active", "pd-active", "pc-active"
        else:
            node_cls, dot_cls, line_cls = "pn-inactive", "pd-inactive", "pc-inactive"

        nodes.append(
            f'<div class="pipeline-node {node_cls}">'
            f'  <div class="pd-dot {dot_cls}"></div>'
            f'  <div class="pn-label">{stage}</div>'
            f'</div>'
        )
        if i < len(_DEAL_STAGES) - 1:
            nodes.append(f'<div class="pc-line {line_cls}"></div>')

    return f'<div class="deal-pipeline">{"".join(nodes)}</div>'


def render_hubspot(data: dict) -> None:
    st.markdown('<div class="agent-section fade-in">', unsafe_allow_html=True)

    deal_stage = data.get("deal_stage_recommendation", "—")
    sentiment  = data.get("perceived_sentiment", "—")
    threat     = data.get("competitor_threat_level", "—")
    notes      = data.get("hubspot_notes_body", "—")
    threat_cls = {"Low": "threat-low", "Medium": "threat-medium", "High": "threat-high"}.get(threat, "threat-medium")

    st.markdown(
        '<div class="as-header">'
        '  <div class="as-icon icon-orange">🏢</div>'
        '  <div><div class="as-title">HUBSPOT CRM</div>'
        '  <div class="as-desc">Deal stage · Sentiment · CRM notes</div></div>'
        '  <span class="as-layer">LAYER 2</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "hubspot.json", "application/json", key="dl_hubspot")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        # Deal stage pipeline
        st.markdown('<div class="sub-title">Deal Stage Pipeline</div>', unsafe_allow_html=True)
        st.markdown(_pipeline_html(deal_stage), unsafe_allow_html=True)

        # Threat + Sentiment side by side
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="sub-title">Competitor Threat</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="threat-badge {threat_cls}">{threat}</span>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="sub-title">Sentiment</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sentiment-box">{sentiment}</div>', unsafe_allow_html=True)

        # CRM notes
        st.markdown('<div class="sub-title">CRM Notes</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="crm-notes">{notes}</div>', unsafe_allow_html=True)

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Agent 4 — Email (preview-style)
# ─────────────────────────────────────────────────────────────────────────────
def render_email(data: dict) -> None:
    st.markdown('<div class="agent-section fade-in">', unsafe_allow_html=True)

    recipient = data.get("recipient_email", "—")
    subject   = data.get("email_subject", "—")
    body      = data.get("email_body", "")

    st.markdown(
        '<div class="as-header">'
        '  <div class="as-icon icon-purple">✉️</div>'
        '  <div><div class="as-title">EMAIL CLOSER</div>'
        '  <div class="as-desc">Follow-up email draft</div></div>'
        '  <span class="as-layer">LAYER 2</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "email.json", "application/json", key="dl_email")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        # Email header fields
        st.markdown(
            f'<div class="email-preview">'
            f'  <div class="ep-meta">'
            f'    <div class="ep-field">'
            f'      <span class="ep-key">To</span>'
            f'      <span class="ep-val">{recipient}</span>'
            f'    </div>'
            f'    <div class="ep-field">'
            f'      <span class="ep-key">Subject</span>'
            f'      <span class="ep-val ep-subj">{subject}</span>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sub-title" style="margin-top:.75rem;">Body</div>', unsafe_allow_html=True)
        # text_area allows easy select-all + copy
        st.text_area(
            label="email_body",
            value=body,
            height=320,
            label_visibility="collapsed",
            key="email_body_area",
        )

        # Plain-text download
        st.download_button(
            "⬇ Download .txt",
            data=f"To: {recipient}\nSubject: {subject}\n\n{body}",
            file_name="email_draft.txt",
            mime="text/plain",
            key="dl_email_txt",
        )

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Job detail panel (right column)
# ─────────────────────────────────────────────────────────────────────────────
def render_job_detail(job: Dict[str, Any]) -> None:
    status = job.get("status", "unknown")
    result = job.get("result") or {}

    if status == "failed":
        st.error(f"**Job failed** — {job.get('error_message', 'Unknown error')[:600]}")
        return

    if status in ("pending", "processing"):
        st.info(f"Job is **{status}** — results will appear here when complete.")
        return

    if not result:
        st.warning("Job completed but no result data was found.")
        return

    render_meeting_header(result, job)
    render_summary_strip(result, job)
    st.divider()

    # ── 2×2 agent grid ────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2, gap="medium")

    with col_l:
        ext = result.get("agent_1_extraction")
        if ext and not ext.get("error"):
            render_extractor(ext)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">Extractor — no data</div>', unsafe_allow_html=True)

    with col_r:
        tmg = result.get("agent_2_tickets")
        if tmg and not tmg.get("error"):
            render_taskmage(tmg)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">Taskmage — no data</div>', unsafe_allow_html=True)

    col_l2, col_r2 = st.columns(2, gap="medium")

    with col_l2:
        hs = result.get("agent_3_hubspot")
        if hs and not hs.get("error"):
            render_hubspot(hs)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">HubSpot — no data</div>', unsafe_allow_html=True)

    with col_r2:
        em = result.get("agent_4_email")
        if em and not em.get("error"):
            render_email(em)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">Email — no data</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("🗂  Full Pipeline Output — JSON"):
        st.code(json.dumps(result, indent=2), language="json")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    init_session_state()
    render_header()
    render_drop_notice()

    if not api_online():
        st.warning(
            "API server not reachable — start it with: "
            "`uvicorn api:app --host 0.0.0.0 --port 8000`"
        )

    jobs = fetch_all_jobs()

    col_queue, col_detail = st.columns([1, 3], gap="large")

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

    # Auto-refresh while jobs are in flight
    if any(j["status"] in ("pending", "processing") for j in jobs):
        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    main()
