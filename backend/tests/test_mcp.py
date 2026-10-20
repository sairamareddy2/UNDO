import asyncio
import json
import threading
import time
import pytest
import uvicorn
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession
from app.mcp_server import create_mcp_server
from app.database import SessionLocal, init_db
from app import models

TEST_PORT = 8019
MCP_URL = f"http://127.0.0.1:{TEST_PORT}/mcp"


@pytest.fixture(scope="module")
def mcp_test_server():
    """Runs a dedicated Streamable HTTP MCP server on port 8019 for the test suite."""
    init_db()
    server = create_mcp_server("undo-test-mcp")
    app = server.streamable_http_app()

    config = uvicorn.Config(app, host="127.0.0.1", port=TEST_PORT, log_level="error")
    uv_server = uvicorn.Server(config)

    thread = threading.Thread(target=uv_server.run, daemon=True)
    thread.start()

    # Wait for server to bind
    for _ in range(50):
        if uv_server.started:
            break
        time.sleep(0.05)

    yield MCP_URL

    uv_server.should_exit = True
    thread.join(timeout=2.0)


def extract_tool_result(res) -> dict:
    """Helper to extract parsed dictionary from CallToolResult."""
    if hasattr(res, "structured_content") and res.structured_content:
        if "result" in res.structured_content and isinstance(res.structured_content["result"], dict):
            return res.structured_content["result"]
        return res.structured_content

    # Fallback to parsing text content
    if hasattr(res, "content") and res.content:
        for c in res.content:
            if hasattr(c, "text"):
                try:
                    return json.loads(c.text)
                except Exception:
                    pass
    return {}


@pytest.mark.anyio
async def test_mcp_tool_discovery(mcp_test_server):
    """1 & 2: Connect over Streamable HTTP and discover registered tools."""
    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]

            expected_tools = [
                "list_groceries",
                "get_household_state",
                "get_action_history",
                "add_grocery_item",
                "create_reminder",
                "set_door_lock",
                "undo_action",
            ]
            for exp in expected_tools:
                assert exp in tool_names, f"Expected tool '{exp}' not found in {tool_names}"


@pytest.mark.anyio
async def test_mcp_call_readonly_tools(mcp_test_server):
    """3: Call read-only tools and verify structured response."""
    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test get_household_state
            state_res = await session.call_tool("get_household_state", {})
            data = extract_tool_result(state_res)
            assert "doors" in data
            assert "groceries" in data
            assert "reminders" in data
            assert len(data["doors"]) >= 1

            # Test list_groceries
            groc_res = await session.call_tool("list_groceries", {})
            gdata = extract_tool_result(groc_res)
            assert "groceries" in gdata
            assert isinstance(gdata["groceries"], list)


@pytest.mark.anyio
async def test_mcp_allowed_state_change_and_persistence(mcp_test_server):
    """4 & 5: Call allowed tool, verify SQLite mutation, and check snapshot."""
    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call add_grocery_item (ALLOW)
            res = await session.call_tool(
                "add_grocery_item",
                {"name": "Organic Honeycrisp Apples", "quantity": 4, "category": "Produce"}
            )
            data = extract_tool_result(res)

            assert data["status"] == "EXECUTED"
            assert data["is_reversible"] is True
            action_id = data["action_id"]
            assert action_id is not None

            # Verify directly in SQLite database
            db = SessionLocal()
            try:
                item = (
                    db.query(models.GroceryItem)
                    .filter(models.GroceryItem.name == "Organic Honeycrisp Apples")
                    .first()
                )
                assert item is not None
                assert item.quantity == 4
                assert item.category == "Produce"

                # Verify Action and ActionPlan were created in DB
                action = db.query(models.Action).filter(models.Action.id == action_id).first()
                assert action is not None
                assert action.status == "EXECUTED"
                assert action.policy_decision == "ALLOW"
                assert action.after_state is not None
            finally:
                db.close()


@pytest.mark.anyio
async def test_mcp_approval_gating_cannot_be_bypassed(mcp_test_server):
    """6a: Verify that high-risk actions (door locks) return REQUIRE_APPROVAL and DO NOT execute."""
    # Ensure front door is locked before test
    db = SessionLocal()
    try:
        door = db.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
        if door:
            door.is_locked = True
            db.commit()
    finally:
        db.close()

    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            res = await session.call_tool(
                "set_door_lock",
                {"door_id": "front_door", "target_state": "unlocked"}
            )
            data = extract_tool_result(res)

            # Must return REQUIRE_APPROVAL and executed: False
            assert data["status"] == "REQUIRE_APPROVAL"
            assert data["executed"] is False
            assert "requires explicit confirmation" in data["message"]

            # Verify door in database was NOT unlocked!
            db = SessionLocal()
            try:
                door = db.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
                assert door.is_locked is True, "Door state was illegally modified without approval!"
            finally:
                db.close()


@pytest.mark.anyio
async def test_mcp_blocked_action_rejected(mcp_test_server):
    """6b: Verify that invalid parameters or blocked actions return BLOCK and do not mutate state."""
    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Empty name must be BLOCKED by policy engine
            res = await session.call_tool(
                "add_grocery_item",
                {"name": "   ", "quantity": 1}
            )
            data = extract_tool_result(res)

            assert data["status"] == "BLOCKED"
            assert data["executed"] is False
            assert "must be a non-empty string" in data["reason"]


@pytest.mark.anyio
async def test_mcp_undo_restores_prior_state(mcp_test_server):
    """7: Call undo_action over MCP and verify prior database state is restored."""
    async with streamable_http_client(mcp_test_server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. Add item
            add_res = await session.call_tool(
                "add_grocery_item",
                {"name": "Greek Strawberry Yogurt", "quantity": 2, "category": "Dairy"}
            )
            add_data = extract_tool_result(add_res)
            action_id = add_data["action_id"]

            # Confirm item exists in DB
            db = SessionLocal()
            try:
                item = db.query(models.GroceryItem).filter(models.GroceryItem.name == "Greek Strawberry Yogurt").first()
                assert item is not None
            finally:
                db.close()

            # 2. Call undo_action over MCP
            undo_res = await session.call_tool("undo_action", {"action_id": action_id})
            undo_data = extract_tool_result(undo_res)

            assert undo_data["status"] == "REVERSED"
            assert undo_data["action_id"] == action_id

            # 3. Confirm item is deleted from SQLite
            db = SessionLocal()
            try:
                item_after = db.query(models.GroceryItem).filter(models.GroceryItem.name == "Greek Strawberry Yogurt").first()
                assert item_after is None, "Item should have been removed from DB on undo!"

                # Verify audit event for reversal
                audit = (
                    db.query(models.AuditEvent)
                    .filter(models.AuditEvent.action_id == action_id, models.AuditEvent.event_type == "ACTION_UNDONE")
                    .first()
                )
                assert audit is not None
            finally:
                db.close()

            # 4. Attempt repeated undo -> must be rejected
            repeat_res = await session.call_tool("undo_action", {"action_id": action_id})
            repeat_data = extract_tool_result(repeat_res)
            assert repeat_data["status"] == "REJECTED"
            assert "already been reversed" in repeat_data["error"]
