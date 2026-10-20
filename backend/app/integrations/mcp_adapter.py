"""
Official Python MCP SDK with Streamable HTTP (Roadmap - Future Milestone)

This module provides the architectural scaffolding for exposing UNDO's reversible
actions and policy engine over the Model Context Protocol (MCP) using Streamable HTTP.
This enables external AI assistants (like Alexa+ agentic tools) to safely invoke
governed actions with human approval checkpoints.
"""
from typing import Any, Dict, List


class MCPStreamableHTTPAdapter:
    """
    Scaffolding for Python MCP SDK Streamable HTTP transport.
    Planned implementation: Milestone 2.
    """

    def __init__(self, port: int = 8001):
        self.port = port
        self.is_running = False

    def get_tool_manifest(self) -> List[Dict[str, Any]]:
        """
        Exposes UNDO's registered capability tools and their parameter schemas for MCP clients.
        """
        return [
            {
                "name": "add_grocery_item",
                "description": "Add an item to the simulated household grocery list (Reversible).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "quantity": {"type": "integer", "description": "Quantity to add", "default": 1},
                        "category": {"type": "string", "description": "Category", "default": "General"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "create_reminder",
                "description": "Schedule a routine household reminder (Reversible).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Reminder text"},
                        "remind_at": {"type": "string", "description": "Time or schedule format"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    },
                    "required": ["title", "remind_at"],
                },
            },
            {
                "name": "set_door_lock",
                "description": "Lock or unlock a simulated entrance door (Requires Approval, Reversible).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "door_id": {"type": "string", "enum": ["front_door", "back_door", "garage_entry"]},
                        "target_state": {"type": "string", "enum": ["locked", "unlocked"]},
                    },
                    "required": ["door_id", "target_state"],
                },
            },
        ]
