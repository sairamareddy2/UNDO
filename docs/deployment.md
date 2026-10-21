# UNDO Cloud Deployment Guide

This guide details how to deploy **UNDO** to cloud hosting platforms (**Vercel**, **Render**, or **Railway**) directly from your GitHub repository, or run it via **Docker**.

---

## Live Deployments

- **Production Frontend (Vercel)**: [https://undo-q4bgl83d3-ramakrishna2.vercel.app/](https://undo-q4bgl83d3-ramakrishna2.vercel.app/)
- **Production Backend (Render)**: [https://undo-governance-engine.onrender.com](https://undo-governance-engine.onrender.com)
- **API Swagger Documentation**: [https://undo-governance-engine.onrender.com/docs](https://undo-governance-engine.onrender.com/docs)
- **Health Check Endpoint**: [https://undo-governance-engine.onrender.com/api/health](https://undo-governance-engine.onrender.com/api/health)

---

## Architecture Overview

In production, UNDO runs as a unified full-stack application inside a lightweight multi-stage Docker container:
1. **Frontend**: React 19 + TypeScript + Tailwind CSS compiled into high-performance static distribution assets.
2. **Backend**: FastAPI running on Uvicorn serving both:
   - High-throughput REST API (`/api/*`)
   - Official Python MCP Streamable HTTP endpoint (`/mcp`)
   - Pre-compiled React Web Dashboard (`/*`)
3. **Database**: SQLite database automatically seeded on initial startup.
4. **AI Planner**: Google Gemini (`google-genai`) with offline fallback if `GEMINI_API_KEY` is omitted.

---

## Option 1: Deploy to Render (Recommended — 2 Minutes)

Render provides free container hosting with HTTPS and automatic deploys on Git push.

### Step 1: Connect Your GitHub Repository
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint** (or **Web Service**).
3. Connect your GitHub account and select repository:
   `https://github.com/sairamareddy2/UNDO`

### Step 2: Configure Blueprint
Render will automatically detect [`render.yaml`](../render.yaml):
- **Service Name**: `undo-governance-engine`
- **Runtime**: `Docker`
- **Plan**: `Free`

### Step 3: Add Your Gemini API Key
In the environment variable prompt:
- Key: `GEMINI_API_KEY`
- Value: Your Google AI Studio API key (`AIza...`)
*(Note: If you omit this, UNDO runs with its built-in offline deterministic parser).*

### Step 4: Deploy
Click **Apply**. Render will build the Docker container and deploy the app at:
`https://undo-governance-engine.onrender.com`

---

## Option 2: Deploy to Railway (1 Minute)

Railway automatically detects Dockerfiles and provisions instant public URLs.

### Step 1: Connect Repository
1. Log in to [Railway.app](https://railway.app/).
2. Click **+ New Project** &rarr; **Deploy from GitHub repo**.
3. Select `sairamareddy2/UNDO`.

### Step 2: Set Environment Variables
In Railway project settings &rarr; **Variables**, add:
- `GEMINI_API_KEY`: Your Google AI Studio API key (optional)
- `GEMINI_MODEL`: `gemini-3.1-flash-lite`

### Step 3: Generate Domain
Under **Settings** &rarr; **Networking**, click **Generate Domain**.
Your application will be live at:
`https://undo-production.up.railway.app`

---

## Option 3: Run via Docker Locally

To test the containerized production build locally:

```bash
# 1. Build and run with Docker Compose:
docker compose up --build

# 2. Or build and run with Docker directly:
docker build -t undo-app .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-key" undo-app
```

Access the dashboard at `http://localhost:8000`.

---

## Verifying the Deployment

Once deployed, verify health and live endpoints:
- **Web Dashboard**: `https://<your-app-domain>/`
- **Health Check**: `https://<your-app-domain>/api/health`
- **Interactive Swagger Docs**: `https://<your-app-domain>/docs`
- **MCP Streamable HTTP Endpoint**: `https://<your-app-domain>/mcp`
