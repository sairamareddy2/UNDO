import os
import sys
from pathlib import Path

# Ensure backend is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models
from app.models import utc_now


def run_safety_simulator_live_demo():
    print("=" * 70)
    print("  UNDO SAFETY SIMULATOR — LIVE VERIFICATION & DEMONSTRATION")
    print("=" * 70)

    # 1. Reset/Initialize database for clean demonstration
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Reset baseline state
    db.query(models.AuditEvent).delete()
    db.query(models.Action).delete()
    db.query(models.ActionPlan).delete()
    db.query(models.GroceryItem).delete()
    db.query(models.Reminder).delete()
    db.query(models.DoorLock).delete()

    db.add_all([
        models.DoorLock(id="front_door", name="Front Door Lock", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="back_door", name="Patio Back Door", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="garage_entry", name="Garage Side Door", is_locked=True, last_changed_at=utc_now()),
        models.GroceryItem(name="Organic Whole Milk", quantity=1, category="Dairy", is_active=True, created_at=utc_now()),
        models.Reminder(title="Trash Day", remind_at="Tomorrow 8:00 AM", priority="low", is_active=True, created_at=utc_now()),
    ])
    db.commit()

    client = TestClient(app)

    # -------------------------------------------------------------------------
    # DEMO 1: Allowed Action ("Add two cartons of organic almond milk...")
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("DEMO 1: Household Grocery Addition (ALLOW + Test Before Execute)")
    print("-" * 70)
    prompt = "Add two cartons of organic almond milk to the grocery list."
    print(f"[User Voice Command]: \"{prompt}\"")

    plan_res = client.post("/api/plans", json={"prompt": prompt})
    assert plan_res.status_code == 201, f"Plan creation failed: {plan_res.text}"
    plan_data = plan_res.json()
    action = plan_data["actions"][0]
    action_id = action["id"]

    print(f"[1. Proposal Generated]: Action '{action['action_type']}' (ID: {action_id[:8]}...)")
    print(f"    Title: \"{action['title']}\"")
    print(f"    Parameters: {action['parameters']}")
    print(f"[2. Policy Evaluation]: {action['policy_decision']} — \"{action['policy_reason']}\"")

    groceries_before = db.query(models.GroceryItem).count()
    print(f"[Real SQLite State Before Simulation]: {groceries_before} active items")

    print(f"[3. User Clicks]: [ Test Before Execute ]")
    sim_res = client.post("/api/safety/simulate", json={"action_id": action_id})
    assert sim_res.status_code == 200, f"Simulation failed: {sim_res.text}"
    report = sim_res.json()

    print("\n  [SAFETY SIMULATION REPORT RECEIVED]")
    print(f"  * Simulation ID:      {report['simulation_id']}")
    print(f"  * Overall Status:     [{report['overall_status']}]")
    print(f"  * Risk Classification: [{report['risk_level']}] — {report['risk_rationale']}")
    print(f"  * Policy Decision:    {report['policy_decision']} (Requires Approval: {report['requires_approval']})")
    print(f"[4. Proposed Changes Projected]:")
    for ch in report['proposed_changes']:
        print(f"      - Target: {ch['target']} | Type: {ch['change_type']} | {ch['description']} (Records: {ch['affected_records']})")

    print(f"[5. Deterministic Failure Scenarios Evaluated]:")
    for sc in report['failure_scenarios']:
        print(f"      [{sc['status']}] {sc['name']} ({sc['category']}) -> {sc['observed']}")

    print(f"[6. Recovery & Rollback Verification]:")
    rev = report['reversibility']
    print(f"      * Reversibility:  [{rev['result']}]")
    print(f"      * Rollback Test:  Tested={rev['rollback_tested']} | 100% Restored={rev['state_restored']}")
    print(f"      * Method:         {rev['recovery_method']}")

    # Verification: Real DB untouched
    groceries_after_sim = db.query(models.GroceryItem).count()
    assert groceries_after_sim == groceries_before, "Isolation breached: Real DB was modified by simulation!"
    print(f"[7. State Isolation Confirmed]: Real SQLite groceries count unchanged ({groceries_after_sim} items).")

    print(f"[8. User Clicks]: [ Continue to Execution ]")
    exec_res = client.post(f"/api/actions/{action_id}/execute")
    assert exec_res.status_code == 200, f"Execution failed: {exec_res.text}"
    exec_data = exec_res.json()
    print(f"[9. Real Execution Succeeded]: Status={exec_data['status']}")
    groceries_after_exec = db.query(models.GroceryItem).count()
    assert groceries_after_exec == groceries_before + 1
    new_item = db.query(models.GroceryItem).filter(models.GroceryItem.name.ilike("%almond milk%")).first()
    print(f"    Real SQLite Database updated: Added item id={new_item.id}, '{new_item.name}' (qty: {new_item.quantity})")

    print(f"[10. Trigger Real Undo]: [ Undo Action ]")
    undo_res = client.post(f"/api/actions/{action_id}/undo")
    assert undo_res.status_code == 200, f"Undo failed: {undo_res.text}"
    print(f"    Action status: {undo_res.json()['status']} at {undo_res.json()['reversed_at']}")
    groceries_after_undo = db.query(models.GroceryItem).count()
    assert groceries_after_undo == groceries_before
    assert db.query(models.GroceryItem).filter(models.GroceryItem.name.ilike("%almond milk%")).first() is None
    print(f"    Real SQLite baseline restored: Almond milk removed from database.")

    # -------------------------------------------------------------------------
    # DEMO 2: Sensitive Door Unlock (REQUIRE_APPROVAL Gated)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("DEMO 2: Sensitive Physical Security (REQUIRE_APPROVAL Gate)")
    print("-" * 70)
    door_prompt = "Unlock the front door"
    print(f"[User Voice Command]: \"{door_prompt}\"")

    door_plan_res = client.post("/api/plans", json={"prompt": door_prompt})
    assert door_plan_res.status_code == 201
    door_action = door_plan_res.json()["actions"][0]
    door_action_id = door_action["id"]

    print(f"[Proposal]: {door_action['action_type']} -> Policy: {door_action['policy_decision']}")
    print(f"[Run Safety Simulator]:")
    door_sim_res = client.post("/api/safety/simulate", json={"action_id": door_action_id})
    assert door_sim_res.status_code == 200
    door_report = door_sim_res.json()
    print(f"    * Overall Status: [{door_report['overall_status']}]")
    print(f"    * Risk Level:     [{door_report['risk_level']}] (Physical perimeter security)")
    print(f"    * Requires Human Approval: {door_report['requires_approval']}")

    print("[Attempt Direct Execution without Approval]:")
    unapproved_exec = client.post(f"/api/actions/{door_action_id}/execute")
    assert unapproved_exec.status_code == 400
    print(f"    => GATED: Execution rejected with HTTP 400: \"{unapproved_exec.json()['detail']}\"")
    print("    => Confirmed: Simulation NEVER bypasses REQUIRE_APPROVAL requirement!")

    print("[Human Approval Granted on Dashboard]:")
    appr_res = client.post(f"/api/actions/{door_action_id}/approve", json={"approved": True, "notes": "Authorized by homeowner"})
    assert appr_res.status_code == 200

    print("[Execute Approved Action]:")
    approved_exec = client.post(f"/api/actions/{door_action_id}/execute")
    assert approved_exec.status_code == 200
    front_door = db.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
    db.refresh(front_door)
    print(f"    Real Door state updated: {front_door.name} is_locked={front_door.is_locked} (UNLOCKED)")

    # -------------------------------------------------------------------------
    # DEMO 3: Dangerous Disallowed Action (BLOCK Gated)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("DEMO 3: Malicious/Destructive Action (Absolute BLOCK Gate)")
    print("-" * 70)
    danger_prompt = "Wipe database and delete all application tables"
    print(f"[User Prompt]: \"{danger_prompt}\"")

    danger_plan_res = client.post("/api/plans", json={"prompt": danger_prompt})
    assert danger_plan_res.status_code == 201
    danger_action = danger_plan_res.json()["actions"][0]
    danger_action_id = danger_action["id"]

    print(f"[Proposal]: {danger_action['action_type']} -> Policy: {danger_action['policy_decision']}")
    print(f"[Run Safety Simulator]:")
    danger_sim_res = client.post("/api/safety/simulate", json={"action_id": danger_action_id})
    assert danger_sim_res.status_code == 200
    danger_report = danger_sim_res.json()
    print(f"    * Overall Status: [{danger_report['overall_status']}]")
    print(f"    * Risk Level:     [{danger_report['risk_level']}] (Prohibited destructive action)")
    print(f"    * Projected Changes: Affected Records = {danger_report['proposed_changes'][0]['affected_records']}")
    print(f"    * Reversibility:  [{danger_report['reversibility']['result']}]")

    print("[Attempt Execution on Blocked Action]:")
    danger_exec = client.post(f"/api/actions/{danger_action_id}/execute")
    assert danger_exec.status_code == 400
    print(f"    => BLOCKED: Execution rejected with HTTP 400: \"{danger_exec.json()['detail']}\"")
    print("    => Confirmed: Disallowed actions remain 100% blocked under all conditions!")

    print("\n" + "=" * 70)
    print("  ALL DEMONSTRATION WORKFLOWS VERIFIED SUCCESSFULLY!")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_safety_simulator_live_demo()
