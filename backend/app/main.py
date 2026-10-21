from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import health, plans, actions, state, mcp, safety


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schemas and baseline seeds safely
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic action-governance and reversible operations engine for Alexa+ simulated experiences.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for local frontend development and deployed Vercel origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https://[a-zA-Z0-9_-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Mount API routers
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(plans.router, prefix="/api", tags=["Action Plans"])
app.include_router(actions.router, prefix="/api", tags=["Actions"])
app.include_router(safety.router, prefix="/api", tags=["Safety Simulator"])
app.include_router(state.router, prefix="/api", tags=["Application State"])
app.include_router(mcp.router, prefix="/api", tags=["MCP"])

# Mount MCP Streamable HTTP ASGI application for unified single-port deployments
from app.mcp_server import mcp_app
app.mount("/mcp", mcp_app)

# Mount frontend static distribution if built, fallback to JSON status
frontend_dist = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"))
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "service": settings.APP_NAME,
            "version": "1.0.0",
            "status": "operational",
            "docs_url": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
