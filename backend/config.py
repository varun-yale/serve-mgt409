"""Configuration and secrets.

`.env` is loaded from the SERVE project root first, then from its parent
directory. Values already found are never overwritten, so the project's own
`.env` wins. As a convenience for the course folder layout (where the shared
key lives a couple of levels up), further ancestors are checked last.

Secrets stay on the server: nothing in this module is ever sent to the browser.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = Path(os.getenv("SERVE_DB_PATH", DATA_DIR / "serve.db"))
PRICES_PATH = BACKEND_DIR / "prices.json"
FRONTEND_DIST = PROJECT_ROOT / "dist"


def _env_files() -> list[Path]:
    """Project root first, then parent, then any further ancestors."""
    files = [PROJECT_ROOT / ".env", PROJECT_ROOT.parent / ".env"]
    files += [p / ".env" for p in PROJECT_ROOT.parent.parents]
    return files


LOADED_ENV_FILES: list[str] = []
for _f in _env_files():
    if _f.is_file():
        load_dotenv(_f, override=False)
        LOADED_ENV_FILES.append(str(_f))

MODEL_NAME = os.getenv("SERVE_MODEL", "gpt-6-luna")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
TIMEZONE = ZoneInfo("America/New_York")


def portkey_key() -> str | None:
    return os.getenv("PORTKEY_API_KEY")


def openai_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def portkey_provider() -> str | None:
    """Optional Portkey provider slug (e.g. `@openai-personal`). Only needed when
    the Portkey key has no default provider/config attached."""
    return os.getenv("PORTKEY_PROVIDER") or None


# Admin access is a shared token sent in the X-Admin-Token header. This is a
# demo-grade gate, not real user authentication. If none is configured a random
# token is generated at startup and printed to the server console.
ADMIN_TOKEN = os.getenv("SERVE_ADMIN_TOKEN") or secrets.token_urlsafe(12)
ADMIN_TOKEN_GENERATED = not os.getenv("SERVE_ADMIN_TOKEN")

# The member portal has a single demo member (no member login in this prototype).
DEMO_MEMBER_ID = "mem_arjun_patel"
