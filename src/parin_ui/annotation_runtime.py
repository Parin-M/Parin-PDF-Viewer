"""Bounded runtime helpers for high-volume PDF annotation sessions."""

from __future__ import annotations

import math
from collections import OrderedDict


MAX_STROKE_POINTS = 4096
MAX_PREVIEW_POINTS = 768
MIN_STROKE_DISTANCE_PX = 1.25
DEFAULT_PAGE_CACHE_BYTES = 48 * 1024 * 1024


def _coordinates(point) -> tuple[float, float]:
    """Read a finite x/y pair from a tuple or Qt-like point object."""
    try:
        x_value = getattr(point, "x")
        y_value = getattr(point, "y")
        x = x_value() if callable(x_value) else x_value
        y = y_value() if callable(y_value) else y_value
    except AttributeError:
        try:
            x, y = point[0], point[1]
        except (TypeError, ValueError, IndexError, KeyError) as exc:
            raise ValueError("A stroke point must contain x and y coordinates.") from exc
    try:
        result = float(x), float(y)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Stroke coordinates must be finite numbers.") from exc
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Stroke coordinates must be finite numbers.")
    return result


def append_stroke_sample(
    pdf_points: list,
    view_points: list,
    pdf_point,
    view_point,
    *,
    minimum_distance_px: float = MIN_STROKE_DISTANCE_PX,
    max_points: int = MAX_STROKE_POINTS,
) -> bool:
    """Append a synchronized PDF/screen sample while bounding stroke memory.

    Near-duplicate screen samples are discarded. If a stroke grows past its
    point budget, alternate interior samples are compacted while preserving
    the first and last points. A stroke may continue indefinitely in time
    without allowing its point arrays to grow indefinitely.
    """
    if not isinstance(pdf_points, list) or not isinstance(view_points, list):
        raise ValueError("Stroke sample buffers must be mutable lists.")
    if len(pdf_points) != len(view_points):
        raise ValueError("PDF and screen stroke buffers must have equal lengths.")
    if isinstance(max_points, bool) or not isinstance(max_points, int) or max_points < 3:
        raise ValueError("max_points must be an integer of at least three.")
    if (
        isinstance(minimum_distance_px, bool)
        or not isinstance(minimum_distance_px, (int, float))
        or not math.isfinite(float(minimum_distance_px))
        or minimum_distance_px < 0
    ):
        raise ValueError("minimum_distance_px must be a finite non-negative number.")

    pdf_xy = _coordinates(pdf_point)
    view_xy = _coordinates(view_point)
    if view_points:
        last_x, last_y = _coordinates(view_points[-1])
        dx = view_xy[0] - last_x
        dy = view_xy[1] - last_y
        threshold = float(minimum_distance_px)
        if dx * dx + dy * dy < threshold * threshold:
            return False

    pdf_points.append(pdf_xy)
    view_points.append(view_xy)
    if len(pdf_points) > max_points:
        keep = [0, *range(2, len(pdf_points) - 1, 2), len(pdf_points) - 1]
        pdf_points[:] = [pdf_points[index] for index in keep]
        view_points[:] = [view_points[index] for index in keep]
    return True


def preview_stroke_points(points, *, max_points: int = MAX_PREVIEW_POINTS) -> list[tuple[float, float]]:
    """Return a visually representative, bounded preview path."""
    if isinstance(max_points, bool) or not isinstance(max_points, int) or max_points < 2:
        raise ValueError("max_points must be an integer of at least two.")
    normalized = [_coordinates(point) for point in points]
    if len(normalized) <= max_points:
        return normalized
    last_index = len(normalized) - 1
    indexes = [
        round(index * last_index / (max_points - 1))
        for index in range(max_points)
    ]
    return [normalized[index] for index in indexes]


class PageRenderCache:
    """Byte-bounded LRU cache for rendered page images.

    Cache keys are expected to start with (document_token, page_index). Values
    are held by reference; Qt pixmaps are created and accessed by the GUI thread.
    """

    def __init__(self, max_bytes: int = DEFAULT_PAGE_CACHE_BYTES) -> None:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise ValueError("max_bytes must be a positive integer.")
        self.max_bytes = max_bytes
        self._items: OrderedDict[tuple, tuple[object, int]] = OrderedDict()
        self._current_bytes = 0

    @property
    def current_bytes(self) -> int:
        return self._current_bytes

    def __len__(self) -> int:
        return len(self._items)

    def get(self, key):
        entry = self._items.get(key)
        if entry is None:
            return None
        self._items.move_to_end(key)
        return entry[0]

    def put(self, key, value, byte_size: int) -> bool:
        if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 0:
            raise ValueError("byte_size must be a non-negative integer.")
        previous = self._items.pop(key, None)
        if previous is not None:
            self._current_bytes -= previous[1]
        if byte_size == 0 or byte_size > self.max_bytes:
            return False
        while self._items and self._current_bytes + byte_size > self.max_bytes:
            _, (_, removed_size) = self._items.popitem(last=False)
            self._current_bytes -= removed_size
        self._items[key] = (value, byte_size)
        self._current_bytes += byte_size
        return True

    def invalidate_page(self, page_index: int, *, document_token=None) -> int:
        """Remove cached renders for one page, optionally in one document."""
        keys = [
            key for key in self._items
            if len(key) >= 2
            and key[1] == page_index
            and (document_token is None or key[0] == document_token)
        ]
        for key in keys:
            _, size = self._items.pop(key)
            self._current_bytes -= size
        return len(keys)

    def clear(self) -> None:
        self._items.clear()
        self._current_bytes = 0


__all__ = [
    "MAX_STROKE_POINTS",
    "MAX_PREVIEW_POINTS",
    "MIN_STROKE_DISTANCE_PX",
    "DEFAULT_PAGE_CACHE_BYTES",
    "append_stroke_sample",
    "preview_stroke_points",
    "PageRenderCache",
]
