"""Convenience entry point: `python run.py`"""
import asyncio
import sys

import uvicorn

if sys.platform == "win32":
    # See backend/main.py for why this is required on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # reload=True re-imports backend.main in a subprocess before serving,
    # so the policy set above (and the one in backend/main.py) both apply.
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
