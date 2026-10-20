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
        # SCENE 1: Introduction (Target: ~24.5s)
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
        ]
        for b in badges:
            if b.count() > 0:
                move_cursor_to(page, b, steps=15)
                page.wait_for_timeout(1000)

        # 3. Overview of Smart Home Doors
        doors_card = page.locator("text=Front Door Lock").first
        if doors_card.count() > 0:
            move_cursor_to(page, doors_card, steps=20)
            page.wait_for_timeout(1500)

        # 4. Overview of Groceries & Reminders
        groceries_card = page.locator("text=Organic Whole Milk").first
        if groceries_card.count() > 0:
            move_cursor_to(page, groceries_card, steps=15)
            page.wait_for_timeout(1200)

        # 5. Sidebar Policy Matrix
        policy_matrix = page.locator("text=Policy Matrix").first
        if policy_matrix.count() > 0:
            move_cursor_to(page, policy_matrix, steps=20)
            page.wait_for_timeout(2000)

        # Hold for Scene 1 spoken narration
        while (time.time() - t_global_start) < 24.5:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 1 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 2: Natural-Language Planning (Target: ~20s)
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
        page.wait_for_selector("button:has-text('Execute Action'):not([disabled])", timeout=35000)
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

        while (time.time() - t_global_start - s2_time) < 19.5:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 2 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 3: ALLOW, Execute, and Undo (Target: ~21s)
        # =====================================================================
        s3_time = time.time() - t_global_start
        scene_timestamps["scene3"] = round(s3_time, 2)
        print(f"\n[RECORD] === SCENE 3: EXECUTE & UNDO (Start: {s3_time:.2f}s) ===")
        exec_btn = page.locator("button:has-text('Execute Action'):not([disabled])").first
        click_with_cursor(page, exec_btn)
        page.wait_for_timeout(1500)

        dash_tab = page.locator("button:has-text('Dashboard')").first
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)

        # Highlight new grocery item in table
        grocery_item = page.locator("text=Organic Almond Milk").first
        if grocery_item.count() > 0:
            move_cursor_to(page, grocery_item, steps=20)
            page.wait_for_timeout(1800)

        # Switch to Action History to undo
        history_tab = page.locator("button:has-text('Action History')").first
        click_with_cursor(page, history_tab)
        page.wait_for_timeout(1200)

        page.wait_for_selector("button:has-text('Undo Action'):not([disabled])", timeout=15000)
        undo_btn = page.locator("button:has-text('Undo Action'):not([disabled])").first
        click_with_cursor(page, undo_btn)
        page.wait_for_timeout(1500)

        # Switch back to Dashboard to show rollback verified
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1500)

        while (time.time() - t_global_start - s3_time) < 21.0:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 3 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 4: Human Approval (Target: ~26s)
        # =====================================================================
        s4_time = time.time() - t_global_start
        scene_timestamps["scene4"] = round(s4_time, 2)
        print(f"\n[RECORD] === SCENE 4: HUMAN APPROVAL (Start: {s4_time:.2f}s) ===")
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(800)

        unlock_quick_btn = page.locator("button:has-text('Unlock Door (Approval)')").first
        click_with_cursor(page, unlock_quick_btn)

        print("[RECORD] Waiting for REQUIRE APPROVAL proposal card...")
        page.wait_for_selector("button:has-text('Approve'):not([disabled])", timeout=35000)
        inject_cursor(page)

        # Highlight REQUIRE APPROVAL badge
        req_badge = page.locator("text=REQUIRE APPROVAL").first
        if req_badge.count() > 0:
            move_cursor_to(page, req_badge, steps=15)
            page.wait_for_timeout(2000)

        # Highlight policy reason
        sec_reason = page.locator("text=Physical security impact:").first
        if sec_reason.count() > 0:
            move_cursor_to(page, sec_reason, steps=15)
            page.wait_for_timeout(2000)

        # Click Approve (wait until enabled)
        approve_btn = page.locator("button:has-text('Approve'):not([disabled])").first
        click_with_cursor(page, approve_btn)
        
        # Wait for Execute Action to become enabled
        page.wait_for_selector("button:has-text('Execute Action'):not([disabled])", timeout=15000)
        page.wait_for_timeout(800)

        # Click Execute Action
        exec_btn = page.locator("button:has-text('Execute Action'):not([disabled])").first
        click_with_cursor(page, exec_btn)
        page.wait_for_timeout(1500)

        # Switch to Dashboard to show UNLOCKED door
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)
        door_status = page.locator("text=UNLOCKED").first
        if door_status.count() > 0:
            move_cursor_to(page, door_status, steps=20)
            page.wait_for_timeout(2500)

        while (time.time() - t_global_start - s4_time) < 26.0:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 4 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 5: Destructive Action Blocked (Target: ~23s)
        # =====================================================================
        s5_time = time.time() - t_global_start
        scene_timestamps["scene5"] = round(s5_time, 2)
        print(f"\n[RECORD] === SCENE 5: BLOCKED (Start: {s5_time:.2f}s) ===")
        click_with_cursor(page, planner_tab)
        page.wait_for_timeout(800)

        dangerous_quick_btn = page.locator("button:has-text('Dangerous (Blocked)')").first
        click_with_cursor(page, dangerous_quick_btn)

        print("[RECORD] Waiting for BLOCK card...")
        page.wait_for_selector("text=BLOCK", timeout=35000)
        inject_cursor(page)

        # Highlight BLOCK badge
        block_badge = page.locator("text=BLOCK").first
        if block_badge.count() > 0:
            move_cursor_to(page, block_badge, steps=15)
            page.wait_for_timeout(2000)

        # Switch to Action History to show audit log
        click_with_cursor(page, history_tab)
        page.wait_for_timeout(1000)

        audit_tab_btn = page.locator("button:has-text('Audit Log')").first
        if audit_tab_btn.count() > 0:
            click_with_cursor(page, audit_tab_btn)
            page.wait_for_timeout(2500)

        while (time.time() - t_global_start - s5_time) < 23.0:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 5 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 6: MCP Streamable HTTP Integration (Target: ~21s)
        # =====================================================================
        s6_time = time.time() - t_global_start
        scene_timestamps["scene6"] = round(s6_time, 2)
        print(f"\n[RECORD] === SCENE 6: MCP INTEGRATION (Start: {s6_time:.2f}s) ===")
        mcp_btn = page.locator("button:has-text('MCP:')").first
        click_with_cursor(page, mcp_btn)
        page.wait_for_timeout(1200)

        tools = [
            page.locator("text=list_groceries").first,
            page.locator("text=get_household_state").first,
            page.locator("text=set_door_lock").first,
            page.locator("text=undo_action").first,
        ]
        for t in tools:
            if t.count() > 0:
                move_cursor_to(page, t, steps=12)
                page.wait_for_timeout(800)

        mcp_url = page.locator("text=:8001/mcp").first
        if mcp_url.count() > 0:
            move_cursor_to(page, mcp_url, steps=15)
            page.wait_for_timeout(2000)

        while (time.time() - t_global_start - s6_time) < 20.5:
            page.wait_for_timeout(200)
        print(f"[RECORD] Scene 6 ended at {time.time() - t_global_start:.2f}s")

        # =====================================================================
        # SCENE 7: Closing Summary (Target: ~17s)
        # =====================================================================
        s7_time = time.time() - t_global_start
        scene_timestamps["scene7"] = round(s7_time, 2)
        print(f"\n[RECORD] === SCENE 7: CLOSING (Start: {s7_time:.2f}s) ===")
        click_with_cursor(page, dash_tab)
        page.wait_for_timeout(1200)

        completed_metric = page.locator("text=Completed Actions").first
        if completed_metric.count() > 0:
            move_cursor_to(page, completed_metric, steps=15)
            page.wait_for_timeout(1800)

        undo_metric = page.locator("text=Rollbacks (Undos)").first
        if undo_metric.count() > 0:
            move_cursor_to(page, undo_metric, steps=15)
            page.wait_for_timeout(1800)

        move_cursor_to(page, logo, steps=20)
        page.wait_for_timeout(2500)

        while (time.time() - t_global_start - s7_time) < 17.0:
            page.wait_for_timeout(200)

        total_elapsed = time.time() - t_global_start
        scene_timestamps["total_duration"] = round(total_elapsed, 2)
        print(f"[RECORD] Scene 7 completed. TOTAL DURATION: {total_elapsed:.2f}s ({total_elapsed/60:.2f} min)")

        with open(TIMESTAMPS_FILE, "w") as f:
            json.dump(scene_timestamps, f, indent=2)
        print("[RECORD] Scene timestamps saved to:", TIMESTAMPS_FILE)

        print("\n[RECORD] Closing Playwright context and saving video file...")
        context.close()
        browser.close()
        print("[RECORD] Raw browser recording completed successfully!")

if __name__ == "__main__":
    record_demo()
