# UNDO — Alexa+ Action Governance & Reversibility Layer

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_3-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org)
[![Pytest](https://img.shields.io/badge/Testing-Pytest_(27/27_Passed)-0A9EDC.svg?style=flat&logo=pytest)](https://pytest.org)

**UNDO** is a reliable action-governance layer built for the **Alexa+ simulated web experience track**, with a planned **AWS Builder integration** (Amazon Bedrock with Boto3 and the official Python MCP SDK with Streamable HTTP).

It guarantees that agentic operations (mutating household grocery lists, scheduling notifications, and actuating smart home doors) undergo **deterministic policy evaluation** prior to execution, and maintains **before-and-after state snapshots** for atomic, verified rollback.

---

## Key Features

1. **Deterministic Policy Engine**:
   - Strictly rule-based safety evaluation (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`).
   - Zero reliance on unverified LLM risk scores for security decisions.
   - Enforces approval gates on physical entry points (e.g., door locks) and bulk quantity thresholds.
   - Blocks destructive or unknown commands outright (e.g., `wipe_database`, `transfer_funds`).

2. **Reversible Database-backed Operations**:
   - Real SQLite-persisted entities: Simulated Groceries, Reminders, and Smart Door Locks.
   - Saves previous state and well-defined inverse operations.
   - Enforces strict undo invariants: only executed, reversible actions can be undone; repeated undos are rejected.
   - Every execution and undo produces an immutable event in the audit trail.

3. **Polished Alexa+ Web Dashboard**:
   - Dark navy interface (`#080C16`) with restrained violet accents.
   - Chat-style input with one-click simulation templates.
   - Interactive action cards with live policy reasonings and state diff inspections.
   - Live SQLite database state viewer updating in real-time on every execution or rollback.
   - Complete action ledger and immutable audit log.

---

## Project Structure

```text
undo/
├── backend/
│   ├── app/
│   │   ├── api/                   # REST endpoints (health, plans, actions, state)
│   │   ├── executor/              # Safe action execution & state rollback manager
│   │   ├── integrations/          # AWS Bedrock & Python MCP SDK roadmap adapters
│   │   ├── planner/               # Natural language intent proposal parser
│   │   ├── policy/                # Deterministic policy engine (ALLOW, REQUIRE_APPROVAL, BLOCK)
│   │   ├── config.py              # Application settings & environment configuration
│   │   ├── database.py            # SQLite engine, sessionmaker, and baseline seeding
│   │   ├── main.py                # FastAPI entry point & CORS configuration
│   │   ├── models.py              # SQLAlchemy ORM models (Plans, Actions, State, Audit)
│   │   └── schemas.py             # Pydantic validation & serialization models
│   ├── tests/                     # 27 automated tests (policy, execution, undo, api)
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/            # Sidebar, Header, ChatInput, ActionCard, History, StateMonitor
│   │   ├── services/api.ts        # Typed client API service
│   │   ├── types/index.ts         # TypeScript schema definitions
│   │   ├── App.tsx                # Master dashboard state and views
│   │   └── index.css              # Custom Tailwind theme & scrollbar styling
│   ├── tailwind.config.js         # Dark navy & violet palette configuration
│   ├── vite.config.ts             # Vite configuration with /api backend proxy
│   └── package.json               # Frontend dependencies (React, Lucide, Tailwind)
├── docs/
│   ├── architecture.md            # Deep dive on governance, reversibility, and state flow
│   └── future_integrations.md     # Amazon Bedrock & Python MCP SDK roadmap specifications
├── .env.example                   # Root environment configuration template
├── .gitignore                     # Repository ignore rules
└── README.md                      # Documentation
```

---

## Quickstart Guide

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ (tested with Node v22.18 / npm 10.9)

### 1. Backend Setup & Run

In the project root, activate the Python environment and run:

```bash
# If creating a fresh virtual environment:
python -m venv .venv
.\.venv\Scripts\Activate.ps1       # Windows PowerShell
# or: source .venv/bin/activate    # Linux / macOS

# Install dependencies:
pip install -r backend/requirements.txt

# Start the FastAPI server (runs on port 8000):
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive API documentation is available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Frontend Setup & Run

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at:
- **Dashboard UI**: [http://localhost:5173](http://localhost:5173)

---

## How to Verify Database-backed Operations & Undo

1. **Verify ALLOW Policy & Live Database Mutation**:
   - In the Chat Input, click **"Add Groceries"** or type: `Add 2 cartons of organic milk and sourdough bread to my grocery list`.
   - Click **Propose Plan**.
   - Notice the policy badge indicates **ALLOW** with the reason: *"Standard household grocery list addition within verified safe quantity limits"*.
   - Click **Execute Action**.
   - Observe the **Live SQLite Database State** card immediately reflect the added items with their quantities.

2. **Verify State Reversibility (Undo)**:
   - On the executed action card, click the **Undo Action** button.
   - Observe the action status switch to **Reversed (Undone)**.
   - Check the **Live SQLite Database State** card: the grocery item is instantly removed from the database, restoring prior state.
   - Navigate to the **Action History** -> **Immutable Audit Log** to inspect the `ACTION_UNDONE` record.

3. **Verify REQUIRE_APPROVAL Security Gate**:
   - Click the preset **"Unlock Door (Approval)"** or type: `Unlock the front door`.
   - Observe the policy badge **REQUIRE APPROVAL** with the reason: *"Physical security impact: Changing front door lock state to 'unlocked' requires explicit confirmation"*.
   - Direct execution is locked out until you click **Approve**.
   - Click **Approve**, then click **Execute Action**.
   - Observe the door state change from **LOCKED** to **UNLOCKED** in the database.
   - Click **Undo Action** on the door card: the door state instantly locks back to **LOCKED**.

4. **Verify BLOCK Guardrail**:
   - Click **"Dangerous (Blocked)"** or type: `Wipe database and delete all application tables`.
   - Observe the policy badge **BLOCK** with the reason: *"Disallowed operation: 'wipe_database' is strictly prohibited by security policy"*.
   - Execution controls are completely disabled and no state is mutated.

---

## Automated Test Suite

Run all automated unit and integration tests using pytest:

```bash
$env:PYTHONPATH="backend"
python -m pytest backend/tests -v
```

### Test Results
```text
backend/tests/test_api.py::test_health_endpoint PASSED                   [  3%]
backend/tests/test_api.py::test_create_plan_with_allowed_and_approval_actions PASSED [  7%]
backend/tests/test_api.py::test_approval_and_execution_lifecycle PASSED  [ 11%]
backend/tests/test_api.py::test_reject_action_lifecycle PASSED           [ 14%]
backend/tests/test_api.py::test_blocked_intent_creation PASSED           [ 18%]
backend/tests/test_execution.py::test_execute_add_grocery_success PASSED [ 22%]
backend/tests/test_execution.py::test_execute_create_reminder_success PASSED [ 25%]
backend/tests/test_execution.py::test_execute_door_lock_success PASSED   [ 29%]
backend/tests/test_execution.py::test_cannot_execute_unapproved_action PASSED [ 33%]
backend/tests/test_execution.py::test_cannot_execute_blocked_action PASSED [ 37%]
backend/tests/test_policy.py::test_add_grocery_item_allowed PASSED       [ 40%]
backend/tests/test_policy.py::test_add_grocery_bulk_requires_approval PASSED [ 44%]
backend/tests/test_policy.py::test_add_grocery_invalid_name_blocked PASSED [ 48%]
backend/tests/test_policy.py::test_add_grocery_negative_quantity_blocked PASSED [ 51%]
backend/tests/test_policy.py::test_create_reminder_allowed PASSED        [ 55%]
backend/tests/test_policy.py::test_create_reminder_missing_title_blocked PASSED [ 59%]
backend/tests/test_policy.py::test_create_reminder_missing_schedule_blocked PASSED [ 62%]
backend/tests/test_policy.py::test_door_lock_requires_approval PASSED    [ 66%]
backend/tests/test_policy.py::test_door_lock_unknown_location_blocked PASSED [ 70%]
backend/tests/test_policy.py::test_door_lock_invalid_state_blocked PASSED [ 74%]
backend/tests/test_policy.py::test_dangerous_operations_strictly_blocked PASSED [ 77%]
backend/tests/test_policy.py::test_unknown_tool_strictly_blocked PASSED  [ 81%]
backend/tests/test_undo.py::test_undo_add_grocery PASSED                 [ 85%]
backend/tests/test_undo.py::test_undo_door_lock_restores_previous_state PASSED [ 88%]
backend/tests/test_undo.py::test_cannot_undo_twice PASSED                [ 92%]
backend/tests/test_undo.py::test_cannot_undo_unexecuted_action PASSED    [ 96%]
backend/tests/test_undo.py::test_cannot_undo_non_reversible_action PASSED [100%]

======================== 27 passed, 1 warning in 0.46s ========================
```

---

## Roadmap

- [x] **Milestone 1**: Foundation implementation (Deterministic Policy Engine, Reversibility Manager, SQLite persistence, React + Vite + Tailwind dashboard, 27 automated tests).
- [ ] **Milestone 2**: Amazon Bedrock integration using `boto3` (Claude 3.5 Sonnet Converse API with tool definitions).
- [ ] **Milestone 3**: Official Python MCP SDK integration with Streamable HTTP transport exposing UNDO tools to external agent runtimes.
