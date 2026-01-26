from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from the repo root .env (if present).

    Uvicorn can be launched from different working directories; using an explicit
    path avoids "it works in one terminal but not another" issues.
    """

    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)

    # Back-compat: accept AZURE_OPENAI_API_BASE from other samples/configs.
    # Normalize it to what the OpenAI SDK expects: AZURE_OPENAI_ENDPOINT.
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        api_base = os.getenv("AZURE_OPENAI_API_BASE")
        if api_base:
            parsed = urlparse(api_base)
            if parsed.scheme and parsed.netloc:
                # e.g. https://<resource>.openai.azure.com/openai/v1/ -> https://<resource>.openai.azure.com
                os.environ["AZURE_OPENAI_ENDPOINT"] = f"{parsed.scheme}://{parsed.netloc}"


def validate_required_env() -> None:
    """Validate required environment variables for Azure calls.

    Raises:
        RuntimeError: if required variables are missing.
    """

    required = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_CONTENT_SAFETY_ENDPOINT",
        "AZURE_CONTENT_SAFETY_KEY",
    ]

    missing = [name for name in required if not os.getenv(name)]
    # AZURE_OPENAI_ENDPOINT can be provided directly or derived from AZURE_OPENAI_API_BASE.
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        missing.append("AZURE_OPENAI_ENDPOINT (or AZURE_OPENAI_API_BASE)")

    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables: "
            f"{missing_list}. "
            "Check your .env in the repo root."
        )
