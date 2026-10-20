import os
import uvicorn
from typing import Any, Dict, List, Optional
from mcp.server import MCPServer
from app.config import settings
from app.database import SessionLocal, init_db
from app import models
from app.models import utc_now
from app.policy.engine import PolicyEngine, PolicyDecision
from app.executor.executor import ActionExecutor, ActionExecutionError
from app.executor.undo import UndoManager, UndoError


def create_mcp_server(name: str = "undo-action-governance") -> MCPServer:
    """
    Initializes and configures the official Python MCP server for UNDO.
    Exposes read-only inspection tools and governed, reversible mutating tools.
    All state changes reuse the existing database and deterministic policy engine.
    """
    server = MCPServer(
        name=name,
        instructions=(
            "UNDO is a deterministic action-governance layer for Alexa+ simulated experiences. "
            "Tools allow inspecting household state (doors, groceries, reminders) and executing "
            "governed, reversible operations. High-risk operations (such as door locks) strictly "
            "require human confirmation through the UNDO dashboard and cannot be executed directly."
        ),
    )

    # 1. Tool: list_groceries (Read-Only)
    @server.tool()
    def list_groceries() -> Dict[str, Any]:
        """
        List all active items in the simulated household grocery list.
        Read-only query against the SQLite database.
        """
        db = SessionLocal()
        try:
            items = (
                db.query(models.GroceryItem)
                .filter(models.GroceryItem.is_active == True)  # noqa: E712
                .order_by(models.GroceryItem.created_at.desc())
                .all()
            )
            groceries = [
                {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "category": item.category,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ]
            return {"count": len(groceries), "groceries": groceries}
        finally:
            db.close()

    # 2. Tool: get_household_state (Read-Only)
    @server.tool()
    def get_household_state() -> Dict[str, Any]:
        """
        Retrieve current state of all simulated household entities (door locks, reminders, groceries).
        Read-only query against the SQLite database.
        """
        db = SessionLocal()
        try:
            doors = db.query(models.DoorLock).all()
            groceries = (
                db.query(models.GroceryItem)
                .filter(models.GroceryItem.is_active == True)  # noqa: E712
                .all()
            )
            reminders = (
                db.query(models.Reminder)
                .filter(models.Reminder.is_active == True)  # noqa: E712
                .all()
            )

            return {
                "doors": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "is_locked": d.is_locked,
                        "last_changed_at": d.last_changed_at.isoformat() if d.last_changed_at else None,
                    }
                    for d in doors
                ],
                "groceries": [
                    {"id": g.id, "name": g.name, "quantity": g.quantity, "category": g.category}
                    for g in groceries
                ],
                "reminders": [
                    {"id": r.id, "title": r.title, "remind_at": r.remind_at, "priority": r.priority}
                    for r in reminders
                ],
            }
        finally:
            db.close()

    # 3. Tool: get_action_history (Read-Only)
    @server.tool()
    def get_action_history(limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve recent actions, their policy governance decisions, execution state, and reversibility flags.
        """
        db = SessionLocal()
        try:
            actions = (
                db.query(models.Action)
                .order_by(models.Action.created_at.desc())
                .limit(min(max(1, limit), 50))
                .all()
            )
            return {
                "count": len(actions),
                "actions": [
                    {
                        "id": a.id,
                        "action_type": a.action_type,
                        "title": a.title,
                        "policy_decision": a.policy_decision,
                        "policy_reason": a.policy_reason,
                        "status": a.status,
                        "is_reversible": a.is_reversible,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                        "executed_at": a.executed_at.isoformat() if a.executed_at else None,
                        "reversed_at": a.reversed_at.isoformat() if a.reversed_at else None,
                    }
                    for a in actions
                ],
            }
        finally:
            db.close()

    # 4. Tool: add_grocery_item (State-Changing, Governed, Reversible)
    @server.tool()
    def add_grocery_item(name: str, quantity: int = 1, category: str = "General") -> Dict[str, Any]:
        """
        Add an item to the simulated grocery list.
        Evaluates the deterministic policy engine before execution.
        Standard quantities are allowed; bulk orders (>100 units) require human approval; empty names are blocked.
        Captures state snapshot for verified reversal.
        """
        db = SessionLocal()
        try:
            # 1. Deterministic Policy Evaluation
            evaluation = PolicyEngine.evaluate("add_grocery_item", {
                "name": name,
                "quantity": quantity,
                "category": category,
            })

            validated_params = evaluation.validated_params or {"name": name, "quantity": quantity, "category": category}

            # 2. Record ActionPlan and Action in SQLite
            plan = models.ActionPlan(prompt=f"MCP: Add {quantity}x {name} ({category})", status="PENDING")
            db.add(plan)
            db.flush()

            action_status = "BLOCKED" if evaluation.decision == PolicyDecision.BLOCK else "PENDING"
            action = models.Action(
                plan_id=plan.id,
                action_type="add_grocery_item",
                title=f"Add {validated_params.get('quantity', quantity)}x {validated_params.get('name', name)} to Groceries",
                parameters=validated_params,
                policy_decision=evaluation.decision,
                policy_reason=evaluation.reason,
                status=action_status,
                is_reversible=evaluation.is_reversible,
                created_at=utc_now(),
            )
            db.add(action)
            db.flush()

            # Record audit event
            db.add(models.AuditEvent(
                action_id=action.id,
                event_type="POLICY_EVALUATED",
                details={"source": "mcp", "decision": evaluation.decision, "reason": evaluation.reason},
                timestamp=utc_now(),
            ))

            # 3. Handle Policy Decision
            if evaluation.decision == PolicyDecision.BLOCK:
                db.commit()
                return {
                    "status": "BLOCKED",
                    "action_id": action.id,
                    "reason": evaluation.reason,
                    "executed": False,
                    "message": "Action was blocked by deterministic security policy.",
                }

            if evaluation.decision == PolicyDecision.REQUIRE_APPROVAL:
                db.commit()
                return {
                    "status": "REQUIRE_APPROVAL",
                    "action_id": action.id,
                    "reason": evaluation.reason,
                    "executed": False,
                    "message": "Bulk purchase exceeds threshold. Action queued for human approval via UNDO dashboard.",
                }

            # 4. ALLOW: Execute action and record before/after state
            executed_action = ActionExecutor.execute_action(db, action)
            db.commit()

            return {
                "status": "EXECUTED",
                "action_id": executed_action.id,
                "is_reversible": True,
                "result": executed_action.execution_result,
                "after_state": executed_action.after_state,
                "message": f"Successfully added {quantity}x '{name}' to grocery list (Reversible).",
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e), "executed": False}
        finally:
            db.close()

    # 5. Tool: create_reminder (State-Changing, Governed, Reversible)
    @server.tool()
    def create_reminder(title: str, remind_at: str, priority: str = "medium") -> Dict[str, Any]:
        """
        Schedule a household reminder.
        Evaluates parameters and deterministic policy engine.
        Reversible through undo_action.
        """
        db = SessionLocal()
        try:
            evaluation = PolicyEngine.evaluate("create_reminder", {
                "title": title,
                "remind_at": remind_at,
                "priority": priority,
            })

            validated_params = evaluation.validated_params or {"title": title, "remind_at": remind_at, "priority": priority}

            plan = models.ActionPlan(prompt=f"MCP: Reminder '{title}' at {remind_at}", status="PENDING")
            db.add(plan)
            db.flush()

            action_status = "BLOCKED" if evaluation.decision == PolicyDecision.BLOCK else "PENDING"
            action = models.Action(
                plan_id=plan.id,
                action_type="create_reminder",
                title=f"Reminder: {validated_params.get('title', title)} at {validated_params.get('remind_at', remind_at)}",
                parameters=validated_params,
                policy_decision=evaluation.decision,
                policy_reason=evaluation.reason,
                status=action_status,
                is_reversible=evaluation.is_reversible,
                created_at=utc_now(),
            )
            db.add(action)
            db.flush()

            db.add(models.AuditEvent(
                action_id=action.id,
                event_type="POLICY_EVALUATED",
                details={"source": "mcp", "decision": evaluation.decision, "reason": evaluation.reason},
                timestamp=utc_now(),
            ))

            if evaluation.decision == PolicyDecision.BLOCK:
                db.commit()
                return {
                    "status": "BLOCKED",
                    "action_id": action.id,
                    "reason": evaluation.reason,
                    "executed": False,
                }

            executed_action = ActionExecutor.execute_action(db, action)
            db.commit()

            return {
                "status": "EXECUTED",
                "action_id": executed_action.id,
                "is_reversible": True,
                "result": executed_action.execution_result,
                "message": f"Reminder '{title}' scheduled for {remind_at}.",
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e), "executed": False}
        finally:
            db.close()

    # 6. Tool: set_door_lock (Physical Entry, Strictly Requires Approval)
    @server.tool()
    def set_door_lock(door_id: str, target_state: str) -> Dict[str, Any]:
        """
        Request changing a smart door lock state (locked/unlocked).
        STRICT REQUIREMENT: Door lock mutations always require explicit human confirmation.
        This tool queues the action as PENDING approval on the UNDO dashboard.
        Tool invocation does NOT execute or bypass approval.
        """
        db = SessionLocal()
        try:
            evaluation = PolicyEngine.evaluate("set_door_lock", {
                "door_id": door_id,
                "target_state": target_state,
            })

            plan = models.ActionPlan(prompt=f"MCP: Set {door_id} lock to {target_state}", status="PENDING")
            db.add(plan)
            db.flush()

            action_status = "BLOCKED" if evaluation.decision == PolicyDecision.BLOCK else "PENDING"
            action = models.Action(
                plan_id=plan.id,
                action_type="set_door_lock",
                title=f"Set {door_id.replace('_', ' ').title()} to {target_state.upper()}",
                parameters=evaluation.validated_params or {"door_id": door_id, "target_state": target_state},
                policy_decision=evaluation.decision,
                policy_reason=evaluation.reason,
                status=action_status,
                is_reversible=evaluation.is_reversible,
                created_at=utc_now(),
            )
            db.add(action)
            db.flush()

            db.add(models.AuditEvent(
                action_id=action.id,
                event_type="POLICY_EVALUATED",
                details={"source": "mcp", "decision": evaluation.decision, "reason": evaluation.reason},
                timestamp=utc_now(),
            ))

            db.commit()

            if evaluation.decision == PolicyDecision.BLOCK:
                return {
                    "status": "BLOCKED",
                    "action_id": action.id,
                    "reason": evaluation.reason,
                    "executed": False,
                }

            # Return requirement for human confirmation
            return {
                "status": "REQUIRE_APPROVAL",
                "action_id": action.id,
                "reason": evaluation.reason,
                "executed": False,
                "message": (
                    f"Physical security impact: Changing {door_id} lock state to '{target_state}' "
                    "requires explicit confirmation on the UNDO dashboard. Tool call cannot bypass approval."
                ),
            }
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e), "executed": False}
        finally:
            db.close()

    # 7. Tool: undo_action (State Reversal / Rollback)
    @server.tool()
    def undo_action(action_id: str) -> Dict[str, Any]:
        """
        Undo a previously executed reversible action and restore prior database state.
        Validates that the action is in EXECUTED state, supports reversal, and has not already been reversed.
        """
        db = SessionLocal()
        try:
            action = db.query(models.Action).filter(models.Action.id == action_id).first()
            if not action:
                return {"status": "ERROR", "message": f"Action '{action_id}' not found."}

            reversed_action = UndoManager.undo_action(db, action)
            return {
                "status": "REVERSED",
                "action_id": reversed_action.id,
                "action_type": reversed_action.action_type,
                "reversed_at": reversed_action.reversed_at.isoformat() if reversed_action.reversed_at else None,
                "restored_before_state": reversed_action.before_state,
                "message": f"Successfully reversed action '{action_id}'. Previous state restored in SQLite.",
            }
        except UndoError as e:
            return {"status": "REJECTED", "error": str(e), "message": "Undo request rejected by governance rules."}
        except Exception as e:
            db.rollback()
            return {"status": "FAILED", "error": str(e)}
        finally:
            db.close()

    return server


# Global server instance and Starlette Streamable HTTP application
mcp_server = create_mcp_server()
mcp_app = mcp_server.streamable_http_app()


def run_mcp_server(host: str = "127.0.0.1", port: Optional[int] = None):
    """Entry point to run the standalone MCP server on port 8001."""
    init_db()
    server_port = port or settings.MCP_SERVER_PORT
    print(f"Starting UNDO MCP Server (Streamable HTTP) on http://{host}:{server_port}/mcp ...")
    uvicorn.run(mcp_app, host=host, port=server_port, log_level="info")


if __name__ == "__main__":
    run_mcp_server()
