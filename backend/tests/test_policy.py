import pytest
from app.policy.engine import PolicyEngine, PolicyDecision


def test_add_grocery_item_allowed():
    result = PolicyEngine.evaluate("add_grocery_item", {"name": "Bananas", "quantity": 3, "category": "Produce"})
    assert result.decision == PolicyDecision.ALLOW
    assert result.is_reversible is True
    assert result.validated_params["name"] == "Bananas"
    assert result.validated_params["quantity"] == 3


def test_add_grocery_bulk_requires_approval():
    result = PolicyEngine.evaluate("add_grocery_item", {"name": "Bottles of Water", "quantity": 150})
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    assert "Bulk purchase threshold" in result.reason
    assert result.is_reversible is True


def test_add_grocery_invalid_name_blocked():
    result = PolicyEngine.evaluate("add_grocery_item", {"name": "   ", "quantity": 2})
    assert result.decision == PolicyDecision.BLOCK
    assert "must be a non-empty string" in result.reason


def test_add_grocery_negative_quantity_blocked():
    result = PolicyEngine.evaluate("add_grocery_item", {"name": "Bread", "quantity": -5})
    assert result.decision == PolicyDecision.BLOCK
    assert "must be at least 1" in result.reason


def test_create_reminder_allowed():
    result = PolicyEngine.evaluate("create_reminder", {"title": "Doctor Appointment", "remind_at": "4:00 PM", "priority": "high"})
    assert result.decision == PolicyDecision.ALLOW
    assert result.is_reversible is True
    assert result.validated_params["title"] == "Doctor Appointment"
    assert result.validated_params["priority"] == "high"


def test_create_reminder_missing_title_blocked():
    result = PolicyEngine.evaluate("create_reminder", {"title": "", "remind_at": "4:00 PM"})
    assert result.decision == PolicyDecision.BLOCK
    assert "must be a non-empty string" in result.reason


def test_create_reminder_missing_schedule_blocked():
    result = PolicyEngine.evaluate("create_reminder", {"title": "Workout", "remind_at": "  "})
    assert result.decision == PolicyDecision.BLOCK
    assert "schedule string is required" in result.reason


def test_door_lock_requires_approval():
    result = PolicyEngine.evaluate("set_door_lock", {"door_id": "front_door", "target_state": "unlocked"})
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    assert result.is_reversible is True
    assert "Physical security impact" in result.reason


def test_door_lock_unknown_location_blocked():
    result = PolicyEngine.evaluate("set_door_lock", {"door_id": "secret_bunker_door", "target_state": "unlocked"})
    assert result.decision == PolicyDecision.BLOCK
    assert "Unknown door location" in result.reason


def test_door_lock_invalid_state_blocked():
    result = PolicyEngine.evaluate("set_door_lock", {"door_id": "front_door", "target_state": "half_open"})
    assert result.decision == PolicyDecision.BLOCK
    assert "Invalid target state" in result.reason


def test_dangerous_operations_strictly_blocked():
    for dangerous in ["wipe_database", "delete_account", "transfer_funds", "shell_exec", "format_drive"]:
        result = PolicyEngine.evaluate(dangerous, {"param": "value"})
        assert result.decision == PolicyDecision.BLOCK
        assert "strictly prohibited" in result.reason
        assert result.is_reversible is False


def test_unknown_tool_strictly_blocked():
    result = PolicyEngine.evaluate("launch_rocket", {"target": "moon"})
    assert result.decision == PolicyDecision.BLOCK
    assert "Unknown tool or capability" in result.reason
