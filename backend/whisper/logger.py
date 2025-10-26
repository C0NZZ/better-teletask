import os
import threading
from datetime import datetime

_lock = threading.Lock()


def _format_line(msg: str) -> str:
    """Return a single log line prefixed with a local ISO timestamp.

    Kept at module scope so multiple logging functions reuse the same
    formatting logic and it's easy to change in one place.
    """
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    return f"[{ts}] {msg.rstrip()}\n"

def log(message: str) -> None:
    """
    Append `message` as a new line to ./logs/log.txt (relative to the current working directory).
    Creates the logs directory if it doesn't exist. Thread-safe.
    """
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "log.txt")

    # Ensure a single writer at a time
    with _lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(_format_line(message))
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # fsync may fail on some platforms; ignore to keep logging robust
                pass

def logAborts(message: str) -> None:
    """
    Append `message` as a new line to ./logs/log.txt (relative to the current working directory).
    Creates the logs directory if it doesn't exist. Thread-safe.
    """
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "aborts.txt")

    # Ensure a single writer at a time
    with _lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(_format_line(message))
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # fsync may fail on some platforms; ignore to keep logging robust
                pass