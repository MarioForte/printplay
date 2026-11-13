"""Locate the TiMini-Print checkout without requiring PYTHONPATH."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def ensure_timiniprint_path() -> None:
    """Add a sibling or TIMINIPRINT_ROOT checkout to sys.path if present."""
    candidates: list[Path] = []
    env = os.environ.get("TIMINIPRINT_ROOT")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path(__file__).resolve().parent.parent.parent / "timini-print")
    candidates.append(Path.cwd() / "timini-print")

    for candidate in candidates:
        if not (candidate / "timiniprint").is_dir():
            continue
        resolved = str(candidate.resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
        return
