"""Qt stylesheet generation for the Parin Aurora semantic tokens."""

from __future__ import annotations

from .theme_tokens import ThemeMode, ThemeTokens, get_theme_tokens


def build_stylesheet(tokens: ThemeTokens) -> str:
    """Build a compact, semantic stylesheet for the modular v10 workspace."""
    c = tokens
    return f"""
QMainWindow, QWidget#parin_workspace {{
    background: {c.app_background};
    color: {c.text};
    font-family: "Inter", "Noto Sans", sans-serif;
    font-size: 10pt;
}}
QFrame#parin_header {{
    background: {c.header_background};
    border: none;
    border-bottom: 1px solid {c.border};
}}
QLabel#brand_title {{
    color: {c.header_text};
    font-size: 15pt;
    font-weight: 700;
}}
QLabel#brand_subtitle {{
    color: #B5C6DD;
    font-size: 8pt;
}}
QLabel#version_chip {{
    color: {c.header_text};
    background: rgba(112, 169, 255, 0.18);
    border: 1px solid rgba(160, 195, 255, 0.28);
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 8pt;
    font-weight: 700;
}}
QFrame#toolbar, QFrame#context_toolbar {{
    background: {c.panel_background};
    border: none;
    border-bottom: 1px solid {c.border};
}}
QFrame#navigation_panel, QFrame#inspector_panel {{
    background: {c.panel_background};
    border: none;
}}
QFrame#navigation_panel {{
    border-right: 1px solid {c.border};
}}
QFrame#inspector_panel {{
    border-left: 1px solid {c.border};
}}
QFrame#workspace_canvas {{
    background: {c.canvas_background};
    border: none;
}}
QFrame#status_bar {{
    background: {c.panel_background};
    border-top: 1px solid {c.border};
}}
QLabel {{
    color: {c.text};
    background: transparent;
}}
QLabel[role="muted"] {{
    color: {c.muted_text};
}}
QPushButton, QToolButton {{
    color: {c.text};
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    min-height: 26px;
    padding: 3px 9px;
}}
QPushButton:hover, QToolButton:hover {{
    background: {c.elevated_surface};
    border-color: {c.border};
}}
QPushButton:pressed, QToolButton:pressed {{
    background: {c.accent_soft};
}}
QPushButton#primary_action {{
    color: #FFFFFF;
    background: {c.accent};
    border: 1px solid {c.accent};
    font-weight: 700;
}}
QPushButton#primary_action:hover {{
    background: {c.accent_hover};
    border-color: {c.accent_hover};
}}
QToolButton#workspace_nav {{
    text-align: left;
    min-height: 30px;
    padding: 5px 10px;
}}
QToolButton#workspace_nav:checked {{
    color: {c.accent};
    background: {c.accent_soft};
    border: 1px solid {c.border};
    font-weight: 700;
}}
QToolButton#command_button {{
    color: {c.header_text};
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    padding: 5px 12px;
}}
QLineEdit, QComboBox, QSpinBox {{
    color: {c.text};
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: 7px;
    min-height: 28px;
    padding: 3px 8px;
    selection-background-color: {c.selection_background};
    selection-color: {c.selection_text};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {c.accent};
}}
QListWidget {{
    color: {c.text};
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: 8px;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    min-height: 32px;
    padding: 5px 8px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    color: {c.selection_text};
    background: {c.selection_background};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c.border};
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QToolTip {{
    color: {c.tooltip_text};
    background: {c.tooltip_background};
    border: 1px solid {c.border};
    padding: 5px 7px;
}}
"""


class ThemeEngine:
    """Small stateful adapter used by the v10 widgets."""

    def __init__(self, mode: ThemeMode = "dark") -> None:
        self._tokens = get_theme_tokens(mode)

    @property
    def mode(self) -> ThemeMode:
        return self._tokens.mode

    @property
    def tokens(self) -> ThemeTokens:
        return self._tokens

    @property
    def stylesheet(self) -> str:
        return build_stylesheet(self._tokens)

    def set_mode(self, mode: ThemeMode) -> ThemeTokens:
        self._tokens = get_theme_tokens(mode)
        return self._tokens

    def apply(self, widget: object) -> None:
        """Apply this theme to a Qt widget without importing Qt at module load."""
        setter = getattr(widget, "setStyleSheet", None)
        if not callable(setter):
            raise TypeError("ThemeEngine.apply expects an object with setStyleSheet().")
        setter(self.stylesheet)
