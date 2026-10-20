# UNDO — Final Hackathon Video Narration & Visual Storyboard

> **Hackathon Track**: Alexa+ Simulated Web Experience  
> **Target Video Runtime**: **2 minutes 40 seconds (160 seconds)**  
> **Strict Duration Ceiling**: Under 3 minutes (< 2:59)  
> **Estimated Word Count**: ~375 words (paced at ~140 words/minute for clear, authoritative delivery)  
> **System Requirements Verified**: FastAPI Backend (:8000), Official Python MCP Server (:8001), React 19 Frontend (:5173), Google Gemini 3.1 Flash-Lite, SQLite.

---

## Storyboard Overview & Timing Matrix

| Scene | Timestamp | Duration | Focus Area | Key UI Elements Demonstrated |
| :--- | :--- | :--- | :--- | :--- |
| **Scene 1** | `0:00 – 0:18` | 18s | Introduction & Problem | Dashboard overview, header badges, core problem of LLM agency |
| **Scene 2** | `0:18 – 0:38` | 20s | Architecture & AI Planning | Gemini model badge, Policy Matrix, dual-pillar governance |
| **Scene 3** | `0:38 – 1:00` | 22s | Allowed Execution & State Rollback | Add Groceries template, ALLOW decision, SQLite commit, Undo rollback |
| **Scene 4** | `1:00 – 1:27` | 27s | Human-in-the-Loop Approval | Unlock Door template, REQUIRE_APPROVAL gate, explicit human confirmation |
| **Scene 5** | `1:27 – 1:48` | 21s | Absolute Security Policy Block | Wipe Database template, BLOCK decision, execution lockout, audit logging |
| **Scene 6** | `1:48 – 2:15` | 27s | Official Python MCP Server Integration | MCP Header pill (7 tools), Streamable HTTP transport, client tool call |
| **Scene 7** | `2:15 – 2:40` | 25s | Conclusion, Verification & Impact | 45 passing tests, safety impact, pure software simulation disclosure |

---

## Scene-by-Scene Script & Action Cues

### Scene 1: Introduction and Problem (0:00 – 0:18 · 18 seconds)

#### Visual Cues:
* **Starting View**: Web browser open full-screen at `http://localhost:5173` showing the **Dashboard** view.
* **Camera / Focus**: Mouse hovers smoothly over the top title **UNDO**, then glides across the top status badges: `Day 4 · Hackathon Ready`, `Alexa+ Web Track`, and `SQLite Active`.
* **Household Overview**: Mouse points briefly to the **Live Application State** cards showing smart door locks (`Front Door Lock: LOCKED`), active groceries, and reminders.

#### Spoken Narration:
> *"This is **UNDO** — a reversible, risk-aware action governance engine designed for the Alexa+ simulated web experience track.*  
> *When autonomous conversational assistants take actions on behalf of users, large language models can hallucinate parameters, delete data, or execute unsafe physical operations with zero rollback mechanism.*  
> *UNDO solves this problem by inserting an authoritative governance layer between AI intent and real-world execution."*

---

### Scene 2: Architecture and AI Planning (0:18 – 0:38 · 20 seconds)

#### Visual Cues:
* **Camera / Focus**: Mouse highlights the **AI Planner Badge** in the top header (`gemini-3.1-flash-lite` with pulsing spark icon).
* **Sidebar Inspection**: Mouse moves down the left sidebar to hover over the **Policy Matrix** card showing the three deterministic tiers:
  * <span style="color:#10b981;font-weight:bold;">ALLOW</span> (Safe low-risk actions)
  * <span style="color:#f59e0b;font-weight:bold;">REQUIRE_APPROVAL</span> (Sensitive state changes)
  * <span style="color:#ef4444;font-weight:bold;">BLOCK</span> (Destructive/prohibited operations)
* **Switch View**: Click on the **Action Planner** tab in the sidebar.

