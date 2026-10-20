# UNDO — Hackathon Video Recording & Technical Production Checklist

> **Track**: Alexa+ Simulated Web Experience  
> **Target Video Runtime**: **2 minutes 40 seconds (160 seconds)**  
> **Strict Duration Ceiling**: Under 3 minutes (< 2:59)  
> **Recording Goal**: Clean, professional, high-definition screen recording with live application demonstration and synchronized narration.

---

## 1. Technical Audio & Video Specifications

| Setting | Recommended Value | Reason |
| :--- | :--- | :--- |
| **Resolution** | `1920 x 1080` (Full HD, 16:9) | Standard format for YouTube, Devpost, and hackathon judges |
| **Framerate** | `60 fps` (or `30 fps`) | Smooth mouse movement and UI animations |
| **Audio Sample Rate** | `48 kHz`, Stereo / Mono 16-bit | Crisp voice clarity with zero clipping or hiss |
| **Browser Zoom** | `110%` to `125%` | Ensures all badges, JSON payloads, and policy reasons are easily readable on mobile or laptop screens |
| **Audio Level** | Target `-14` to `-16 LUFS` (Peak: `-2 dB`) | Clear voiceover volume without distortion |
| **Notification Settings**| **Windows Focus Assist / Do Not Disturb ON** | Eliminates desktop popups, Slack pings, or calendar banners |
| **Desktop State** | Clean wallpaper, hide Windows taskbar (auto-hide) | Maximizes screen real estate for the application |

---

## 2. Pre-Flight Service Verification

Before beginning recording, run this quick pre-flight command in PowerShell to confirm all three servers are live:

```powershell
# 1. Verify FastAPI Backend
curl.exe -s http://127.0.0.1:8000/api/health

# 2. Verify Frontend
curl.exe -s -I http://127.0.0.1:5173

# 3. Test MCP Client Handshake & Tools
.\.venv\Scripts\python scripts/mcp_client_demo.py
```

### Expected Pre-Flight Status:
* **Backend**: `{"status":"healthy","database_connected":true,"gemini_connected":true,...}`
* **Frontend**: `HTTP/1.1 200 OK`
* **MCP**: Handshake succeeds with protocol `2025-11-25`, discovers 7 tools, and completes in ~5s.

---

## 3. Database Baseline Initialization

Ensure the database starts from a pristine baseline before recording:

1. Click the **`Reset Demo DB`** button in the top right of the UNDO dashboard header, OR run:
   ```bash
   curl.exe -s -X POST http://127.0.0.1:8000/api/state/reset
   ```
2. **Verify initial state on the Dashboard**:
   * Doors: `Front Door Lock (LOCKED)`, `Patio Back Door (LOCKED)`, `Garage Side Door (LOCKED)`.
   * Groceries: 2 baseline items (`Organic Whole Milk`, `Sourdough Bread`).
   * Reminders: 1 baseline reminder (`Team Standup Sync`).
   * Metrics: `Pending Approvals: 0`.

---

## 4. Screen Layout & Presentation Staging

Choose between two presentation layouts:

### Recommended Layout: Focused Browser (Full 1080p)
* **Main Area**: Chrome / Edge browser maximized at `http://localhost:5173`.
* **MCP Demonstration**: Demonstrated using the interactive **`MCP: 7 Tools`** pill in the top header, which displays a clean popover listing all 7 tools, the Streamable HTTP transport endpoint, and active connection status.
* **Advantage**: Ultra-clean, zero clutter, high readability for judges.

### Alternative Layout: Split Screen (Sidecar Terminal)
* **Left 75%**: Web browser showing UNDO Dashboard (`http://localhost:5173`).
* **Right 25%**: Windows Terminal (dark theme, large font ~14pt) ready to run `python scripts/mcp_client_demo.py` during Scene 6.
* **Advantage**: Live terminal proof showing raw MCP protocol JSON messages.

---

## 5. Step-by-Step Recording Walkthrough (Rehearsal Guide)

Follow this step-by-step cue sheet during your recording take:

### [0:00 – 0:18] Scene 1: Introduction & Problem
1. Start recording on the **Dashboard** view.
2. Move mouse across header badges: `Day 4 · Hackathon Ready`, `Alexa+ Web Track`, `SQLite Active`.
3. Speak **Scene 1** narration steadily.

### [0:18 – 0:38] Scene 2: Architecture & AI Planning
1. Point cursor to the pulsing blue `gemini-3.1-flash-lite` badge.
2. Glide cursor down the sidebar to the **Policy Matrix** card (ALLOW / REQUIRE_APPROVAL / BLOCK).
3. Click the **Action Planner** tab in the sidebar.
4. Speak **Scene 2** narration.

