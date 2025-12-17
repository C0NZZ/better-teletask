import uvicorn
import asyncio
from fastapi import FastAPI
import contextlib
from collections import deque
from typing import List,Optional

from database import (
    get_missing_available_inbetween_ids,
    getSmallestTeletaskID,
    original_language_exists,
    initDatabase
)
from kratzer import get_upper_ids, pingVideoByID, transcribePipelineVideoByID

# setup logging
import logger
import logging
logger = logging.getLogger("btt_root_logger")

class AsyncQueue:
    def __init__(self):
        self._queue = deque()
        self._lock = asyncio.Lock()

    # ----------------------
    # Lock-protected methods
    # ----------------------

    async def add(self, item_id: str):
        """Add an ID to the queue (if not already present)."""
        async with self._lock:
            if item_id not in self._queue:
                self._queue.append(item_id)

    async def remove(self, item_id: str):
        """Remove an ID from the queue (if present)."""
        async with self._lock:
            try:
                self._queue.remove(item_id)
            except ValueError:
                pass  # item not in queue

    async def contains(self, item_id: str) -> bool:
        """Check if an ID is in the queue."""
        async with self._lock:
            return item_id in self._queue

    async def get_all(self) -> list[str]:
        """Get a copy of all items."""
        async with self._lock:
            return list(self._queue)

    async def replace(self, new_items: list[str]):
        """Replace the entire queue with a new, ordered list."""
        async with self._lock:
            # dict.fromkeys removes duplicates, preserves order
            self._queue = deque(dict.fromkeys(new_items))

    async def peek(self) -> Optional[str]:
        """Return the first item (without removing it)."""
        async with self._lock:
            return self._queue[0] if self._queue else None

    async def dequeue(self) -> Optional[str]:
        """Remove and return the first item (FIFO)."""
        async with self._lock:
            return self._queue.popleft() if self._queue else None
    async def sort_reverse(self):
        """Sort the queue in reverse order."""
        async with self._lock:
            self._queue = deque(sorted(self._queue, reverse=True))

    # ----------------------
    # Unlocked (non-blocking) methods
    # ----------------------

    async def add_unlocked(self, item_id: str):
        """Add an ID without acquiring lock."""
        if item_id not in self._queue:
            self._queue.append(item_id)

    async def remove_unlocked(self, item_id: str):
        """Remove an ID without acquiring lock."""
        try:
            self._queue.remove(item_id)
        except ValueError:
            pass

    async def contains_unlocked(self, item_id: str) -> bool:
        """Check if an ID exists without lock."""
        return item_id in self._queue

    async def get_all_unlocked(self) -> list[str]:
        """Return all items without lock."""
        return list(self._queue)

    async def replace_unlocked(self, new_items: list[str]) -> None:
        """Replace the queue without lock."""
        self._queue = deque(dict.fromkeys(new_items))  # deduplicate & preserve order

    async def peek_unlocked(self) -> Optional[str]:
        """Return first item without lock."""
        return self._queue[0] if self._queue else None

    async def dequeue_unlocked(self) -> Optional[str]:
        """Remove and return first item without lock."""
        return self._queue.popleft() if self._queue else None
    async def sort_reverse_unlocked(self):
        """Sort the queue in reverse order without lock."""
        self._queue = deque(sorted(self._queue, reverse=True))

@contextlib.asynccontextmanager
async def multi_lock(queues: List['AsyncQueue']):
    """Acquire multiple AsyncQueue locks safely, avoiding deadlocks."""
    sorted_queues = sorted(queues, key=id)
    # Keep track of acquired locks
    acquired_locks = []
    try:
        for q in sorted_queues:
            await q._lock.acquire()
            acquired_locks.append(q._lock)
        yield
    finally:
        # Release in reverse order
        for lock in reversed(acquired_locks):
            lock.release()


app = FastAPI()

prio_queue = AsyncQueue()
forward_queue = AsyncQueue()
in_between_queue = AsyncQueue()
backward_queue = AsyncQueue()

in_process_queue = AsyncQueue()