#### Spoken Narration:
> *"UNDO operates on a two-pillar safety architecture.*  
> *First, natural language prompts are parsed into typed action proposals using **Google Gemini**.*  
> *Second, before any operation touches the database, every proposal must pass through an authoritative **deterministic policy engine**.*  
> *The policy evaluates parameters against strict household rules, classifying every action as ALLOW, REQUIRE_APPROVAL, or BLOCK — saving complete pre-execution snapshots for guaranteed rollback."*

---

### Scene 3: Allowed Execution and Reversibility (0:38 – 1:00 · 22 seconds)

#### Visual Cues:
* **Prompt Input**: Click the quick simulation template button **"Add Groceries"** (`Add 2 cartons of organic milk and sourdough bread to my grocery list`).
* **Submit**: Click **Propose Plan** (or auto-submitted).
* **Proposal Card**: The action card renders instantly:
  * Decision: <span style="color:#10b981;font-weight:bold;">ALLOW</span>
  * Policy Reason: *"Standard household grocery list addition within verified safe quantity limits."*
* **Execute**: Click the green **Execute Action** button. The badge transitions to `EXECUTED`.
* **State Check**: Switch to **Dashboard** $\rightarrow$ items appear in the live SQLite grocery list.
* **Rollback (Undo)**: Switch to **Action History** tab $\rightarrow$ click **Undo Action** on the executed grocery item.
  * Status changes to `REVERSED`.
  * Return to **Dashboard** $\rightarrow$ item is cleanly removed from the database!

#### Spoken Narration:
> *"Let's test an everyday instruction: adding groceries. Gemini parses the natural language into structured parameters. Our policy engine verifies the quantities and marks it as ALLOW.*  
> *When we execute, the item commits to SQLite, captures before-and-after snapshots, and updates our live household state.*  
> *And here is UNDO's superpower: with one click on the Action History ledger, we can undo the action. The database atomically rolls back to its exact prior state, and repeat rollbacks are permanently locked out."*

---

### Scene 4: Human Approval for Sensitive Actions (1:00 – 1:27 · 27 seconds)

#### Visual Cues:
* **Switch View**: Return to the **Action Planner** tab.
* **Prompt Input**: Click the quick simulation template button **"Unlock Door (Approval)"** (`Unlock the front door`).
* **Proposal Card**: The action card renders:
  * Decision: <span style="color:#f59e0b;font-weight:bold;">REQUIRE_APPROVAL</span>
  * Status: `PENDING`
  * Policy Reason: *"Physical security impact: Changing front door lock state to 'unlocked' requires explicit confirmation."*
* **Gating Demonstration**: Point mouse at the card — notice there is **no direct execution button**. The agent is strictly blocked from executing unilateral commands.
* **Human Approval**: Click the green **Approve** button $\rightarrow$ card unlocks to show **Execute Action**.
* **Execute**: Click **Execute Action**.
* **State Check**: Switch to **Dashboard** tab $\rightarrow$ `Front Door Lock` transitions to `UNLOCKED` in amber.

#### Spoken Narration:
> *"Next, let's ask the assistant to unlock the front door. Even though an AI model parsed the instruction, smart home security demands human oversight.*  
> *The deterministic policy engine classifies this action as REQUIRE_APPROVAL. It is impossible for any model or autonomous agent to bypass this gate.*  
> *Execution is completely blocked until a human explicitly reviews the parameters and clicks Approve on the dashboard. Only then can the simulated lock state transition to unlocked."*

---

### Scene 5: Dangerous Actions Are Blocked (1:27 – 1:48 · 21 seconds)

#### Visual Cues:
* **Switch View**: Return to the **Action Planner** tab.
* **Prompt Input**: Click the quick simulation template button **"Dangerous (Blocked)"** (`Wipe database and delete all application tables`).
* **Proposal Card**: The action card renders with a bright red border:
  * Decision: <span style="color:#ef4444;font-weight:bold;">BLOCK</span>
  * Status: `BLOCKED`
  * Policy Reason: *"Disallowed operation: 'wipe_database' is strictly prohibited by security policy."*
