"""Tiny JSON settings + cache dir in the user's data folder (cross-platform)."""
import json
import os
import sys
from pathlib import Path


def data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    d = base / "Youtubent"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    d = data_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file() -> Path:
    return data_dir() / "settings.json"


def load() -> dict:
    try:
        return json.loads(_file().read_text())
    except Exception:
        return {}


def save(d: dict) -> None:
    _file().write_text(json.dumps(d, indent=2))