### [0:38 – 1:00] Scene 3: Allowed Execution & State Rollback
1. Click the quick template **"Add Groceries"** (`Add 2 cartons of organic milk...`).
2. Show the rendered card with the green **ALLOW** badge.
3. Click **Execute Action** $\rightarrow$ card shows `EXECUTED`.
4. Switch to **Dashboard** tab $\rightarrow$ point to newly added item in grocery table.
5. Switch to **Action History** tab $\rightarrow$ click purple **Undo Action** button.
6. Switch back to **Dashboard** $\rightarrow$ show that the grocery table is back to baseline!
7. Speak **Scene 3** narration.

### [1:00 – 1:27] Scene 4: Human-in-the-Loop Door Approval Gate
1. Return to **Action Planner** tab.
2. Click the quick template **"Unlock Door (Approval)"** (`Unlock the front door`).
3. Show the amber **REQUIRE_APPROVAL** card. Point out that **Execute** is disabled/hidden.
4. Click the green **Approve** button.
5. Click **Execute Action** $\rightarrow$ card shows `EXECUTED`.
6. Switch to **Dashboard** $\rightarrow$ show `Front Door Lock` is now `UNLOCKED` in amber.
7. Speak **Scene 4** narration.

### [1:27 – 1:48] Scene 5: Absolute Security Block
1. Return to **Action Planner** tab.
2. Click the quick template **"Dangerous (Blocked)"** (`Wipe database and delete...`).
3. Show the red **BLOCK** card: *"Disallowed operation: 'wipe_database' is strictly prohibited by security policy."*
4. Point out that zero execution buttons exist.
5. Click **Action History** $\rightarrow$ show the blocked security event in the ledger.
6. Speak **Scene 5** narration.

### [1:48 – 2:15] Scene 6: MCP Streamable HTTP Integration
1. Click the purple **`MCP: 7 Tools`** button in the top header.
2. Show the dropdown menu detailing the 7 exposed tools over Streamable HTTP (`:8001/mcp`).
3. *(If using side terminal)*: Run `.\.venv\Scripts\python scripts/mcp_client_demo.py` and show tool discovery and approval gating.
4. Speak **Scene 6** narration.

### [2:15 – 2:40] Scene 7: Conclusion & Wrap-Up
1. Return to the clean **Dashboard** view.
2. Show the top status badges and overall application health.
3. Deliver the concluding statement and track disclosures.
4. Stop recording at **2:40** (or within 2:35–2:45).

---

## 6. Contingency & Backup Plans

### A. What if Gemini API reaches quota or has high latency?
* **Automatic Failover**: UNDO's `ActionIntentParser` and `GeminiAdapter` are equipped with automatic model failover (`gemini-3.1-flash-lite` $\rightarrow$ `gemini-3-flash-preview` $\rightarrow$ `gemini-flash-latest`) and an instant deterministic fallback parser.
* If an API quota is exhausted, the header badge displays `Offline Fallback`, but all 5 demo actions will parse identically into exact Pydantic action tuples and pass through the policy engine without errors.

### B. What if an action is misclicked during a take?
* Do not panic. Simply click the **`Reset Demo DB`** button in the top header.
* In less than 200 milliseconds, the SQLite database re-seeds all doors to locked and restores baseline grocery and reminder tables.

### C. What if audio has background noise or pacing was rushed?
* If you speak too fast and finish under 2:15, pause slightly longer on the MCP tool popover and the Action History audit ledger.
* If you speak too slow and exceed 2:50, trim 1-2 sentences from Scene 6 and Scene 7 to guarantee staying under the 3-minute mark.

---

## 7. Post-Recording Quality Verification

Before submitting the video file to Devpost or YouTube:

- [ ] **Exact Duration**: Is the video length between **2:25 and 2:55**? (Hard limit: Strictly $< 3:00$).
- [ ] **Resolution**: Is the export rendered at `1920x1080` (1080p, 16:9)?
- [ ] **Audio Clarity**: Is the voice audible, clear, and synchronized with screen actions?
- [ ] **No Secret Leaks**: Verify that no API keys, `.env` files, or personal directory paths were visible.
- [ ] **Honest Disclosures**:
  - Confirmed software simulation for Alexa+ Simulated Web Track (no claims of controlling physical hardware locks).
  - No claims of AWS Builder mini-challenge prize (Bedrock is acknowledged as a future integration scaffold).
- [ ] **Core Capabilities Demonstrated**:
  - AI intent planning (Google Gemini).
  - Deterministic policy enforcement (ALLOW, REQUIRE_APPROVAL, BLOCK).
  - State reversibility / Atomic Undo with SQLite.
  - Model Context Protocol (MCP) server with official Python SDK over Streamable HTTP.
