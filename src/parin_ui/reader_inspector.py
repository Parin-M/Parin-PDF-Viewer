"""Live metadata and quick actions for the Parin v10 Reader Studio."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ReaderInspector(QWidget):
    """Read-only document and page context, with action signals for the host."""

    findRequested = Signal()
    rotateLeftRequested = Signal()
    rotateRightRequested = Signal()
    fitWidthRequested = Signal()
    fitPageRequested = Signal()

    _LABELS = {
        "en": {
            "document": "DOCUMENT",
            "file": "File",
            "pages": "Pages",
            "page": "Current page",
            "size": "Page size",
            "title": "Title",
            "author": "Author",
            "subject": "Subject",
            "state": "State",
            "ready": "Ready",
            "unsaved": "Unsaved changes",
            "saved": "Saved",
            "no_document": "No document open",
            "quick": "QUICK ACTIONS",
            "find": "Find in PDF",
            "rotate_left": "Rotate left",
            "rotate_right": "Rotate right",
            "fit_width": "Fit width",
            "fit_page": "Fit page",
        },
        "fa": {
            "document": "مشخصات سند",
            "file": "فایل",
            "pages": "تعداد صفحات",
            "page": "صفحهٔ جاری",
            "size": "ابعاد صفحه",
            "title": "عنوان",
            "author": "نویسنده",
            "subject": "موضوع",
            "state": "وضعیت",
            "ready": "آماده",
            "unsaved": "تغییرات ذخیره‌نشده",
            "saved": "ذخیره‌شده",
            "no_document": "سندی باز نیست",
            "quick": "عملیات سریع",
            "find": "جست‌وجو در PDF",
            "rotate_left": "چرخش به چپ",
            "rotate_right": "چرخش به راست",
            "fit_width": "تناسب با عرض",
            "fit_page": "تناسب با صفحه",
        },
        "de": {
            "document": "DOKUMENT",
            "file": "Datei",
            "pages": "Seiten",
            "page": "Aktuelle Seite",
            "size": "Seitengröße",
            "title": "Titel",
            "author": "Autor",
            "subject": "Betreff",
            "state": "Status",
            "ready": "Bereit",
            "unsaved": "Nicht gespeicherte Änderungen",
            "saved": "Gespeichert",
            "no_document": "Kein Dokument geöffnet",
            "quick": "SCHNELLAKTIONEN",
            "find": "Im PDF suchen",
            "rotate_left": "Nach links drehen",
            "rotate_right": "Nach rechts drehen",
            "fit_width": "An Seitenbreite anpassen",
            "fit_page": "An Seite anpassen",
        },
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reader_inspector")
        self._language = "en"
        self._last_snapshot: tuple[object, str, int, float, bool] | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        self.document_heading = QLabel()
        self.document_heading.setProperty("role", "muted")
        root.addWidget(self.document_heading)

        self.file_name = QLabel()
        self.file_name.setWordWrap(True)
        self.file_name.setStyleSheet("font-weight:700;font-size:11pt;")
        root.addWidget(self.file_name)

        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setProperty("role", "muted")
        root.addWidget(self.path_label)

        rule = QFrame(self)
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setObjectName("inspector_separator")
        root.addWidget(rule)

        self.details_grid = QGridLayout()
        self.details_grid.setHorizontalSpacing(10)
        self.details_grid.setVerticalSpacing(9)
        root.addLayout(self.details_grid)
        self.detail_labels: dict[str, QLabel] = {}
        for row, key in enumerate(("pages", "page", "size", "title", "author", "subject", "state")):
            label = QLabel()
            label.setProperty("role", "muted")
            value = QLabel("—")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.details_grid.addWidget(label, row, 0)
            self.details_grid.addWidget(value, row, 1)
            self.detail_labels[key] = label
            setattr(self, f"{key}_value", value)

        action_rule = QFrame(self)
        action_rule.setFrameShape(QFrame.Shape.HLine)
        action_rule.setObjectName("inspector_separator")
        root.addWidget(action_rule)

        self.actions_heading = QLabel()
        self.actions_heading.setProperty("role", "muted")
        root.addWidget(self.actions_heading)

        self.find_button = QPushButton()
        self.rotate_left_button = QPushButton()
        self.rotate_right_button = QPushButton()
        self.fit_width_button = QPushButton()
        self.fit_page_button = QPushButton()
        for button in (
            self.find_button,
            self.rotate_left_button,
            self.rotate_right_button,
            self.fit_width_button,
            self.fit_page_button,
        ):
            button.setMinimumHeight(30)
            root.addWidget(button)

        self.find_button.clicked.connect(self.findRequested)
        self.rotate_left_button.clicked.connect(self.rotateLeftRequested)
        self.rotate_right_button.clicked.connect(self.rotateRightRequested)
        self.fit_width_button.clicked.connect(self.fitWidthRequested)
        self.fit_page_button.clicked.connect(self.fitPageRequested)
        root.addStretch(1)
        self.set_language("en")
        self.clear_document()

    def set_language(self, language: str) -> None:
        normalized = str(language).lower()
        self._language = normalized if normalized in self._LABELS else "en"
        labels = self._LABELS[self._language]
        self.document_heading.setText(labels["document"])
        for key, label in self.detail_labels.items():
            label.setText(labels[key])
        self.actions_heading.setText(labels["quick"])
        self.find_button.setText(labels["find"])
        self.rotate_left_button.setText(labels["rotate_left"])
        self.rotate_right_button.setText(labels["rotate_right"])
        self.fit_width_button.setText(labels["fit_width"])
        self.fit_page_button.setText(labels["fit_page"])
        if self._last_snapshot is not None:
            doc, path, page, zoom, dirty = self._last_snapshot
            self.update_document(doc, path, page, zoom, dirty)
        else:
            self.clear_document()

    def clear_document(self) -> None:
        labels = self._LABELS[self._language]
        self.file_name.setText(labels["no_document"])
        self.path_label.setText("")
        for key in self.detail_labels:
            getattr(self, f"{key}_value").setText("—")
        for button in (
            self.find_button,
            self.rotate_left_button,
            self.rotate_right_button,
            self.fit_width_button,
            self.fit_page_button,
        ):
            button.setEnabled(False)

    def update_document(
        self,
        document: object | None,
        file_path: str = "",
        current_page: int = 0,
        zoom: float = 1.0,
        dirty: bool = False,
    ) -> None:
        if document is None:
            self._last_snapshot = None
            self.clear_document()
            return

        self._last_snapshot = (document, file_path, current_page, zoom, dirty)
        labels = self._LABELS[self._language]
        metadata = getattr(document, "metadata", None) or {}
        page_count = int(getattr(document, "page_count", 0) or 0)
        page_number = min(max(int(current_page), 0), max(page_count - 1, 0))
        page_size = "—"
        try:
            page = document.load_page(page_number)
            rect = page.rect
            page_size = f"{round(float(rect.width))} × {round(float(rect.height))} pt"
        except Exception:
            pass

        self.file_name.setText(Path(file_path).name if file_path else labels["no_document"])
        self.path_label.setText(file_path)
        self.pages_value.setText(str(page_count))
        self.page_value.setText(f"{page_number + 1} / {page_count}" if page_count else "0 / 0")
        self.size_value.setText(page_size)
        self.title_value.setText(str(metadata.get("title") or "—"))
        self.author_value.setText(str(metadata.get("author") or "—"))
        self.subject_value.setText(str(metadata.get("subject") or "—"))
        state = labels["unsaved"] if dirty else labels["saved"]
        self.state_value.setText(state if file_path else labels["ready"])

        for button in (
            self.find_button,
            self.rotate_left_button,
            self.rotate_right_button,
            self.fit_width_button,
            self.fit_page_button,
        ):
            button.setEnabled(True)

    def set_zoom(self, zoom: float) -> None:
        # The value is retained in the snapshot so a later language change
        # cannot discard the current Reader context.
        if self._last_snapshot is None:
            return
        doc, path, page, _old_zoom, dirty = self._last_snapshot
        self._last_snapshot = (doc, path, page, float(zoom), dirty)
