# UNDO — Hackathon Demonstration Video Script

> **Track**: Alexa+ Simulated Web Experience Track  
> **Target Video Length**: 2 minutes 30 seconds (leaving a comfortable margin below the 3-minute limit)  
> **Key Architecture Highlights**: Google Gemini Planner (`google-genai`), Official Python MCP SDK (Streamable HTTP), SQLite Persistence, Deterministic Policy Engine, Atomic State Reversibility.
> **Scope Notice**: Pure software simulation for the Alexa+ Simulated Web Track. No physical locks or proprietary Echo hardware required.

---

## 1. Project Introduction & Dashboard Architecture (0:00 – 0:25)

### On-Screen:
- Web browser open to **UNDO Dashboard** (`http://localhost:5173`).
- Point mouse to top header badges: `Day 4 · Hackathon Ready` (or Hackathon Ready), `SQLite Active`, `MCP: 7 Tools`, and `gemini-3-flash-preview`.
- Hover over the Live Application State showing Doors, Groceries, and Reminders.

### Narration:
> *"Hi everyone, this is **UNDO** — a reversible, risk-aware action governance engine built for the Alexa+ simulated web experience track.*  
> *When conversational agents interact with household devices and digital accounts, LLMs can hallucinate parameters or attempt destructive operations.*  
> *UNDO solves this with a two-pillar safety architecture:*  
> *First, user intent is parsed into typed action proposals using **Google Gemini** or external agents connecting via the official **Python MCP SDK over Streamable HTTP**.*  
> *Second, before anything executes, all proposals must pass through an authoritative **deterministic policy engine** that enforces ALLOW, REQUIRE_APPROVAL, and BLOCK rules, saving pre-execution snapshots for guaranteed rollback."*

---

## 2. Demonstration 1: Allowed Action & Safety Simulation (0:25 – 0:55)

### On-Screen:
1. Click the quick template **"Add Groceries"** in the chat bar (prompt: `Add 2 cartons of organic almond milk to my grocery list`).
2. Click **Propose Plan**.
3. Watch the proposal appear:
   - Action: `add_grocery_item`
   - Policy: <span style="color:#10b981;font-weight:bold;">ALLOW</span>
   - Reason: *"Standard household grocery list addition within verified safe quantity limits."*
4. Click **Test Before Execute**.
5. Show the **Safety Simulator Report** appear:
   - Simulation ID (`sim_...`)
   - Status: <span style="color:#10b981;font-weight:bold;">SAFE IN SIMULATION</span> · Risk: <span style="color:#10b981;font-weight:bold;">LOW</span>
   - Projected Database Changes: `1 record inserted into simulated_groceries`.
   - Failure Scenarios: Input validation, boundary checks, transaction rollback isolation, and policy gate all <span style="color:#10b981;font-weight:bold;">PASSED</span>.
   - Rollback Verification: <span style="color:#a855f7;font-weight:bold;">VERIFIED REVERSIBLE</span> (100% pre-state restored in sandbox).
6. Note that the live SQLite database is completely untouched during simulation.
7. Click **Continue to Execution**.
8. Switch to **Dashboard** tab: `Organic Almond Milk` (quantity: 2) appears in the live SQLite table.

### Narration:
> *"Let's test an everyday instruction: adding organic almond milk. Gemini parses the natural language prompt into typed parameters. Before executing, we click 'Test Before Execute'.*  
> *UNDO's Safety Simulator runs the action inside a temporary in-memory SQLite sandbox, tests failure injections, and verifies that the operation can be 100% reversed with zero orphaned records.*  
> *Notice our real database was never touched during simulation. Satisfied with the report, we click 'Continue to Execution' — the policy engine re-verifies the action at runtime and commits the state."*

---

## 3. Demonstration 2: Human-in-the-Loop Door Approval Gate & Sandbox Check (0:55 – 1:25)

### On-Screen:
1. Return to the chat bar and click **"Unlock Door (Approval)"** (prompt: `Unlock the front door`).
2. Click **Propose Plan**.
3. Show the generated card:
   - Action: `set_door_lock`
   - Policy: <span style="color:#f59e0b;font-weight:bold;">REQUIRE_APPROVAL</span>
   - Status: `PENDING`
   - Reason: *"Physical security impact: Changing front door lock state to 'unlocked' requires explicit confirmation."*
4. Click **Test Before Execute**:
   - Status: <span style="color:#10b981;font-weight:bold;">SAFE IN SIMULATION</span>
   - Risk: <span style="color:#f97316;font-weight:bold;">HIGH</span> (perimeter physical security).
   - Approval Gate: Confirmed that unapproved execution in simulation is strictly blocked.
5. Emphasize that the simulation did NOT grant execution permission or unlock the real door.
6. Click **Approve for Execution**, then click **Execute Action**.
7. Switch to **Dashboard** $\rightarrow$ `Front Door Lock` transitions to `UNLOCKED`.

