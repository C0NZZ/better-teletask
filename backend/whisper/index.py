import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from checker import checkerLoop

# 1. Create the FastAPI app instance
app = FastAPI()

# 2. Define the /ping endpoint
@app.get("/ping")
async def ping_pong():
    #checkerLoop();
    return "pong"


# Single boolean flag to indicate whether checkerLoop is currently running.
# Use this to prevent starting multiple concurrent checker runs.
checker_running = False


def _set_checker_running(value: bool) -> None:
    global checker_running
    checker_running = value


def is_checker_running() -> bool:
    return checker_running


# Async lock to protect check-and-set of checker_running to avoid races
_checker_lock = asyncio.Lock()


async def _run_checker_background():
    """Run the (possibly blocking) checkerLoop in a threadpool and clear the flag when done."""
    loop = asyncio.get_running_loop()
    try:
        # run in executor in case checkerLoop is blocking
        await loop.run_in_executor(None, checkerLoop)
    finally:
        # Ensure we clear the running flag under the same lock to avoid races
        async with _checker_lock:
            _set_checker_running(False)


@app.get("/start-checker")
async def start_checker():
    """Start checkerLoop in background if not already running."""
    # Protect check-and-set with a lock to avoid a race where two requests
    # both see the flag as False and both start the checker.
    async with _checker_lock:
        if is_checker_running():
            return {"message": "checker already running"}
        _set_checker_running(True)

    # Start background run without holding the lock
    asyncio.create_task(_run_checker_background())
    return {"message": "checker started"}


@app.get("/checker-status")
async def checker_status():
    return {"running": is_checker_running()}


# 4. Add the main entry point to run the server
if __name__ == "__main__":
    # This block allows you to run: python index.py
    print("Starting minimal server at http://127.0.0.1:8000")
    print("Try visiting http://127.0.0.1:8000/ping or http://127.0.0.1:8000/1")
    uvicorn.run(app, host="127.0.0.1", port=8000)

