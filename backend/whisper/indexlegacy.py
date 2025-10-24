import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from typing import Any, Dict
from checker import checkVideoByID

# 1. Create the FastAPI app instance
app = FastAPI()

# Very small "seen" trackers (non-persistent). If an id was requested once,
# subsequent requests will get a short acknowledgement instead of re-processing.
_seen_ids: set[str] = set()
_seen_keys: set[tuple] = set()

# Per-key asyncio locks to avoid races when two requests for the same id arrive
# concurrently. Use a small lock-map protected by _locks_lock when creating new locks.
_locks: Dict[Any, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()


async def _get_lock_for(key: Any) -> asyncio.Lock:
    """Return an asyncio.Lock for the given key, creating it if necessary.

    This function is safe to call concurrently.
    """
    async with _locks_lock:
        lock = _locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _locks[key] = lock
        return lock

# 2. Define the /ping endpoint
@app.get("/ping")
async def ping_pong():
    """
    When this endpoint is hit, it returns the string "pong".
    FastAPI automatically handles converting this to a JSON response.
    """
    return "pong"


# 3. Dynamic route that accepts any natural number (positive integer)
@app.get("/{item_id}")
async def request_transcription_by_id(item_id: str):
    """Return a simple response for any natural-number id.

    Simpler behavior: if this id was already requested earlier, respond with
    a short acknowledgement. Otherwise perform the work once.
    """
    # Use a per-id lock to prevent a race where two concurrent requests both
    # observe the id as unseen and both proceed. Only one will run the work.
    lock = await _get_lock_for(item_id)
    async with lock:
        if item_id in _seen_ids:
            return {"message": "already request came in"}

        # Mark as seen and perform the work once
        _seen_ids.add(item_id)

        # Replace with real work (DB, file, etc.). Keep async-friendly.
        async def do_work(i: int):
            await asyncio.sleep(0)
            checkVideoByID(item_id)
            return {"id": i, "message": f"Requested resource for id {i}"}

        result = await do_work(item_id)
        return result


@app.get("/{item_id}/{language}")
async def get_by_id_and_language(item_id: int, language: str):
    """Return a response for a given teletask id and language.

    Simpler behavior: if this id+language was already requested earlier, return
    a short acknowledgement. Otherwise perform the work once.
    """
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="ID must be a positive integer")

    cache_key = (item_id, language)

    lock = await _get_lock_for(cache_key)
    async with lock:
        if cache_key in _seen_keys:
            return {"message": "already request came in"}

        _seen_keys.add(cache_key)

        async def do_work(i: int, lang: str):
            await asyncio.sleep(0)
            return {"id": i, "language": lang, "message": f"Requested resource for id {i} and language {lang}"}

        result = await do_work(item_id, language)
        return result


# 4. Add the main entry point to run the server
if __name__ == "__main__":
    # This block allows you to run: python index.py
    print("Starting minimal server at http://127.0.0.1:8000")
    print("Try visiting http://127.0.0.1:8000/ping or http://127.0.0.1:8000/1")
    uvicorn.run(app, host="127.0.0.1", port=8000)