async def get_id_for_worker() -> Optional[int]:
    """Get the next ID to process from the queues in order of priority."""
    logger.info("Getting ID for worker...")
    async with multi_lock([prio_queue, forward_queue, in_between_queue, backward_queue]):
        logger.debug("Got locks for all queues")
        if await prio_queue.peek_unlocked() is not None:
            id = await prio_queue.dequeue_unlocked()
            logger.info(f"Found ID {id} in priority queue")
        elif await forward_queue.peek_unlocked() is not None:
            id = await forward_queue.dequeue_unlocked()
            logger.info(f"Found ID {id} in forward queue")
        elif await in_between_queue.peek_unlocked() is not None:
            id = await in_between_queue.dequeue_unlocked()
            logger.info(f"Found ID {id} in in-between queue")
        elif await backward_queue.peek_unlocked() is not None:
            id = await backward_queue.dequeue_unlocked()
            logger.info(f"Found ID {id} in backward queue")
    if id is not None:
        res = pingVideoByID(str(id))
        if original_language_exists(id):
            logger.info(f"ID {id} already has original language, skipping.")
            return await get_id_for_worker()
        elif res == "200":
            logger.info(f"Fetched ID {id} from queue and it is available for processing, starting worker")
            # call a set timeout function that will add the id to in_process_queue and remove it after some time
            await in_process_queue.add_unlocked(id)
            asyncio.create_task(remove_id_from_in_process(id))

            return id
        else:
            logger.info(f"ID {id} not HTTP 200 (response: {res}), trying next ID.")
            return await get_id_for_worker()
    else:
        return None

async def remove_id_from_in_process(id: int):
    """Remove an ID from the in-process queue."""
    logger.debug(f"ID {id} will be removed from in-process queue after timeout.")
    await asyncio.sleep(1200)  # wait 20 minutes
    logger.debug(f"Removing ID {id} from in-process queue.")
    await in_process_queue.remove(id)

