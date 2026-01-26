"""Compatibility shim.

Backend logic was moved to the `backend/` package.
"""

from backend.openai_client import get_llm_response  # noqa: F401
