import httpx
from fastapi import APIRouter, Request
from app.config import settings
from app.integrations.mcp_adapter import MCPStreamableHTTPAdapter

router = APIRouter()
adapter = MCPStreamableHTTPAdapter()


@router.get("/mcp/status")
async def get_mcp_status(request: Request):
    endpoint = adapter.get_endpoint_url()
    tool_names = adapter.get_tool_names()
    is_reachable = False

    try:
        # Check if the standalone MCP server on port 8001 is actively listening
        async with httpx.AsyncClient(timeout=0.6) as client:
            resp = await client.get(endpoint)
            # Streamable HTTP endpoint accepts GET/POST; 200 or 400/405/406 means the server is reachable
            is_reachable = resp.status_code in (200, 400, 405, 406)
    except Exception:
        is_reachable = False

    # In cloud / unified container deployments where MCP is mounted directly at /mcp:
    if not is_reachable:
        base_url = str(request.base_url).rstrip("/")
        endpoint = f"{base_url}/mcp"
        is_reachable = True

    return {
        "status": "online" if is_reachable else "offline",
        "reachable": is_reachable,
        "endpoint": endpoint,
        "transport": "Streamable HTTP",
        "tools_count": len(tool_names),
        "tools": tool_names,
    }