async def transcribe_worker():
    """Worker that continuously processes IDs from the queues."""
    sleep_time = 40
    await asyncio.sleep(10)  # Initial delay before starting
    logger.info("Transcribe worker started.")
    while True:
        id = await get_id_for_worker()
        logger.info(f"Got ID for worker: {id}")
        if id is not None:
            logger.info(f"Transcribing ID: {id}")
            try:
                logger.debug(f"Starting transcription for ID {id} in separate thread.")
                await asyncio.to_thread(transcribePipelineVideoByID, str(id))
            except Exception as e:
                logger.error(f"Transcription failed for ID {id}: {e}")
            # await asyncio.sleep(1000)
        else:
            logger.info(f"No IDs available to transcribe, waiting {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)  # Wait before checking again
        
async def update_upper_ids_periodically():
    """Periodically update the forward queue with new upper IDs."""
    sleep_time = 1200
    await asyncio.sleep(5)
    while True:
        logger.info("Updating upper IDs...")
        upper_ids = get_upper_ids()
        async with multi_lock([forward_queue, in_process_queue, prio_queue]):
            for uid in upper_ids:
                if not await forward_queue.contains_unlocked(uid) and not await in_process_queue.contains_unlocked(uid) and not await prio_queue.contains_unlocked(uid):
                    logger.info(f"Adding new upper ID to forward queue: {uid}")
                    await forward_queue.add_unlocked(uid)
        logger.info(f"Upper IDs update complete. Sleeping for {sleep_time // 60} minutes.")
        await asyncio.sleep(sleep_time)

async def update_inbetween_ids_periodically():
    """Periodically update the in-between queue with missing IDs."""
    sleep_time = 1200
    await asyncio.sleep(30)
    while True:
        logger.info("Updating in-between IDs...")
        missing_ids = get_missing_available_inbetween_ids()
        async with multi_lock([in_between_queue, backward_queue, in_process_queue, prio_queue]):
            for mid in missing_ids:
                if not await in_between_queue.contains_unlocked(mid) and not await in_process_queue.contains_unlocked(mid) and not await prio_queue.contains_unlocked(mid):
                    await in_between_queue.add_unlocked(mid)
                    if await backward_queue.contains_unlocked(mid):
                        logger.info(f"Removing ID {mid} from backward queue as it's now in in-between queue.")
                        await backward_queue.remove_unlocked(mid)
            await in_between_queue.sort_reverse_unlocked()
        logger.info(f"In-between IDs update complete. Sleeping for {sleep_time // 60} minutes.")
        await asyncio.sleep(sleep_time) 

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    initDatabase()
    upper_ids = get_upper_ids()
    if upper_ids is not None:
        await forward_queue.replace(upper_ids)
    smallest_id = getSmallestTeletaskID()
    if smallest_id is not None:
        await backward_queue.replace(list(range(smallest_id-1, 0, -1)))
    missing_ids = get_missing_available_inbetween_ids()
    if missing_ids:
        await in_between_queue.replace(sorted(missing_ids, reverse=True))

    logger.info("Application startup: Queues initialized.")
    logger.info("Forward queue: %s", await forward_queue.get_all())
    logger.info("In-between queue: %s", await in_between_queue.get_all())
    logger.info("Backward queue: %s", await backward_queue.get_all())
    
    # Start background tasks
    transcribe_worker_task = asyncio.create_task(transcribe_worker())
    update_upper_ids_task = asyncio.create_task(update_upper_ids_periodically())
    update_inbetween_ids_task = asyncio.create_task(update_inbetween_ids_periodically())
    yield  # Yield control to start the server
    
    transcribe_worker_task.cancel()
    try:
        await transcribe_worker_task
    except asyncio.CancelledError:
        logger.error("Can not cancel transcribe worker task.")
    logger.info("Cancelled transcribe worker task.")

    # Cancel background tasks
    update_upper_ids_task.cancel()
    update_inbetween_ids_task.cancel()
    try:
        await update_upper_ids_task
    except asyncio.CancelledError:
        logger.error("Can not cancel update upper IDs task.")
    logger.info("Cancelled update upper IDs task.")
    try:
        await update_inbetween_ids_task
    except asyncio.CancelledError:
        logger.error("Can not cancel update in-between IDs task.")
    logger.info("Cancelled update in-between IDs task.")

    logger.info("Application shutdown complete.")

# Initialize FastAPI with the lifespan
app = FastAPI(lifespan=lifespan)

#DEBUGGING ENDPOINTS
@app.get("/queues")
async def get_queues():
    prio = await prio_queue.get_all()
    forward = await forward_queue.get_all()
    in_between = await in_between_queue.get_all()
    backward = await backward_queue.get_all()
    in_process = await in_process_queue.get_all()
    return {
        "priority_queue": prio,
        "forward_queue": forward,
        "in_between_queue": in_between,
        "backward_queue": backward,
        "in_process_queue": in_process
    }

@app.get("/ping")
async def ping_pong():
    return "pong"

@app.post("/prioritize/{id}")
async def prioritize_id(id: int):
    res = pingVideoByID(str(id))
    if res == "200":
        async with multi_lock([prio_queue, forward_queue, in_between_queue, backward_queue, in_process_queue]):
            if await in_process_queue.contains_unlocked(id):
                logger.info(f"ID {id} is currently being processed; cannot prioritize.")
                return {"message": f"ID {id} is currently being processed; cannot prioritize."}
            if await prio_queue.contains_unlocked(id):
                logger.info(f"ID {id} is already in priority queue.")
                return {"message": f"ID {id} was already prioritized."}
            if await forward_queue.contains_unlocked(id):
                await forward_queue.remove_unlocked(id)
                logger.info(f"Removed ID {id} from forward queue for prioritization.")
            if await in_between_queue.contains_unlocked(id):
                await in_between_queue.remove_unlocked(id)
                logger.info(f"Removed ID {id} from in-between queue for prioritization.")
            if await backward_queue.contains_unlocked(id):
                await backward_queue.remove_unlocked(id)
                logger.info(f"Removed ID {id} from backward queue for prioritization.")
            await prio_queue.add_unlocked(id)
            logger.info(f"Added ID {id} to priority queue.")
            return {"message": f"ID {id} prioritized."}
    else:
        logger.error(f"ID {id} cannot be prioritized as it is not available (response: {res}).")
        return {"message": f"ID {id} cannot be prioritized as it is not available."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)