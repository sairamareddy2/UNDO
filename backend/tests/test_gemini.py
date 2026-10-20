import pytest
from unittest.mock import MagicMock, patch
from app.integrations.gemini_adapter import GeminiAdapter, ActionPlanProposal, ProposedAction
from app.planner.parser import ActionIntentParser
from app.policy.engine import PolicyEngine, PolicyDecision


def test_gemini_adapter_availability():
    # When key is None or whitespace
    adapter_no_key = GeminiAdapter(api_key=None)
    adapter_no_key._api_key = None
    assert adapter_no_key.is_available() is False

    adapter_empty_key = GeminiAdapter(api_key="   ")
    adapter_empty_key._api_key = "   "
    assert adapter_empty_key.is_available() is False

    # When key is set
    adapter_with_key = GeminiAdapter(api_key="mock-gemini-key")
    assert adapter_with_key.is_available() is True


def test_gemini_adapter_successful_response_mocked():
    adapter = GeminiAdapter(api_key="mock-key")

    mock_proposal = ActionPlanProposal(
        actions=[
            ProposedAction(
                action_type="add_grocery_item",
                title="Add 2x Oat Milk to Groceries",
                parameters={"name": "Oat Milk", "quantity": 2, "category": "Dairy"},
            ),
            ProposedAction(
                action_type="set_door_lock",
                title="Unlock Front Door",
                parameters={"door_id": "front_door", "target_state": "unlocked"},
            ),
        ],
        reasoning="User requested milk and door unlock.",
    )

    mock_response = MagicMock()
    mock_response.parsed = mock_proposal
    mock_response.text = mock_proposal.model_dump_json()

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(adapter, "_get_client", return_value=mock_client):
        proposals = adapter.generate_action_proposals("Add oat milk and unlock front door")

        assert len(proposals) == 2
        assert proposals[0][0] == "add_grocery_item"
        assert proposals[0][1] == "Add 2x Oat Milk to Groceries"
        assert proposals[0][2]["quantity"] == 2

        assert proposals[1][0] == "set_door_lock"
        assert proposals[1][2]["target_state"] == "unlocked"


def test_gemini_adapter_malformed_model_output():
    adapter = GeminiAdapter(api_key="mock-key")

    # Mock response with invalid JSON text and None parsed
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = "{ this is invalid json !!!"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(adapter, "_get_client", return_value=mock_client):
        proposals = adapter.generate_action_proposals("Random command")
        # Should gracefully return empty list on malformed output
        assert proposals == []


def test_gemini_adapter_api_error_handling():
    adapter = GeminiAdapter(api_key="mock-key")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Google GenAI 429 Quota Exceeded")

    with patch.object(adapter, "_get_client", return_value=mock_client):
        proposals = adapter.generate_action_proposals("Add apples")
        # Should handle API error gracefully without crashing
        assert proposals == []


def test_parser_fallback_to_deterministic_when_gemini_fails():
    with patch("app.planner.parser.gemini_adapter.is_available", return_value=True):
        with patch("app.planner.parser.gemini_adapter.generate_action_proposals", return_value=[]):
            # When Gemini returns empty or errors, fallback to deterministic parser
            actions = ActionIntentParser.parse_prompt("Add 2 cartons of milk to groceries")
            assert len(actions) >= 1
            assert actions[0][0] == "add_grocery_item"
            assert actions[0][2]["quantity"] == 2


def test_gemini_proposals_enforce_policy_engine(client):
    """
    Verifies that actions proposed by Gemini are strictly governed by PolicyEngine.
    Never bypasses ALLOW, REQUIRE_APPROVAL, or BLOCK rules.
    """
    mock_proposal = ActionPlanProposal(
        actions=[
            # 1. Allowed action
            ProposedAction(
                action_type="add_grocery_item",
                title="Add 1x Sourdough Bread",
                parameters={"name": "Sourdough Bread", "quantity": 1, "category": "Bakery"},
            ),
            # 2. Approval-required action (door unlock)
            ProposedAction(
                action_type="set_door_lock",
                title="Unlock Front Door",
                parameters={"door_id": "front_door", "target_state": "unlocked"},
            ),
            # 3. Disallowed action (wipe database)
            ProposedAction(
                action_type="wipe_database",
                title="Wipe Entire Database",
                parameters={"target": "all"},
            ),
        ]
    )

    with patch("app.planner.parser.gemini_adapter.is_available", return_value=True):
        with patch("app.planner.parser.gemini_adapter.generate_action_proposals", return_value=[
            (a.action_type, a.title, a.parameters) for a in mock_proposal.actions
        ]):
            response = client.post("/api/plans", json={"prompt": "Complex command"})
            assert response.status_code == 201
            plan = response.json()
            actions = plan["actions"]
            assert len(actions) == 3

            # Verify Policy Engine governance on each Gemini proposal:
            grocery_action = actions[0]
            assert grocery_action["action_type"] == "add_grocery_item"
            assert grocery_action["policy_decision"] == PolicyDecision.ALLOW
            assert grocery_action["status"] == "PENDING"

            door_action = actions[1]
            assert door_action["action_type"] == "set_door_lock"
            assert door_action["policy_decision"] == PolicyDecision.REQUIRE_APPROVAL
            assert door_action["status"] == "PENDING"
            assert "Physical security impact" in door_action["policy_reason"]

            wipe_action = actions[2]
            assert wipe_action["action_type"] == "wipe_database"
            assert wipe_action["policy_decision"] == PolicyDecision.BLOCK
            assert wipe_action["status"] == "BLOCKED"
            assert "strictly prohibited" in wipe_action["policy_reason"]
