"""Transactional PDF page organizer dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from parin_pdf_helpers import ensure_pdf_extension, same_path
from parin_ui.page_operations import (
    apply_page_edit_plan,
    create_page_edit_plan,
    extract_pdf_pages,
)


class PageOrganizerDialog(QDialog):
    """Transactional page organizer with drag/drop reorder, rotation, removal, and extraction."""
    def __init__(self, viewer):
        super().__init__(viewer)
        self.viewer = viewer
        self.rotations = {}
        self.setWindowTitle("Manage PDF pages")
        self.resize(520, 620)
        self.setModal(True)
        root = QVBoxLayout(self)
        intro = QLabel("Drag pages to reorder them. Rotate, remove, or extract selected pages; changes apply only when you choose Apply.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        self.pages = QListWidget()
        self.pages.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pages.setDragEnabled(True)
        self.pages.setAcceptDrops(True)
        self.pages.setDropIndicatorShown(True)
        self.pages.setDragDropMode(QAbstractItemView.InternalMove)
        self.pages.setDefaultDropAction(Qt.MoveAction)
        for index in range(viewer.doc.page_count):
            item = QListWidgetItem(f"Page {index + 1}")
            item.setData(Qt.UserRole, index)
            self.pages.addItem(item)
        self.pages.setCurrentRow(viewer.current_page)
        root.addWidget(self.pages, 1)
        controls = QHBoxLayout()
        self.rotate_button = QPushButton("Rotate selected +90°")
        self.remove_button = QPushButton("Remove selected")
        self.extract_button = QPushButton("Extract selected…")
        controls.addWidget(self.rotate_button)
        controls.addWidget(self.remove_button)
        root.addLayout(controls)
        root.addWidget(self.extract_button)
        self.rotate_button.clicked.connect(self.rotate_selected)
        self.remove_button.clicked.connect(self.remove_selected)
        self.extract_button.clicked.connect(self.extract_selected)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        self.buttons.button(QDialogButtonBox.Apply).setText("Apply changes")
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes)
        root.addWidget(self.buttons)

    def rotate_selected(self):
        for item in self.pages.selectedItems():
            page_index = item.data(Qt.UserRole)
            self.rotations[page_index] = (self.rotations.get(page_index, 0) + 90) % 360
            delta = self.rotations[page_index]
            item.setText(f"Page {page_index + 1}" + (f" · rotate +{delta}°" if delta else ""))

    def remove_selected(self):
        rows = sorted((self.pages.row(item) for item in self.pages.selectedItems()), reverse=True)
        for row in rows:
            self.pages.takeItem(row)

    def extract_selected(self):
        selected = {item.data(Qt.UserRole) for item in self.pages.selectedItems()}
        ordered = [
            self.pages.item(row).data(Qt.UserRole)
            for row in range(self.pages.count())
            if self.pages.item(row).data(Qt.UserRole) in selected
        ]
        if not ordered:
            QMessageBox.information(self, "Extract pages", "Select at least one page first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Extract pages to PDF", "extracted-pages.pdf", "PDF files (*.pdf)"
        )
        if not path:
            return
        path = ensure_pdf_extension(path)
        if self.viewer.file_path and same_path(path, self.viewer.file_path):
            QMessageBox.warning(
                self,
                "Extract pages",
                "Choose a different file name so the open PDF is not overwritten.",
            )
            return
        try:
            result = extract_pdf_pages(self.viewer.doc, ordered, path)
            QMessageBox.information(
                self,
                "Extract pages",
                f"Extracted {result.page_count} page(s) to:\n{result.file_path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Extract pages failed", str(exc))

    def apply_changes(self):
        order = [
            self.pages.item(row).data(Qt.UserRole)
            for row in range(self.pages.count())
        ]
        try:
            plan = create_page_edit_plan(
                self.viewer.doc.page_count,
                order,
                self.rotations,
            )
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Manage PDF pages", str(exc))
            return
        if not plan.has_changes:
            self.accept()
            return

        self.viewer._record_undo()
        old_current = self.viewer.current_page
        try:
            apply_page_edit_plan(self.viewer.doc, plan)
            self.viewer.current_page = (
                plan.order.index(old_current)
                if old_current in plan.order
                else min(old_current, len(plan.order) - 1)
            )
            self.viewer._after_document_structure_change()
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Could not update pages", str(exc))
            self.viewer.undo_edit()
