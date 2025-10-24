import uvicorn
from fastapi import FastAPI, HTTPException

# 1. Create the FastAPI app instance
app = FastAPI()

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
async def get_by_id(item_id: int):
    """Return a simple response for any natural-number id.

    - Accepts only integers via path parameter typing.
    - Validates that the number is a natural number (> 0).
    """
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="ID must be a positive integer")

    # Here you can implement lookup logic (database, file, etc.).
    # For now return a JSON payload that includes the id so the caller can see it reflected.
    return {"id": item_id, "message": f"Requested resource for id {item_id}"}


@app.get("/{item_id}/{language}")
async def get_by_id(item_id: int, language: str):
    """Return a simple response for any natural-number id.

    - Accepts only integers via path parameter typing.
    - Validates that the number is a natural number (> 0).
    """
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="ID must be a positive integer")

    # Here you can implement lookup logic (database, file, etc.).
    # For now return a JSON payload that includes the id so the caller can see it reflected.
    return {"id": item_id, "message": f"Requested resource for id {item_id} and language {language}"}


# 4. Add the main entry point to run the server
if __name__ == "__main__":
    # This block allows you to run: python index.py
    print("Starting minimal server at http://127.0.0.1:8000")
    print("Try visiting http://127.0.0.1:8000/ping or http://127.0.0.1:8000/1")
    uvicorn.run(app, host="127.0.0.1", port=8000)

