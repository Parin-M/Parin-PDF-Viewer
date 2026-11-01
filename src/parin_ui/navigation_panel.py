"""Navigation dock, PDF outline and lazy page thumbnails."""

from __future__ import annotations

from collections import OrderedDict

import pymupdf as fitz
from PySide6.QtCore import QPoint, QTimer, Qt, QSize
from PySide6.QtGui import QImage, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
)


class NavigationPanelController:
    """Own navigation widgets and visible-page thumbnail rendering.

    The main viewer remains the document/navigation authority. This controller
    owns the dock widgets, outline projection, thumbnail cache and refresh timer,
    while preserving the legacy viewer attribute aliases used by integrations.
    """

    def __init__(self, viewer, translations):
        self.viewer = viewer
        self.translations = translations
        self.thumbnail_cache = OrderedDict()
        self.dock = QDockWidget(self.nav_text("dock"), viewer)
        self.dock.setObjectName("navigation_dock")
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable
        )
        self.dock.setMinimumWidth(230)

        self.tabs = QTabWidget(self.dock)
        self.outline_tree = QTreeWidget(self.tabs)
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemActivated.connect(viewer._navigate_outline_item)

        self.page_list = QListWidget(self.tabs)
        self.page_list.setIconSize(QSize(76, 100))
        self.page_list.setUniformItemSizes(True)
        self.page_list.setSpacing(6)
        self.page_list.setAlternatingRowColors(True)
        self.page_list.currentRowChanged.connect(viewer._navigate_page_list)
        self.page_list.verticalScrollBar().valueChanged.connect(
            self.schedule_thumbnail_refresh
        )

        self.tabs.addTab(self.outline_tree, self.nav_text("outline"))
        self.tabs.addTab(self.page_list, self.nav_text("pages"))
        self.dock.setWidget(self.tabs)
        viewer.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.dock.hide()

        self.refresh_timer = QTimer(viewer)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(80)
        self.refresh_timer.timeout.connect(self.load_visible_thumbnails)

        # Compatibility aliases: other viewer services and older tests still
        # access these widgets/cache through the main-window instance.
        viewer.navigation_dock = self.dock
        viewer.navigation_tabs = self.tabs
        viewer.outline_tree = self.outline_tree
        viewer.page_list = self.page_list
        viewer._thumbnail_cache = self.thumbnail_cache
        viewer._thumbnail_refresh_timer = self.refresh_timer
        viewer._navigation_needs_refresh = True

    def _is_navigation_visible(self) -> bool:
        viewer = self.viewer
        if hasattr(viewer, "v10_shell"):
            return viewer.v10_shell.navigation_panel.isVisible()
        return self.dock.isVisible()

    def nav_text(self, key: str, **kwargs) -> str:
        language = self.translations.get(
            self.viewer.current_lang, self.translations["en"]
        )
        template = language.get(
            key, self.translations["en"].get(key, key)
        )
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    def retranslate(self) -> None:
        viewer = self.viewer
        self.dock.setWindowTitle(self.nav_text("dock"))
        if hasattr(viewer, "navigation_action"):
            viewer.navigation_action.setText(self.nav_text("nav_action"))
        if hasattr(viewer, "recent_menu"):
            viewer.recent_menu.setTitle(self.nav_text("recent"))
        self.tabs.setTabText(0, self.nav_text("outline"))
        self.tabs.setTabText(1, self.nav_text("pages"))
        if self._is_navigation_visible():
            self.refresh()

    def refresh(self) -> None:
        viewer = self.viewer
        if self.page_list is None:
            return
        if not self._is_navigation_visible():
            viewer._navigation_needs_refresh = True
            return

        viewer._navigation_needs_refresh = False
        self.thumbnail_cache.clear()
        self.page_list.blockSignals(True)
        try:
            self.page_list.clear()
            document = viewer.doc
            if document is not None and not getattr(document, "is_closed", False):
                for index in range(document.page_count):
                    item = QListWidgetItem(
                        self.nav_text("page", n=index + 1)
                    )
                    item.setData(Qt.ItemDataRole.UserRole, index)
                    self.page_list.addItem(item)
                if self.page_list.count():
                    row = min(max(viewer.current_page, 0), self.page_list.count() - 1)
                    self.page_list.setCurrentRow(row)
        finally:
            self.page_list.blockSignals(False)

        self.outline_tree.clear()
        document = viewer.doc
        if document is not None and not getattr(document, "is_closed", False):
            try:
                stack = []
                for entry in document.get_toc(simple=True):
                    if len(entry) < 3:
                        continue
                    level, title, page_number = entry[:3]
                    if not isinstance(page_number, int) or page_number < 1:
                        continue
                    item = QTreeWidgetItem(
                        [str(title or f"Page {page_number}")]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, page_number - 1)
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    if stack:
                        stack[-1][1].addChild(item)
                    else:
                        self.outline_tree.addTopLevelItem(item)
                    stack.append((level, item))
                if self.outline_tree.topLevelItemCount() == 0:
                    empty = QTreeWidgetItem([self.nav_text("no_outline")])
                    empty.setDisabled(True)
                    self.outline_tree.addTopLevelItem(empty)
                self.outline_tree.expandToDepth(1)
            except Exception as exc:
                viewer.statusBar().showMessage(
                    f"Could not read PDF outline: {exc}", 5000
                )
        self.schedule_thumbnail_refresh()

    def schedule_thumbnail_refresh(self, *_args) -> None:
        if self.refresh_timer is not None:
            self.refresh_timer.start()

    def sync_current_page(self) -> None:
        viewer = self.viewer
        if (
            not viewer._navigation_needs_refresh
            and 0 <= viewer.current_page < self.page_list.count()
            and self.page_list.currentRow() != viewer.current_page
        ):
            self.page_list.blockSignals(True)
            try:
                self.page_list.setCurrentRow(viewer.current_page)
            finally:
                self.page_list.blockSignals(False)
            self.schedule_thumbnail_refresh()

    def load_visible_thumbnails(self) -> None:
        viewer = self.viewer
        document = viewer.doc
        if (
            document is None
            or getattr(document, "is_closed", False)
            or self.page_list.count() == 0
        ):
            return
        if not self._is_navigation_visible():
            return

        first = self.page_list.indexAt(QPoint(5, 5)).row()
        if first < 0:
            first = max(0, self.page_list.currentRow())
        visible_count = max(
            8, min(16, self.page_list.viewport().height() // 90 + 4)
        )
        for index in range(
            first, min(self.page_list.count(), first + visible_count)
        ):
            item = self.page_list.item(index)
            if index in self.thumbnail_cache:
                item.setIcon(self.thumbnail_cache[index])
                self.thumbnail_cache.move_to_end(index)
                continue
            try:
                page = document.load_page(index)
                width = max(1, page.rect.width)
                height = max(1, page.rect.height)
                scale = min(88 / width, 112 / height, 0.28)
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(scale, scale), alpha=False
                )
                image = QImage(
                    pix.samples,
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_RGB888,
                ).copy()
                icon = QIcon(QPixmap.fromImage(image))
                item.setIcon(icon)
                self.thumbnail_cache[index] = icon
                while len(self.thumbnail_cache) > 40:
                    expired_index, _ = self.thumbnail_cache.popitem(last=False)
                    expired_item = self.page_list.item(expired_index)
                    if expired_item is not None:
                        expired_item.setIcon(QIcon())
            except Exception:
                continue


__all__ = ["NavigationPanelController"]
