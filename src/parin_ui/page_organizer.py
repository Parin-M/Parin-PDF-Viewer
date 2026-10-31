"""Transactional PDF page organizer dialog."""

from __future__ import annotations

import pymupdf as fitz
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
        ordered = [self.pages.item(row).data(Qt.UserRole) for row in range(self.pages.count())
                   if self.pages.item(row).data(Qt.UserRole) in selected]
        if not ordered:
            QMessageBox.information(self, "Extract pages", "Select at least one page first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Extract pages to PDF", "extracted-pages.pdf", "PDF files (*.pdf)")
        if not path:
            return
        path = ensure_pdf_extension(path)
        if self.viewer.file_path and same_path(path, self.viewer.file_path):
            QMessageBox.warning(self, "Extract pages", "Choose a different file name so the open PDF is not overwritten.")
            return
        output = None
        try:
            output = fitz.open()
            for page_index in ordered:
                output.insert_pdf(self.viewer.doc, from_page=page_index, to_page=page_index)
            output.save(path)
            QMessageBox.information(self, "Extract pages", f"Extracted {len(ordered)} page(s) to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Extract pages failed", str(exc))
        finally:
            if output is not None:
                output.close()

    def apply_changes(self):
        order = [self.pages.item(row).data(Qt.UserRole) for row in range(self.pages.count())]
        if not order:
            QMessageBox.warning(self, "Manage PDF pages", "A PDF must contain at least one page.")
            return
        if len(order) != len(set(order)):
            QMessageBox.warning(self, "Manage PDF pages", "The page list is invalid; no changes were applied.")
            return
        original_order = list(range(self.viewer.doc.page_count))
        included = set(order)
        has_rotation = any(delta and page_index in included for page_index, delta in self.rotations.items())
        if order == original_order and not has_rotation:
            self.accept()
            return
        self.viewer._record_undo()
        old_current = self.viewer.current_page
        try:
            for page_index, delta in self.rotations.items():
                if delta and page_index in included:
                    page = self.viewer.doc.load_page(page_index)
                    page.set_rotation((page.rotation + delta) % 360)
            self.viewer.doc.select(order)
            self.viewer.current_page = order.index(old_current) if old_current in order else min(old_current, len(order) - 1)
            self.viewer._after_document_structure_change()
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Could not update pages", str(exc))
            self.viewer.undo_edit()
