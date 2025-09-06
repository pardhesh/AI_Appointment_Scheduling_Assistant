
# AI Appointment Scheduling Assistant

A modular, multi-agent system that automates appointment scheduling and follow-up. The project combines LLM-driven information extraction with structured scheduling logic, a conversational Streamlit interface, and automated notifications via SMS and email. The design uses lightweight Excel/CSV files to simulate clinic data stores for rapid development and evaluation.

---

## Key Features

- **Multi-agent orchestration** using LangChain and LangGraph to coordinate modular tasks across the booking workflow.  
- **Conversational UI** built with Streamlit for guided, turn-based appointment booking.  
- **LLM-powered extraction** (Groq-hosted LLaMA models) for robust parsing of patient free-text inputs.  
- **Automated communications** via Twilio (SMS) and SendGrid (Email) for confirmations, cancellations, and reminders.  
- **Standalone reminder agent** that sends three staged reminders relative to the appointment date (3, 2, and 1 day before).  
- **Simple persistence** using CSV/Excel files for patient data, doctor schedules, and admin reporting (easy to replace with a DB later).

---

## Project Layout

```
.
├── data/
│   ├── synthetic_patients.csv      # Simulated patient EMR
│   ├── doctor_schedule.xlsx        # Doctor availability calendar
│   ├── patient_status.xlsx         # Admin report for confirmed bookings (created on first booking)
│   └── form/
│       └── New_Patient_Intake_Form.pdf
├── src/
│   └── agents/                     # Backend agent modules
│       ├── patient_info_agent.py
│       ├── patient_lookup_agent.py
│       ├── appointment_scheduler_agent.py
│       ├── confirmation_agent.py
│       ├── form_agent.py
│       └── remainder_agent.py
├── tests/                          # Unit tests for agents
├── .env                            # API keys and credentials (not committed)
├── app.py                          # Streamlit web interface
├── patient_flow_graph.py           # LangGraph flow for CLI testing
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.9+
- Virtual environment tool (venv, virtualenv, conda, etc.)
- (Optional) Graphviz for visualizations

---

## Initial Setup

1. Create and activate a Python virtual environment:

```bash
# Create venv
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add the required API keys (replace placeholders):

```env
# Groq / LLM
GROQ_API_KEY=""

# Twilio (SMS)
TWILIO_ACCOUNT_SID=""
TWILIO_AUTH_TOKEN=""
TWILIO_PHONE_NUMBER=""

# SendGrid (Email)
SENDGRID_API_KEY=""
SENDER_EMAIL=""
```

> **Security note:** Never commit `.env` or any secret keys to source control. Use environment-specific secret management in production.

---

## Data files

Place the following files under `data/` before running the app (some files are created automatically):

- `data/synthetic_patients.csv` — Simulated patient EMR (can be generated or provided).  
- `data/doctor_schedule.xlsx` — Doctor availability calendar (used for booking and preventing double-booking).  
- `data/form/New_Patient_Intake_Form.pdf` — Intake form for new patients.  

`data/patient_status.xlsx` will be created automatically when the first confirmed appointment is logged.

---

## Running the application

There are two primary components to run during development:

### 1) Streamlit UI (Interactive Chatbot)

Start the conversation UI (recommended):

```bash
streamlit run app.py
```

This launches the Streamlit app in your browser. The app manages the stage-based conversation and calls the underlying agents to perform extraction, lookup, scheduling, confirmation, and form distribution.

### 2) Optional: CLI Flow (LangGraph)

For a quick CLI test of the end-to-end backend flow:

```bash
python -m patient_flow_graph
# or
python -m src.agents.patient_flow_graph
```

### 3) Reminder Agent (Background job)

Run the standalone reminder agent (sends reminders based on `patient_status.xlsx`):

```bash
python -m src.agents.remainder_agent
```

> In production, schedule the reminder agent to run periodically (e.g., via cron, systemd timer, or APScheduler).

---

## Running tests

Run the unit tests included in the `tests/` directory:

```bash
pytest -q
# or
python -m pytest -q
```

Make sure your virtual environment is activated and dependencies are installed before running tests.

---

## Notes & Troubleshooting

- **Twilio / SendGrid credentials:** If API keys are not set, Twilio calls are simulated or produce informative warnings. Ensure correct environment variables are provided for real messaging.  
- **Excel write-permissions:** If the app cannot write to the Excel files (PermissionError), check that files are not open in another program (e.g., Excel) and that your user has write permission. On Windows, close the file in Excel before running.  
- **Phone number formatting:** Phone numbers are normalized to E.164 where possible (e.g., `+91xxxxxxxxxx`). Use real, properly formatted numbers when testing Twilio.  
- **Local dev vs production:** This repository simulates a clinic environment using CSV/Excel files for ease of testing. For production readiness, replace file-based storage with a proper database, secure secret storage, and hosted services for background scheduling and monitoring.

---

## Contribution

Contributions, suggestions, and bug reports are welcome. If you want to contribute:

1. Fork the repository.  
2. Create a feature branch: `git checkout -b feature/your-change`.  
3. Commit your changes and push.  
4. Open a pull request with a clear description of your changes.  

## Author

**Pardhesh Maddala** —  Developer
