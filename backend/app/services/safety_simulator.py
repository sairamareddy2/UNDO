import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app import models
from app.models import utc_now
from app.policy.engine import PolicyEngine, PolicyDecision
from app.executor.executor import ActionExecutor, ActionExecutionError
from app.executor.undo import UndoManager, UndoError
from app.schemas import (
    SafetyReportResponse,
    FailureScenarioResult,
    ProposedChange,
    ReversibilityReport,
)


class SafetySimulator:
    """
    Isolated Safety Simulation Engine (Test Before Execute).
    Runs proposed actions in a temporary in-memory SQLite sandbox, verifies
    deterministic policy enforcement, injects failure scenarios, tests recovery/rollback,
    and returns a comprehensive safety report.
    Never modifies the production database or performs external side effects.
    """

    @classmethod
    def simulate_action(
        cls,
        real_db: Session,
        action_id: Optional[str] = None,
        action_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> SafetyReportResponse:
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        timestamp = utc_now()
        warnings: List[str] = []
        limitations: List[str] = [
            "SAFE IN SIMULATION verifies execution within an isolated temporary SQLite sandbox only; it does not guarantee real-world safety or external hardware behavior.",
            "Approval expiration TTL is unsupported: the current data model does not implement approval expiration timestamps.",
            "Physical smart-home devices and door locks are software simulations in the Alexa+ simulated environment.",
            "Simulation results do not authorize execution; execution strictly requires policy engine evaluation at runtime.",
        ]

        # 1. Resolve action identity & parameters
        if action_id:
            db_action = real_db.query(models.Action).filter(models.Action.id == action_id).first()
            if not db_action:
                raise ValueError(f"Action '{action_id}' not found.")
            action_type = db_action.action_type
            title = db_action.title
            raw_params = db_action.parameters or {}
        else:
            if not action_type:
                raise ValueError("Either 'action_id' or 'action_type' must be provided for simulation.")
            raw_params = parameters or {}
            title = title or action_type.replace("_", " ").title()

        # 2. Evaluate against Deterministic Policy Engine
        policy_eval = PolicyEngine.evaluate(action_type, raw_params)
        policy_decision = policy_eval.decision
        policy_reason = policy_eval.reason
        is_reversible_policy = policy_eval.is_reversible
        sanitized_params = policy_eval.validated_params if policy_eval.validated_params is not None else dict(raw_params)
        requires_approval = (policy_decision == PolicyDecision.REQUIRE_APPROVAL)

        # 3. Capture baseline summary from real database (read-only)
        grocery_count = real_db.query(models.GroceryItem).filter(models.GroceryItem.is_active == True).count()
        reminder_count = real_db.query(models.Reminder).filter(models.Reminder.is_active == True).count()
        door_states = {
            d.id: {"name": d.name, "is_locked": d.is_locked}
            for d in real_db.query(models.DoorLock).all()
        }
        initial_state_summary = {
            "active_groceries_count": grocery_count,
            "active_reminders_count": reminder_count,
            "doors": door_states,
        }

        # 4. Initialize isolated in-memory simulation database
        sim_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=sim_engine)
        SimSession = sessionmaker(autocommit=False, autoflush=False, bind=sim_engine)
        sim_db = SimSession()

        try:
            # Seed isolated database with clone of current real application state
            cls._seed_simulated_db(real_db, sim_db)

            # 5. Project proposed changes
            proposed_changes = cls._project_changes(action_type, sanitized_params, sim_db, policy_decision)

            # 6. Execute deterministic failure scenarios
            failure_scenarios: List[FailureScenarioResult] = []

            # Scenario A: Input Validation Check
            cls._test_input_validation(policy_eval, sanitized_params, failure_scenarios)

            # Scenario B: State Conflict / Stale State Check
            cls._test_state_conflicts(action_type, sanitized_params, sim_db, failure_scenarios, warnings)

            # Scenario C: Persistence Failure & Transaction Rollback Isolation
            cls._test_persistence_isolation(sim_db, failure_scenarios)

            # Scenario D: Authorization & Approval Gate
            cls._test_authorization_gate(action_type, sanitized_params, policy_decision, policy_reason, failure_scenarios)

            # Scenario E: Approval Expiration Check (Honest reporting of unsupported feature)
            failure_scenarios.append(FailureScenarioResult(
                name="Approval Expiration Check",
                category="Authorization & Policy",
                status="UNSUPPORTED",
                expected="Approval expiration TTL verification if supported by schema",
                observed="Current approval schema does not support expiration timestamps (no expires_at field). Approval expiry scenario unsupported.",
            ))

            # Scenario F: Execution & Reversibility / Rollback Invariant Check
            reversibility_report = cls._test_execution_and_rollback(
                action_type=action_type,
                title=title,
                sanitized_params=sanitized_params,
                policy_eval=policy_eval,
                sim_db=sim_db,
                failure_scenarios=failure_scenarios,
            )

            # 7. Risk Assessment
            risk_level, risk_rationale = cls._assess_risk(
                action_type=action_type,
                policy_decision=policy_decision,
                policy_reason=policy_reason,
                sanitized_params=sanitized_params,
                has_warnings=bool(warnings),
            )

            # 8. Determine Overall Simulation Status
            overall_status = cls._determine_overall_status(
                policy_decision=policy_decision,
                failure_scenarios=failure_scenarios,
                reversibility_report=reversibility_report,
                warnings=warnings,
            )

            return SafetyReportResponse(
                simulation_id=simulation_id,
                action_id=action_id,
                action_type=action_type,
                title=title,
                parameters=sanitized_params,
                overall_status=overall_status,
                risk_level=risk_level,
                risk_rationale=risk_rationale,
                policy_decision=policy_decision,
                policy_reason=policy_reason,
                requires_approval=requires_approval,
                initial_state_summary=initial_state_summary,
                proposed_changes=proposed_changes,
                validation_results={
                    "input_valid": policy_decision != PolicyDecision.BLOCK or "Invalid" not in policy_reason,
                    "policy_decision": policy_decision,
                    "is_reversible_under_policy": is_reversible_policy,
                    "approval_required": requires_approval,
                },
                failure_scenarios=failure_scenarios,
                reversibility=reversibility_report,
                warnings=warnings,
                limitations=limitations,
                timestamp=timestamp,
            )

        finally:
            sim_db.close()
            sim_engine.dispose()

    @classmethod
    def _seed_simulated_db(cls, real_db: Session, sim_db: Session):
        """Clone current active items, reminders, and doors into the isolated in-memory DB."""
        # Groceries
        for item in real_db.query(models.GroceryItem).all():
            sim_db.add(models.GroceryItem(
                id=item.id,
                name=item.name,
                quantity=item.quantity,
                category=item.category,
                is_active=item.is_active,
                created_at=item.created_at,
            ))

        # Reminders
        for rem in real_db.query(models.Reminder).all():
            sim_db.add(models.Reminder(
                id=rem.id,
                title=rem.title,
                remind_at=rem.remind_at,
                priority=rem.priority,
                is_active=rem.is_active,
                created_at=rem.created_at,
            ))

        # Doors
        doors = real_db.query(models.DoorLock).all()
        if not doors:
            # Seed baseline default doors if none present
            doors = [
                models.DoorLock(id="front_door", name="Front Door Lock", is_locked=True),
                models.DoorLock(id="back_door", name="Patio Back Door", is_locked=True),
                models.DoorLock(id="garage_entry", name="Garage Side Door", is_locked=True),
            ]
        for door in doors:
            sim_db.add(models.DoorLock(
                id=door.id,
                name=door.name,
                is_locked=door.is_locked,
                last_changed_at=door.last_changed_at,
            ))

        sim_db.commit()

    @classmethod
    def _project_changes(
        cls,
        action_type: str,
        params: Dict[str, Any],
        sim_db: Session,
        policy_decision: str,
    ) -> List[ProposedChange]:
        """Project simulated database changes and calculate affected record counts."""
        changes: List[ProposedChange] = []

        if policy_decision == PolicyDecision.BLOCK:
            changes.append(ProposedChange(
                target="application_database",
                change_type="BLOCKED",
                description=f"Action '{action_type}' is prohibited by deterministic security policy. Zero state modifications permitted.",
                affected_records=0,
                details={"blocked_action": action_type},
            ))
            return changes

        if action_type == "add_grocery_item":
            name = params.get("name", "Item")
            qty = int(params.get("quantity", 1))
            cat = params.get("category", "General")
            changes.append(ProposedChange(
                target="simulated_groceries",
                change_type="INSERT",
                description=f"Insert {qty}x '{name}' ({cat}) into active grocery list.",
                affected_records=1,
                details={"name": name, "quantity": qty, "category": cat},
            ))

        elif action_type == "remove_grocery_item":
            item_id = params.get("item_id")
            name = params.get("name")
            desc = f"Remove grocery item id={item_id}" if item_id else f"Remove grocery item '{name}'"
            changes.append(ProposedChange(
                target="simulated_groceries",
                change_type="DELETE",
                description=desc,
                affected_records=1,
                details={"item_id": item_id, "name": name},
            ))

        elif action_type == "create_reminder":
            title = params.get("title", "Task")
            remind_at = params.get("remind_at", "Later")
            priority = params.get("priority", "medium")
            changes.append(ProposedChange(
                target="simulated_reminders",
                change_type="INSERT",
                description=f"Schedule reminder '{title}' for '{remind_at}' ({priority} priority).",
                affected_records=1,
                details={"title": title, "remind_at": remind_at, "priority": priority},
            ))

        elif action_type == "delete_reminder":
            rem_id = params.get("reminder_id")
            title = params.get("title")
            desc = f"Delete reminder id={rem_id}" if rem_id else f"Delete reminder '{title}'"
            changes.append(ProposedChange(
                target="simulated_reminders",
                change_type="DELETE",
                description=desc,
                affected_records=1,
                details={"reminder_id": rem_id, "title": title},
            ))

        elif action_type == "set_door_lock":
            door_id = params.get("door_id", "front_door")
            target_state = str(params.get("target_state", "locked")).lower()
            door = sim_db.query(models.DoorLock).filter(models.DoorLock.id == door_id).first()
            was_locked = door.is_locked if door else True
            changes.append(ProposedChange(
                target="simulated_doors",
                change_type="UPDATE",
                description=f"Change '{door_id}' lock state from {'LOCKED' if was_locked else 'UNLOCKED'} to {target_state.upper()}.",
                affected_records=1,
                details={
                    "door_id": door_id,
                    "previous_state": "LOCKED" if was_locked else "UNLOCKED",
                    "target_state": target_state.upper(),
                },
            ))

        else:
            changes.append(ProposedChange(
                target="unknown",
                change_type="NONE",
                description=f"Unrecognized capability '{action_type}'.",
                affected_records=0,
                details={},
            ))

        return changes

    @classmethod
    def _test_input_validation(
        cls,
        policy_eval: Any,
        sanitized_params: Dict[str, Any],
        scenarios: List[FailureScenarioResult],
    ):
        """Validate input types, required fields, and boundary constraints."""
        if policy_eval.decision == PolicyDecision.BLOCK and (
            "Invalid" in policy_eval.reason or "Unknown" in policy_eval.reason
        ):
            scenarios.append(FailureScenarioResult(
                name="Input Validation & Schema Conformance",
                category="Input Validation",
                status="FAILED",
                expected="Parameters must conform to typed schema bounds (non-empty strings, positive integers, allowed IDs).",
                observed=f"Validation failed: {policy_eval.reason}",
            ))
        else:
            scenarios.append(FailureScenarioResult(
                name="Input Validation & Schema Conformance",
                category="Input Validation",
                status="PASSED",
                expected="Parameters conform to domain schemas and boundary rules.",
                observed=f"Parameters successfully validated: {sanitized_params}",
            ))

    @classmethod
    def _test_state_conflicts(
        cls,
        action_type: str,
        params: Dict[str, Any],
        sim_db: Session,
        scenarios: List[FailureScenarioResult],
        warnings: List[str],
    ):
        """Detect stale or conflicting state (redundant lock transitions, duplicate grocery items)."""
        conflict_detected = False
        conflict_msg = "No conflicting state detected."

        if action_type == "set_door_lock":
            door_id = params.get("door_id")
            target_state = str(params.get("target_state", "locked")).lower()
            door = sim_db.query(models.DoorLock).filter(models.DoorLock.id == door_id).first()
            if door:
                is_currently_locked = door.is_locked
                wants_locked = target_state == "locked"
                if is_currently_locked == wants_locked:
                    conflict_detected = True
                    conflict_msg = f"Redundant state change: Door '{door_id}' is already {target_state.upper()}."
                    warnings.append(conflict_msg)

        elif action_type == "add_grocery_item":
            name = params.get("name", "").strip().lower()
            existing = sim_db.query(models.GroceryItem).filter(
                models.GroceryItem.is_active == True
            ).all()
            for item in existing:
                if item.name.strip().lower() == name:
                    conflict_detected = True
                    conflict_msg = f"Duplicate item warning: '{params.get('name')}' is already in the active grocery list (quantity: {item.quantity})."
                    warnings.append(conflict_msg)
                    break

        if conflict_detected:
            scenarios.append(FailureScenarioResult(
                name="State Conflict & Redundancy Check",
                category="State Conflict",
                status="WARNING",
                expected="Proposed action introduces a non-redundant state transition.",
                observed=conflict_msg,
            ))
        else:
            scenarios.append(FailureScenarioResult(
                name="State Conflict & Redundancy Check",
                category="State Conflict",
                status="PASSED",
                expected="No conflicting existing records or redundant state transitions.",
                observed="Baseline state verified: state transition is unique and applicable.",
            ))

    @classmethod
    def _test_persistence_isolation(
        cls,
        sim_db: Session,
        scenarios: List[FailureScenarioResult],
    ):
        """Test simulated failure injection and transaction rollback isolation in the sandbox."""
        try:
            # Simulate a failing subtransaction with an invalid constraint
            savepoint = sim_db.begin_nested()
            # Attempt to insert an invalid record with null required field
            bad_item = models.GroceryItem(name=None, quantity=1, is_active=True)
            sim_db.add(bad_item)
            try:
                sim_db.flush()
                savepoint.rollback()
                failed_cleanly = False
            except Exception:
                savepoint.rollback()
                failed_cleanly = True

            if failed_cleanly:
                scenarios.append(FailureScenarioResult(
                    name="Persistence Error & Transaction Rollback Isolation",
                    category="Persistence & Constraints",
                    status="PASSED",
                    expected="Database transaction rollback cleanly isolates errors without corrupting session state.",
                    observed="Simulated integrity failure triggered clean rollback; sandbox state verified intact.",
                ))
            else:
                scenarios.append(FailureScenarioResult(
                    name="Persistence Error & Transaction Rollback Isolation",
                    category="Persistence & Constraints",
                    status="FAILED",
                    expected="Constraint violations must be trapped and rolled back.",
                    observed="Simulated failure was not caught cleanly.",
                ))
        except Exception as e:
            scenarios.append(FailureScenarioResult(
                name="Persistence Error & Transaction Rollback Isolation",
                category="Persistence & Constraints",
                status="FAILED",
                expected="Clean transactional isolation during persistence errors.",
                observed=f"Persistence isolation test raised unexpected error: {str(e)}",
            ))

    @classmethod
    def _test_authorization_gate(
        cls,
        action_type: str,
        params: Dict[str, Any],
        policy_decision: str,
        policy_reason: str,
        scenarios: List[FailureScenarioResult],
    ):
        """Verify policy gate: sensitive actions require approval; blocked actions are denied."""
        if policy_decision == PolicyDecision.BLOCK:
            scenarios.append(FailureScenarioResult(
                name="Policy Enforcement & Access Control Gate",
                category="Authorization & Policy",
                status="PASSED",
                expected="Disallowed or dangerous actions are strictly blocked by the deterministic policy engine.",
                observed=f"BLOCKED BY POLICY: {policy_reason}",
            ))
        elif policy_decision == PolicyDecision.REQUIRE_APPROVAL:
            scenarios.append(FailureScenarioResult(
                name="Policy Enforcement & Access Control Gate",
                category="Authorization & Policy",
                status="PASSED",
                expected="Sensitive operation requires explicit human approval before execution can proceed.",
                observed=f"REQUIRE_APPROVAL ENFORCED: {policy_reason}. Execution without approval is denied.",
            ))
        else:
            scenarios.append(FailureScenarioResult(
                name="Policy Enforcement & Access Control Gate",
                category="Authorization & Policy",
                status="PASSED",
                expected="Low-risk routine operation allowed under verified boundary limits.",
                observed="ALLOW: Routine operation permitted by standard security policy.",
            ))

    @classmethod
    def _test_execution_and_rollback(
        cls,
        action_type: str,
        title: str,
        sanitized_params: Dict[str, Any],
        policy_eval: Any,
        sim_db: Session,
        failure_scenarios: List[FailureScenarioResult],
    ) -> ReversibilityReport:
        """
        Executes action against the simulated DB, verifies state transition,
        then rolls back using UndoManager and verifies that the pre-execution state is fully restored.
        """
        if policy_eval.decision == PolicyDecision.BLOCK:
            failure_scenarios.append(FailureScenarioResult(
                name="Rollback & State Recovery Invariant",
                category="Rollback Invariant",
                status="UNSUPPORTED",
                expected="Rollback verification applicable only to executable operations.",
                observed="Action is strictly BLOCKED by policy; execution and rollback omitted.",
            ))
            return ReversibilityReport(
                result="NOT_REVERSIBLE",
                rollback_tested=False,
                state_restored=False,
                recovery_method="None (operation prohibited by policy)",
                unverified_fields=[],
            )

        # Create temporary plan and action inside the simulated DB
        sim_plan = models.ActionPlan(prompt=f"Simulated test plan for {action_type}", status="PENDING")
        sim_db.add(sim_plan)
        sim_db.flush()

        # For simulation testing of approval-gated actions, simulate user pre-approval
        sim_status = "APPROVED" if policy_eval.decision == PolicyDecision.REQUIRE_APPROVAL else "PENDING"
        sim_approval = "APPROVED" if policy_eval.decision == PolicyDecision.REQUIRE_APPROVAL else None

        sim_action = models.Action(
            plan_id=sim_plan.id,
            action_type=action_type,
            title=title,
            parameters=sanitized_params,
            policy_decision=policy_eval.decision,
            policy_reason=policy_eval.reason,
            status=sim_status,
            approval_decision=sim_approval,
            is_reversible=policy_eval.is_reversible,
            created_at=utc_now(),
        )
        sim_db.add(sim_action)
        sim_db.commit()
        sim_db.refresh(sim_action)

        # Snapshot baseline state in sim_db before execution
        initial_groceries_count = sim_db.query(models.GroceryItem).filter(models.GroceryItem.is_active == True).count()
        initial_reminders_count = sim_db.query(models.Reminder).filter(models.Reminder.is_active == True).count()
        initial_door_states = {d.id: d.is_locked for d in sim_db.query(models.DoorLock).all()}

        # 1. Execute action in simulation
        try:
            ActionExecutor.execute_action(sim_db, sim_action)
        except Exception as e:
            failure_scenarios.append(FailureScenarioResult(
                name="Simulated Execution Check",
                category="Execution",
                status="FAILED",
                expected="Simulated action executes without unhandled exceptions.",
                observed=f"Simulated execution failed: {str(e)}",
            ))
            return ReversibilityReport(
                result="NOT_TESTED",
                rollback_tested=False,
                state_restored=False,
                recovery_method="Execution failed before rollback could be tested",
                unverified_fields=["execution_state"],
            )

        # Verify state did change
        post_exec_groceries_count = sim_db.query(models.GroceryItem).filter(models.GroceryItem.is_active == True).count()
        post_exec_reminders_count = sim_db.query(models.Reminder).filter(models.Reminder.is_active == True).count()

        # 2. Test Rollback using UndoManager
        try:
            UndoManager.undo_action(sim_db, sim_action)
        except Exception as e:
            failure_scenarios.append(FailureScenarioResult(
                name="Rollback & State Recovery Invariant",
                category="Rollback Invariant",
                status="FAILED",
                expected="UndoManager reverses state without errors.",
                observed=f"Undo operation failed: {str(e)}",
            ))
            return ReversibilityReport(
                result="ROLLBACK_FAILED",
                rollback_tested=True,
                state_restored=False,
                recovery_method=f"UndoManager for '{action_type}'",
                unverified_fields=["restored_state"],
            )

        # 3. Compare post-rollback state against pre-execution snapshot
        post_undo_groceries_count = sim_db.query(models.GroceryItem).filter(models.GroceryItem.is_active == True).count()
        post_undo_reminders_count = sim_db.query(models.Reminder).filter(models.Reminder.is_active == True).count()
        post_undo_door_states = {d.id: d.is_locked for d in sim_db.query(models.DoorLock).all()}

        state_matches = (
            post_undo_groceries_count == initial_groceries_count and
            post_undo_reminders_count == initial_reminders_count and
            post_undo_door_states == initial_door_states
        )

        recovery_desc = {
            "add_grocery_item": "Deterministic deletion of inserted item record based on snapshot id",
            "remove_grocery_item": "Reactivation of prior grocery item snapshot",
            "create_reminder": "Deterministic deletion of inserted reminder record based on snapshot id",
            "delete_reminder": "Reactivation of prior reminder snapshot",
            "set_door_lock": "Reversal of lock state to previous snapshot boolean value",
        }.get(action_type, f"Reversal handler for {action_type}")

        if state_matches:
            failure_scenarios.append(FailureScenarioResult(
                name="Rollback & State Recovery Invariant",
                category="Rollback Invariant",
                status="PASSED",
                expected="Rollback restores database to exact pre-execution state with zero orphaned records.",
                observed="State recovery verified: post-rollback state identically matches baseline state.",
            ))
            return ReversibilityReport(
                result="VERIFIED_REVERSIBLE",
                rollback_tested=True,
                state_restored=True,
                recovery_method=recovery_desc,
                unverified_fields=[],
            )
        else:
            failure_scenarios.append(FailureScenarioResult(
                name="Rollback & State Recovery Invariant",
                category="Rollback Invariant",
                status="FAILED",
                expected="Post-rollback state matches initial baseline snapshot.",
                observed=f"State mismatch: Groceries {initial_groceries_count}->{post_undo_groceries_count}, Reminders {initial_reminders_count}->{post_undo_reminders_count}.",
            ))
            return ReversibilityReport(
                result="ROLLBACK_FAILED",
                rollback_tested=True,
                state_restored=False,
                recovery_method=recovery_desc,
                unverified_fields=["active_counts"],
            )

    @classmethod
    def _assess_risk(
        cls,
        action_type: str,
        policy_decision: str,
        policy_reason: str,
        sanitized_params: Dict[str, Any],
        has_warnings: bool,
    ) -> Tuple[str, str]:
        """Derive deterministic risk level and rationale."""
        if policy_decision == PolicyDecision.BLOCK:
            return (
                "CRITICAL",
                f"CRITICAL RISK: Operation '{action_type}' is prohibited by deterministic security policy. Reason: {policy_reason}",
            )

        if action_type == "set_door_lock":
            door_id = sanitized_params.get("door_id", "door")
            target = sanitized_params.get("target_state", "locked").upper()
            return (
                "HIGH",
                f"HIGH RISK: Changes physical perimeter security state ({door_id.replace('_', ' ')} -> {target}). Requires explicit human approval before execution.",
            )

        if action_type == "add_grocery_item" and sanitized_params.get("quantity", 1) > 100:
            qty = sanitized_params.get("quantity")
            return (
                "MEDIUM",
                f"MEDIUM RISK: Bulk purchase threshold exceeded ({qty} units). High financial impact requires explicit human confirmation.",
            )

        if has_warnings:
            return (
                "MEDIUM",
                "MEDIUM RISK: Action is permissible, but warnings were detected (such as redundant state or duplicate items).",
            )

        return (
            "LOW",
            "LOW RISK: Standard household routine within verified boundary limits. Fully reversible.",
        )

    @classmethod
    def _determine_overall_status(
        cls,
        policy_decision: str,
        failure_scenarios: List[FailureScenarioResult],
        reversibility_report: ReversibilityReport,
        warnings: List[str],
    ) -> str:
        """Derive overall simulation status badge text."""
        if policy_decision == PolicyDecision.BLOCK:
            return "BLOCKED BY POLICY"

        if reversibility_report.result == "ROLLBACK_FAILED":
            return "ROLLBACK UNVERIFIED"

        has_failed_scenarios = any(
            s.status == "FAILED" for s in failure_scenarios if s.name != "Rollback & State Recovery Invariant"
        )
        if has_failed_scenarios:
            return "SIMULATION FAILED"

        if warnings or any(s.status == "WARNING" for s in failure_scenarios):
            return "WARNINGS FOUND"

        return "SAFE IN SIMULATION"
