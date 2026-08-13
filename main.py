from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router

# On Windows, asyncio's default SelectorEventLoop cannot spawn
# subprocesses (NotImplementedError from loop.subprocess_exec). The
# MCP client launches the Fetch MCP server as a subprocess over
# stdio, so we need the ProactorEventLoop instead. This must run
# before uvicorn creates its event loop, so it lives at module import
# time here rather than inside a startup hook.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("mcp_fetch_agent")

app = FastAPI(title="MCP Fetch Agent")

# CORS: permissive for local development only. Tighten before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
