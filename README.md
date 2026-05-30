# DealFlow

> **Automated Sales Call Intelligence Pipeline** — Transform Fireflies.ai meeting transcripts into actionable CRM updates, JIRA tasks, and follow-up emails using Google's ADK (Agent Development Kit) with Gemini AI.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Google ADK](https://img.shields.io/badge/Google%20ADK-2.0+-orange.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Agents](#agents)
- [API Reference](#api-reference)
- [Output Examples](#output-examples)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Sales Copilot is an intelligent multi-agent system that automates post-sales-call workflows. It processes meeting transcripts from Fireflies.ai and automatically:

1. **Extracts** key topics, pain points, and competitor mentions
2. **Generates** actionable JIRA-style tasks assigned to internal team members
3. **Updates** CRM (HubSpot) with deal stage recommendations and sentiment analysis
4. **Composes** professional follow-up emails to clients

Built on **Google's Agent Development Kit (ADK)**, the system uses a two-layer parallel processing architecture for optimal performance.

---

## ✨ Features

### Core Capabilities

- **📝 Transcript Parsing**: Seamlessly ingests Fireflies.ai JSON transcripts with speaker diarization
- **🤖 Multi-Agent Pipeline**: Four specialized AI agents working in coordinated parallel layers
- **📊 Topic Extraction**: Identifies discussion topics, summaries, pain points, and competitors
- **✅ Task Generation**: Automatically creates action items mapped to specific internal employees
- **🎯 CRM Integration**: Generates HubSpot-ready deal stage recommendations and sentiment analysis
- **📧 Email Automation**: Composes contextualized follow-up emails referencing specific discussion points
- **💾 Database Storage**: SQLite-backed task tracking with meeting linkage
- **🖥️ Web UI**: Professional Streamlit interface with real-time processing visualization

### Technical Highlights

- **Parallel Processing**: Layer 1 (Extractor + Taskmage) and Layer 2 (HubSpot + Email) run concurrently
- **Structured Output**: Pydantic schemas ensure consistent, validated JSON responses
- **Error Handling**: Comprehensive logging with both terminal and UI output
- **Flexible Input**: Supports both CLI batch processing and interactive web interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fireflies.ai Transcript                     │
│                        (JSON Input)                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TranscriptParser                         │
│  • Extract metadata (meeting_id, title, duration)               │
│  • Parse internal & customer attendees                          │
│  • Clean transcript body                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DealFlowOrchestrator                         │
├─────────────────────────────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────┐   │
│   │          LAYER 1 (Parallel Execution)                   │   │
│   │  ┌──────────────────┐    ┌──────────────────┐           │   │
│   │  │ Extractor Agent  │    │  Taskmage Agent  │           │   │
│   │  │ • Topics         │    │ • Action Items   │           │   │
│   │  │ • Pain Points    │    │ • Assignees      │           │   │
│   │  │ • Competitors    │    │ • Blockers       │           │   │
│   │  └──────────────────┘    └──────────────────┘           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                │                                │
│                                ▼                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                LAYER 2 (Parallel Execution)             │   │
│   │  ┌──────────────────┐    ┌──────────────────┐           │   │
│   │  │  HubSpot Agent   │    │  Email Agent     │           │   │
│   │  │ • Deal Stage     │    │ • Subject Line   │           │   │
│   │  │ • Sentiment      │    │ • Email Body     │           │   │
│   │  │ • Threat Level   │    │ • Recipient      │           │   │
│   │  │ • CRM Notes      │    │                  │           │   │
│   │  └──────────────────┘    └──────────────────┘           │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │   SQLite DB  │ │  JSON Files  │ │  Email Draft │
        │   (Tasks)    │ │  (Output)    │ │  (TXT/JSON)  │
        └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Google Cloud project with Gemini API enabled

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sales-copilot
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   GEMINI_MODEL_NAME=gemini-1.5-pro
   ```

5. **Verify installation**
   ```bash
   python -c "from config import GOOGLE_API_KEY; print('Config loaded successfully')"
   ```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Your Google Cloud API key for Gemini | - | ✅ Yes |
| `GEMINI_MODEL_NAME` | Gemini model to use | `gemini-1.5-pro` | ✅ Yes |

### Directory Structure (Auto-created)

The application automatically creates the following directories on first run:

```
data/
├── input/          # Place Fireflies.ai JSON transcripts here
├── output/         # Generated outputs (emails, CRM data, full results)
└── tasks.db        # SQLite database for task storage
```

---

## 🚀 Usage

### Command-Line Interface

Process a single transcript:

```bash
python main.py path/to/fireflies_transcript.json
```

Use a sample transcript (if available):

```bash
python main.py --sample
```

**Example Output:**
```
Processing transcript: ff-20250108-ml-relevance-001
Title: Maritime Logic - Relevance Orientation & Hosted API
Executing Layer 1 (Extractor + Taskmage in parallel)...

=== RESULTS ===

--- AGENT 1: EXTRACTION ---
{
  "topics": [...],
  "pain_points": [...],
  "competitors": [...]
}

--- AGENT 2: TASKS ---
{
  "tasks": [
    {"assignee": "John Doe", "action_item": "...", "blocker": null}
  ]
}

--- AGENT 3: HUBSPOT ---
{
  "deal_stage_recommendation": "Demo/Validation",
  "perceived_sentiment": "Cautiously optimistic",
  "competitor_threat_level": "Medium",
  "hubspot_notes_body": "..."
}

--- AGENT 4: EMAIL ---
{
  "recipient_email": "client@company.com",
  "email_subject": "Next Steps: API Integration Discussion",
  "email_body": "..."
}

Full output saved to: data/output/output_ff-20250108-ml-relevance-001.json
```

### Web Interface (Streamlit)

Launch the interactive UI:

```bash
streamlit run ui.py
```

The UI provides:

- **Drag-and-drop transcript upload**
- **Real-time processing pipeline visualization**
- **Live logging console**
- **Formatted agent output cards**
- **Downloadable results**

Access the UI at `http://localhost:8501`

---

## 📁 Project Structure

```
sales-copilot/
├── main.py                 # CLI entry point
├── orchestrator.py         # Core orchestration logic (DealFlowOrchestrator)
├── ui.py                   # Streamlit web interface
├── config.py               # Configuration and environment setup
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── agents/                 # AI Agent definitions
│   ├── extractor_agent/    # Topic & insight extraction
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── schema.py
│   ├── task_agent/         # Task generation & assignment
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── schema.py
│   ├── crm_agent/          # CRM update generation
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── schema.py
│   └── email_agent/        # Follow-up email composition
│       ├── agent.py
│       ├── prompts.py
│       └── schema.py
│
├── services/               # Backend services
│   ├── database_services.py    # SQLite task management
│   ├── storage_services.py     # File output handling
│   └── tickets_table_schema.sql # Database schema
│
├── utils/                  # Utility modules
│   ├── __init__.py
│   └── transcript_parser.py # Fireflies JSON parser
│
├── data/                   # Data directory (auto-created)
│   ├── input/              # Input transcripts
│   ├── output/             # Generated outputs
│   └── tasks.db            # SQLite database
│
└── assets/                 # Screenshots and media
    ├── ui.png
    ├── extractor_result.png
    ├── task_result.png
    ├── crm_result.png
    └── email_result.png
```

---

## 🤖 Agents

### Layer 1 Agents (Parallel)

#### 1. Extractor Agent
**Purpose**: Analyze transcripts and extract structured insights.

**Input**: Raw transcript text
**Output Schema**:
```python
class ExtractionOutputSchema(BaseModel):
    topics: List[TopicSummarizer]  # Topic names + summaries
    pain_points: List[str]         # Client complaints/frustrations
    competitors: List[str]         # Competitor mentions
```

**Prompt Strategy**: Focuses on business-relevant exchanges, ignoring pleasantries. Identifies product features, pricing, security, integration discussions.

---

#### 2. Taskmage Agent
**Purpose**: Map conversation commitments to actionable tasks.

**Input**: Transcript + internal employee list
**Output Schema**:
```python
class TaskOutput(BaseModel):
    tasks: List[TaskItem]

class TaskItem(BaseModel):
    assignee: str       # Internal employee name
    action_items: str   # Clear task definition
    blocker: Optional[str]  # Dependencies if any
```

**Prompt Strategy**: Scans for commitment language ("I will", "we'll"), cross-references with speaker tags, assigns only to internal staff.

---

### Layer 2 Agents (Parallel)

#### 3. HubSpot Agent
**Purpose**: Generate CRM field updates and deal positioning.

**Input**: Extraction results + Task assignments
**Output Schema**:
```python
class HubSpotOutput(BaseModel):
    deal_stage_recommendation: str  # Discovery, Demo, Proposal, etc.
    perceived_sentiment: str        # Interest level assessment
    competitor_threat_level: Literal["Low", "Medium", "High"]
    hubspot_notes_body: str         # Consolidated meeting summary
```

**Prompt Strategy**: Evaluates customer disposition, competitive landscape, and commitment levels to recommend next funnel stage.

---

#### 4. Email Agent
**Purpose**: Compose professional follow-up emails.

**Input**: Extraction results + Task assignments
**Output Schema**:
```python
class EmailOutput(BaseModel):
    recipient_email: str
    email_subject: str
    email_body: str
```

**Prompt Strategy**: Balances collaborative tone with structured recap. References specific pain points and outlines internal next steps.

---

## 🔌 API Reference

### DealFlowOrchestrator

Main orchestration class that coordinates all agents.

#### Methods

##### `process_transcript(raw_json: Dict) -> Dict`
Process a Fireflies.ai transcript through the entire pipeline.

**Parameters:**
- `raw_json`: Parsed Fireflies.ai JSON transcript

**Returns:**
```python
{
    "agent_1_extraction": {...},
    "agent_2_tickets": {...},
    "agent_3_hubspot": {...},
    "agent_4_email": {...},
    "metadata": {...}
}
```

##### `save_tasks_to_database(tasks_output: Dict, meeting_id: str) -> None`
Persist generated tasks to SQLite database.

---

### DatabaseService

SQLite-backed task management.

#### Methods

- `insert_tasks(assignee, action_item, blocker, meeting_id)` - Single task insertion
- `insert_tasks_batch(tasks, meeting_id)` - Batch insert multiple tasks
- `get_tasks_by_assignee(assignee_name)` - Retrieve tasks for specific employee
- `get_all_tasks()` - Retrieve all tasks
- `update_task_status(task_id, status)` - Update task status

---

### StorageService

File output management.

#### Methods

- `save_hubspot_payload(data, meeting_id)` - Save CRM update JSON
- `save_email_draft(data, meeting_id)` - Save email draft (TXT)
- `save_mail_payload(data, meeting_id)` - Save email JSON payload
- `save_full_output(data, meeting_id)` - Save complete pipeline output

---

### TranscriptParser

Fireflies.ai JSON parsing utility.

#### Methods

##### `parse_fireflies_json(raw_json: Dict) -> Dict`
Parse raw Fireflies JSON into structured format.

**Returns:**
```python
{
    "metadata": {...},           # Meeting details
    "transcript_text": str,      # Cleaned transcript body
    "internal_employees": List,  # Internal attendee names
    "customer_attendees": List,  # Customer attendee names
    "raw_data": Dict             # Original JSON
}
```

---

## 📊 Output Examples

### Sample Extraction Output
```json
{
  "topics": [
    {
      "topic_name": "API Integration Requirements",
      "summary": "Discussion around REST API endpoints, authentication methods, and rate limiting requirements for their use case."
    },
    {
      "topic_name": "Security Compliance",
      "summary": "Client expressed need for SOC2 compliance documentation and data encryption standards."
    }
  ],
  "pain_points": [
    "Current provider has unreliable uptime (99.5% vs promised 99.9%)",
    "Lack of dedicated support channel causing delayed responses",
    "Documentation is outdated and lacks code examples"
  ],
  "competitors": ["CompetitorX", "AltSolution Pro"]
}
```

### Sample Task Output
```json
{
  "tasks": [
    {
      "assignee": "Sarah Chen",
      "action_item": "Send SOC2 compliance documentation and security whitepaper",
      "blocker": null
    },
    {
      "assignee": "Mike Rodriguez",
      "action_item": "Provision sandbox environment with API credentials",
      "blocker": "Requires legal approval for NDA"
    },
    {
      "assignee": "Sarah Chen",
      "action_item": "Schedule technical deep-dive session with engineering team",
      "blocker": null
    }
  ]
}
```

### Sample HubSpot Output
```json
{
  "deal_stage_recommendation": "Demo/Validation",
  "perceived_sentiment": "Cautiously optimistic - interested but raising concerns about migration complexity",
  "competitor_threat_level": "Medium",
  "hubspot_notes_body": "Customer is actively evaluating solutions due to reliability issues with current provider. Key decision drivers: uptime SLA, support responsiveness, and documentation quality. Technical validation phase required before proposal. Assigned follow-ups: Sarah to send security docs, Mike to provision sandbox. Timeline: 2-3 weeks for evaluation."
}
```

### Sample Email Output
```json
{
  "recipient_email": "john.smith@clientcorp.com",
  "email_subject": "Follow-up: API Integration & Security Discussion",
  "email_body": "Hi John,\n\nThank you for taking the time to speak with us today...\n\nAs discussed, here are the next steps:\n• Sarah will send SOC2 documentation by EOD tomorrow\n• Mike will provision your sandbox environment (pending NDA)\n• We'll schedule a technical deep-dive for next week\n\nPlease don't hesitate to reach out with any questions...\n\nBest regards,\nThe Team"
}
```

---

## 🧪 Testing

Run the sample transcript (if available):

```bash
python main.py --sample
```

Verify database operations:

```bash
python -c "
from services.database_services import DatabaseService
db = DatabaseService()
print('Database initialized successfully')
print(f'Total tasks: {len(db.get_all_tasks())}')
"
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. Missing API Key**
```
Error: GOOGLE_API_KEY not found in environment
```
**Solution**: Ensure `.env` file exists with valid `GOOGLE_API_KEY`.

**2. Transcript Parsing Failure**
```
ValueError: Transcript text is empty after parsing
```
**Solution**: Verify the input JSON follows Fireflies.ai format with `transcript` field.

**3. Agent Output Parsing Error**
```
JSON parse failed for extraction
```
**Solution**: Check that the Gemini model is returning valid JSON. May require prompt tuning.

**4. Database Lock**
```
sqlite3.OperationalError: database is locked
```
**Solution**: Ensure no other process is accessing `tasks.db`. Close other connections.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public methods
- Write meaningful commit messages

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [Google Agent Development Kit (ADK)](https://github.com/google/adk)
- [Fireflies.ai](https://fireflies.ai) for transcript data format
- [Streamlit](https://streamlit.io) for the web interface
- [Gemini AI](https://ai.google.dev) for language model capabilities

---

## 📞 Support

For issues, questions, or contributions:

- **GitHub Issues**: [Create an issue](../../issues)
- **Email**: support@example.com

---

<div align="center">

**Built with ❤️ using Google ADK & Gemini AI**

[⬆ Back to Top](#sales-copilot-)


</div>