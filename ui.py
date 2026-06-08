import json
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st

from core.config import API_BASE_URL

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
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0A0C10; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 4px; }

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

div[data-testid="stDownloadButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.65rem !important;
    background: transparent !important; color: #484F58 !important;
    border: 1px solid #21262D !important; padding: 0.25rem 0.6rem !important;
    border-radius: 5px !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: #58A6FF !important; color: #58A6FF !important;
}

div[data-testid="stTabs"] button {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.7rem !important;
    letter-spacing: 0.07em !important; color: #484F58 !important;
    text-transform: uppercase !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58A6FF !important; border-bottom-color: #58A6FF !important;
}

.stCodeBlock { font-size: 0.76rem !important; }

textarea {
    background: #010409 !important; color: #C9D1D9 !important;
    border: 1px solid #21262D !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important; border-radius: 8px !important;
}

details { background: #0D1117 !important; border: 1px solid #21262D !important; border-radius: 8px !important; }
summary { color: #8B949E !important; font-size: 0.85rem !important; }

hr { border-color: #21262D !important; }

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

.agent-section {
    background: #0D1117; border: 1px solid #21262D; border-radius: 12px;
    padding: 1.25rem 1.4rem; margin-bottom: 1rem;
}

.sub-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    text-transform: uppercase; letter-spacing: 0.12em; color: #484F58;
    margin: 0.85rem 0 0.45rem; padding-bottom: 0.25rem; border-bottom: 1px solid #21262D;
}

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

.pain-item {
    display: flex; align-items: flex-start; gap: 0.55rem;
    padding: 0.4rem 0; font-size: 0.82rem; color: #C9D1D9;
}
.pain-dot { color: #F85149; font-size: 0.55rem; margin-top: 0.35rem; flex-shrink: 0; }

.comp-chip {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #161B22; border: 1px solid #30363D; border-radius: 20px;
    padding: 0.22rem 0.65rem; font-size: 0.78rem; color: #8B949E;
    margin: 0.2rem 0.25rem 0 0;
}

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

.deal-pipeline {
    display: flex; align-items: center; margin: 0.6rem 0 1.1rem;
    overflow-x: auto; padding-bottom: 0.2rem;
}
.pipeline-node {
    display: flex; flex-direction: column; align-items: center;
    min-width: 72px; flex-shrink: 0;
}
.pd-dot { width: 10px; height: 10px; border-radius: 50%; margin-bottom: 0.3rem; }
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
.pc-line { flex: 1; height: 2px; min-width: 14px; margin-bottom: 1rem; }
.pc-active   { background: #3FB950; }
.pc-inactive { background: #21262D; }

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

@keyframes pulse-badge { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
.fade-in { animation: fadeIn .35s ease forwards; }
</style>
"""

st.set_page_config(
    page_title="DealFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(STYLES, unsafe_allow_html=True)


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


def render_meeting_header(result: dict, job: dict) -> None:
    meta = result.get("metadata") or {}
    title = meta.get("title") or job.get("source_file") or "Untitled Meeting"
    date = (meta.get("recording_at") or job.get("created_at") or "")[:10]
    duration = meta.get("duration_minutes")
    company = meta.get("customer_company") or ""
    call_t = meta.get("call_type") or ""

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
    tickets = result.get("agent_2_tickets") or {}
    hubspot = result.get("agent_3_hubspot") or {}

    n_topics = len(extraction.get("topics", []))
    n_pain = len(extraction.get("pain_points", []))
    n_comps = len(extraction.get("competitors", []))
    n_tasks = len(tickets.get("tasks", []))
    deal_stage = hubspot.get("deal_stage_recommendation") or "—"
    threat = hubspot.get("competitor_threat_level") or "—"
    elapsed = _elapsed(job)
    threat_color = {"Low": "ss-green", "Medium": "ss-yellow", "High": "ss-red"}.get(threat, "")

    st.markdown(
        f"""
        <div class="summary-strip fade-in">
            <div class="ss-chip"><span class="ss-label">Topics</span><span class="ss-value ss-blue">{n_topics}</span></div>
            <div class="ss-chip"><span class="ss-label">Pain Points</span><span class="ss-value">{n_pain}</span></div>
            <div class="ss-chip"><span class="ss-label">Competitors</span><span class="ss-value">{n_comps}</span></div>
            <div class="ss-chip"><span class="ss-label">Tasks</span><span class="ss-value ss-green">{n_tasks}</span></div>
            <div class="ss-chip"><span class="ss-label">Deal Stage</span><span class="ss-value ss-blue" style="font-size:0.78rem;">{deal_stage}</span></div>
            <div class="ss-chip"><span class="ss-label">Threat Level</span><span class="ss-value {threat_color}">{threat}</span></div>
            <div class="ss-chip"><span class="ss-label">Process Time</span><span class="ss-value">{'%.1fs' % elapsed if elapsed else '—'}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_extractor(data: dict, uid: str) -> None:
    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "extractor.json", "application/json", key=f"dl_extractor_{uid}")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        topics = data.get("topics", [])
        if topics:
            st.markdown(f'<div class="sub-title">Topics Discussed &nbsp;({len(topics)})</div>', unsafe_allow_html=True)
            rows = "".join(
                f'<div class="topic-row">'
                f'  <div class="tr-num">0{i}</div>'
                f'  <div><div class="tr-name">{t.get("topic_name", "—")}</div>'
                f'  <div class="tr-summary">{t.get("summary", "")}</div></div>'
                f'</div>'
                for i, t in enumerate(topics, 1)
            )
            st.markdown(rows, unsafe_allow_html=True)

        pain = data.get("pain_points", [])
        if pain:
            st.markdown(f'<div class="sub-title">Pain Points &nbsp;({len(pain)})</div>', unsafe_allow_html=True)
            st.markdown(
                "".join(f'<div class="pain-item"><span class="pain-dot">●</span><span>{p}</span></div>' for p in pain),
                unsafe_allow_html=True,
            )

        comps = data.get("competitors", [])
        if comps:
            st.markdown(f'<div class="sub-title">Competitors Mentioned &nbsp;({len(comps)})</div>', unsafe_allow_html=True)
            st.markdown(
                "".join(f'<span class="comp-chip">⚔ {c}</span>' for c in comps),
                unsafe_allow_html=True,
            )

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")


def render_taskmage(data: dict, uid: str) -> None:
    tasks = data.get("tasks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    grouped: Dict[str, list] = defaultdict(list)
    for task in tasks:
        grouped[task.get("assignee", "Unknown")].append(task)

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "taskmage.json", "application/json", key=f"dl_taskmage_{uid}")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        if not tasks:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:.5rem 0;">No tasks generated.</div>', unsafe_allow_html=True)

        for assignee, atasks in grouped.items():
            count = len(atasks)
            st.markdown(
                f'<div style="margin-bottom:1rem;">'
                f'  <div class="assignee-header">'
                f'    <div class="assignee-avatar">{_initials(assignee)}</div>'
                f'    <span class="assignee-name">{assignee}</span>'
                f'    <span class="assignee-count">{count} task{"s" if count != 1 else ""}</span>'
                f'  </div>',
                unsafe_allow_html=True,
            )
            for task in atasks:
                blocker_html = f'<div class="task-blocker">🚧 {task["blocker"]}</div>' if task.get("blocker") else ""
                st.markdown(
                    f'<div class="task-card">'
                    f'  <div class="task-action">{task.get("action_items", "—")}</div>'
                    f'  {blocker_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")


_DEAL_STAGES = ["Discovery", "Demo/Validation", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]


def _pipeline_html(current: str) -> str:
    current_lower = (current or "").lower()
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


def render_hubspot(data: dict, uid: str) -> None:
    deal_stage = data.get("deal_stage_recommendation", "—")
    sentiment = data.get("perceived_sentiment", "—")
    threat = data.get("competitor_threat_level", "—")
    notes = data.get("hubspot_notes_body", "—")
    threat_cls = {"Low": "threat-low", "Medium": "threat-medium", "High": "threat-high"}.get(threat, "threat-medium")

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "hubspot.json", "application/json", key=f"dl_hubspot_{uid}")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        st.markdown('<div class="sub-title">Deal Stage Pipeline</div>', unsafe_allow_html=True)
        st.markdown(_pipeline_html(deal_stage), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="sub-title">Competitor Threat</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="threat-badge {threat_cls}">{threat}</span>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="sub-title">Sentiment</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sentiment-box">{sentiment}</div>', unsafe_allow_html=True)

        st.markdown('<div class="sub-title">CRM Notes</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="crm-notes">{notes}</div>', unsafe_allow_html=True)

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")


def render_email(data: dict, uid: str) -> None:
    recipient = data.get("recipient_email", "—")
    subject = data.get("email_subject", "—")
    body = data.get("email_body", "")

    col_dl, _ = st.columns([1, 6])
    with col_dl:
        st.download_button("⬇ JSON", json.dumps(data, indent=2),
                           "email.json", "application/json", key=f"dl_email_{uid}")

    tab_fmt, tab_raw = st.tabs(["Formatted", "Raw JSON"])

    with tab_fmt:
        st.markdown(
            f'<div class="email-preview">'
            f'  <div class="ep-meta">'
            f'    <div class="ep-field"><span class="ep-key">To</span><span class="ep-val">{recipient}</span></div>'
            f'    <div class="ep-field"><span class="ep-key">Subject</span><span class="ep-val ep-subj">{subject}</span></div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sub-title" style="margin-top:.75rem;">Body</div>', unsafe_allow_html=True)
        st.text_area(label="email_body", value=body, height=320,
                     label_visibility="collapsed", key=f"email_body_{uid}")
        st.download_button(
            "⬇ Download .txt",
            data=f"To: {recipient}\nSubject: {subject}\n\n{body}",
            file_name="email_draft.txt",
            mime="text/plain",
            key=f"dl_email_txt_{uid}",
        )

    with tab_raw:
        st.code(json.dumps(data, indent=2), language="json")


def render_job_tab(job: Dict[str, Any]) -> None:
    status = job.get("status", "unknown")
    uid = job["id"][:8]

    if status == "pending":
        st.info("Queued — waiting for a worker to pick this up.")
        return

    if status == "processing":
        st.info("Processing — agents are running...")
        return

    if status == "failed":
        st.error(f"Failed — {job.get('error_message', 'Unknown error')[:600]}")
        return

    if status == "dead":
        st.error(f"Dead — exhausted all retries. {job.get('error_message', '')[:600]}")
        return

    full_job = fetch_job(job["id"])
    if not full_job:
        st.error("Could not load job details.")
        return

    result = full_job.get("result") or {}
    if not result:
        st.warning("Job completed but no result data found.")
        return

    render_meeting_header(result, full_job)
    render_summary_strip(result, full_job)
    st.divider()

    # Inner tabs — one per agent
    tab_ext, tab_tasks, tab_hs, tab_email = st.tabs([
        "🔍  Extraction", "📋  Tasks", "🏢  HubSpot CRM", "✉️  Email",
    ])

    with tab_ext:
        ext = result.get("agent_1_extraction")
        if ext and not ext.get("error"):
            render_extractor(ext, uid)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">No extraction data.</div>', unsafe_allow_html=True)

    with tab_tasks:
        tmg = result.get("agent_2_tickets")
        if tmg and not tmg.get("error"):
            render_taskmage(tmg, uid)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">No task data.</div>', unsafe_allow_html=True)

    with tab_hs:
        hs = result.get("agent_3_hubspot")
        if hs and not hs.get("error"):
            render_hubspot(hs, uid)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">No HubSpot data.</div>', unsafe_allow_html=True)

    with tab_email:
        em = result.get("agent_4_email")
        if em and not em.get("error"):
            render_email(em, uid)
        else:
            st.markdown('<div style="color:#484F58;font-size:.8rem;padding:1rem;">No email data.</div>', unsafe_allow_html=True)

    with st.expander("🗂  Full Pipeline Output — JSON"):
        st.code(json.dumps(result, indent=2), language="json")


def main() -> None:
    render_header()
    render_drop_notice()

    if not api_online():
        st.warning("API server not reachable — start it with: `uvicorn api:app --host 0.0.0.0 --port 8000`")
        return

    jobs = fetch_all_jobs()

    if not jobs:
        st.markdown(
            '<div style="color:#484F58;font-family:IBM Plex Mono,monospace;font-size:.85rem;padding:2rem 1rem;">'
            'No transcripts yet — drop a JSON file into data/input/ to begin.'
            '</div>',
            unsafe_allow_html=True,
        )
        time.sleep(3)
        st.rerun()
        return

    tab_labels = [job.get("source_file") or job["id"][:12] for job in jobs]
    tabs = st.tabs(tab_labels)

    for tab, job in zip(tabs, jobs):
        with tab:
            render_job_tab(job)

    if any(j["status"] in ("pending", "processing") for j in jobs):
        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    main()
