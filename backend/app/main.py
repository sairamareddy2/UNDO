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

# Configure CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(plans.router, prefix="/api", tags=["Action Plans"])
app.include_router(actions.router, prefix="/api", tags=["Actions"])
app.include_router(safety.router, prefix="/api", tags=["Safety Simulator"])
app.include_router(state.router, prefix="/api", tags=["Application State"])
app.include_router(mcp.router, prefix="/api", tags=["MCP"])


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
