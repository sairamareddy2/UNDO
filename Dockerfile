# ===================================================
# Stage 1: Build Frontend (React 19 + Vite + Tailwind)
# ===================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies with frozen lockfile for deterministic builds
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and compile static production distribution
COPY frontend/ ./
RUN npm run build

# ===================================================
# Stage 2: Production Python Runtime (FastAPI + MCP)
# ===================================================
FROM python:3.11-slim AS production
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8000 \
    HOST=0.0.0.0

# Install curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source
COPY backend/ ./backend/

# Copy built frontend static bundle from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose HTTP ports (8000 for unified web & MCP, 8001 for standalone MCP)
EXPOSE 8000 8001

# Health check to ensure FastAPI is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/api/health || exit 1

# Run FastAPI serving the complete app (Dashboard + API + MCP) via Uvicorn
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