* **Security Verification**: Point mouse to the card — zero execution controls exist. The action is dead-on-arrival.
* **Audit Ledger**: Switch to **Action History** $\rightarrow$ toggle **Audit Log** to show the security incident logged with timestamp.

#### Spoken Narration:
> *"What happens if a prompt attempts something dangerous or malicious, like wiping the database?*  
> *The policy engine evaluates the requested action type against our immutable security policy and issues an absolute BLOCK.*  
> *Zero database queries run, no execution buttons are rendered, and a security alert is recorded into the audit trail. Safety is enforced deterministically in code, never left to the discretion of an LLM."*

---

### Scene 6: MCP Integration (1:48 – 2:15 · 27 seconds)

#### Visual Cues:
* **MCP Header Pill**: In the top navigation bar, click on the purple badge **`MCP: 7 Tools`**.
* **Popover Menu**: Show the popover listing:
  * Transport: `Streamable HTTP (:8001/mcp)`
  * Protocol: `Official Python MCP SDK`
  * Tools: `list_groceries`, `get_household_state`, `get_action_history`, `add_grocery_item`, `create_reminder`, `set_door_lock`, `undo_action`.
* *(Split screen or side-by-side terminal)*: Show terminal running `python scripts/mcp_client_demo.py` connecting to `http://127.0.0.1:8001/mcp`.
  * Output prints handshake, tool discovery, read-only household state query, and approval gating on `set_door_lock`.

#### Spoken Narration:
> *"UNDO is also an open governance layer for autonomous agent ecosystems.*  
> *Running on port 8001 is a genuine Model Context Protocol server built with the official Python MCP SDK using Streamable HTTP transport.*  
> *External agents can connect, discover our 7 governed tools, and query live household state.*  
> *Crucially, MCP clients cannot bypass governance: when an external agent calls `set_door_lock`, the server enqueues a pending approval action rather than executing it directly. The exact same policy engine protects both web users and MCP agents."*

---

### Scene 7: Closing & Verification Wrap-Up (2:15 – 2:40 · 25 seconds)

#### Visual Cues:
* **Terminal Proof**: Switch briefly to the terminal displaying automated test results:
  * `45 passed in 7.84s`
  * `frontend production build: 0 errors`
* **Dashboard Return**: Switch back to the clean **UNDO Dashboard** view (`http://localhost:5173`) showing healthy green status indicators.
* **Final Mouse Glide**: Hover over the logo and subtitle: *"Alexa+ Action Governance & Reversibility Layer"*.

#### Spoken Narration:
> *"Under the hood, UNDO is built with FastAPI, SQLite, React 19, Google Gemini, the official Python MCP SDK, and 45 passing automated tests.*  
> *All smart-home door operations in this demo are fully simulated in software for the Alexa+ simulated web experience track.*  
> *By combining LLM intelligence with deterministic policy governance and true state reversibility, UNDO makes autonomous AI assistants safe, accountable, and trustworthy.*  
> *Thank you for watching!"*

---

## Word Count & Timing Calibration

* **Scene 1**: 44 words $\div$ 2.4 wps $\approx$ **18 seconds**
* **Scene 2**: 50 words $\div$ 2.5 wps $\approx$ **20 seconds**
* **Scene 3**: 57 words $\div$ 2.6 wps $\approx$ **22 seconds**
* **Scene 4**: 66 words $\div$ 2.45 wps $\approx$ **27 seconds**
* **Scene 5**: 53 words $\div$ 2.5 wps $\approx$ **21 seconds**
* **Scene 6**: 68 words $\div$ 2.5 wps $\approx$ **27 seconds**
* **Scene 7**: 61 words $\div$ 2.45 wps $\approx$ **25 seconds**
* **Total Words**: **399 words**  
* **Total Pacing**: **160 seconds = 2 minutes 40 seconds** *(leaving 20 seconds of safety margin below the 3:00 limit)*.
