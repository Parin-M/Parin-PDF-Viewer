"""Transactional PDF serialization and validated file replacement.

The service owns temporary output creation, encryption policy, output
validation and atomic replacement. The Reader remains responsible for
transferring the returned document into its UI and updating reader state.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

import pymupdf as fitz

from .document_service import is_document_encrypted


@dataclass(frozen=True)
class SavedPDF:
    """A fully written and validated PDF ready for the Reader to adopt."""

    document: object
    file_path: str
    page_index: int
    encrypted: bool
    password: str


def save_pdf_document(
    document,
    save_path,
    *,
    page_index: int = 0,
    encrypted: bool = False,
    source_password: str = "",
    password_after: str | None = None,
    large_file_mode: bool = False,
    save_options: dict | None = None,
) -> SavedPDF:
    """Save to a same-directory temporary file, validate it, then replace target.

    The source document is never closed or mutated by this service. Until
    os.replace succeeds, an existing destination file remains untouched.
    On failure, the candidate handle and temporary output are cleaned up.
    """
    if document is None or getattr(document, "is_closed", False):
        raise ValueError("There is no open PDF document to save.")

    normalized_path = os.path.abspath(os.path.expanduser(os.fspath(save_path)))
    output_dir = os.path.dirname(normalized_path) or os.getcwd()
    temp_path = None
    candidate = None

    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=".parin-pdf-",
            suffix=".pdf",
            dir=output_dir,
        )
        os.close(fd)
        os.unlink(temp_path)

        options = {
            "garbage": 0 if large_file_mode else 4,
            "deflate": True,
        }
        if save_options:
            options.update(save_options)
        elif encrypted:
            # Preserve encrypted PDFs even when their user password is empty.
            options["encryption"] = fitz.PDF_ENCRYPT_KEEP

        document.save(temp_path, **options)

        # Validate the candidate while the active source remains available.
        candidate = fitz.open(temp_path)
        candidate_encrypted = is_document_encrypted(candidate)
        candidate_password = (
            source_password if password_after is None else str(password_after)
        )
        if (
            candidate_encrypted
            and getattr(candidate, "needs_pass", False)
            and not candidate.authenticate(candidate_password)
        ):
            raise RuntimeError(
                "The saved PDF could not be unlocked with the selected password."
            )
        if candidate.page_count < 1:
            raise RuntimeError("The saved PDF contains no readable pages.")

        target_page = max(0, min(int(page_index), candidate.page_count - 1))
        candidate.load_page(target_page)

        # The temporary file is in the destination directory: replacement is
        # atomic on the same filesystem and occurs only after full validation.
        os.replace(temp_path, normalized_path)
        temp_path = None

        result = SavedPDF(
            document=candidate,
            file_path=normalized_path,
            page_index=target_page,
            encrypted=candidate_encrypted,
            password=candidate_password,
        )
        candidate = None
        return result
    except Exception:
        if candidate is not None:
            try:
                candidate.close()
            except Exception:
                pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise


__all__ = ["SavedPDF", "save_pdf_document"]
