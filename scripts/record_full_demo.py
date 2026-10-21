import os
import sys
import time
import json
import requests
from playwright.sync_api import sync_playwright

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
RAW_VIDEO_DIR = "artifacts/raw_video"
TIMESTAMPS_FILE = "artifacts/scene_timestamps.json"

def reset_database():
    print("[RECORD] Resetting baseline database state via API...")
    try:
        r = requests.post(f"{BACKEND_URL}/api/state/reset", timeout=5)
        print("[RECORD] Database reset response:", r.json())
    except Exception as e:
        print("[RECORD] Warning: database reset failed:", e)

def inject_cursor(page):
    js = """
    if (!document.getElementById('playwright-cursor')) {
        const cursor = document.createElement('div');
        cursor.id = 'playwright-cursor';
        cursor.style.position = 'fixed';
        cursor.style.width = '24px';
        cursor.style.height = '24px';
        cursor.style.borderRadius = '50%';
        cursor.style.backgroundColor = 'rgba(168, 85, 247, 0.75)';
        cursor.style.border = '2.5px solid #ffffff';
        cursor.style.boxShadow = '0 0 14px rgba(168, 85, 247, 0.95)';
        cursor.style.pointerEvents = 'none';
        cursor.style.zIndex = '9999999';
        cursor.style.transition = 'transform 0.12s ease-out, background-color 0.1s ease';
        cursor.style.transform = 'translate(-50%, -50%)';
        cursor.style.left = '960px';
        cursor.style.top = '540px';
        document.body.appendChild(cursor);

        window.triggerCursorClick = function() {
            cursor.style.transform = 'translate(-50%, -50%) scale(0.75)';
            cursor.style.backgroundColor = 'rgba(236, 72, 153, 0.95)';
            setTimeout(() => {
                cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                cursor.style.backgroundColor = 'rgba(168, 85, 247, 0.75)';
            }, 150);
        };
    }
    """
    page.evaluate(js)

def move_cursor_to(page, target_locator, steps=20, delay=0.012):
    try:
        inject_cursor(page)
        box = target_locator.bounding_box()
        if box:
            tx = box["x"] + box["width"] / 2
            ty = box["y"] + box["height"] / 2
            page.mouse.move(tx, ty, steps=steps)
            page.evaluate(f"""
                const c = document.getElementById('playwright-cursor');
                if (c) {{ c.style.left = '{tx}px'; c.style.top = '{ty}px'; }}
            """)
            time.sleep(delay)
    except Exception:
        pass

def click_with_cursor(page, target_locator):
    try:
        move_cursor_to(page, target_locator, steps=15)
        page.evaluate("if (window.triggerCursorClick) window.triggerCursorClick();")
        page.wait_for_timeout(100)
        target_locator.click(force=True)
    except Exception as e:
        print("[RECORD] Click fallback:", e)
        target_locator.click(force=True)

