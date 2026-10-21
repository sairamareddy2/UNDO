# UNDO — Hackathon Submission Checklist & Track Guide

## Track: Alexa+ Simulated Web Experience Track

This document details all deliverables, verification checks, feedback, and friction logs required for the final hackathon submission.

---

## 1. Hackathon Requirements Matrix

| Requirement | Implementation in UNDO | Verification Status |
| :--- | :--- | :--- |
| **Simulated Web Experience** | Responsive React 19 + Tailwind CSS dashboard with dark navy aesthetic, real-time SQLite entity viewer, interactive action planner, and audit ledger. | ✅ Verified (Port 5173) |
| **Safety Simulator (Test Before Execute)** | Isolated in-memory sandbox engine evaluating actions before execution, testing failure scenarios, deriving deterministic risk, and verifying 100% rollback recovery. | ✅ Verified (14 new safety tests, 59/59 total) |
| **Deterministic Policy Engine** | Authoritative rule-based engine returning `ALLOW`, `REQUIRE_APPROVAL`, and `BLOCK`. Zero reliance on unverified LLM risk scores for security decisions. | ✅ Verified (59/59 tests pass) |
| **State Reversibility (Undo)** | Exact before-and-after SQLite state snapshots with inverse operations. Rollback restores previous state; repeat reversals are strictly prevented. | ✅ Verified in SQLite & MCP |
| **Official MCP Server** | Real Model Context Protocol server built with official Python MCP SDK (`mcp>=2.3.0`) over Streamable HTTP on port 8001 (`/mcp`). | ✅ Verified (`mcp_client_demo.py`) |
| **Natural Language Planning** | Google Gemini API integration using official `google-genai` SDK (`gemini-3-flash-preview`) with structured Pydantic schema and instant offline fallback. | ✅ Verified (`verify_gemini_live.py`) |
| **Future Integrations** | Amazon Bedrock adapter scaffolded (`backend/app/integrations/bedrock_adapter.py`) with Boto3 configuration ready for cloud deployment. | ✅ Documented in roadmap (Not claiming AWS Builder mini-challenge prize) |
| **Open Source License** | Full repository covered by standard open-source MIT License. | ✅ Included (`LICENSE`) |
| **Security & Secrets Hygiene** | All API keys and secrets read from environment variables; `.env` is git-ignored; zero hardcoded credentials. | ✅ Verified via git audit |

---

## 2. Submission Deliverables Checklist

- [x] **Public Code Repository**: Clean Git repository with structured `frontend/`, `backend/`, `scripts/`, `docs/`, and root files.
- [x] **Open Source License**: `LICENSE` file present (MIT License).
- [x] **Configuration Template**: `.env.example` in root and `backend/.env.example` containing clean placeholders.
- [x] **Root README.md**: Complete project documentation with architecture diagrams, quickstart guides, test results, and tool tables.
- [x] **Automated Test Suite**: 59 unit, integration, MCP, safety simulation, and end-to-end workflow tests passing in Pytest.
- [x] **Frontend Production Build**: Zero compilation or linting errors via `tsc -b && vite build`.
- [x] **Demo Materials**:
  - `docs/demo_script.md`: 2-minute demonstration script with exact on-screen actions and narration.
  - `docs/submission_checklist.md`: Comprehensive checklist, feedback, and friction log.
- [ ] **Demo Video Recording**: 2-minute English video recorded following `docs/demo_script.md` (must be under 3 minutes).

---

## 3. Required Product Feedback: AI Agent Governance & Assistive Systems

### A. The Case for Deterministic Policy Gating over LLM "Self-Evaluation"
During development of UNDO, we evaluated whether generative models should assess their own action risk. We found that asking an LLM to assign risk scores (e.g., "rate this action 1-10") is fundamentally unsuited for physical device actuation or financial mutation:
1. **Adversarial and Prompt Injection Vulnerability**: Prompt framing can easily trick an LLM into downgrading a destructive command's perceived risk.
2. **Deterministic Rules Are Essential**: Safety gates (such as requiring explicit user confirmation before unlocking a door or ordering bulk quantities) must remain deterministic, hardcoded, and mathematically verifiable.
3. **The Proposal vs. Execution Separation**: Treating the LLM solely as a *semantic parser and proposal generator* while leaving execution and validation strictly to a backend policy engine proved to be the most robust architecture for next-generation assistants like Alexa+.

### B. Model Context Protocol (MCP) Streamable HTTP Feedback
1. **Standardization Victory**: Using the official Python MCP SDK with Streamable HTTP transport allows external agents (Claude Desktop, custom autonomous agents, IDEs) to discover and call UNDO's household tools without custom glue code.
2. **Approval Over Protocol Gap**: A major open problem in the MCP ecosystem is **interactive human-in-the-loop approvals**. Currently, when a tool requires approval (such as unlocking a door), the tool call cannot easily pause and prompt the user in the client UI. UNDO resolved this by recording a `REQUIRE_APPROVAL` status in SQLite and returning a pending action token, requiring dashboard interaction. An official MCP specification standard for human-in-the-loop approval challenges would be a valuable addition to the protocol.

---

## 4. Friction Log: Developer Experience & Learnings

| Topic | Encountered Friction | How UNDO Solved It |
| :--- | :--- | :--- |
| **Gemini Developer API vs Schema Constraints** | Passing `Dict[str, Any]` inside Pydantic schemas caused Google AI Studio to reject requests with `additionalProperties is only supported in Gemini Enterprise Agent Platform mode`. | Designed an explicit typed `ActionParameters` model with optional typed attributes, completely eliminating `additionalProperties` from the generated JSON schema while maintaining flexible typing. |
| **Model Version Transition** | Early requests to `gemini-2.0-flash` or `gemini-2.5-flash` were rejected with 404s advising migration to `gemini-3.8-flash` or `gemini-3-flash-preview`. | Tested available models directly via SDK and standardized on `gemini-3-flash-preview`, which consistently responds with structured output in under 4 seconds. |
| **Windows PowerShell Encoding** | Standard PowerShell 5.1 consoles with `cp1252` encoding threw `UnicodeEncodeError` when python scripts attempted to print unicode emojis (e.g. `\u274c`). | Sanitized all terminal verification scripts (`verify_gemini_live.py`) to use ASCII badges (`[+]`, `[-]`, `[!]`), ensuring reliable execution across all developer environments. |
| **MCP Lifecycles & Async Testing** | The official Python MCP SDK relies on AnyIO and Streamable HTTP streams which require precise session initialization and clean teardown during automated testing. | Built test fixtures using `starlette.testclient` and AnyIO event loops with in-memory SQLite isolation, preventing database locking and session collisions. |
