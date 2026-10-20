from dataclasses import dataclass
from typing import Any, Dict, Optional


class PolicyDecision:
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


@dataclass
class PolicyEvaluation:
    decision: str
    reason: str
    is_reversible: bool
    validated_params: Optional[Dict[str, Any]] = None


class PolicyEngine:
    """
    Deterministic Policy Engine for UNDO.
    Evaluates actions strictly against explicit domain safety rules and validated parameters.
    No unverified LLM risk scores are trusted.
    """

    ALLOWED_DOOR_IDS = {"front_door", "back_door", "garage_entry"}
    DANGEROUS_ACTIONS = {
        "wipe_database",
        "delete_account",
        "transfer_funds",
        "shell_exec",
        "disable_security_camera",
        "purchase_gift_cards",
        "format_drive",
        "export_all_contacts",
    }

    @classmethod
    def evaluate(cls, action_type: str, parameters: Any) -> PolicyEvaluation:
        if hasattr(parameters, "model_dump"):
            parameters = parameters.model_dump(exclude_none=True)
        elif not isinstance(parameters, dict):
            parameters = dict(parameters) if parameters else {}

        # 1. Check for explicitly disallowed high-risk/dangerous operations
        if action_type in cls.DANGEROUS_ACTIONS:
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason=f"Disallowed operation: '{action_type}' is strictly prohibited by security policy.",
                is_reversible=False,
            )

        # 2. Evaluate known actions
        if action_type == "add_grocery_item":
            return cls._evaluate_add_grocery(parameters)

        if action_type == "remove_grocery_item":
            return cls._evaluate_remove_grocery(parameters)

        if action_type == "create_reminder":
            return cls._evaluate_create_reminder(parameters)

        if action_type == "delete_reminder":
            return cls._evaluate_delete_reminder(parameters)

        if action_type == "set_door_lock":
            return cls._evaluate_set_door_lock(parameters)

        # 3. Any unregistered action is strictly blocked
        return PolicyEvaluation(
            decision=PolicyDecision.BLOCK,
            reason=f"Unknown tool or capability '{action_type}'. Actions must match registered tool definitions.",
            is_reversible=False,
        )

    @classmethod
    def _evaluate_add_grocery(cls, params: Dict[str, Any]) -> PolicyEvaluation:
        name = params.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: grocery item 'name' must be a non-empty string.",
                is_reversible=False,
            )

        name = name.strip()
        raw_quantity = params.get("quantity", 1)
        try:
            quantity = int(raw_quantity)
        except (ValueError, TypeError):
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason=f"Invalid parameter: 'quantity' must be an integer, got '{raw_quantity}'.",
                is_reversible=False,
            )

        if quantity <= 0:
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameter: 'quantity' must be at least 1.",
                is_reversible=False,
            )

        category = params.get("category", "General")
        if not isinstance(category, str) or not category.strip():
            category = "General"

        validated = {"name": name, "quantity": quantity, "category": category.strip()}

        # Bulk order threshold rule: > 100 units requires human sign-off
        if quantity > 100:
            return PolicyEvaluation(
                decision=PolicyDecision.REQUIRE_APPROVAL,
                reason=f"Bulk purchase threshold exceeded ({quantity} units). High-quantity orders require confirmation.",
                is_reversible=True,
                validated_params=validated,
            )

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW,
            reason="Standard household grocery list addition within verified safe quantity limits.",
            is_reversible=True,
            validated_params=validated,
        )

    @classmethod
    def _evaluate_remove_grocery(cls, params: Dict[str, Any]) -> PolicyEvaluation:
        item_id = params.get("item_id")
        name = params.get("name")

        if not item_id and (not name or not isinstance(name, str) or not name.strip()):
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: either 'item_id' or 'name' must be specified to remove grocery item.",
                is_reversible=False,
            )

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW,
            reason="Low-risk removal from grocery list.",
            is_reversible=True,
            validated_params={"item_id": item_id, "name": name.strip() if name else None},
        )

    @classmethod
    def _evaluate_create_reminder(cls, params: Dict[str, Any]) -> PolicyEvaluation:
        title = params.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: reminder 'title' must be a non-empty string.",
                is_reversible=False,
            )

        remind_at = params.get("remind_at")
        if not remind_at or not isinstance(remind_at, str) or not remind_at.strip():
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: 'remind_at' time/schedule string is required.",
                is_reversible=False,
            )

        priority = str(params.get("priority", "medium")).lower()
        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW,
            reason="Routine notification creation with validated schedule and parameters.",
            is_reversible=True,
            validated_params={"title": title.strip(), "remind_at": remind_at.strip(), "priority": priority},
        )

    @classmethod
    def _evaluate_delete_reminder(cls, params: Dict[str, Any]) -> PolicyEvaluation:
        reminder_id = params.get("reminder_id")
        title = params.get("title")

        if not reminder_id and (not title or not isinstance(title, str) or not title.strip()):
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: either 'reminder_id' or 'title' must be provided.",
                is_reversible=False,
            )

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW,
            reason="Routine cancellation of a scheduled reminder.",
            is_reversible=True,
            validated_params={"reminder_id": reminder_id, "title": title.strip() if title else None},
        )

    @classmethod
    def _evaluate_set_door_lock(cls, params: Dict[str, Any]) -> PolicyEvaluation:
        door_id = params.get("door_id")
        if not door_id or not isinstance(door_id, str):
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason="Invalid parameters: 'door_id' is required.",
                is_reversible=False,
            )

        door_id = door_id.strip().lower()
        if door_id not in cls.ALLOWED_DOOR_IDS:
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason=f"Unknown door location '{door_id}'. Allowed locations: {', '.join(sorted(cls.ALLOWED_DOOR_IDS))}.",
                is_reversible=False,
            )

        target_state = params.get("target_state")
        if target_state is None:
            # Check boolean 'locked'
            if "locked" in params and isinstance(params["locked"], bool):
                target_state = "locked" if params["locked"] else "unlocked"
            else:
                return PolicyEvaluation(
                    decision=PolicyDecision.BLOCK,
                    reason="Invalid parameters: 'target_state' must be 'locked' or 'unlocked'.",
                    is_reversible=False,
                )

        target_state = str(target_state).strip().lower()
        if target_state not in {"locked", "unlocked"}:
            return PolicyEvaluation(
                decision=PolicyDecision.BLOCK,
                reason=f"Invalid target state '{target_state}'. Must be 'locked' or 'unlocked'.",
                is_reversible=False,
            )

        # Physical security rule: changing door lock status MUST require human approval!
        return PolicyEvaluation(
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"Physical security impact: Changing {door_id.replace('_', ' ')} lock state to '{target_state}' requires explicit confirmation.",
            is_reversible=True,
            validated_params={"door_id": door_id, "target_state": target_state},
        )
