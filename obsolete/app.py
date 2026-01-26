"""Compatibility shim.

Backend logic was moved to the `backend/` package.
Prefer running `uvicorn backend.app:app --reload`.
"""

from backend.app import app  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
