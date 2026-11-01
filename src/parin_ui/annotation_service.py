"""Qt-free PDF annotation creation and erasing operations."""

from __future__ import annotations

import math
from collections.abc import Sequence

import pymupdf as fitz


def _point_xy(point) -> tuple[float, float]:
    try:
        x, y = float(point.x), float(point.y)
    except AttributeError:
        try:
            x, y = float(point[0]), float(point[1])
        except (TypeError, ValueError, IndexError, KeyError) as exc:
            raise ValueError("A valid PDF point is required.") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("PDF point coordinates must be finite.")
    return x, y


def _rgb_color(color: Sequence[float]) -> tuple[float, float, float]:
    try:
        values = tuple(float(component) for component in color)
    except (TypeError, ValueError) as exc:
        raise ValueError("Annotation color must contain three RGB values.") from exc
    if len(values) != 3 or any(
        not math.isfinite(component) or component < 0.0 or component > 1.0
        for component in values
    ):
        raise ValueError("RGB color components must be finite values from 0 to 1.")
    return values


def _require_page(page):
    if page is None or getattr(page, "parent", None) is None:
        raise ValueError("An open PDF page is required.")
    return page


def add_ink_annotation(
    page,
    stroke: Sequence[Sequence[float]],
    color: Sequence[float],
    *,
    tool: str = "pen",
):
    """Create a pen or translucent highlighter ink annotation."""
    page = _require_page(page)
    rgb = _rgb_color(color)
    if tool not in ("pen", "highlight"):
        raise ValueError("Ink tool must be 'pen' or 'highlight'.")
    try:
        points = [(float(point[0]), float(point[1])) for point in stroke]
    except (TypeError, ValueError, IndexError, KeyError) as exc:
        raise ValueError("Ink stroke must contain coordinate pairs.") from exc
    if len(points) < 2 or any(
        not math.isfinite(value) for point in points for value in point
    ):
        raise ValueError("Ink stroke must contain at least two finite points.")

    annotation = page.add_ink_annot([points])
    try:
        annotation.set_colors(stroke=rgb)
        if tool == "pen":
            annotation.set_border(width=2)
        else:
            annotation.set_border(width=14)
            annotation.set_opacity(0.35)
        annotation.update()
        return annotation
    except Exception:
        try:
            page.delete_annot(annotation)
        except Exception:
            pass
        raise


def add_text_annotation(
    page,
    text: str,
    point,
    *,
    font_size: int = 12,
    font_name: str = "helv",
    text_color: Sequence[float] = (0.0, 0.0, 0.0),
):
    """Place a FreeText annotation, keeping its rectangle inside the page bounds."""
    page = _require_page(page)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text annotation content cannot be empty.")
    if isinstance(font_size, bool) or not isinstance(font_size, (int, float)):
        raise ValueError("Text annotation font size must be a positive number.")
    if not math.isfinite(float(font_size)) or font_size <= 0:
        raise ValueError("Text annotation font size must be a positive number.")
    if not isinstance(font_name, str) or not font_name.strip():
        raise ValueError("A valid PDF font name is required.")
    rgb = _rgb_color(text_color)
    px, py = _point_xy(point)

    # Preserve the Reader's existing width/height heuristics and edge clamping.
    width = min(max(80.0, len(text) * font_size * 0.68), max(40.0, page.rect.width))
    height = min(max(30.0, font_size * 2.6), max(20.0, page.rect.height))
    x_max = max(page.rect.x0, page.rect.x1 - width)
    y_max = max(page.rect.y0, page.rect.y1 - height)
    x = min(max(page.rect.x0, px), x_max)
    y = min(max(page.rect.y0, py), y_max)
    rect = fitz.Rect(x, y, x + width, y + height)

    annotation = page.add_freetext_annot(
        rect,
        text,
        fontsize=font_size,
        fontname=font_name,
        text_color=rgb,
        fill_color=None,
        border_width=0,
    )
    try:
        annotation.update()
        return annotation
    except Exception:
        try:
            page.delete_annot(annotation)
        except Exception:
            pass
        raise


def erase_annotations_at_point(
    page,
    point,
    *,
    zoom_factor: float = 1.0,
    base_radius: float = 20.0,
) -> int:
    """Delete annotations whose bounds intersect the eraser's PDF-space brush."""
    page = _require_page(page)
    if (
        isinstance(zoom_factor, bool)
        or not isinstance(zoom_factor, (int, float))
        or not math.isfinite(float(zoom_factor))
        or zoom_factor <= 0
    ):
        raise ValueError("Zoom factor must be a positive finite number.")
    if (
        isinstance(base_radius, bool)
        or not isinstance(base_radius, (int, float))
        or not math.isfinite(float(base_radius))
        or base_radius <= 0
    ):
        raise ValueError("Eraser radius must be a positive finite number.")
    px, py = _point_xy(point)
    radius = float(base_radius) / float(zoom_factor)
    erase_rect = fitz.Rect(px - radius, py - radius, px + radius, py + radius)
    annotations = list(page.annots() or ())
    matches = [annotation for annotation in annotations if annotation.rect.intersects(erase_rect)]
    for annotation in matches:
        page.delete_annot(annotation)
    return len(matches)


__all__ = [
    "add_ink_annotation",
    "add_text_annotation",
    "erase_annotations_at_point",
]
