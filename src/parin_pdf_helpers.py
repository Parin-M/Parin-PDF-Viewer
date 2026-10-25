"""Small, dependency-free helpers shared by Parin PDF Viewer and its tests."""
from __future__ import annotations

import math
import os
from collections.abc import Iterable
from pathlib import Path

APP_VERSION = "8.9.0"
RECENT_FILES_LIMIT = 10


def normalize_recent_files(paths: object, limit: int = RECENT_FILES_LIMIT) -> list[str]:
    """Return absolute, unique recent paths in most-recent-first order."""
    if limit <= 0:
        return []
    if isinstance(paths, (str, os.PathLike)):
        candidates = [paths]
    elif isinstance(paths, Iterable):
        candidates = paths
    else:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, (str, os.PathLike)):
            continue
        raw = os.fspath(candidate).strip()
        if not raw:
            continue
        absolute = os.path.abspath(os.path.expanduser(raw))
        key = os.path.normcase(absolute)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(absolute)
        if len(normalized) >= limit:
            break
    return normalized


def add_recent_file(paths: object, file_path: str | os.PathLike[str], limit: int = RECENT_FILES_LIMIT) -> list[str]:
    """Move a path to the front of the recent-file list and enforce its limit."""
    existing = normalize_recent_files(paths, limit=max(limit, RECENT_FILES_LIMIT))
    return normalize_recent_files([file_path, *existing], limit=limit)


def ensure_pdf_extension(file_path: str | os.PathLike[str]) -> str:
    """Ensure a chosen output path ends in .pdf, without changing its directory."""
    path = os.fspath(file_path)
    if not path.strip():
        raise ValueError("A non-empty output path is required.")
    return path if Path(path).suffix.lower() == ".pdf" else path + ".pdf"


def same_path(first: str | os.PathLike[str], second: str | os.PathLike[str]) -> bool:
    """Compare paths robustly, including relative paths and platform case rules."""
    if not first or not second:
        return False
    a = os.path.normcase(os.path.abspath(os.path.expanduser(os.fspath(first))))
    b = os.path.normcase(os.path.abspath(os.path.expanduser(os.fspath(second))))
    return a == b


def clamp_zoom(value: float, minimum: float = 0.1, maximum: float = 8.0) -> float:
    """Clamp zoom to finite positive bounds, even when persisted settings are corrupt."""
    try:
        zoom = float(value)
    except (TypeError, ValueError):
        return 1.0
    if not math.isfinite(zoom):
        return 1.0
    if minimum <= 0 or maximum < minimum:
        raise ValueError("Invalid zoom bounds.")
    return max(minimum, min(zoom, maximum))
