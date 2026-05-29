import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime

from orchestrator import SalesCopilotOrchestrator

st.set_page_config(
    page_title="Sales Copilot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .agent-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1E88E5;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-processing { background: #fff3cd; color: #856404; }
    .status-complete { background: #d4edda; color: #155724; }
    .status-error { background: #f8d7da; color: #721c24; }
    .status-pending { background: #e2e3e5; color: #383d42; }
    .status-running { background: #cfe2ff; color: #084298; }
    .progress-container {
        background: #f0f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .layer-indicator {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 0.5rem 0;
    }
    .layer-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ccc;
    }
    .layer-dot.active { background: #1E88E5; }
    .layer-dot.complete { background: #28a745; }
    .layer-label { font-weight: 500; color: #555; }
    .expandable-content {
        background: #fafafa;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .json-view {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
    }
    div[data-testid="stTab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "results" not in st.session_state:
        st.session_state.results = None
    if "processing_time" not in st.session_state:
        st.session_state.processing_time = None
    if "layer_status" not in st.session_state:
        st.session_state.layer_status = {"layer1": "pending", "layer2": "pending"}

def reset_state():
    st.session_state.processing = False
    st.session_state.results = None
    st.session_state.processing_time = None
    st.session_state.layer_status = {"layer1": "pending", "layer2": "pending"}

def render_progress_section():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Processing Status")
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)

        layer1_col, layer2_col = st.columns(2)
        with layer1_col:
            dot_class = "complete" if st.session_state.layer_status["layer1"] == "complete" else "active" if st.session_state.layer_status["layer1"] == "running" else ""
            st.markdown(f'<div class="layer-indicator"><span class="layer-dot {dot_class}"></span><span class="layer-label">Layer 1: Extractor + Taskmage</span><span class="status-badge status-{st.session_state.layer_status["layer1"]}">{st.session_state.layer_status["layer1"].upper()}</span></div>', unsafe_allow_html=True)
        with layer2_col:
            dot_class = "complete" if st.session_state.layer_status["layer2"] == "complete" else "active" if st.session_state.layer_status["layer2"] == "running" else ""
            st.markdown(f'<div class="layer-indicator"><span class="layer-dot {dot_class}"></span><span class="layer-label">Layer 2: HubSpot + Email</span><span class="status-badge status-{st.session_state.layer_status["layer2"]}">{st.session_state.layer_status["layer2"].upper()}</span></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.session_state.processing_time:
            st.metric("Processing Time", f"{st.session_state.processing_time:.1f}s")

def render_agent_card(agent_name: str, icon: str, data: dict, description: str):
    with st.expander(f"{icon} {agent_name}", expanded=True):
        st.markdown(f"**{description}**")

        col1, col2 = st.columns([1, 4])
        with col1:
            st.code(json.dumps(data, indent=2)[:100] + "... (click tabs for full view)")
        with col2:
            download_key = f"download_{agent_name}"
            st.download_button(
                "Download JSON",
                json.dumps(data, indent=2),
                f"{agent_name.lower().replace(' ', '_')}.json",
                key=download_key
            )

        st.markdown('<div class="expandable-content">', unsafe_allow_html=True)

        tab_json, tab_formatted = st.tabs(["Raw JSON", "Formatted View"])

        with tab_json:
            st.code(json.dumps(data, indent=2), language="json")

        with tab_formatted:
            render_formatted_output(agent_name, data)

        st.markdown('</div>', unsafe_allow_html=True)

def render_formatted_output(agent_name: str, data: dict):
    if agent_name == "Agent 1: Extractor":
        if "topics" in data:
            for i, topic in enumerate(data.get("topics", [])):
                st.markdown(f"**Topic {i+1}: {topic.get('topic_name', 'N/A')}**")
                st.write(topic.get("summary", ""))
                st.divider()

        st.markdown("**Pain Points:**")
        for point in data.get("pain_points", []):
            st.markdown(f"- {point}")

        st.markdown("**Competitors Mentioned:**")
        for comp in data.get("competitors_mentioned", []):
            st.markdown(f"- {comp}")

    elif agent_name == "Agent 2: Taskmage":
        tasks = data.get("tasks", data) if isinstance(data, dict) else data
        if not isinstance(tasks, list):
            tasks = [tasks]

        for i, task in enumerate(tasks):
            assignee = task.get("assignee", "Unknown")
            action = task.get("action_item", "No action")
            blocker = task.get("blocker")

            st.markdown(f"**Task {i+1} - Assignee: {assignee}**")
            st.write(action)
            if blocker:
                st.warning(f"Blocker: {blocker}")
            st.divider()

    elif agent_name == "Agent 3: HubSpot":
        st.markdown(f"**Deal Stage:** {data.get('deal_stage_recommendation', 'N/A')}")
        st.markdown(f"**Sentiment:** {data.get('perceived_sentiment', 'N/A')}")

        threat = data.get('competitor_threat_level', 'Low')
        threat_color = "High" if threat == "High" else "Medium" if threat == "Medium" else "Low"
        st.markdown(f"**Competitor Threat:** {threat_color}")

        st.markdown("**CRM Notes:**")
        st.write(data.get('hubspot_notes_body', 'N/A'))

    elif agent_name == "Agent 4: Email Closer":
        st.markdown(f"**To:** {data.get('recipient_email', 'N/A')}")
        st.markdown(f"**Subject:** {data.get('email_subject', 'N/A')}")

        st.markdown("**Email Body:**")
        email_body = data.get('email_body', 'N/A')
        st.text_area("", email_body, height=300, label_visibility="collapsed", key=f"email_body_{agent_name}")

def main():
    init_session_state()

    st.markdown('<p class="main-header">Sales Copilot - Multi-Agent Analysis</p>', unsafe_allow_html=True)

    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### Upload Transcript")

    uploaded_file = st.file_uploader(
        "Drop a Fireflies JSON file here",
        type=["json"],
        help="Upload your Fireflies.ai transcript export in JSON format"
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        process_button = st.button("Analyze", type="primary", disabled=st.session_state.processing)
    with col2:
        if st.button("Clear"):
            reset_state()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.processing or st.session_state.results:
        render_progress_section()

    if process_button and uploaded_file:
        try:
            json_data = json.load(uploaded_file)

            if "meeting_id" not in json_data and "transcript" not in json_data:
                st.error("Invalid file format. Please upload a valid Fireflies JSON transcript.")
                return

            st.session_state.processing = True

            progress_bar = st.progress(0, text="Initializing...")
            status_text = st.empty()

            import asyncio
            orchestrator = SalesCopilotOrchestrator()
            start_time = time.time()

            progress_bar.progress(0.1, text="Running Layer 1: Extraction + Task Assignments...")
            st.session_state.layer_status["layer1"] = "running"

            async def run_analysis():
                result = await orchestrator.process_transcript(json_data)
                return result

            result = asyncio.run(run_analysis())

            progress_bar.progress(0.5, text="Layer 1 Complete. Running Layer 2...")
            st.session_state.layer_status["layer1"] = "complete"

            progress_bar.progress(0.7, text="Running Layer 2: CRM + Email Generation...")
            st.session_state.layer_status["layer2"] = "running"

            progress_bar.progress(1.0, text="Analysis Complete!")

            st.session_state.results = result
            st.session_state.processing_time = time.time() - start_time
            st.session_state.layer_status["layer2"] = "complete"
            st.session_state.processing = False

            st.rerun()

        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please check the file format.")
            st.session_state.processing = False
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.session_state.processing = False

    if st.session_state.results:
        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Extractor",
            "Taskmage",
            "HubSpot",
            "Email Closer"
        ])

        with tab1:
            if st.session_state.results.get("agent_1_extraction"):
                render_agent_card(
                    "Agent 1: Extractor",
                    "",
                    st.session_state.results["agent_1_extraction"],
                    "Topics, pain points, and competitor mentions"
                )

        with tab2:
            if st.session_state.results.get("agent_2_tickets"):
                render_agent_card(
                    "Agent 2: Taskmage",
                    "",
                    st.session_state.results["agent_2_tickets"],
                    "Task assignments mapped to internal employees"
                )

        with tab3:
            if st.session_state.results.get("agent_3_hubspot"):
                render_agent_card(
                    "Agent 3: HubSpot",
                    "",
                    st.session_state.results["agent_3_hubspot"],
                    "CRM field updates and deal positioning"
                )

        with tab4:
            if st.session_state.results.get("agent_4_email"):
                render_agent_card(
                    "Agent 4: Email Closer",
                    "",
                    st.session_state.results["agent_4_email"],
                    "Follow-up email draft"
                )

        st.divider()

        with st.expander("View Full Output JSON"):
            st.code(
                json.dumps(st.session_state.results, indent=2),
                language="json"
            )

if __name__ == "__main__":
    main()