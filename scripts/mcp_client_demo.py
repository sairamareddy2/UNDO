"""
Interactive Demonstration Client for UNDO MCP Server (Streamable HTTP)

Connects to the live UNDO MCP Server on port 8001, discovers exposed tools,
calls read-only and governed mutating tools, demonstrates policy approval gating,
and tests state rollback (undo).
"""
import asyncio
import json
import sys
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

MCP_URL = "http://127.0.0.1:8001/mcp"


def print_section(title: str):
    print(f"\n{'='*70}\n[MCP CLIENT] {title}\n{'='*70}")


def extract_content(res):
    if hasattr(res, "structured_content") and res.structured_content:
        return res.structured_content.get("result", res.structured_content)
    if hasattr(res, "content") and res.content:
        for c in res.content:
            if hasattr(c, "text"):
                try:
                    return json.loads(c.text)
                except Exception:
                    return c.text
    return str(res)


async def main():
    print(f"Connecting to UNDO MCP Server at: {MCP_URL} ...")

    try:
        async with streamable_http_client(MCP_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # 1. Initialize
                print_section("1. MCP Client Handshake & Initialization")
                init_res = await session.initialize()
                print(f"Connected to: {init_res.server_info.name} v{init_res.server_info.version}")
                print(f"Protocol version: {session.protocol_version}")

                # 2. Discover Tools
                print_section("2. Tool Discovery")
                tools_res = await session.list_tools()
                print(f"Discovered {len(tools_res.tools)} tools:")
                for tool in tools_res.tools:
                    print(f"  • {tool.name:22} - {tool.description.strip().splitlines()[0]}")

                # 3. Call Read-Only Tool: get_household_state
                print_section("3. Calling Read-Only Tool: get_household_state")
                state_res = await session.call_tool("get_household_state", {})
                state_data = extract_content(state_res)
                print(json.dumps(state_data, indent=2))

                # 4. Call Allowed Mutating Tool: add_grocery_item
                print_section("4. Calling Allowed Tool: add_grocery_item (ALLOW Policy)")
                add_res = await session.call_tool(
                    "add_grocery_item",
                    {"name": "Organic Honeycrisp Apples", "quantity": 3, "category": "Produce"}
                )
                add_data = extract_content(add_res)
                print(json.dumps(add_data, indent=2))
                action_id = add_data.get("action_id")

                # 5. Call Approval-Required Tool: set_door_lock
                print_section("5. Calling Gated Tool: set_door_lock (REQUIRE_APPROVAL Policy)")
                door_res = await session.call_tool(
                    "set_door_lock",
                    {"door_id": "front_door", "target_state": "unlocked"}
                )
                door_data = extract_content(door_res)
                print(json.dumps(door_data, indent=2))
                print(">> Notice: Action was NOT executed directly; it requires dashboard approval.")

                # 6. Call Blocked Action (Empty name)
                print_section("6. Calling Invalid Tool: add_grocery_item (BLOCK Policy)")
                block_res = await session.call_tool(
                    "add_grocery_item",
                    {"name": "   ", "quantity": 1}
                )
                block_data = extract_content(block_res)
                print(json.dumps(block_data, indent=2))

                # 7. Call Undo Tool: undo_action
                if action_id:
                    print_section(f"7. Calling Undo Tool: undo_action (action_id={action_id})")
                    undo_res = await session.call_tool("undo_action", {"action_id": action_id})
                    undo_data = extract_content(undo_res)
                    print(json.dumps(undo_data, indent=2))

                print_section("DEMO COMPLETED SUCCESSFULLY!")

    except Exception as e:
        print(f"Failed to connect or execute MCP client demo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
