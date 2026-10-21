# UNDO — Alexa+ Action Governance & Reversibility Layer

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_3-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![Google GenAI](https://img.shields.io/badge/AI_Planner-Google_GenAI_(SDK_v2.31)-4285F4.svg?style=flat&logo=google)](https://ai.google.dev)
[![MCP](https://img.shields.io/badge/Protocol-Official_Python_MCP_SDK_(Streamable_HTTP)-8B5CF6.svg?style=flat)](https://modelcontextprotocol.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org)
[![Pytest](https://img.shields.io/badge/Testing-Pytest_(59/59_Passed)-0A9EDC.svg?style=flat&logo=pytest)](https://pytest.org)

**UNDO** is a reliable action-governance, risk-simulation, and state-reversibility layer for the **Alexa+ simulated web experience track**, featuring:
- **UNDO Safety Simulator (Test Before Execute)**: An isolated sandbox engine that simulates actions, tests realistic failure injections, verifies 100% rollback recovery, and derives deterministic risk profiles before touching real data.
- **Natural Language Action Planning**: Built with the official **Google Gen AI Python SDK** (`google-genai`).
- **Live Model Context Protocol (MCP) Server**: Using the official **Python MCP SDK over Streamable HTTP** with 7 tools.
- **Deterministic Policy Engine**: Enforcing `ALLOW`, `REQUIRE_APPROVAL`, and `BLOCK` safety invariants.
- **State Snapshots & Undo Support**: Atomic state restoration with idempotent transaction guards.
- **Planned Cloud Integration**: Scaffolded AWS Builder integration (Amazon Bedrock with Boto3).

It guarantees that agentic operations (modifying household grocery lists, scheduling notifications, and actuating smart home doors) undergo **deterministic policy evaluation** prior to execution, and maintains **before-and-after state snapshots** for atomic, verified rollback.

---

## Key Features

1. **Natural Language Action Planner (Google Gemini & Fallback)**:
   - Uses the official Google Gen AI Python SDK (`google-genai`).
   - Converts natural conversational prompts into structured action proposals via Pydantic schemas (`ActionPlanProposal`, `ProposedAction`).
   - Powered by `gemini-3-flash-preview` with typed JSON schema enforcement.
   - Robust offline/fallback parser activates automatically if no API key is provided or during transient network/API issues.

2. **Deterministic Policy Engine (Authoritative Gatekeeper)**:
   - Strictly rule-based safety evaluation (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`).
   - **Zero reliance on unverified LLM risk scores for security decisions**: all Gemini output is treated as untrusted proposals and passed through the deterministic policy engine.
   - Enforces human approval gates on physical entry points (e.g. smart door locks) and bulk quantity thresholds.
   - Blocks destructive or unknown commands outright (e.g. `wipe_database`, `transfer_funds`).

3. **Official Python MCP Server (Streamable HTTP)**:
   - Built with the official Python MCP SDK (`mcp>=2.3.0`).
   - Runs a dedicated Streamable HTTP listener on port `8001` (`http://127.0.0.1:8001/mcp`).
   - Exposes 7 typed tools for state inspection, policy-governed mutation, and rollback.
   - Reuses the shared SQLite database and authoritative deterministic policy engine.
   - Real client verification script included (`scripts/mcp_client_demo.py`).

4. **Reversible Database-backed Operations**:
   - Real SQLite-persisted entities: Simulated Groceries, Reminders, and Smart Door Locks.
   - Saves previous state and well-defined inverse operations before mutating the database.
   - Enforces strict undo invariants: only executed, reversible actions can be undone; repeated undos are rejected.
   - Every execution and undo produces an immutable event in the audit trail.

5. **UNDO Safety Simulator (Test Before Execute)**:
   - Dedicated sandbox engine (`backend/app/services/safety_simulator.py`) operating on isolated temporary in-memory SQLite clones.
   - Evaluates actions against deterministic failure injections, constraint checks, and state conflict detections before touching real data.
   - Rigorously tests rollback recovery by applying the action, reversing it with `UndoManager`, and comparing pre- and post-rollback states for a 100% verified match.
   - Returns structured safety reports with clear status badges (`SAFE IN SIMULATION`, `WARNINGS FOUND`, `BLOCKED BY POLICY`, `SIMULATION FAILED`, `ROLLBACK UNVERIFIED`), risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), projected database changes, and limitations.
   - Never bypasses the deterministic policy engine or approval requirements.

6. **Polished Alexa+ Web Dashboard**:
   - Dark navy interface (`#080C16`) with restrained violet accents.
   - Live MCP server status indicator showing connection state, transport, and exposed tool count.
   - Chat-style input with one-click simulation templates.
   - Interactive action cards with live policy reasonings and state diff inspections.
   - Live SQLite database state viewer updating in real-time on every execution or rollback.

---

## Google Gemini Integration & Safety Architecture

```
                       User Prompt / Alexa+ Command
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │     Action Intent Parser    │
                     └──────────────┬──────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
   [GEMINI_API_KEY Present]                   [No Key / API Error]
┌──────────────────────────────┐          ┌──────────────────────────────┐
│  GeminiAdapter (google-genai)│          │  Deterministic Intent Parser │
│  - gemini-3.8-flash          │          │  - Regex / semantic rules    │
│  - Structured Pydantic JSON  │          │  - Instant offline fallback  │
└──────────────┬───────────────┘          └──────────────┬───────────────┘
               │                                         │
               └────────────────────┬────────────────────┘
                                    │ Untrusted Action Proposals
                                    ▼
                     ┌─────────────────────────────┐
                     │ Deterministic Policy Engine │
                     └──────────────┬──────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
      [ALLOW]              [REQUIRE_APPROVAL]               [BLOCK]
   - Grocery Item          - Smart Door Locks          - Wipe Database
   - Valid Reminder        - Bulk Quantities (>100)    - Financial Transfer
         │                          │                          │
         ▼                          ▼                          ▼
   Ready to Execute       Requires Human Approval      Rejected Immediately
   (State Snapshot)        (Dashboard Interface)       (Logged to Audit)
```

### Key Safety Invariants:
- **Untrusted Proposals**: The AI model is strictly a semantic planner; it has zero authority to execute actions or bypass policy rules.
- **Credential Hygiene**: `GEMINI_API_KEY` is loaded through Pydantic BaseSettings from `.env`. The key is never logged, printed, returned in API responses, or committed to git.
- **Fail-Safe Fallback**: If Gemini encounters a network error, rate limit, or outputs invalid JSON, UNDO logs a sanitized warning and seamlessly falls back to the deterministic parser without failing the user's request.

---

## UNDO Safety Simulator (Test Before Execute)

The **Safety Simulator** allows users, reviewers, and operators to evaluate any proposed action in an isolated sandbox before committing state changes to the live SQLite database.

```
       [Proposed Action]
               │
               ▼
   [Test Before Execute Button]
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│              Safety Simulator (Sandbox Engine)              │
│                                                             │
│ 1. Clone live state into isolated in-memory SQLite sandbox  │
│ 2. Evaluate against Deterministic Policy Engine             │
│ 3. Project database changes and affected record counts      │
│ 4. Run deterministic failure scenario injections:           │
│    - Input validation & schema boundaries                   │
│    - State conflicts & redundancy checks (e.g. door locked) │
│    - Transaction rollback & persistence isolation           │
│    - Policy & approval gate enforcement                     │
│    - Approval expiration (reported honestly as unsupported) │
│ 5. Execute action against in-memory sandbox                 │
│ 6. Rollback using UndoManager & compare pre/post states     │
│ 7. Synthesize Safety Report (Status, Risk, Warnings, Diff)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    [Safety Report Displayed]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ALLOW / APPROVED]                   [BLOCK]
   "Continue to Execution"         "Action Blocked by Policy"
               │                               │
               ▼                               ▼
   Re-evaluated by Policy            No execution allowed
   Committed to live SQLite          Zero queries executed
```

### Safety Report Structure
- **Simulation Summary**: Unique ID (`sim_...`), timestamp, overall status badge, risk level, policy decision, approval requirement.
- **Projected Changes**: Exact database tables affected, mutation type (`INSERT`, `UPDATE`, `DELETE`, `BLOCKED`), and affected record counts.
- **Failure Injections**: Deterministic scenarios tested with observed vs expected outcomes and clear status pills (`PASSED`, `WARNING`, `UNSUPPORTED`, `FAILED`).
- **Recovery & Reversibility**: Empirical rollback verification confirming whether pre-execution state was 100% restored.
- **Disclaimers & Limitations**: Explicit disclosures that sandbox simulation does not guarantee real-world safety or control physical hardware.

### Simulation API Endpoint
- **Method & Route**: `POST /api/safety/simulate`
- **Request**: `{ "action_id": "<uuid>" }` or `{ "action_type": "...", "parameters": { ... } }`
- **Response**: Typed `SafetyReportResponse` schema with complete simulation telemetry.

---

## MCP Server Architecture & Tools

The MCP server runs independently from the REST API, listening on `http://127.0.0.1:8001/mcp`:

### Exposed Governed MCP Tools
| Tool Name | Parameters | Safety / Policy | Reversibility | Description |
| :--- | :--- | :--- | :--- | :--- |
| `list_groceries` | None | Read-Only | N/A | Lists active grocery items from SQLite. |
| `get_household_state` | None | Read-Only | N/A | Full snapshot of doors, groceries, and reminders. |
| `get_action_history` | `limit: int = 10` | Read-Only | N/A | Recent actions, policy reasons, and execution statuses. |
| `add_grocery_item` | `name: str`, `quantity: int = 1`, `category: str = "General"` | ALLOW (or REQUIRE_APPROVAL if > 100) | **Yes** | Adds item, captures state snapshot, creates action plan. |
| `create_reminder` | `title: str`, `remind_at: str`, `priority: str = "medium"` | ALLOW (valid params) | **Yes** | Schedules routine household notification. |
| `set_door_lock` | `door_id: str`, `target_state: str` | **REQUIRE_APPROVAL** | **Yes** | Queues door action. Tool call cannot bypass approval. |
| `undo_action` | `action_id: str` | Governed Rollback | N/A | Reverts executed action to prior state in SQLite. |

---

## Quickstart Guide

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ (tested with Node v22.18 / npm 10.9)
- Google AI Studio Gemini API Key (optional; deterministic fallback active if omitted)

### 1. Configuration (`.env`)

Create a `.env` file in the project root by copying `.env.example`:

```powershell
cp .env.example .env
```

Add your Google AI Studio API key:
```ini
GEMINI_API_KEY="your_google_ai_studio_key_here"
GEMINI_MODEL="gemini-3-flash-preview"
```

> **Note**: `.env` is ignored by Git. Never commit API keys.

### 2. Verify Gemini API Integration

You can run the standalone verification script to test live Gemini communication and policy gating:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/verify_gemini_live.py
```

### 3. Backend Setup & Run (Port 8000)

```powershell
# 1. Activate Python virtual environment:
.\.venv\Scripts\Activate.ps1       # Windows PowerShell
# or: source .venv/bin/activate    # Linux / macOS

# 2. Run the FastAPI development server:
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **MCP Probe Endpoint**: [http://127.0.0.1:8000/api/mcp/status](http://127.0.0.1:8000/api/mcp/status)

### 4. Standalone MCP Server Run (Port 8001)

In a separate terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend"
python -m app.mcp_server
```
- **Streamable HTTP Endpoint**: `http://127.0.0.1:8001/mcp`

### 5. Frontend Setup & Run (Port 5173)

In a separate terminal:

```powershell
cd frontend
npm run dev
```
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## How to Connect an MCP Client

### Interactive Demo Script
Run the automated MCP client demo that connects to `http://127.0.0.1:8001/mcp`, discovers tools, calls tools, tests policy gating, and verifies state rollback:

```powershell
$env:PYTHONPATH="backend"
python scripts/mcp_client_demo.py
```

### Programmatic Python MCP Client
```python
import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

async def main():
    # Connect to the Streamable HTTP transport
    async with streamable_http_client("http://127.0.0.1:8001/mcp") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. Discover tools
            tools = await session.list_tools()
            print("Discovered tools:", [t.name for t in tools.tools])

            # 2. Call read-only tool
            state = await session.call_tool("get_household_state", {})
            print("Household state:", state)

            # 3. Call allowed mutating tool (adds grocery, captures snapshot)
            result = await session.call_tool(
                "add_grocery_item",
                {"name": "Organic Almond Milk", "quantity": 2, "category": "Dairy"}
            )
            print("Result:", result)

            # 4. Attempt physical door unlock (requires dashboard approval!)
            door_result = await session.call_tool(
                "set_door_lock",
                {"door_id": "front_door", "target_state": "unlocked"}
            )
            print("Approval required:", door_result)

asyncio.run(main())
```

---

## Automated Test Suite

Run all automated unit, integration, and MCP tests:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend/tests -v
```

### Test Results (59 Passed)
```text
backend/tests/test_api.py::test_health_endpoint PASSED                   [  1%]
backend/tests/test_api.py::test_create_plan_with_allowed_and_approval_actions PASSED [  3%]
backend/tests/test_api.py::test_approval_and_execution_lifecycle PASSED  [  5%]
backend/tests/test_api.py::test_reject_action_lifecycle PASSED           [  6%]
backend/tests/test_api.py::test_blocked_intent_creation PASSED           [  8%]
backend/tests/test_e2e_workflows.py::test_e2e_grocery_workflow_allow_execute_undo_invariants PASSED [ 10%]
backend/tests/test_e2e_workflows.py::test_e2e_door_unlock_require_approval_gate PASSED [ 11%]
backend/tests/test_e2e_workflows.py::test_e2e_dangerous_request_blocked PASSED [ 13%]
backend/tests/test_e2e_workflows.py::test_e2e_gemini_unavailable_or_quota_fallback PASSED [ 15%]
backend/tests/test_e2e_workflows.py::test_e2e_gemini_malformed_model_output PASSED [ 16%]
backend/tests/test_e2e_workflows.py::test_e2e_action_history_ledger_accuracy PASSED [ 18%]
backend/tests/test_execution.py::test_execute_add_grocery_success PASSED [ 20%]
backend/tests/test_execution.py::test_execute_create_reminder_success PASSED [ 22%]
backend/tests/test_execution.py::test_execute_door_lock_success PASSED   [ 23%]
backend/tests/test_execution.py::test_cannot_execute_unapproved_action PASSED [ 25%]
backend/tests/test_execution.py::test_cannot_execute_blocked_action PASSED [ 27%]
backend/tests/test_gemini.py::test_gemini_adapter_availability PASSED    [ 28%]
backend/tests/test_gemini.py::test_gemini_adapter_successful_response_mocked PASSED [ 30%]
backend/tests/test_gemini.py::test_gemini_adapter_malformed_model_output PASSED [ 32%]
backend/tests/test_gemini.py::test_gemini_adapter_api_error_handling PASSED [ 33%]
backend/tests/test_gemini.py::test_parser_fallback_to_deterministic_when_gemini_fails PASSED [ 35%]
backend/tests/test_gemini.py::test_gemini_proposals_enforce_policy_engine PASSED [ 37%]
backend/tests/test_mcp.py::test_mcp_tool_discovery[asyncio] PASSED       [ 38%]
backend/tests/test_mcp.py::test_mcp_call_readonly_tools[asyncio] PASSED  [ 40%]
backend/tests/test_mcp.py::test_mcp_allowed_state_change_and_persistence[asyncio] PASSED [ 42%]
backend/tests/test_mcp.py::test_mcp_approval_gating_cannot_be_bypassed[asyncio] PASSED [ 44%]
backend/tests/test_mcp.py::test_mcp_blocked_action_rejected[asyncio] PASSED [ 45%]
backend/tests/test_mcp.py::test_mcp_undo_restores_prior_state[asyncio] PASSED [ 47%]
backend/tests/test_policy.py::test_add_grocery_item_allowed PASSED       [ 49%]
backend/tests/test_policy.py::test_add_grocery_bulk_requires_approval PASSED [ 50%]
backend/tests/test_policy.py::test_add_grocery_invalid_name_blocked PASSED [ 52%]
backend/tests/test_policy.py::test_add_grocery_negative_quantity_blocked PASSED [ 54%]
backend/tests/test_policy.py::test_create_reminder_allowed PASSED        [ 55%]
backend/tests/test_policy.py::test_create_reminder_missing_title_blocked PASSED [ 57%]
backend/tests/test_policy.py::test_create_reminder_missing_schedule_blocked PASSED [ 59%]
backend/tests/test_policy.py::test_door_lock_requires_approval PASSED    [ 61%]
backend/tests/test_policy.py::test_door_lock_unknown_location_blocked PASSED [ 62%]
backend/tests/test_policy.py::test_door_lock_invalid_state_blocked PASSED [ 64%]
backend/tests/test_policy.py::test_dangerous_operations_strictly_blocked PASSED [ 66%]
backend/tests/test_policy.py::test_unknown_tool_strictly_blocked PASSED  [ 67%]
backend/tests/test_safety_simulator.py::test_valid_grocery_simulation_preserves_real_db PASSED [ 69%]
backend/tests/test_safety_simulator.py::test_valid_reminder_simulation_isolated PASSED [ 71%]
backend/tests/test_safety_simulator.py::test_simulated_door_action_preserves_approval_requirement PASSED [ 72%]
backend/tests/test_safety_simulator.py::test_blocked_destructive_request_remains_blocked PASSED [ 74%]
backend/tests/test_safety_simulator.py::test_invalid_parameters_produce_clear_validation_result PASSED [ 76%]
backend/tests/test_safety_simulator.py::test_simulated_db_failures_do_not_damage_real_db PASSED [ 77%]
backend/tests/test_safety_simulator.py::test_supported_action_marked_reversible_only_after_state_comparison PASSED [ 79%]
backend/tests/test_safety_simulator.py::test_failed_rollback_produces_honest_failure_status PASSED [ 81%]
backend/tests/test_safety_simulator.py::test_approval_expiration_honestly_reported_as_unsupported PASSED [ 83%]
backend/tests/test_safety_simulator.py::test_continuing_to_execution_reruns_policy_and_authorization PASSED [ 84%]
backend/tests/test_safety_simulator.py::test_blocked_action_cannot_be_executed_after_simulation PASSED [ 86%]
backend/tests/test_safety_simulator.py::test_safety_simulate_api_schema PASSED [ 88%]
backend/tests/test_safety_simulator.py::test_state_conflict_warning_for_redundant_door_lock PASSED [ 89%]
backend/tests/test_safety_simulator.py::test_bulk_purchase_triggers_medium_risk_and_approval PASSED [ 91%]
backend/tests/test_undo.py::test_undo_add_grocery PASSED                 [ 93%]
backend/tests/test_undo.py::test_undo_door_lock_restores_previous_state PASSED [ 94%]
backend/tests/test_undo.py::test_cannot_undo_twice PASSED                [ 96%]
backend/tests/test_undo.py::test_cannot_undo_unexecuted_action PASSED    [ 98%]
backend/tests/test_undo.py::test_cannot_undo_non_reversible_action PASSED [100%]

======================== 59 passed, 1 warning in 8.63s ========================
```

---

## Hackathon Demo & Submission Materials

1. **[Demo Video Script (~2:30)](docs/demo_script.md)**: Narration and on-screen workflow steps covering Allowed Actions, Approval Gating, Security Blocks, and Undo Reversibility.
2. **[Submission Checklist & Track Guide](docs/submission_checklist.md)**: Deliverables matrix, feedback on AI agent governance, and developer friction log.
3. **[Architecture Specification](docs/architecture.md)**: Detailed schema and state-machine transitions.
4. **[Open Source License](LICENSE)**: MIT License.

---

## Simulated Environment & Scope Disclosures

> [!IMPORTANT]
> **Simulated Alexa+ Web Experience**: UNDO models smart home device actuation (door locks), household management (groceries), and scheduling (reminders) within a simulated web sandbox. It does **not** connect to physical hardware locks, live payment rails, or proprietary Amazon Echo hardware.
>
> **AWS Builder Mini-Challenge Scope**: An Amazon Bedrock adapter using Boto3 is scaffolded under [`backend/app/integrations/bedrock_adapter.py`](backend/app/integrations/bedrock_adapter.py) with typed parameter definitions for future cloud deployment. However, because live AWS Bedrock calls were not active during this milestone, UNDO is submitted strictly to the **Alexa+ Simulated Web Experience Track** and does not claim AWS Builder mini-challenge prize eligibility.

---

## Known Limitations

1. **Amazon Bedrock Integration**: Boto3 client adapter is scaffolded under [`backend/app/integrations/bedrock_adapter.py`](backend/app/integrations/bedrock_adapter.py) with full parameter specifications, scheduled for future production deployment.
2. **Approval over MCP**: By design, high-risk tools return `REQUIRE_APPROVAL` and write a pending action to the database. External MCP clients currently cannot deliver an interactive human approval token over the standard tool response; approval occurs via the UNDO Web Dashboard.
