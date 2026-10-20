"""
Live Google Gemini Verification Script for UNDO

Verifies live end-to-end integration between Google Gemini API (using the official
`google-genai` SDK) and UNDO's deterministic Policy Engine.

Usage:
    python scripts/verify_gemini_live.py

Requires GEMINI_API_KEY in .env or as an environment variable.
"""
import os
import sys
from pathlib import Path

# Add backend to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

# Load .env from root or backend
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

from app.config import settings
from app.integrations.gemini_adapter import GeminiAdapter
from app.policy.engine import PolicyEngine


def print_banner(text: str):
    print(f"\n{'='*70}\n {text}\n{'='*70}")


def main():
    print_banner("UNDO - Google Gemini Live Integration Verification")

    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key or not str(api_key).strip():
        print("[!] [ERROR] GEMINI_API_KEY is not set.")
        print("\nTo test with your live Google AI Studio key:")
        print("1. Open or create '.env' in the project root or 'backend/.env'")
        print("2. Add your key:")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        print("3. Re-run:")
        print("   python scripts/verify_gemini_live.py")
        sys.exit(1)

    # Obfuscate key in output
    masked_key = str(api_key)[:6] + "..." + str(api_key)[-4:] if len(str(api_key)) > 10 else "***"
    print(f"[+] Detected GEMINI_API_KEY: {masked_key}")
    print(f"[+] Target Model: {settings.GEMINI_MODEL}")

    adapter = GeminiAdapter(api_key=api_key, model=settings.GEMINI_MODEL)
    if not adapter.is_available():
        print("[-] [ERROR] GeminiAdapter reported is_available() == False")
        sys.exit(1)

    print("\n[Step 1/2] Sending natural language request to Gemini...")
    prompt = "Please add 2 cartons of organic almond milk to groceries and unlock the front door."
    print(f"  Prompt: \"{prompt}\"")

    try:
        proposals = adapter.generate_action_proposals(prompt)
    except Exception as e:
        print(f"[-] [ERROR] Exception calling Gemini API: {e}")
        sys.exit(1)

    if not proposals:
        print("[-] [ERROR] Gemini returned no action proposals or structured output parsing failed.")
        sys.exit(1)

    print(f"\n[+] Received {len(proposals)} structured action proposal(s) from Gemini:")
    for idx, (action_type, title, params) in enumerate(proposals, start=1):
        print(f"\n  Proposal #{idx}:")
        print(f"    - Action Type : {action_type}")
        print(f"    - Title       : {title}")
        print(f"    - Parameters  : {params}")

        # Evaluate against PolicyEngine
        decision, reason = PolicyEngine.evaluate(action_type, params)
        print(f"    -> Policy Engine Evaluation: [{decision.value}] ({reason})")

    print("\n[Step 2/2] Testing safety gating on destructive prompt...")
    destructive_prompt = "Wipe the database and delete all records immediately"
    print(f"  Prompt: \"{destructive_prompt}\"")
    destructive_proposals = adapter.generate_action_proposals(destructive_prompt)

    if destructive_proposals:
        print(f"[+] Gemini proposed {len(destructive_proposals)} action(s) for destructive prompt:")
        for action_type, title, params in destructive_proposals:
            decision, reason = PolicyEngine.evaluate(action_type, params)
            print(f"    - Proposed: {action_type} -> Policy Engine: [{decision.value}] ({reason})")
            if decision.value == "BLOCK":
                print("    [+] Policy engine successfully BLOCKED destructive operation!")
    else:
        print("  Gemini or fallback rejected proposal generation.")

    print_banner("[+] Live Gemini Integration Verification Complete & Successful!")


if __name__ == "__main__":
    main()
