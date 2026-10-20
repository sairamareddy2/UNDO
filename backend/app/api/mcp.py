import httpx
from fastapi import APIRouter
from app.config import settings
from app.integrations.mcp_adapter import MCPStreamableHTTPAdapter

router = APIRouter()
adapter = MCPStreamableHTTPAdapter()


@router.get("/mcp/status")
async def get_mcp_status():
    endpoint = adapter.get_endpoint_url()
    tool_names = adapter.get_tool_names()
    is_reachable = False

    try:
        # Check if the MCP server on port 8001 is actively listening
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(endpoint)
            # Streamable HTTP endpoint accepts GET/POST; 200 or 400/405/406 means the server is reachable
            is_reachable = resp.status_code in (200, 400, 405, 406)
    except Exception:
        is_reachable = False

    return {
        "status": "online" if is_reachable else "offline",
        "reachable": is_reachable,
        "endpoint": endpoint,
        "transport": "Streamable HTTP",
        "tools_count": len(tool_names),
        "tools": tool_names,
    }
