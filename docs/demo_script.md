# UNDO — Hackathon Demonstration Video Script

> **Track**: Alexa+ Simulated Web Experience Track  
> **Target Video Length**: 2 minutes (under 3-minute hard ceiling)  
> **Key Architecture Highlights**: Google Gemini Planner (`google-genai`), Official Python MCP SDK (Streamable HTTP), SQLite Persistence, Deterministic Policy Engine, Atomic State Reversibility.

---

## 1. Project Introduction (0:00 – 0:25)

### On-Screen:
- Web browser open to **UNDO Dashboard** (`http://localhost:5173`).
- Point mouse to the top header badges: `Day 4 · Hackathon Ready`, `SQLite Active`, `MCP: 7 Tools`, and `Gemini Active`.

### Narration:
> *"Hi everyone, this is **UNDO** — an action-governance and state-reversibility layer for the Alexa+ simulated web experience track.*  
> *When conversational AI agents interact with the physical and digital world, LLMs can hallucinate parameters, misinterpret risk, or attempt irreversible actions.*  
> *UNDO solves this with a two-pillar safety architecture:*  
> *First, every user request is parsed into structured candidate actions using **Google Gemini** or an external agent connected via the official **Python MCP SDK over Streamable HTTP**.*  
> *Second, before any tool executes, it must pass through an authoritative **deterministic policy engine** that strictly enforces ALLOW, REQUIRE_APPROVAL, and BLOCK rules, with verified database snapshots for instantaneous, verifiable rollback."*

---

## 2. Demonstration 1: Allowed Action & Instant Execution (0:25 – 0:50)

### On-Screen:
1. Click the quick template **"Add Groceries"** in the chat bar (or type: `Add 2 cartons of organic almond milk to my grocery list`).
2. Click **Propose Plan**.
3. Watch the proposal appear:
   - Action: `add_grocery_item`
   - Policy: <span style="color:#10b981;font-weight:bold;">ALLOW</span>
   - Reason: *"Standard household grocery list addition within verified safe quantity limits."*
4. Click **Execute Action**.
5. Switch to **Dashboard** tab to show the Live Household State: `Organic Almond Milk` (quantity: 2) appears in SQLite.

### Narration:
> *"Let's test an everyday instruction: adding organic almond milk. Gemini parses the natural language prompt into typed parameters. The policy engine inspects the quantity and category, confirms it is within safe bounds, and flags it as ALLOW.*  
> *We click Execute — the action commits to SQLite, captures before-and-after snapshots, and updates our live household state in real time."*

---

## 3. Demonstration 2: Human-in-the-Loop Approval Gating (0:50 – 1:15)

### On-Screen:
1. Return to the chat bar and click **"Unlock Door (Approval)"** (prompt: `Unlock the front door`).
2. Click **Propose Plan**.
3. Show the generated card:
   - Action: `set_door_lock`
   - Policy: <span style="color:#f59e0b;font-weight:bold;">REQUIRE_APPROVAL</span>
   - Status: `PENDING`
   - Reason: *"Physical security impact: Changing front door lock state to 'unlocked' requires explicit confirmation."*
4. Attempt to execute or highlight that no execution occurs automatically.
5. Click the green **Approve** button, then click **Execute Action**.
6. Show the **Dashboard** $\rightarrow$ `Front Door Lock` transitions to `UNLOCKED`.

### Narration:
> *"Now, let's ask Alexa+ to unlock the front door. Even though the LLM generated the parameters, an AI model should never have unilateral authority over physical entry points.*  
> *The deterministic policy engine classifies this as REQUIRE_APPROVAL. It is impossible for an agent or MCP client to bypass this gate — execution is strictly blocked until a human explicitly reviews and approves the request on the dashboard."*

---

## 4. Demonstration 3: Absolute Security Block (1:15 – 1:35)

### On-Screen:
1. Click the quick template **"Dangerous (Blocked)"** (prompt: `Wipe database and delete all application tables`).
2. Click **Propose Plan**.
3. Show the card:
   - Action: `wipe_database`
   - Policy: <span style="color:#ef4444;font-weight:bold;">BLOCK</span>
   - Status: `BLOCKED`
   - Reason: *"Disallowed operation: 'wipe_database' is strictly prohibited by security policy."*
4. Note that there are **no execution buttons** — the action is dead-on-arrival and logged to the immutable audit trail.

### Narration:
> *"What about malicious or catastrophic commands? If someone asks to wipe the database or transfer funds, the policy engine blocks the request immediately. No database queries run, no execution controls exist, and a security alert is recorded in the audit trail."*

---

## 5. Demonstration 4: Verified State Rollback (Undo) (1:35 – 1:55)

### On-Screen:
1. Navigate to the **Action History** tab.
2. Filter by **Completed Actions**.
3. Locate the `add_grocery_item` (Organic Almond Milk) action from Demonstration 1.
4. Click **Undo Action**.
5. Show the banner: *"Restored to Prior State"*.
6. Switch to the **Dashboard** tab: `Organic Almond Milk` has vanished from the active SQLite database!
7. Point out that the Undo button is now disabled, preventing duplicate reversals.

### Narration:
> *"Here is UNDO's signature capability: true state reversibility. Because every executed mutating operation stores its exact pre-execution state, we can click 'Undo Action' at any time.*  
> *The backend restores the prior database state atomically, records an ACTION_UNDONE audit event, and locks out repeat reversals. The almond milk is gone, and the database is back to its exact original state."*

---

## 6. Real Integration Summary & Wrap-Up (1:55 – 2:05)

### On-Screen:
- Click the **MCP Pill** in the header to expand the 7 exposed tools (`list_groceries`, `get_household_state`, `undo_action`, etc.).
- Show terminal with pytest passing all 45 automated tests.

### Narration:
> *"Under the hood, UNDO is powered by Google Gemini via the official google-genai SDK, a real Streamable HTTP MCP server on port 8001, SQLite persistence, and 45 passing automated tests.*  
> *Thank you for watching the UNDO demonstration!"*

---

## 7. Recording Backup Plan (If Network or Gemini Fails)

1. **Automatic Deterministic Fallback**:
   - If the network drops or the Gemini API returns a 429 / quota error, UNDO's built-in `ActionIntentParser` seamlessly falls back to its deterministic regex/semantic parser.
   - The UI Header will display `Offline Fallback`, but all 5 demo actions will still parse into exact Pydantic action tuples and pass through the policy engine identically.
2. **Database Reset**:
   - If the database gets cluttered during takes, simply click **"Reset Demo DB"** in the top header. This resets all doors to `locked` and re-seeds baseline groceries and reminders in one click.
3. **MCP Standalone Verification**:
   - If live MCP terminal demonstration is desired, run `python scripts/mcp_client_demo.py` in a side terminal to showcase live Streamable HTTP tool calls in under 5 seconds.
