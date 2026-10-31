"""Modular Parin v10 Hybrid Pro workspace shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .command_palette import Command, CommandPaletteDialog, CommandRegistry
from .layout import LayoutMetrics, get_layout_metrics
from .theme_engine import ThemeEngine


WORKSPACES = (
    ("reader", "Reader Studio"),
    ("focus", "Focus Studio"),
    ("research", "Research Studio"),
    ("compare", "Compare Studio"),
    ("hub", "Document Hub"),
)


class ParinWorkspaceShell(QWidget):
    """High-density shell with replaceable content and functional command routing.

    The PDF renderer is intentionally injected through set_workspace_widget().
    This keeps the new shell independent of the legacy renderer while migration
    proceeds and makes layout behaviour testable without opening a document.
    """

    openRequested = Signal()
    saveRequested = Signal()
    searchRequested = Signal()
    zoomInRequested = Signal()
    zoomOutRequested = Signal()
    fitWidthRequested = Signal()
    fitPageRequested = Signal()
    workspaceChanged = Signal(str)
    commandTriggered = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        theme_mode: str = "dark",
        density: str = "high",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("parin_workspace")
        self.theme = ThemeEngine(theme_mode)
        self.metrics: LayoutMetrics = get_layout_metrics(density)
        self._active_workspace = "reader"
        self._workspace_widget: QWidget | None = None
        self._navigation_buttons: dict[str, QToolButton] = {}
        self.command_registry = CommandRegistry()
        self._build_ui()
        self._register_commands()
        self.theme.apply(self)

        command_action = QAction("Open command palette", self)
        command_action.setShortcut(QKeySequence("Ctrl+K"))
        command_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        command_action.triggered.connect(self.open_command_palette)
        self.addAction(command_action)
        self._command_action = command_action

    @property
    def active_workspace(self) -> str:
        return self._active_workspace

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self._root_layout = root
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header_frame = self._build_header()
        self.toolbar_frame = self._build_toolbar()
        self.context_toolbar_frame = self._build_context_toolbar()
        self.main_area = self._build_main_area()
        self.status_strip = self._build_status_bar()
        root.addWidget(self.header_frame)
        root.addWidget(self.toolbar_frame)
        root.addWidget(self.context_toolbar_frame)
        root.addWidget(self.main_area, 1)
        root.addWidget(self.status_strip)

    def _build_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName("parin_header")
        header.setFixedHeight(self.metrics.header_height)
        row = QHBoxLayout(header)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)
        self._header_layout = row

        brand = QLabel("P", header)
        brand.setObjectName("brand_mark")
        brand.setFixedSize(30, 30)
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(
            "background:#367CD4;color:white;border-radius:9px;font-weight:800;"
        )
        row.addWidget(brand)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("Parin", header)
        title.setObjectName("brand_title")
        subtitle = QLabel("PDF WORKSPACE", header)
        subtitle.setObjectName("brand_subtitle")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        row.addLayout(brand_text)

        version = QLabel("V10  ·  HYBRID PRO", header)
        version.setObjectName("version_chip")
        row.addWidget(version)
        row.addStretch(1)

        self.command_button = QPushButton("Search commands    Ctrl+K", header)
        self.command_button.setObjectName("command_button")
        self.command_button.clicked.connect(self.open_command_palette)
        row.addWidget(self.command_button)
        return header

    def _tool_button(self, text: str, object_name: str) -> QToolButton:
        button = QToolButton(self)
        button.setText(text)
        button.setObjectName(object_name)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setFixedHeight(self.metrics.control_height)
        return button

    def _build_toolbar(self) -> QFrame:
        toolbar = QFrame(self)
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(self.metrics.toolbar_height)
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(6)

        self.open_button = QPushButton("Open PDF", toolbar)
        self.open_button.setObjectName("primary_action")
        self.open_button.setFixedHeight(self.metrics.control_height)
        self.open_button.clicked.connect(self.openRequested)
        row.addWidget(self.open_button)

        self.save_button = self._tool_button("Save", "toolbar_action")
        self.save_button.clicked.connect(self.saveRequested)
        row.addWidget(self.save_button)

        row.addSpacing(10)
        self.search_button = self._tool_button("Find", "toolbar_action")
        self.search_button.clicked.connect(self.searchRequested)
        row.addWidget(self.search_button)

        row.addStretch(1)

        self.zoom_out_button = self._tool_button("−", "toolbar_action")
        self.zoom_out_button.setToolTip("Zoom out")
        self.zoom_out_button.clicked.connect(self.zoomOutRequested)
        row.addWidget(self.zoom_out_button)

        self.zoom_value = QLabel("100%", toolbar)
        self.zoom_value.setMinimumWidth(48)
        self.zoom_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.zoom_value)

        self.zoom_in_button = self._tool_button("+", "toolbar_action")
        self.zoom_in_button.setToolTip("Zoom in")
        self.zoom_in_button.clicked.connect(self.zoomInRequested)
        row.addWidget(self.zoom_in_button)
        return toolbar

    def _build_context_toolbar(self) -> QFrame:
        context = QFrame(self)
        context.setObjectName("context_toolbar")
        context.setFixedHeight(self.metrics.context_toolbar_height)
        row = QHBoxLayout(context)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(8)

        self.workspace_title = QLabel("Reader Studio", context)
        self.workspace_title.setStyleSheet("font-weight:700;")
        row.addWidget(self.workspace_title)
        row.addStretch(1)

        self.fit_width_button = self._tool_button("Fit Width", "context_action")
        self.fit_width_button.clicked.connect(self.fitWidthRequested)
        row.addWidget(self.fit_width_button)
        self.fit_page_button = self._tool_button("Fit Page", "context_action")
        self.fit_page_button.clicked.connect(self.fitPageRequested)
        row.addWidget(self.fit_page_button)
        return context

    def _build_main_area(self) -> QFrame:
        body = QFrame(self)
        body.setObjectName("main_area")
        row = QHBoxLayout(body)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.navigation_panel = self._build_navigation_panel()
        self.navigation_panel.setFixedWidth(self.metrics.sidebar_width)
        row.addWidget(self.navigation_panel)

        self.workspace_stack = QStackedWidget(body)
        self.workspace_stack.setObjectName("workspace_stack")
        self.workspace_stack.setMinimumWidth(260)
        self.canvas = QFrame(self.workspace_stack)
        self.canvas.setObjectName("workspace_canvas")
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(self.metrics.page_gutter, self.metrics.page_gutter,
                                          self.metrics.page_gutter, self.metrics.page_gutter)
        empty_state = QLabel("Open a PDF to start reading", self.canvas)
        empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_state.setProperty("role", "muted")
        canvas_layout.addWidget(empty_state, 1)
        self.workspace_stack.addWidget(self.canvas)
        row.addWidget(self.workspace_stack, 1)

        self.inspector_panel = self._build_inspector_panel()
        self.inspector_panel.setFixedWidth(self.metrics.inspector_width)
        row.addWidget(self.inspector_panel)
        return body

    def _build_navigation_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("navigation_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 14, 10, 12)
        layout.setSpacing(5)
        self._navigation_layout = layout

        heading = QLabel("WORKSPACES", panel)
        heading.setProperty("role", "muted")
        layout.addWidget(heading)

        for workspace_id, title in WORKSPACES:
            button = QToolButton(panel)
            button.setObjectName("workspace_nav")
            button.setText(title)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setFixedHeight(self.metrics.navigation_item_height)
            button.setChecked(workspace_id == self._active_workspace)
            button.clicked.connect(
                lambda checked=False, key=workspace_id: self.set_active_workspace(key)
            )
            layout.addWidget(button)
            self._navigation_buttons[workspace_id] = button

        layout.addStretch(1)
        return panel

    def _build_inspector_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("inspector_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)
        self._inspector_layout = layout

        heading = QLabel("INSPECTOR", panel)
        heading.setProperty("role", "muted")
        layout.addWidget(heading)

        self.inspector_title = QLabel("Document", panel)
        self.inspector_title.setStyleSheet("font-size:12pt;font-weight:700;")
        layout.addWidget(self.inspector_title)

        self.inspector_hint = QLabel(
            "Document details and contextual tools will appear here.",
            panel,
        )
        self.inspector_hint.setWordWrap(True)
        self.inspector_hint.setProperty("role", "muted")
        layout.addWidget(self.inspector_hint)
        layout.addStretch(1)
        return panel

    def _build_status_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName("status_bar")
        bar.setFixedHeight(self.metrics.statusbar_height)
        row = QHBoxLayout(bar)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(8)
        self.document_status = QLabel("No document open", bar)
        self.document_status.setProperty("role", "muted")
        row.addWidget(self.document_status)
        row.addStretch(1)
        self.page_status = QLabel("Page 0 of 0", bar)
        self.page_status.setProperty("role", "muted")
        row.addWidget(self.page_status)
        return bar

    def _register_commands(self) -> None:
        commands = (
            Command("file.open", "Open PDF", "File", self.openRequested.emit,
                    ("open", "document", "file"), "Ctrl+O"),
            Command("file.save", "Save PDF", "File", self.saveRequested.emit,
                    ("save", "document"), "Ctrl+S"),
            Command("document.search", "Find in document", "Document",
                    self.searchRequested.emit, ("search", "find", "text"), "Ctrl+F"),
            Command("view.zoom_in", "Zoom in", "View", self.zoomInRequested.emit,
                    ("zoom", "larger"), "Ctrl++"),
            Command("view.zoom_out", "Zoom out", "View", self.zoomOutRequested.emit,
                    ("zoom", "smaller"), "Ctrl+-"),
            Command("view.fit_width", "Fit page width", "View", self.fitWidthRequested.emit,
                    ("fit", "width"), ""),
            Command("view.fit_page", "Fit full page", "View", self.fitPageRequested.emit,
                    ("fit", "page"), ""),
        )
        for command in commands:
            self.command_registry.register(command)

        for workspace_id, title in WORKSPACES:
            self.command_registry.register(
                Command(
                    f"workspace.{workspace_id}",
                    f"Switch to {title}",
                    "Workspace",
                    lambda key=workspace_id: self.set_active_workspace(key),
                    (workspace_id, title.casefold(), "workspace"),
                )
            )

    def set_active_workspace(self, workspace_id: str) -> None:
        titles = dict(WORKSPACES)
        if workspace_id not in titles:
            raise ValueError(f"Unknown workspace: {workspace_id}")
        self._active_workspace = workspace_id
        self.workspace_title.setText(titles[workspace_id])
        self._navigation_buttons[workspace_id].setChecked(True)
        self.commandTriggered.emit(f"workspace.{workspace_id}")
        self.workspaceChanged.emit(workspace_id)

    def set_workspace_widget(self, widget: QWidget) -> None:
        """Replace the placeholder canvas with a real PDF or studio widget."""
        if widget is self._workspace_widget:
            return
        if self._workspace_widget is not None:
            old_index = self.workspace_stack.indexOf(self._workspace_widget)
            if old_index >= 0:
                self.workspace_stack.removeWidget(self._workspace_widget)
                self._workspace_widget.setParent(None)
        self._workspace_widget = widget
        self.workspace_stack.addWidget(widget)
        self.workspace_stack.setCurrentWidget(widget)

    def set_toolbar_widget(self, widget: QWidget) -> None:
        """Replace the starter toolbar with the viewer's complete action row."""
        if widget is self.toolbar_frame:
            return
        index = self._root_layout.indexOf(self.toolbar_frame)
        self.toolbar_frame.setParent(None)
        self.toolbar_frame.deleteLater()
        self.toolbar_frame = widget
        widget.setParent(self)
        self._root_layout.insertWidget(max(0, index), widget)

    def set_header_accessories(self, widgets: list[QWidget]) -> None:
        """Place existing search/settings/language controls in the v10 header."""
        for widget in widgets:
            if widget is None:
                continue
            widget.setParent(self.header_frame)
            self._header_layout.insertWidget(max(0, self._header_layout.count() - 1), widget)

    def set_navigation_content(self, widget: QWidget) -> None:
        """Mount the existing PDF outline and page thumbnails below workspace links."""
        if widget.parent() is self.navigation_panel:
            return
        widget.setParent(self.navigation_panel)
        self._navigation_layout.insertWidget(max(0, self._navigation_layout.count() - 1), widget, 1)

    def set_inspector_widget(self, widget: QWidget) -> None:
        """Replace the starter inspector text with a live document inspector."""
        while self._inspector_layout.count() > 1:
            item = self._inspector_layout.takeAt(1)
            old_widget = item.widget()
            if old_widget is not None:
                old_widget.setParent(None)
                old_widget.deleteLater()
        widget.setParent(self.inspector_panel)
        self._inspector_layout.insertWidget(1, widget, 1)

    def set_command_palette_callback(self, callback) -> None:
        """Route header palette requests through the active application's registry."""
        try:
            self.command_button.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.command_button.clicked.connect(callback)
        self._command_action.setShortcut(QKeySequence())

    def set_status_strip_visible(self, visible: bool) -> None:
        """Allow a QMainWindow status bar to remain the single status surface."""
        self.status_strip.setVisible(bool(visible))

    def set_navigation_visible(self, visible: bool) -> None:
        self.navigation_panel.setVisible(bool(visible))

    def set_document_status(self, text: str, page_text: str = "Page 0 of 0") -> None:
        self.document_status.setText(text)
        self.page_status.setText(page_text)

    def set_inspector_content(self, title: str, description: str) -> None:
        self.inspector_title.setText(title)
        self.inspector_hint.setText(description)

    def set_theme_mode(self, mode: str) -> None:
        self.theme.set_mode(mode)
        self.theme.apply(self)

    def open_command_palette(self) -> None:
        dialog = CommandPaletteDialog(self.command_registry, self.theme, self)
        dialog.exec()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = event.size().width()
        self.inspector_panel.setVisible(width >= self.metrics.compact_breakpoint)
        if width < self.metrics.narrow_breakpoint:
            self.navigation_panel.setVisible(False)
        elif not self.navigation_panel.isHidden():
            self.navigation_panel.setVisible(True)