def record_demo():
    os.makedirs(RAW_VIDEO_DIR, exist_ok=True)
    for f in os.listdir(RAW_VIDEO_DIR):
        if f.endswith(".webm") or f.endswith(".mp4"):
            try:
                os.remove(os.path.join(RAW_VIDEO_DIR, f))
            except Exception:
                pass

    reset_database()

    scene_timestamps = {}
    
    print("[RECORD] Launching Playwright Chromium in 1920x1080 with video recording...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            headless=True
        )
        context = browser.new_context(
            record_video_dir=RAW_VIDEO_DIR,
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        t_global_start = time.time()

        # =====================================================================
        # SCENE 1: Introduction and Problem (Target: 0:00 – 0:18)
        # =====================================================================
        scene_timestamps["scene1"] = 0.0
        print("\n[RECORD] === SCENE 1: INTRODUCTION ===")
        page.goto(FRONTEND_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        inject_cursor(page)

        # 1. Hover over Logo & Subtitle
        logo = page.locator("text=UNDO").first
        move_cursor_to(page, logo, steps=20)
        page.wait_for_timeout(1500)

        # 2. Hover over header badges
        badges = [
            page.locator("text=Day 4 · Hackathon Ready").first,
            page.locator("text=Alexa+ Web Track").first,
            page.locator("text=SQLite Active").first,
            page.locator("div:has-text('gemini')").first,
            page.locator("button:has-text('MCP:')").first,
        ]
        for b in badges:
            if b.count() > 0:
                move_cursor_to(page, b, steps=15)
                page.wait_for_timeout(900)

        # 3. Overview of Smart Home Doors & Household state
        doors_card = page.locator("text=Front Door Lock").first
        if doors_card.count() > 0:
            move_cursor_to(page, doors_card, steps=20)
            page.wait_for_timeout(1200)

        # 4. Overview of Groceries Table
        groceries_card = page.locator("text=Organic Whole Milk").first
        if groceries_card.count() > 0:
            move_cursor_to(page, groceries_card, steps=15)
            page.wait_for_timeout(1200)

        # 5. Policy Matrix in Sidebar
        policy_matrix = page.locator("text=Policy Matrix").first
        if policy_matrix.count() > 0:
            move_cursor_to(page, policy_matrix, steps=20)
            page.wait_for_timeout(1500)

        while (time.time() - t_global_start) < 17.5:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 1 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 2: Natural-Language AI Planning (Target: 0:18 – 0:35)
        # =====================================================================
        s2_time = time.time() - t_global_start
        scene_timestamps["scene2"] = round(s2_time, 2)
        print(f"\n[RECORD] === SCENE 2: PLANNING (Start: {s2_time:.2f}s) ===")
        planner_tab = page.locator("button:has-text('Action Planner')").first
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(800)

        input_box = page.locator("input[placeholder*='Give an Alexa+ instruction']").first
        move_cursor_to(page, input_box, steps=15)
        input_box.click(force=True)
        page.wait_for_timeout(300)
        input_box.fill("Add two cartons of organic almond milk to the grocery list.")
        page.wait_for_timeout(500)

        propose_btn = page.locator("button:has-text('Propose Plan')").first
        click_with_cursor(page, propose_btn)

        print("[RECORD] Waiting for proposal card...")
        page.wait_for_selector("text=add_grocery_item", timeout=35000)
        page.wait_for_selector("button:has-text('Test Before Execute'):not([disabled])", timeout=15000)
        inject_cursor(page)

        # Highlight ALLOW badge
        allow_badge = page.locator("span:has-text('ALLOW')").first
        if allow_badge.count() > 0:
            move_cursor_to(page, allow_badge, steps=15)
            page.wait_for_timeout(1500)

        # Highlight Policy Rule
        policy_rule = page.locator("text=Policy Rule:").first
        if policy_rule.count() > 0:
            move_cursor_to(page, policy_rule, steps=15)
            page.wait_for_timeout(1500)

        while (time.time() - t_global_start) < 35.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 2 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 3: Test Before Execute — Safety Simulator (Target: 0:35 – 1:08)
        # =====================================================================
        s3_time = time.time() - t_global_start
        scene_timestamps["scene3"] = round(s3_time, 2)
        print(f"\n[RECORD] === SCENE 3: SAFETY SIMULATOR (Start: {s3_time:.2f}s) ===")
        
        # Click "Test Before Execute"
        test_btn = page.locator("button:has-text('Test Before Execute'):not([disabled])").first
        click_with_cursor(page, test_btn)

        print("[RECORD] Waiting for Safety Simulator Report...")
        page.wait_for_selector("text=Safety Simulator Report", timeout=25000)
        inject_cursor(page)
        page.wait_for_timeout(1000)

        # 1. Highlight Simulation ID & Status Badge
        status_badge = page.locator("text=SAFE IN SIMULATION").first
        if status_badge.count() > 0:
            move_cursor_to(page, status_badge, steps=20)
            page.wait_for_timeout(2000)

        # 2. Highlight Risk Level
        risk_badge = page.locator("text=RISK: LOW").first
        if risk_badge.count() > 0:
            move_cursor_to(page, risk_badge, steps=15)
            page.wait_for_timeout(1500)

        # 3. Highlight Projected Database Changes
        changes_sec = page.locator("text=Projected Database Changes").first
        if changes_sec.count() > 0:
            move_cursor_to(page, changes_sec, steps=20)
            page.wait_for_timeout(2500)

        # 4. Highlight Failure Injections (Input Validation, Persistence, Policy)
        failures_sec = page.locator("text=Failure Injections & Boundary Scenarios").first
        if failures_sec.count() > 0:
            move_cursor_to(page, failures_sec, steps=20)
            page.wait_for_timeout(3000)

        # 5. Highlight Rollback Verification
        rollback_sec = page.locator("text=Rollback Verification").first
        if rollback_sec.count() > 0:
            move_cursor_to(page, rollback_sec, steps=20)
            page.wait_for_timeout(2500)

        # 6. Prove real DB was NOT touched: switch to Dashboard tab briefly
        dash_tab = page.locator("button:has-text('Dashboard')").first
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1500)

        # Show that almonds milk is NOT yet in the table
        groceries_view = page.locator("text=Groceries").first
        if groceries_view.count() > 0:
            move_cursor_to(page, groceries_view, steps=15)
            page.wait_for_timeout(1500)

        # Switch back to Action Planner
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(1200)

        while (time.time() - t_global_start) < 68.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 3 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 4: Controlled Execution and Undo (Target: 1:08 – 1:32)
        # =====================================================================
        s4_time = time.time() - t_global_start
        scene_timestamps["scene4"] = round(s4_time, 2)
        print(f"\n[RECORD] === SCENE 4: CONTROLLED EXECUTION & UNDO (Start: {s4_time:.2f}s) ===")
        
        # Click Continue to Execution or Execute Action
        continue_exec_btn = page.locator("button:has-text('Continue to Execution'):not([disabled])").first
        if continue_exec_btn.count() > 0:
            click_with_cursor(page, continue_exec_btn)
        else:
            exec_btn = page.locator("button:has-text('Execute Action'):not([disabled])").first
            click_with_cursor(page, exec_btn)

        page.wait_for_timeout(2000)

        # Switch to Dashboard tab to observe new item
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)

        almond_item = page.locator("text=organic almond milk").first
        if almond_item.count() == 0:
            almond_item = page.locator("text=Almond Milk").first
        if almond_item.count() > 0:
            move_cursor_to(page, almond_item, steps=20)
            page.wait_for_timeout(2000)

        # Switch to Action History to trigger Undo
        history_tab = page.locator("button:has-text('Action History')").first
        click_with_cursor(page, history_tab)
        page.wait_for_timeout(1500)

        page.wait_for_selector("button:has-text('Undo Action'):not([disabled])", timeout=15000)
        undo_btn = page.locator("button:has-text('Undo Action'):not([disabled])").first
        click_with_cursor(page, undo_btn)
        page.wait_for_timeout(2000)

        # Switch back to Dashboard to verify baseline restoration
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(2000)

        while (time.time() - t_global_start) < 92.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 4 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 5: Human Approval Gate & Sandbox Check (Target: 1:32 – 1:56)
        # =====================================================================
        s5_time = time.time() - t_global_start
        scene_timestamps["scene5"] = round(s5_time, 2)
        print(f"\n[RECORD] === SCENE 5: HUMAN APPROVAL (Start: {s5_time:.2f}s) ===")
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(800)

        unlock_quick = page.locator("button:has-text('Unlock Door (Approval)')").first
        click_with_cursor(page, unlock_quick)

        print("[RECORD] Waiting for REQUIRE APPROVAL proposal card...")
        page.wait_for_selector("text=set_door_lock", timeout=35000)
        page.wait_for_selector("button:has-text('Approve'):not([disabled])", timeout=15000)
        inject_cursor(page)

        req_badge = page.locator("span:has-text('REQUIRE APPROVAL')").first
        if req_badge.count() > 0:
            move_cursor_to(page, req_badge, steps=15)
            page.wait_for_timeout(1500)

        # Test Before Execute on sensitive door unlock
        test_door_btn = page.locator("button:has-text('Test Before Execute'):not([disabled])").first
        click_with_cursor(page, test_door_btn)

        print("[RECORD] Waiting for Door Safety Report...")
        page.wait_for_selector("text=Safety Simulator Report", timeout=25000)
        inject_cursor(page)
        page.wait_for_timeout(1000)

        # Highlight Risk Level: HIGH (physical perimeter security)
        high_risk_badge = page.locator("text=RISK: HIGH").first
        if high_risk_badge.count() > 0:
            move_cursor_to(page, high_risk_badge, steps=20)
            page.wait_for_timeout(2000)

        # Highlight Approval Requirement: Required
        approval_req = page.locator("text=Human Approval: Required").first
        if approval_req.count() > 0:
            move_cursor_to(page, approval_req, steps=15)
            page.wait_for_timeout(1500)

        # Now approve for execution
        approve_action_btn = page.locator("button:has-text('Approve for Execution'):not([disabled])").first
        if approve_action_btn.count() == 0:
            approve_action_btn = page.locator("button:has-text('Approve'):not([disabled])").first
        click_with_cursor(page, approve_action_btn)
        page.wait_for_timeout(1500)

        # Execute approved action
        page.wait_for_selector("button:has-text('Execute Action'):not([disabled])", timeout=15000)
        exec_door_btn = page.locator("button:has-text('Execute Action'):not([disabled])").first
        click_with_cursor(page, exec_door_btn)
        page.wait_for_timeout(2000)

        # Switch to Dashboard to show UNLOCKED state
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)

        front_door_card = page.locator("text=Front Door Lock").first
        if front_door_card.count() > 0:
            move_cursor_to(page, front_door_card, steps=20)
            page.wait_for_timeout(2000)

        while (time.time() - t_global_start) < 116.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 5 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 6: Destructive Action Blocked (Target: 1:56 – 2:14)
        # =====================================================================
        s6_time = time.time() - t_global_start
        scene_timestamps["scene6"] = round(s6_time, 2)
        print(f"\n[RECORD] === SCENE 6: DESTRUCTIVE BLOCKED (Start: {s6_time:.2f}s) ===")
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(800)

        danger_quick = page.locator("button:has-text('Dangerous (Blocked)')").first
        click_with_cursor(page, danger_quick)

        print("[RECORD] Waiting for BLOCK card...")
        page.wait_for_selector("text=wipe_database", timeout=35000)
        page.wait_for_selector("span:has-text('BLOCK')", timeout=15000)
        inject_cursor(page)

        block_badge = page.locator("span:has-text('BLOCK')").first
        move_cursor_to(page, block_badge, steps=15)
        page.wait_for_timeout(1500)

        # Test Before Execute on dangerous action
        test_danger_btn = page.locator("button:has-text('Test Before Execute'):not([disabled])").first
        click_with_cursor(page, test_danger_btn)

        print("[RECORD] Waiting for Blocked Safety Report...")
        page.wait_for_selector("text=BLOCKED BY POLICY", timeout=25000)
        inject_cursor(page)
        page.wait_for_timeout(1000)

        # Highlight BLOCKED BY POLICY & CRITICAL risk
        blocked_status = page.locator("text=BLOCKED BY POLICY").first
        move_cursor_to(page, blocked_status, steps=15)
        page.wait_for_timeout(1500)

        crit_risk = page.locator("text=RISK: CRITICAL").first
        move_cursor_to(page, crit_risk, steps=15)
        page.wait_for_timeout(1500)

        while (time.time() - t_global_start) < 134.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 6 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 7: MCP Streamable HTTP Integration (Target: 2:14 – 2:30)
        # =====================================================================
        s7_time = time.time() - t_global_start
        scene_timestamps["scene7"] = round(s7_time, 2)
        print(f"\n[RECORD] === SCENE 7: MCP SERVER (Start: {s7_time:.2f}s) ===")
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)

        mcp_badge = page.locator("button:has-text('MCP:')").first
        click_with_cursor(page, mcp_badge)
        page.wait_for_timeout(1500)

        # Hover over popover tools
        mcp_popover = page.locator("text=Exposed Tools (7)").first
        if mcp_popover.count() > 0:
            move_cursor_to(page, mcp_popover, steps=15)
            page.wait_for_timeout(2000)

        while (time.time() - t_global_start) < 150.0:
            page.wait_for_timeout(100)
        print(f"[RECORD] Scene 7 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 8: Closing Summary (Target: 2:30 – 2:45)
        # =====================================================================
        s8_time = time.time() - t_global_start
        scene_timestamps["scene8"] = round(s8_time, 2)
        print(f"\n[RECORD] === SCENE 8: CLOSING (Start: {s8_time:.2f}s) ===")
        # Close popover by clicking dashboard area
        dash_header = page.locator("text=Live SQLite Database State").first
        click_with_cursor(page, dash_header)
        page.wait_for_timeout(1500)

        # Hover across live state & audit trail
        audit_sec = page.locator("text=Audit Trail").first
        if audit_sec.count() > 0:
            move_cursor_to(page, audit_sec, steps=20)
            page.wait_for_timeout(2000)

        policy_sec = page.locator("text=Policy Matrix").first
        if policy_sec.count() > 0:
            move_cursor_to(page, policy_sec, steps=20)
            page.wait_for_timeout(2000)

        while (time.time() - t_global_start) < 164.5:
            page.wait_for_timeout(100)

        total_rec_dur = time.time() - t_global_start
        print(f"\n[RECORD] TOTAL RECORDING TIME: {total_rec_dur:.2f}s (~{total_rec_dur/60:.2f} min)")

        scene_timestamps["total_duration"] = round(total_rec_dur, 2)
        with open(TIMESTAMPS_FILE, "w") as f:
            json.dump(scene_timestamps, f, indent=2)
        print("[RECORD] Saved scene timestamps to:", TIMESTAMPS_FILE)

        # Clean browser flush: close context directly to ensure video file is saved cleanly
        print("[RECORD] Closing context to flush video to disk...")
        context.close()
        browser.close()
        print("[RECORD] Browser closed successfully. Video flushed!")

if __name__ == "__main__":
    record_demo()
