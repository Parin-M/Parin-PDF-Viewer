"""Bounded raster sizing for PDF printing."""

from __future__ import annotations

import math


DEFAULT_PRINT_DPI = 180
MAX_PRINT_RENDER_DIMENSION = 12_000
MAX_PRINT_RENDER_PIXELS = 16_000_000


def safe_print_scale(
    width_points: float,
    height_points: float,
    *,
    target_dpi: float = DEFAULT_PRINT_DPI,
    max_dimension: int = MAX_PRINT_RENDER_DIMENSION,
    max_pixels: int = MAX_PRINT_RENDER_PIXELS,
) -> float:
    """Return a finite PDF render scale bounded by pixel count and edge size."""
    values = (width_points, height_points, target_dpi)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
        for value in values
    ):
        raise ValueError("Page dimensions and target DPI must be positive finite numbers.")
    if (
        isinstance(max_dimension, bool)
        or not isinstance(max_dimension, int)
        or max_dimension < 1
        or isinstance(max_pixels, bool)
        or not isinstance(max_pixels, int)
        or max_pixels < 1
    ):
        raise ValueError("Print raster limits must be positive integers.")

    width = float(width_points)
    height = float(height_points)
    requested_scale = float(target_dpi) / 72.0
    edge_limit = float(max_dimension) / max(width, height)
    pixel_limit = math.sqrt(float(max_pixels) / (width * height))
    scale = min(requested_scale, edge_limit, pixel_limit)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("The page cannot be rasterized within the print limits.")
    return scale


__all__ = [
    "DEFAULT_PRINT_DPI",
    "MAX_PRINT_RENDER_DIMENSION",
    "MAX_PRINT_RENDER_PIXELS",
    "safe_print_scale",
]
