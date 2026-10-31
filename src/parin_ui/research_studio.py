"""Research Studio: local notes, page references and PDF highlights."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .research_store import ResearchStore, ResearchStoreError, extract_pdf_highlights


_LABELS = {
    "en": {
        "title": "Research Studio",
        "privacy": "Notes are stored locally on this device and linked to this PDF.",
        "no_document": "Open a PDF in Reader Studio to start research.",
        "notes": "Notes",
        "highlights": "Highlights",
        "new": "New note",
        "delete": "Delete",
        "page": "Page",
        "save": "Save note",
        "editor": "Write a note or source reference…",
        "select_note": "Select a note or create a new one.",
        "saved": "Note saved",
        "deleted": "Note deleted",
        "empty": "No notes for this document yet.",
        "no_highlights": "No PDF highlights found.",
        "highlight": "Highlight",
        "ink": "Ink highlight",
        "open_reader": "Open in Reader",
        "storage_error": "Research data could not be saved",
    },
    "fa": {
        "title": "محیط پژوهش",
        "privacy": "یادداشت‌ها فقط روی همین دستگاه و در پیوند با این PDF ذخیره می‌شوند.",
        "no_document": "برای شروع پژوهش، ابتدا یک PDF در محیط مطالعه باز کنید.",
        "notes": "یادداشت‌ها",
        "highlights": "هایلایت‌ها",
        "new": "یادداشت جدید",
        "delete": "حذف",
        "page": "صفحه",
        "save": "ذخیرهٔ یادداشت",
        "editor": "یادداشت یا ارجاع منبع را بنویسید…",
        "select_note": "یک یادداشت انتخاب کنید یا یادداشت تازه بسازید.",
        "saved": "یادداشت ذخیره شد",
        "deleted": "یادداشت حذف شد",
        "empty": "هنوز یادداشتی برای این سند وجود ندارد.",
        "no_highlights": "هایلایتی در PDF پیدا نشد.",
        "highlight": "هایلایت",
        "ink": "هایلایت قلمی",
        "open_reader": "نمایش در مطالعه",
        "storage_error": "ذخیره‌سازی داده‌های پژوهش ناموفق بود",
    },
    "de": {
        "title": "Research Studio",
        "privacy": "Notizen werden lokal auf diesem Gerät und zugehörig zu diesem PDF gespeichert.",
        "no_document": "Öffnen Sie zuerst ein PDF im Reader Studio.",
        "notes": "Notizen",
        "highlights": "Markierungen",
        "new": "Neue Notiz",
        "delete": "Löschen",
        "page": "Seite",
        "save": "Notiz speichern",
        "editor": "Notiz oder Quellenverweis eingeben…",
        "select_note": "Notiz auswählen oder eine neue erstellen.",
        "saved": "Notiz gespeichert",
        "deleted": "Notiz gelöscht",
        "empty": "Noch keine Notizen zu diesem Dokument.",
        "no_highlights": "Keine PDF-Markierungen gefunden.",
        "highlight": "Hervorhebung",
        "ink": "Stiftmarkierung",
        "open_reader": "Im Reader öffnen",
        "storage_error": "Forschungsdaten konnten nicht gespeichert werden",
    },
}


class ResearchStudio(QWidget):
    """A document-scoped research workspace with editable local notes."""

    navigateRequested = Signal(int)

    def __init__(
        self,
        store: ResearchStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.document_path = ""
        self.document = None
        self.current_page = 1
        self._document_identity: tuple[str, int] | None = None
        self._notes: list[dict] = []
        self._highlights: list[dict] = []
        self._active_note_id: str | None = None
        self._language = "en"
        self.setObjectName("research_studio")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(10)

        self.heading = QLabel()
        self.heading.setStyleSheet("font-size:18pt;font-weight:750;")
        root.addWidget(self.heading)
        self.document_label = QLabel()
        self.document_label.setProperty("role", "muted")
        root.addWidget(self.document_label)
        self.privacy_label = QLabel()
        self.privacy_label.setProperty("role", "muted")
        root.addWidget(self.privacy_label)

        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)

        left = QVBoxLayout()
        self.tabs = QTabWidget(self)
        self.notes_list = QListWidget(self)
        self.highlights_list = QListWidget(self)
        self.tabs.addTab(self.notes_list, "Notes")
        self.tabs.addTab(self.highlights_list, "Highlights")
        left.addWidget(self.tabs, 1)

        list_actions = QHBoxLayout()
        self.new_button = QPushButton()
        self.delete_button = QPushButton()
        list_actions.addWidget(self.new_button)
        list_actions.addWidget(self.delete_button)
        left.addLayout(list_actions)
        body.addLayout(left, 2)

        right = QVBoxLayout()
        page_row = QHBoxLayout()
        self.page_label = QLabel()
        self.page_spin = QSpinBox(self)
        self.page_spin.setRange(1, 1)
        self.page_spin.setFixedWidth(90)
        page_row.addWidget(self.page_label)
        page_row.addWidget(self.page_spin)
        page_row.addStretch(1)
        right.addLayout(page_row)

        self.note_editor = QTextEdit(self)
        self.note_editor.setAcceptRichText(False)
        self.note_editor.setPlaceholderText("Write a note…")
        right.addWidget(self.note_editor, 1)

        editor_actions = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setProperty("role", "muted")
        editor_actions.addWidget(self.status_label, 1)
        self.save_button = QPushButton()
        self.open_reader_button = QPushButton()
        editor_actions.addWidget(self.open_reader_button)
        editor_actions.addWidget(self.save_button)
        right.addLayout(editor_actions)
        body.addLayout(right, 3)

        self.notes_list.itemActivated.connect(self._activate_note)
        self.highlights_list.itemActivated.connect(self._activate_highlight)
        self.notes_list.currentItemChanged.connect(self._load_selected_note)
        self.new_button.clicked.connect(self.new_note)
        self.delete_button.clicked.connect(self.delete_note)
        self.save_button.clicked.connect(self.save_note)
        self.open_reader_button.clicked.connect(self.open_current_page)
        self.set_language("en")
        self.set_document("", None, 0)

    @property
    def notes(self) -> tuple[dict, ...]:
        return tuple(dict(note) for note in self._notes)

    @property
    def highlights(self) -> tuple[dict, ...]:
        return tuple(dict(item) for item in self._highlights)

    def set_language(self, language: str) -> None:
        normalized = str(language).lower()
        self._language = normalized if normalized in _LABELS else "en"
        labels = _LABELS[self._language]
        self.heading.setText(labels["title"])
        self.privacy_label.setText(labels["privacy"])
        self.tabs.setTabText(0, labels["notes"])
        self.tabs.setTabText(1, labels["highlights"])
        self.new_button.setText(labels["new"])
        self.delete_button.setText(labels["delete"])
        self.page_label.setText(labels["page"])
        self.save_button.setText(labels["save"])
        self.note_editor.setPlaceholderText(labels["editor"])
        self.open_reader_button.setText(labels["open_reader"])
        if self.document is None:
            self.document_label.setText(labels["no_document"])
        self._refresh_notes()
        self._refresh_highlights()

    def set_document(
        self,
        document_path: str,
        document: object | None,
        current_page: int = 0,
    ) -> None:
        path = str(document_path or "")
        identity = (path, id(document)) if document is not None else None
        if identity is not None and identity == self._document_identity:
            self.set_current_page(current_page)
            return

        self.document_path = path
        self.document = document
        self._document_identity = identity
        self.current_page = max(1, int(current_page) + 1)
        labels = _LABELS[self._language]
        if document is None or not path:
            self._notes = []
            self._highlights = []
            self._active_note_id = None
            self.document_label.setText(labels["no_document"])
            self._refresh_notes()
            self._refresh_highlights()
            self._set_editor_enabled(False)
            return

        self.document_label.setText(Path(path).name)
        try:
            self._notes = self.store.list_notes(path)
        except ResearchStoreError as exc:
            self._notes = []
            self.status_label.setText(str(exc))
        self._active_note_id = None
        self._refresh_notes()
        self.refresh_highlights()
        try:
            page_count = max(1, int(getattr(document, "page_count", 1)))
        except (TypeError, ValueError):
            page_count = 1
        self.page_spin.setRange(1, page_count)
        self.set_current_page(current_page)
        self._set_editor_enabled(True)
        self.new_note()

    def set_current_page(self, current_page: int) -> None:
        try:
            page_count = max(1, int(getattr(self.document, "page_count", 1)))
        except (TypeError, ValueError):
            page_count = 1
        page = min(max(int(current_page) + 1, 1), page_count)
        self.current_page = page
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, page_count)
        self.page_spin.setValue(page)
        self.page_spin.blockSignals(False)

    def refresh_highlights(self) -> None:
        self._highlights = extract_pdf_highlights(self.document)
        self._refresh_highlights()

    def _set_editor_enabled(self, enabled: bool) -> None:
        self.page_spin.setEnabled(enabled)
        self.note_editor.setEnabled(enabled)
        self.new_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled and self._active_note_id is not None)
        self.save_button.setEnabled(enabled)
        self.open_reader_button.setEnabled(enabled)

    def _refresh_notes(self) -> None:
        labels = _LABELS[self._language]
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        for note in self._notes:
            first_line = note["text"].splitlines()[0][:76] if note["text"] else ""
            item = QListWidgetItem(f"P{note['page']}  ·  {first_line}")
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, note["page"])
            self.notes_list.addItem(item)
        if not self._notes:
            item = QListWidgetItem(labels["empty"])
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.notes_list.addItem(item)
        self.notes_list.blockSignals(False)
        self.delete_button.setEnabled(self.document is not None and self._active_note_id is not None)

    def _refresh_highlights(self) -> None:
        labels = _LABELS[self._language]
        self.highlights_list.clear()
        for highlight in self._highlights:
            kind = labels["ink"] if str(highlight["type"]).casefold() == "ink" else labels["highlight"]
            excerpt = highlight["excerpt"] or highlight["content"] or kind
            item = QListWidgetItem(f"P{highlight['page']}  ·  {excerpt[:100]}")
            item.setData(Qt.ItemDataRole.UserRole, highlight["page"])
            self.highlights_list.addItem(item)
        if not self._highlights:
            item = QListWidgetItem(labels["no_highlights"])
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.highlights_list.addItem(item)

    def _load_selected_note(self, current: QListWidgetItem | None, _previous=None) -> None:
        if current is None:
            return
        note_id = current.data(Qt.ItemDataRole.UserRole)
        note = next((entry for entry in self._notes if entry["id"] == note_id), None)
        if note is None:
            return
        self._active_note_id = note["id"]
        self.page_spin.setValue(note["page"])
        self.note_editor.setPlainText(note["text"])
        self.delete_button.setEnabled(True)
        self.status_label.clear()

    def _activate_note(self, item: QListWidgetItem) -> None:
        self._load_selected_note(item)
        page = item.data(Qt.ItemDataRole.UserRole + 1)
        if isinstance(page, int):
            self.navigateRequested.emit(page)

    def _activate_highlight(self, item: QListWidgetItem) -> None:
        page = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(page, int):
            self.navigateRequested.emit(page)

    def new_note(self) -> None:
        if self.document is None:
            return
        self._active_note_id = None
        self.notes_list.clearSelection()
        self.page_spin.setValue(self.current_page)
        self.note_editor.clear()
        self.delete_button.setEnabled(False)
        self.status_label.setText(_LABELS[self._language]["select_note"])
        self.note_editor.setFocus()

    def save_note(self) -> bool:
        if self.document is None or not self.document_path:
            return False
        text = self.note_editor.toPlainText()
        page = int(self.page_spin.value())
        try:
            if self._active_note_id:
                saved = self.store.update_note(
                    self.document_path, self._active_note_id, page, text
                )
            else:
                saved = self.store.add_note(self.document_path, page, text)
        except (ResearchStoreError, ValueError, KeyError) as exc:
            self.status_label.setText(str(exc))
            return False

        self._active_note_id = saved["id"]
        self._notes = self.store.list_notes(self.document_path)
        self._refresh_notes()
        for index in range(self.notes_list.count()):
            item = self.notes_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == self._active_note_id:
                self.notes_list.setCurrentItem(item)
                break
        self.status_label.setText(_LABELS[self._language]["saved"])
        self.delete_button.setEnabled(True)
        return True

    def delete_note(self) -> bool:
        if self.document is None or not self.document_path or not self._active_note_id:
            return False
        try:
            deleted = self.store.delete_note(self.document_path, self._active_note_id)
        except ResearchStoreError as exc:
            self.status_label.setText(str(exc))
            return False
        if deleted:
            self._notes = self.store.list_notes(self.document_path)
            self._active_note_id = None
            self.note_editor.clear()
            self._refresh_notes()
            self.status_label.setText(_LABELS[self._language]["deleted"])
        return deleted

    def open_current_page(self) -> None:
        self.navigateRequested.emit(int(self.page_spin.value()))
