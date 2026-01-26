"""Compatibility shim.

Backend logic was moved to the `backend/` package.
"""

from backend.prompt_shield import (  # noqa: F401
    detect_groundness_result,
    is_prompt_safe_from_jailbreak,
    shield_prompt_body,
)
