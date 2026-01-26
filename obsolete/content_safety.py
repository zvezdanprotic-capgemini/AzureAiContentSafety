"""Compatibility shim.

Backend logic was moved to the `backend/` package.
"""

from backend.content_safety import is_content_safe  # noqa: F401
