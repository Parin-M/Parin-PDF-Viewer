"""Responsive layout metrics for Parin v10's high-density workspace."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class LayoutMetrics:
    """Dimensions in logical Qt pixels for a workspace density profile."""

    density: str
    header_height: int
    toolbar_height: int
    context_toolbar_height: int
    sidebar_width: int
    inspector_width: int
    statusbar_height: int
    base_gap: int
    page_gutter: int
    control_height: int
    navigation_item_height: int
    panel_header_height: int
    corner_radius: int
    compact_breakpoint: int
    narrow_breakpoint: int


_PROFILES: Mapping[str, LayoutMetrics] = MappingProxyType(
    {
        "high": LayoutMetrics(
            density="high",
            header_height=54,
            toolbar_height=50,
            context_toolbar_height=40,
            sidebar_width=224,
            inspector_width=288,
            statusbar_height=28,
            base_gap=8,
            page_gutter=16,
            control_height=32,
            navigation_item_height=34,
            panel_header_height=36,
            corner_radius=8,
            compact_breakpoint=1120,
            narrow_breakpoint=860,
        ),
        "comfortable": LayoutMetrics(
            density="comfortable",
            header_height=60,
            toolbar_height=58,
            context_toolbar_height=46,
            sidebar_width=248,
            inspector_width=320,
            statusbar_height=32,
            base_gap=12,
            page_gutter=22,
            control_height=38,
            navigation_item_height=40,
            panel_header_height=42,
            corner_radius=10,
            compact_breakpoint=1240,
            narrow_breakpoint=960,
        ),
        "compact": LayoutMetrics(
            density="compact",
            header_height=48,
            toolbar_height=44,
            context_toolbar_height=36,
            sidebar_width=200,
            inspector_width=256,
            statusbar_height=24,
            base_gap=6,
            page_gutter=12,
            control_height=28,
            navigation_item_height=30,
            panel_header_height=32,
            corner_radius=7,
            compact_breakpoint=1040,
            narrow_breakpoint=800,
        ),
    }
)


def get_layout_metrics(density: str = "high") -> LayoutMetrics:
    """Return the selected immutable density profile."""
    normalized = str(density).strip().lower()
    try:
        return _PROFILES[normalized]
    except KeyError:
        raise ValueError(
            "Unsupported layout density "
            f"{density!r}; expected one of: {', '.join(_PROFILES)}."
        ) from None


def available_layout_densities() -> tuple[str, ...]:
    return ("high", "comfortable", "compact")
