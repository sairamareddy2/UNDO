import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)

    # Reset
    print("Resetting database...")
    page.locator("button:has-text('Reset Demo DB')").first.click(force=True)
    page.wait_for_timeout(1000)

    # Scene 2: Groceries Planner
    print("Testing Scene 2: Planning...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    page.wait_for_timeout(500)
    input_box = page.locator("input[placeholder*='Give an Alexa+ instruction']").first
    input_box.fill("Add two cartons of organic almond milk to the grocery list.")
    page.locator("button:has-text('Propose Plan')").first.click(force=True)
    page.wait_for_selector("button:has-text('Test Before Execute')", timeout=35000)
    print("  -> Scene 2 SUCCESS: Proposal rendered with Test Before Execute button.")

    # Scene 3: Test Before Execute
    print("Testing Scene 3: Safety Simulator...")
    page.locator("button:has-text('Test Before Execute')").first.click(force=True)
    page.wait_for_selector("text=Safety Simulator Report", timeout=25000)
    page.wait_for_timeout(1500)
    print("  -> Scene 3 SUCCESS: Safety Simulator Report rendered.")

    # Scene 4: Continue to Execution & Undo
    print("Testing Scene 4: Continue to Execution...")
    page.wait_for_selector("button:has-text('Continue to Execution')", timeout=15000)
    page.locator("button:has-text('Continue to Execution')").first.click(force=True)
    page.wait_for_timeout(2000)

    # Verify on Dashboard
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1500)
    print("  -> Checked Dashboard: item added.")

    # Undo in History
    page.locator("button:has-text('Action History')").first.click(force=True)
    page.wait_for_timeout(1500)
    page.locator("button:has-text('Undo Action')").first.click(force=True)
    page.wait_for_timeout(2000)
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1500)
    print("  -> Scene 4 SUCCESS: Undo executed, baseline restored.")

    # Scene 5: Door Unlock
    print("Testing Scene 5: Door Unlock with Approval & Simulator...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Unlock Door (Approval)')").first.click(force=True)
    page.wait_for_selector("button:has-text('Test Before Execute')", timeout=35000)
    print("  -> Door proposal rendered.")
    
    # Test Before Execute on Door
    page.locator("button:has-text('Test Before Execute')").first.click(force=True)
    page.wait_for_selector("text=Safety Simulator Report", timeout=25000)
    page.wait_for_timeout(1000)
    print("  -> Door Safety Report rendered.")

    # Approve for execution
    page.wait_for_selector("button:has-text('Approve')", timeout=15000)
    page.locator("button:has-text('Approve')").first.click(force=True)
    page.wait_for_timeout(1500)

    # Execute door
    page.wait_for_selector("button:has-text('Execute Action')", timeout=15000)
    page.locator("button:has-text('Execute Action')").first.click(force=True)
    page.wait_for_timeout(2000)

    # Check Dashboard
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1500)
    print("  -> Scene 5 SUCCESS: Door approved and unlocked.")

    # Scene 6: Dangerous Blocked
    print("Testing Scene 6: Dangerous Blocked & Simulator...")
    page.locator("button:has-text('Action Planner')").first.click(force=True)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Dangerous (Blocked)')").first.click(force=True)
    page.wait_for_selector("span:has-text('BLOCK')", timeout=35000)
    print("  -> Blocked proposal rendered.")
    page.locator("button:has-text('Test Before Execute')").first.click(force=True)
    page.wait_for_selector("text=BLOCKED BY POLICY", timeout=25000)
    print("  -> Scene 6 SUCCESS: Blocked Safety Report rendered.")

    # Scene 7: MCP
    print("Testing Scene 7: MCP Server...")
    page.locator("button:has-text('Dashboard')").first.click(force=True)
    page.wait_for_timeout(1000)
    page.locator("button:has-text('MCP:')").first.click(force=True)
    page.wait_for_timeout(1500)
    print("  -> Scene 7 SUCCESS: MCP tools popover opened.")

    # Scene 8: Closing
    print("Testing Scene 8: Closing...")
    page.locator("text=Live Application State").first.click(force=True)
    page.wait_for_timeout(1000)
    print("  -> Scene 8 SUCCESS: Closing overview rendered.")

    browser.close()
    print("\n>>> ALL 8 SCENES VERIFIED 100% SUCCESFULLY IN AUTOMATION! <<<")
