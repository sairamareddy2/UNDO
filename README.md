# UNDO — Alexa+ Action Governance & Reversibility Layer

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_3-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![MCP](https://img.shields.io/badge/Protocol-Official_Python_MCP_SDK_(Streamable_HTTP)-8B5CF6.svg?style=flat)](https://modelcontextprotocol.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org)
[![Pytest](https://img.shields.io/badge/Testing-Pytest_(33/33_Passed)-0A9EDC.svg?style=flat&logo=pytest)](https://pytest.org)

**UNDO** is a reliable action-governance and state-reversibility layer for the **Alexa+ simulated web experience track**, featuring a live **Model Context Protocol (MCP)** server with **Streamable HTTP transport** and planned **AWS Builder integration** (Amazon Bedrock with Boto3).

It guarantees that agentic operations (modifying household grocery lists, scheduling notifications, and actuating smart home doors) undergo **deterministic policy evaluation** prior to execution, and maintains **before-and-after state snapshots** for atomic, verified rollback.

---

## Key Features

1. **Official Python MCP Server (Streamable HTTP)**:
   - Built with the official Python MCP SDK (`mcp>=2.3.0`).
   - Runs a dedicated Streamable HTTP listener on port `8001` (`http://127.0.0.1:8001/mcp`).
   - Exposes 7 typed tools for state inspection, policy-governed mutation, and rollback.
   - Reuses the shared SQLite database and authoritative deterministic policy engine.
   - Real client verification script included (`scripts/mcp_client_demo.py`).

2. **Deterministic Policy Engine**:
   - Strictly rule-based safety evaluation (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`).
   - Zero reliance on unverified LLM risk scores for security decisions.
   - Enforces human approval gates on physical entry points (e.g. smart door locks) and bulk quantity thresholds.
   - Blocks destructive or unknown commands outright (e.g. `wipe_database`, `transfer_funds`).

3. **Reversible Database-backed Operations**:
   - Real SQLite-persisted entities: Simulated Groceries, Reminders, and Smart Door Locks.
   - Saves previous state and well-defined inverse operations before mutating the database.
   - Enforces strict undo invariants: only executed, reversible actions can be undone; repeated undos are rejected.
   - Every execution and undo produces an immutable event in the audit trail.

4. **Polished Alexa+ Web Dashboard**:
   - Dark navy interface (`#080C16`) with restrained violet accents.
   - Live MCP server status indicator showing connection state, transport, and exposed tool count.
   - Chat-style input with one-click simulation templates.
   - Interactive action cards with live policy reasonings and state diff inspections.
   - Live SQLite database state viewer updating in real-time on every execution or rollback.

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

### Security & Approval Behavior
- **Never treat a tool call as approval**: When an external agent or client calls `set_door_lock` or requests a bulk order, the tool evaluates policy, records the action as `PENDING`, and returns `{ "status": "REQUIRE_APPROVAL", "executed": false }`. The action remains strictly unexecuted until a human approves it on the UNDO dashboard.
- **Authoritative Policy**: Invalid inputs (e.g. empty name, negative quantity) or dangerous actions return `{ "status": "BLOCK", "executed": false }`.
- **Verified State Rollback**: `undo_action` verifies that the target action is in `EXECUTED` state, invokes `UndoManager`, restores the prior SQLite state, records an `ACTION_UNDONE` audit event, and rejects repeated undo calls.

---

## Quickstart Guide

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ (tested with Node v22.18 / npm 10.9)

### 1. Backend Setup & Run (Port 8000)

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

### 2. Standalone MCP Server Run (Port 8001)

In a separate terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend"
python -m app.mcp_server
```
- **Streamable HTTP Endpoint**: `http://127.0.0.1:8001/mcp`

### 3. Frontend Setup & Run (Port 5173)

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

### Test Results (33 Passed)
```text
backend/tests/test_api.py::test_health_endpoint PASSED                   [  3%]
backend/tests/test_api.py::test_create_plan_with_allowed_and_approval_actions PASSED [  6%]
backend/tests/test_api.py::test_approval_and_execution_lifecycle PASSED  [  9%]
backend/tests/test_api.py::test_reject_action_lifecycle PASSED           [ 12%]
backend/tests/test_api.py::test_blocked_intent_creation PASSED           [ 15%]
backend/tests/test_execution.py::test_execute_add_grocery_success PASSED [ 18%]
backend/tests/test_execution.py::test_execute_create_reminder_success PASSED [ 21%]
backend/tests/test_execution.py::test_execute_door_lock_success PASSED   [ 24%]
backend/tests/test_execution.py::test_cannot_execute_unapproved_action PASSED [ 27%]
backend/tests/test_execution.py::test_cannot_execute_blocked_action PASSED [ 30%]
backend/tests/test_mcp.py::test_mcp_tool_discovery[asyncio] PASSED       [ 33%]
backend/tests/test_mcp.py::test_mcp_call_readonly_tools[asyncio] PASSED  [ 36%]
backend/tests/test_mcp.py::test_mcp_allowed_state_change_and_persistence[asyncio] PASSED [ 39%]
backend/tests/test_mcp.py::test_mcp_approval_gating_cannot_be_bypassed[asyncio] PASSED [ 42%]
backend/tests/test_mcp.py::test_mcp_blocked_action_rejected[asyncio] PASSED [ 45%]
backend/tests/test_mcp.py::test_mcp_undo_restores_prior_state[asyncio] PASSED [ 48%]
backend/tests/test_policy.py::test_add_grocery_item_allowed PASSED       [ 51%]
backend/tests/test_policy.py::test_add_grocery_bulk_requires_approval PASSED [ 54%]
backend/tests/test_policy.py::test_add_grocery_invalid_name_blocked PASSED [ 57%]
backend/tests/test_policy.py::test_add_grocery_negative_quantity_blocked PASSED [ 60%]
backend/tests/test_policy.py::test_create_reminder_allowed PASSED        [ 63%]
backend/tests/test_policy.py::test_create_reminder_missing_title_blocked PASSED [ 66%]
backend/tests/test_policy.py::test_create_reminder_missing_schedule_blocked PASSED [ 69%]
backend/tests/test_policy.py::test_door_lock_requires_approval PASSED    [ 72%]
backend/tests/test_policy.py::test_door_lock_unknown_location_blocked PASSED [ 75%]
backend/tests/test_policy.py::test_door_lock_invalid_state_blocked PASSED [ 78%]
backend/tests/test_policy.py::test_dangerous_operations_strictly_blocked PASSED [ 81%]
backend/tests/test_policy.py::test_unknown_tool_strictly_blocked PASSED  [ 84%]
backend/tests/test_undo.py::test_undo_add_grocery PASSED                 [ 87%]
backend/tests/test_undo.py::test_undo_door_lock_restores_previous_state PASSED [ 90%]
backend/tests/test_undo.py::test_cannot_undo_twice PASSED                [ 93%]
backend/tests/test_undo.py::test_cannot_undo_unexecuted_action PASSED    [ 96%]
backend/tests/test_undo.py::test_cannot_undo_non_reversible_action PASSED [100%]

============================= 33 passed in 1.28s ==============================
```

---

## Known Limitations

1. **Amazon Bedrock Integration**: Boto3 client adapter is scaffolded under [`backend/app/integrations/bedrock_adapter.py`](file:///C:/Users/ADMIN/Downloads/undo/backend/app/integrations/bedrock_adapter.py) with full parameter specifications, but active AWS API calls are scheduled for the next milestone.
2. **Approval over MCP**: By design, high-risk tools return `REQUIRE_APPROVAL` and write a pending action to the database. External MCP clients currently cannot deliver an interactive human approval token over the standard tool response; approval occurs via the UNDO Web Dashboard.
