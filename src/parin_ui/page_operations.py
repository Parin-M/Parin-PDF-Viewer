"""Qt-free PDF page operations used by the Reader and Page Organizer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

import pymupdf as fitz

from .document_save_service import save_pdf_document


@dataclass(frozen=True)
class PageEditPlan:
    """Validated page ordering, deletion and rotation instructions."""

    page_count: int
    order: tuple[int, ...]
    rotations: tuple[tuple[int, int], ...]

    @property
    def has_changes(self) -> bool:
        return self.order != tuple(range(self.page_count)) or bool(self.rotations)


@dataclass(frozen=True)
class ExtractedPDF:
    """Summary of an extracted PDF after it has been atomically saved."""

    file_path: str
    page_count: int


def _require_open_document(document, label: str) -> int:
    if document is None or getattr(document, "is_closed", False):
        raise ValueError(f"The {label} PDF document is not open.")
    count = int(document.page_count)
    if count < 1:
        raise ValueError(f"The {label} PDF document contains no pages.")
    return count


def _validate_page_indexes(
    page_count: int,
    page_indexes: Sequence[int],
    *,
    allow_subset: bool,
) -> tuple[int, ...]:
    if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1:
        raise ValueError("The PDF must contain at least one page.")
    try:
        indexes = tuple(page_indexes)
    except TypeError as exc:
        raise ValueError("Page indexes must be an ordered sequence.") from exc
    if not indexes:
        raise ValueError("Select at least one page.")
    if any(isinstance(index, bool) or not isinstance(index, int) for index in indexes):
        raise ValueError("Page indexes must be integers.")
    if any(index < 0 or index >= page_count for index in indexes):
        raise ValueError("A selected page is outside the document.")
    if len(indexes) != len(set(indexes)):
        raise ValueError("A page cannot appear more than once.")
    if not allow_subset and len(indexes) != page_count:
        raise ValueError("A complete page order is required.")
    return indexes


def create_page_edit_plan(
    page_count: int,
    order: Sequence[int],
    rotations: Mapping[int, int] | None = None,
) -> PageEditPlan:
    """Validate an organizer result without mutating the open PDF."""
    normalized_order = _validate_page_indexes(
        page_count,
        order,
        allow_subset=True,
    )
    if rotations is None:
        rotations = {}
    if not isinstance(rotations, Mapping):
        raise ValueError("Page rotations must be a mapping.")

    included = set(normalized_order)
    normalized_rotations = []
    for page_index, delta in rotations.items():
        if (
            isinstance(page_index, bool)
            or not isinstance(page_index, int)
            or page_index < 0
            or page_index >= page_count
        ):
            raise ValueError("A rotation references a page outside the document.")
        if isinstance(delta, bool) or not isinstance(delta, int) or delta % 90:
            raise ValueError("Page rotations must be multiples of 90 degrees.")
        delta %= 360
        if delta and page_index in included:
            normalized_rotations.append((page_index, delta))

    return PageEditPlan(
        page_count=page_count,
        order=normalized_order,
        rotations=tuple(sorted(normalized_rotations)),
    )


def apply_page_edit_plan(document, plan: PageEditPlan) -> None:
    """Apply a previously validated page plan to the live PDF document.

    The caller should record the document's undo checkpoint before invoking
    this operation. Validation is completed before the first mutation.
    """
    page_count = _require_open_document(document, "source")
    if not isinstance(plan, PageEditPlan) or plan.page_count != page_count:
        raise ValueError("The page edit plan does not match the current document.")
    # Revalidate caller-provided plans so manually constructed instances cannot
    # bypass the same range and uniqueness guarantees.
    validated = create_page_edit_plan(page_count, plan.order, dict(plan.rotations))
    for page_index, delta in validated.rotations:
        page = document.load_page(page_index)
        page.set_rotation((page.rotation + delta) % 360)
    if validated.order != tuple(range(page_count)):
        document.select(list(validated.order))


def insert_pdf_pages(target_document, source_document, *, start_at: int) -> int:
    """Insert all readable source pages at the requested target position."""
    target_count = _require_open_document(target_document, "destination")
    source_count = _require_open_document(source_document, "source")
    if isinstance(start_at, bool) or not isinstance(start_at, int):
        raise ValueError("The insertion position must be an integer.")
    if start_at < 0 or start_at > target_count:
        raise ValueError("The insertion position is outside the destination PDF.")
    target_document.insert_pdf(source_document, start_at=start_at)
    return source_count


def extract_pdf_pages(document, page_indexes: Sequence[int], save_path) -> ExtractedPDF:
    """Extract selected pages in the specified order using atomic PDF saving."""
    page_count = _require_open_document(document, "source")
    indexes = _validate_page_indexes(page_count, page_indexes, allow_subset=True)
    normalized_path = os.path.abspath(os.path.expanduser(os.fspath(save_path)))
    output = fitz.open()
    saved_document = None
    try:
        for page_index in indexes:
            output.insert_pdf(
                document,
                from_page=page_index,
                to_page=page_index,
            )
        saved = save_pdf_document(output, normalized_path, page_index=0)
        saved_document = saved.document
        return ExtractedPDF(
            file_path=saved.file_path,
            page_count=len(indexes),
        )
    finally:
        if saved_document is not None:
            saved_document.close()
        output.close()


__all__ = [
    "PageEditPlan",
    "ExtractedPDF",
    "create_page_edit_plan",
    "apply_page_edit_plan",
    "insert_pdf_pages",
    "extract_pdf_pages",
]
