"""
Official Python MCP SDK with Streamable HTTP Transport

This module provides the integration surface for exposing UNDO's reversible
actions and policy engine over the Model Context Protocol (MCP) using Streamable HTTP.
"""
from typing import Any, Dict, List
from app.mcp_server import mcp_server, mcp_app
from app.config import settings


class MCPStreamableHTTPAdapter:
    """
    Adapter interfacing with the live Python MCP SDK MCPServer and Streamable HTTP application.
    """

    def __init__(self, port: int = None):
        self.port = port or settings.MCP_SERVER_PORT
        self.server = mcp_server
        self.app = mcp_app

    def get_endpoint_url(self, host: str = "127.0.0.1") -> str:
        return f"http://{host}:{self.port}/mcp"

    def get_tool_names(self) -> List[str]:
        # MCP SDK registered tools
        return [
            "list_groceries",
            "get_household_state",
            "get_action_history",
            "add_grocery_item",
            "create_reminder",
            "set_door_lock",
            "undo_action",
        ]
