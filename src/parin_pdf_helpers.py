"""Small, dependency-free helpers shared by Parin PDF Viewer and its tests."""
from __future__ import annotations

import math
import os
from collections.abc import Iterable
from pathlib import Path

APP_VERSION = "9.1.4"
RECENT_FILES_LIMIT = 10

# Prefer the native Rust implementation when installed; source checkouts retain a Python fallback.
try:
    from _parin_rust_core import clamp_zoom as _rust_clamp_zoom
except ImportError:
    _rust_clamp_zoom = None


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
    """Clamp zoom using Rust when available, with defensive Python fallback."""
    if _rust_clamp_zoom is not None:
        try:
            return float(_rust_clamp_zoom(value, minimum, maximum))
        except (TypeError, ValueError, OverflowError):
            pass
    try:
        lower = float(minimum)
        upper = float(maximum)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Invalid zoom bounds.") from None
    if not math.isfinite(lower) or not math.isfinite(upper) or lower <= 0 or upper < lower:
        raise ValueError("Invalid zoom bounds.")
    try:
        zoom = float(value)
    except (TypeError, ValueError, OverflowError):
        return max(lower, min(1.0, upper))
    if not math.isfinite(zoom):
        return max(lower, min(1.0, upper))
    return max(lower, min(zoom, upper))
