"""Semantic colour tokens for the Parin Aurora design system."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping

ThemeMode = Literal["dark", "light"]


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Semantic colours consumed by widgets and stylesheets."""

    mode: ThemeMode
    app_background: str
    panel_background: str
    surface: str
    elevated_surface: str
    border: str
    text: str
    muted_text: str
    subtle_text: str
    accent: str
    accent_hover: str
    accent_soft: str
    violet: str
    emerald: str
    danger: str
    header_background: str
    header_text: str
    canvas_background: str
    selection_background: str
    selection_text: str
    tooltip_background: str
    tooltip_text: str


_DARK = ThemeTokens(
    mode="dark",
    app_background="#0B1220",
    panel_background="#111B2C",
    surface="#162238",
    elevated_surface="#1D2B43",
    border="#2B3B56",
    text="#F2F6FC",
    muted_text="#B3C0D2",
    subtle_text="#91A1B8",
    accent="#70A9FF",
    accent_hover="#91BCFF",
    accent_soft="#1C3A63",
    violet="#A697FF",
    emerald="#48C9A5",
    danger="#F07C83",
    header_background="#0B1729",
    header_text="#F7FAFF",
    canvas_background="#202B3E",
    selection_background="#28558A",
    selection_text="#FFFFFF",
    tooltip_background="#17243A",
    tooltip_text="#F7FAFF",
)

_LIGHT = ThemeTokens(
    mode="light",
    app_background="#F2F5FA",
    panel_background="#FFFFFF",
    surface="#F8FAFD",
    elevated_surface="#FFFFFF",
    border="#DCE4EF",
    text="#17263C",
    muted_text="#52647D",
    subtle_text="#697B93",
    accent="#286FC8",
    accent_hover="#1E5DAE",
    accent_soft="#E6F0FF",
    violet="#7258C6",
    emerald="#16856B",
    danger="#C74752",
    header_background="#10213A",
    header_text="#FFFFFF",
    canvas_background="#E6EBF2",
    selection_background="#D5E7FF",
    selection_text="#173B68",
    tooltip_background="#15253D",
    tooltip_text="#FFFFFF",
)

_THEMES: Mapping[str, ThemeTokens] = MappingProxyType(
    {"dark": _DARK, "light": _LIGHT}
)


def get_theme_tokens(mode: str = "dark") -> ThemeTokens:
    """Return immutable semantic tokens for a supported appearance mode."""
    normalized = str(mode).strip().lower()
    try:
        return _THEMES[normalized]
    except KeyError:
        raise ValueError(
            f"Unsupported theme mode {mode!r}; expected 'dark' or 'light'."
        ) from None


def available_theme_modes() -> tuple[str, ...]:
    """Return the supported appearance modes in stable UI order."""
    return ("dark", "light")
