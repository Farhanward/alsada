"""Configuration loading and project paths + enterprise runtime config (``ALSADA_*``)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _dir_override(name: str, default: Path) -> Path:
    """Allow an isolated entity profile via env (config/data/reports), else default.

    Backward compatible: when the var is unset the historical path is used, so the
    scheduled CarbonFlow job is unaffected. Set these to run another entity (e.g.
    a creator profile) without touching the primary client's config, DB or reports.
    """
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


CONFIG_DIR = _dir_override("ALSADA_CONFIG_DIR", PROJECT_ROOT / "config")
DATA_DIR = _dir_override("ALSADA_DATA_DIR", PROJECT_ROOT / "data")
REPORTS_DIR = _dir_override("ALSADA_REPORTS_DIR", PROJECT_ROOT / "reports")


def load_client() -> dict:
    return json.loads((CONFIG_DIR / "client.json").read_text(encoding="utf-8"))


def load_prompts() -> list:
    return json.loads((CONFIG_DIR / "prompts.json").read_text(encoding="utf-8"))["prompts"]


def load_env(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from .env.local into os.environ without overwriting existing vars."""
    p = Path(path) if path else (PROJECT_ROOT / ".env.local")
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


# --- Enterprise service configuration (env-driven) ---------------------------


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


@dataclass(frozen=True)
class ServiceConfig:
    home: Path = field(default_factory=lambda: PROJECT_ROOT)
    api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8808
    max_body_bytes: int = 1_048_576
    log_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    log_level: str = "INFO"

    @property
    def auth_required(self) -> bool:
        return bool(self.api_key)


def load_config() -> ServiceConfig:
    home = _env_path("ALSADA_HOME", PROJECT_ROOT)
    return ServiceConfig(
        home=home,
        api_key=os.environ.get("ALSADA_API_KEY", "").strip(),
        host=os.environ.get("ALSADA_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_env_int("ALSADA_PORT", 8808),
        max_body_bytes=_env_int("ALSADA_MAX_BODY_BYTES", 1_048_576, minimum=1024),
        log_dir=_env_path("ALSADA_LOG_DIR", home / "logs"),
        log_level=os.environ.get("ALSADA_LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