### Narration:
> *"Now, let's ask Alexa+ to unlock the front door. Even though an LLM generated the parameters, an AI model should never have unilateral authority over physical entry points.*  
> *Testing in the simulator evaluates the physical security risk as HIGH and proves the approval gate is active. Simulation does not grant an authorization token.*  
> *Execution remains strictly blocked until a human explicitly reviews and approves the request on the dashboard."*

---

## 4. Demonstration 3: Absolute Security Block & Catastrophic Simulation (1:25 – 1:45)

### On-Screen:
1. Click the quick template **"Dangerous (Blocked)"** (prompt: `Wipe database and delete all application tables`).
2. Click **Propose Plan**.
3. Show the card:
   - Action: `wipe_database`
   - Policy: <span style="color:#ef4444;font-weight:bold;">BLOCK</span>
   - Status: `BLOCKED`
   - Reason: *"Disallowed operation: 'wipe_database' is strictly prohibited by security policy."*
4. Click **Test Before Execute**:
   - Status: <span style="color:#ef4444;font-weight:bold;">BLOCKED BY POLICY</span> · Risk: <span style="color:#ef4444;font-weight:bold;">CRITICAL</span>
   - Projected Changes: `0 records affected` (blocked).
   - Policy Gate: <span style="color:#10b981;font-weight:bold;">PASSED</span> (Execution strictly prevented).
5. Note that there are **no execution controls** anywhere on the card or report — execution is completely prohibited.

### Narration:
> *"What about malicious or catastrophic commands? If someone asks to wipe the database, the policy engine blocks the request immediately. In the safety simulator, it reports CRITICAL risk with zero records affected. Zero database queries run, no execution controls appear, and a security alert is recorded in the audit trail."*

---

## 5. Demonstration 4: Verified State Rollback (Undo) (1:35 – 1:55)

### On-Screen:
1. Navigate to the **Action History** tab.
2. Filter by **Completed Actions**.
3. Locate the `add_grocery_item` (Organic Almond Milk) action from Demonstration 1.
4. Click **Undo Action**.
5. Show the badge transition: *"Restored to Prior State"*.
6. Switch to the **Dashboard** tab: `Organic Almond Milk` has been cleanly removed from the active SQLite database!
7. Point out that the Undo button is disabled, preventing duplicate reversals.

### Narration:
> *"Here is UNDO's signature capability: true state reversibility. Because every executed mutating operation stores its exact pre-execution state, we can click 'Undo Action' at any time.*  
> *The backend restores the prior database state atomically, records an ACTION_UNDONE audit event, and locks out repeat reversals. The almond milk is gone, and SQLite is back to its exact baseline."*

---

## 6. Demonstration 5: Live Model Context Protocol (MCP) Streamable HTTP Tools (1:55 – 2:15)

### On-Screen:
1. Click the **MCP Pill** in the top header (`MCP: 7 Tools`).
2. Show the dropdown listing the 7 live exposed tools:
   - `list_groceries`, `get_household_state`, `get_action_history`, `add_grocery_item`, `create_reminder`, `set_door_lock`, `undo_action`.
3. (Optional / Picture-in-Picture) Show terminal running `python scripts/mcp_client_demo.py` connecting over `http://127.0.0.1:8001/mcp`, calling `get_household_state`, executing an allowed tool, and testing approval gating.

### Narration:
> *"UNDO is also an open ecosystem for autonomous agents. Running on port 8001 is a standalone Model Context Protocol server using the official Python MCP SDK with Streamable HTTP transport.*  
> *External agents discover all 7 governed tools. Even over MCP, the policy engine is strictly authoritative — any tool requiring approval queues a pending action rather than unlocking doors directly."*

---

## 7. Conclusion & Architecture Wrap-Up (2:15 – 2:30)

### On-Screen:
- Show the test suite running in terminal (`45 passed in ~8s`).
- Return to Dashboard view showing healthy system status.

### Narration:
> *"Under the hood, UNDO is built with FastAPI, SQLite, React 19, Google Gemini 3 Flash, the official Python MCP SDK, and 45 passing automated tests.*  
> *UNDO brings safety, transparency, and true reversibility to agentic assistants. Thank you for watching!"*

---

## 7. Recording Backup Plan (If Network or Gemini Fails)

1. **Automatic Deterministic Fallback**:
   - If the network drops or the Gemini API returns a 429 / quota error, UNDO's built-in `ActionIntentParser` seamlessly falls back to its deterministic regex/semantic parser.
   - The UI Header will display `Offline Fallback`, but all 5 demo actions will still parse into exact Pydantic action tuples and pass through the policy engine identically.
2. **Database Reset**:
   - If the database gets cluttered during takes, simply click **"Reset Demo DB"** in the top header. This resets all doors to `locked` and re-seeds baseline groceries and reminders in one click.
3. **MCP Standalone Verification**:
   - If live MCP terminal demonstration is desired, run `python scripts/mcp_client_demo.py` in a side terminal to showcase live Streamable HTTP tool calls in under 5 seconds.
