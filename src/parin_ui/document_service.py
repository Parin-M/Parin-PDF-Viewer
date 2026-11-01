"""PDF document opening, authentication and preflight validation.

This module owns the non-UI part of opening a PDF. It deliberately does not
import Qt or touch the active Reader document; callers decide when a validated
candidate is allowed to replace the currently open document.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

import pymupdf as fitz


MAX_PREFLIGHT_RENDER_DIMENSION = 12_000
MAX_PREFLIGHT_RENDER_PIXELS = 1_000_000


class PasswordRequiredError(RuntimeError):
    """Raised when a PDF needs a non-empty password before it can be inspected."""


class IncorrectPasswordError(RuntimeError):
    """Raised when a supplied PDF password does not authenticate the document."""


@dataclass(frozen=True)
class OpenedPDF:
    """A validated candidate document ready for an explicit UI-side handoff."""

    document: object
    file_path: str
    file_size: int
    encrypted: bool
    password: str


def is_document_encrypted(document) -> bool:
    """Detect encryption even after PyMuPDF auto-authenticates an empty password."""
    if document is None or getattr(document, "is_closed", False):
        return False
    try:
        encryption = (document.metadata or {}).get("encryption")
        if encryption and str(encryption).strip().lower() not in ("none", "null"):
            return True
    except Exception:
        pass
    try:
        return bool(document.is_encrypted)
    except Exception:
        return False


def preflight_pdf_page(
    document,
    page_index: int = 0,
    *,
    max_dimension: int = MAX_PREFLIGHT_RENDER_DIMENSION,
    max_pixels: int = MAX_PREFLIGHT_RENDER_PIXELS,
) -> None:
    """Load and rasterize a bounded sample before a candidate can be adopted."""
    if page_index < 0 or page_index >= document.page_count:
        raise ValueError("The requested PDF page is outside the document.")
    page = document.load_page(page_index)
    width = max(1.0, float(page.rect.width))
    height = max(1.0, float(page.rect.height))
    scale = min(
        0.25,
        max_dimension / max(width, height),
        math.sqrt(max_pixels / (width * height)),
    )
    if not math.isfinite(scale) or scale <= 0:
        raise RuntimeError("The PDF page has invalid dimensions.")
    pix = page.get_pixmap(
        matrix=fitz.Matrix(scale, scale),
        colorspace=fitz.csRGB,
        alpha=False,
    )
    if (
        pix.width < 1
        or pix.height < 1
        or pix.n != 3
        or len(pix.samples) < pix.stride * pix.height
        or pix.width * pix.height > max_pixels
        or max(pix.width, pix.height) > max_dimension
    ):
        raise RuntimeError("The PDF renderer returned an invalid page image.")


def open_pdf_document(file_path, password: str | None = None) -> OpenedPDF:
    """Open and validate a PDF without changing any currently active document.

    When password is None, an empty user password is tried first. A
    PasswordRequiredError signals the UI to request a password. Each failed
    attempt closes its own candidate before returning control to the caller.
    """
    normalized_path = os.path.abspath(os.path.expanduser(os.fspath(file_path)))
    if not os.path.isfile(normalized_path):
        raise FileNotFoundError(f"File does not exist: {normalized_path}")
    file_size = os.path.getsize(normalized_path)
    candidate = None
    try:
        candidate = fitz.open(normalized_path)
        encrypted = is_document_encrypted(candidate)
        accepted_password = ""
        if encrypted and getattr(candidate, "needs_pass", False):
            supplied_password = "" if password is None else str(password)
            if not candidate.authenticate(supplied_password):
                if password is None:
                    raise PasswordRequiredError("This PDF requires a password.")
                raise IncorrectPasswordError("The supplied PDF password is incorrect.")
            accepted_password = supplied_password

        if candidate.page_count < 1:
            raise ValueError("The PDF contains no readable pages.")
        preflight_pdf_page(candidate, 0)
        opened = OpenedPDF(
            document=candidate,
            file_path=normalized_path,
            file_size=file_size,
            encrypted=encrypted,
            password=accepted_password,
        )
        candidate = None
        return opened
    except Exception:
        if candidate is not None:
            try:
                candidate.close()
            except Exception:
                pass
        raise


__all__ = [
    "OpenedPDF",
    "PasswordRequiredError",
    "IncorrectPasswordError",
    "is_document_encrypted",
    "preflight_pdf_page",
    "open_pdf_document",
]
