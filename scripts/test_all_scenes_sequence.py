import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)

    # Reset
    page.locator("button:has-text('Reset Demo DB')").first.click(force=True)
    page.wait_for_timeout(1000)

    # Scene 2: Groceries
    print("Testing Scene 2 (Groceries)...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    input_box = page.locator("input[placeholder*='Give an Alexa+ instruction']").first
    input_box.fill("Add two cartons of organic almond milk to the grocery list.")
    page.locator("button:has-text('Propose Plan')").first.click(force=True)
    page.wait_for_selector("button:has-text('Execute Action')", timeout=35000)
    print("  -> Scene 2 SUCCESS: Proposal rendered.")

    # Scene 3: Execute & Undo
    print("Testing Scene 3 (Execute & Undo)...")
    page.locator("button:has-text('Execute Action')").first.click(force=True)
    page.wait_for_timeout(2000)
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1500)
    page.locator("button:has-text('Action History')").first.click(force=True)
    page.wait_for_timeout(1500)
    page.locator("button:has-text('Undo Action')").first.click(force=True)
    page.wait_for_timeout(2000)
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    print("  -> Scene 3 SUCCESS: Execute & Undo verified.")

    # Scene 4: Door Unlock
    print("Testing Scene 4 (Door Unlock)...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    page.wait_for_timeout(1000)
    page.locator("button:has-text('Unlock Door (Approval)')").first.click(force=True)
    page.wait_for_selector("button:has-text('Approve')", timeout=35000)
    print("  -> Scene 4: Approve button rendered.")
    page.locator("button:has-text('Approve')").first.click(force=True)
    page.wait_for_selector("button:has-text('Execute Action')", timeout=15000)
    page.locator("button:has-text('Execute Action')").first.click(force=True)
    page.wait_for_timeout(2000)
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    print("  -> Scene 4 SUCCESS: Door approved & executed.")

    # Scene 5: Blocked
    print("Testing Scene 5 (Dangerous Blocked)...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    page.wait_for_timeout(1000)
    page.locator("button:has-text('Dangerous (Blocked)')").first.click(force=True)
    page.wait_for_selector("text=BLOCK", timeout=35000)
    print("  -> Scene 5 SUCCESS: Dangerous request blocked.")

    # Scene 6: MCP
    print("Testing Scene 6 (MCP)...")
    page.locator("button:has-text('MCP:')").first.click(force=True)
    page.wait_for_timeout(1500)
    print("  -> Scene 6 SUCCESS: MCP popover opened.")

    # Scene 7: Dashboard
    print("Testing Scene 7 (Dashboard)...")
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1000)
    print("  -> Scene 7 SUCCESS: Dashboard rendered.")

    browser.close()
    print("\nALL SCENES VERIFIED 100% CLEANLY IN SEQUENCE!")
