"""Side-by-side PDF comparison with optional synchronized page navigation."""

from __future__ import annotations

import difflib
import math
import os
from pathlib import Path

import pymupdf as fitz
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QLabel,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


_MAX_RENDER_PIXELS = 16_000_000
_MAX_RENDER_DIMENSION = 12_000


_LABELS = {
    "en": {
        "title": "Compare Studio",
        "subtitle": "Review two local PDFs side by side. Each document stays independent.",
        "left": "LEFT DOCUMENT",
        "right": "RIGHT DOCUMENT",
        "open": "Open PDF",
        "page": "Page",
        "sync": "Synchronize pages",
        "compare_text": "Compare page text",
        "need_both": "Load a PDF in both panes to compare text.",
        "no_diff": "No text differences found on this page.",
        "diff_counts": "{added} added · {removed} removed",
        "diff_truncated": "Text was shortened before comparison.",
        "empty": "Open a PDF to compare",
        "no_document": "No document loaded",
        "ready": "Ready",
        "invalid": "The selected file is not a readable PDF.",
        "open_error": "Could not open PDF",
        "render_error": "Could not render page",
        "password": "PDF password",
        "enter_password": "This PDF is password-protected. Enter its password:",
        "wrong_password": "The password was not accepted.",
    },
    "fa": {
        "title": "محیط مقایسه",
        "subtitle": "دو فایل PDF محلی را کنار هم بررسی کنید؛ هر سند مستقل باقی می‌ماند.",
        "left": "سند سمت چپ",
        "right": "سند سمت راست",
        "open": "باز کردن PDF",
        "page": "صفحه",
        "sync": "همگام‌سازی صفحات",
        "compare_text": "مقایسهٔ متن صفحه",
        "need_both": "برای مقایسهٔ متن، هر دو سند را بارگذاری کنید.",
        "no_diff": "در متن این صفحه تفاوتی پیدا نشد.",
        "diff_counts": "{added} مورد اضافه · {removed} مورد حذف",
        "diff_truncated": "بخشی از متن پیش از مقایسه کوتاه شد.",
        "empty": "برای مقایسه، یک PDF باز کنید",
        "no_document": "سندی بارگذاری نشده است",
        "ready": "آماده",
        "invalid": "فایل انتخاب‌شده PDF قابل‌خواندن نیست.",
        "open_error": "بازکردن PDF ناموفق بود",
        "render_error": "نمایش صفحه ناموفق بود",
        "password": "رمز PDF",
        "enter_password": "این PDF رمز دارد. رمز آن را وارد کنید:",
        "wrong_password": "رمز پذیرفته نشد.",
    },
    "de": {
        "title": "Compare Studio",
        "subtitle": "Zwei lokale PDFs nebeneinander prüfen. Beide Dokumente bleiben unabhängig.",
        "left": "LINKES DOKUMENT",
        "right": "RECHTES DOKUMENT",
        "open": "PDF öffnen",
        "page": "Seite",
        "sync": "Seiten synchronisieren",
        "compare_text": "Seitentext vergleichen",
        "need_both": "Zum Textvergleich beide PDFs laden.",
        "no_diff": "Auf dieser Seite wurden keine Textunterschiede gefunden.",
        "diff_counts": "{added} hinzugefügt · {removed} entfernt",
        "diff_truncated": "Der Text wurde vor dem Vergleich gekürzt.",
        "empty": "PDF zum Vergleichen öffnen",
        "no_document": "Kein Dokument geladen",
        "ready": "Bereit",
        "invalid": "Die ausgewählte Datei ist kein lesbares PDF.",
        "open_error": "PDF konnte nicht geöffnet werden",
        "render_error": "Seite konnte nicht angezeigt werden",
        "password": "PDF-Passwort",
        "enter_password": "Dieses PDF ist geschützt. Passwort eingeben:",
        "wrong_password": "Das Passwort wurde nicht akzeptiert.",
    },
}


class ComparePane(QWidget):
    """One independently loaded PDF document inside Compare Studio."""

    pageChanged = Signal(int)
    documentLoaded = Signal(str, int)

    def __init__(self, side: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if side not in ("left", "right"):
            raise ValueError("Compare pane side must be 'left' or 'right'.")
        self.side = side
        self.document = None
        self.document_path = ""
        self.current_page = 1
        self._language = "en"
        self._pixmap: QPixmap | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        self.side_heading = QLabel()
        self.side_heading.setProperty("role", "muted")
        header.addWidget(self.side_heading)
        header.addStretch(1)
        self.open_button = QPushButton()
        self.open_button.clicked.connect(self.choose_document)
        header.addWidget(self.open_button)
        root.addLayout(header)

        self.document_label = QLabel()
        self.document_label.setWordWrap(True)
        self.document_label.setProperty("role", "muted")
        root.addWidget(self.document_label)

        controls = QHBoxLayout()
        self.page_label = QLabel()
        controls.addWidget(self.page_label)
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setEnabled(False)
        self.page_spin.setFixedWidth(84)
        self.page_spin.valueChanged.connect(self.set_page)
        controls.addWidget(self.page_spin)
        controls.addStretch(1)
        self.page_count_label = QLabel("0 / 0")
        self.page_count_label.setProperty("role", "muted")
        controls.addWidget(self.page_count_label)
        root.addLayout(controls)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setObjectName(f"compare_{side}_scroll")
        self.page_image = QLabel(self.scroll_area)
        self.page_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_image.setMinimumSize(1, 1)
        self.page_image.setText(_LABELS[self._language]["empty"])
        self.scroll_area.setWidget(self.page_image)
        root.addWidget(self.scroll_area, 1)

        self.status_label = QLabel()
        self.status_label.setProperty("role", "muted")
        root.addWidget(self.status_label)

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(120)
        self._render_timer.timeout.connect(self.render_page)
        self.set_language("en")

    def set_language(self, language: str) -> None:
        self._language = language if language in _LABELS else "en"
        labels = _LABELS[self._language]
        self.side_heading.setText(labels[self.side])
        self.open_button.setText(labels["open"])
        self.page_label.setText(labels["page"])
        self.status_label.setText(
            Path(self.document_path).name if self.document_path else labels["no_document"]
        )
        if self.document is None:
            self.page_image.setText(labels["empty"])

    def choose_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            _LABELS[self._language]["open"],
            "",
            "PDF documents (*.pdf *.PDF);;All files (*)",
        )
        if path:
            self.load_document(path, report_errors=True)

    def load_document(self, file_path: str, report_errors: bool = True) -> bool:
        """Open and validate the new PDF before replacing this pane's current PDF."""
        candidate = None
        try:
            path = os.path.abspath(os.path.expanduser(str(file_path)))
            if not os.path.isfile(path):
                raise FileNotFoundError(path)
            candidate = fitz.open(path)
            if getattr(candidate, "needs_pass", False):
                if not candidate.authenticate(""):
                    labels = _LABELS[self._language]
                    while True:
                        password, accepted = QInputDialog.getText(
                            self,
                            labels["password"],
                            labels["enter_password"],
                            QLineEdit.EchoMode.Password,
                        )
                        if not accepted:
                            candidate.close()
                            return False
                        if candidate.authenticate(password):
                            break
                        QMessageBox.warning(self, labels["password"], labels["wrong_password"])
            if candidate.page_count < 1:
                raise ValueError(_LABELS[self._language]["invalid"])
            page = candidate.load_page(0)
            page_width = max(1.0, float(page.rect.width))
            page_height = max(1.0, float(page.rect.height))
            preflight_scale = min(
                0.2,
                _MAX_RENDER_DIMENSION / max(page_width, page_height),
                (_MAX_RENDER_PIXELS / (page_width * page_height)) ** 0.5,
            )
            pix = page.get_pixmap(
                matrix=fitz.Matrix(preflight_scale, preflight_scale),
                colorspace=fitz.csRGB,
                alpha=False,
            )
            if (
                pix.width < 1
                or pix.height < 1
                or pix.width > _MAX_RENDER_DIMENSION
                or pix.height > _MAX_RENDER_DIMENSION
                or pix.width * pix.height > _MAX_RENDER_PIXELS
                or pix.n != 3
                or len(pix.samples) < pix.stride * pix.height
            ):
                raise ValueError(_LABELS[self._language]["invalid"])

            previous = self.document
            self.document = candidate
            candidate = None
            self.document_path = path
            self.current_page = 1
            self.page_spin.blockSignals(True)
            self.page_spin.setRange(1, self.document.page_count)
            self.page_spin.setValue(1)
            self.page_spin.blockSignals(False)
            self.page_spin.setEnabled(True)
            self.document_label.setText(Path(path).name)
            self.page_count_label.setText(f"1 / {self.document.page_count}")
            self.status_label.setText(_LABELS[self._language]["ready"])
            self.render_page()
            if previous is not None:
                try:
                    previous.close()
                except Exception:
                    pass
            self.documentLoaded.emit(path, self.document.page_count)
            return True
        except Exception as exc:
            if candidate is not None:
                try:
                    candidate.close()
                except Exception:
                    pass
            self.status_label.setText(str(exc))
            if report_errors:
                QMessageBox.critical(
                    self,
                    _LABELS[self._language]["open_error"],
                    str(exc),
                )
            return False

    def set_page(self, page_number: int, emit: bool = True) -> None:
        if self.document is None:
            return
        target = min(max(int(page_number), 1), int(self.document.page_count))
        changed = target != self.current_page
        self.current_page = target
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(target)
        self.page_spin.blockSignals(False)
        self.page_count_label.setText(f"{target} / {self.document.page_count}")
        self.render_page()
        if emit and changed:
            self.pageChanged.emit(target)

    def render_page(self) -> None:
        if self.document is None or getattr(self.document, "is_closed", False):
            return
        try:
            page = self.document.load_page(self.current_page - 1)
            width = max(1.0, float(page.rect.width))
            height = max(1.0, float(page.rect.height))
            viewport_width = max(180, self.scroll_area.viewport().width() - 28)
            scale = min(
                1.25,
                viewport_width / width,
                _MAX_RENDER_DIMENSION / max(width, height),
                (_MAX_RENDER_PIXELS / (width * height)) ** 0.5,
            )
            if not math.isfinite(scale) or scale <= 0:
                raise RuntimeError("The PDF page has invalid dimensions.")
            pix = page.get_pixmap(
                matrix=fitz.Matrix(scale, scale),
                colorspace=fitz.csRGB,
                alpha=False,
            )
            if (
                pix.width < 1
                or pix.height < 1
                or pix.width > _MAX_RENDER_DIMENSION
                or pix.height > _MAX_RENDER_DIMENSION
                or pix.width * pix.height > _MAX_RENDER_PIXELS
                or pix.n != 3
                or len(pix.samples) < pix.stride * pix.height
            ):
                raise RuntimeError("The PDF renderer returned an invalid image.")
            image = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888,
            ).copy()
            self._pixmap = QPixmap.fromImage(image)
            self.page_image.setPixmap(self._pixmap)
            self.page_image.resize(self._pixmap.size())
            self.status_label.setText(Path(self.document_path).name)
        except Exception as exc:
            self._pixmap = None
            self.page_image.clear()
            self.page_image.setText(str(exc))
            self.status_label.setText(_LABELS[self._language]["render_error"])

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.document is not None:
            self._render_timer.start()

    def close_document(self) -> None:
        self._render_timer.stop()
        previous = self.document
        self.document = None
        self.document_path = ""
        self.current_page = 1
        self._pixmap = None
        self.page_image.clear()
        self.page_image.setText(_LABELS[self._language]["empty"])
        self.document_label.setText(_LABELS[self._language]["no_document"])
        self.page_count_label.setText("0 / 0")
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.blockSignals(False)
        self.page_spin.setEnabled(False)
        self.status_label.setText(_LABELS[self._language]["no_document"])
        if previous is not None:
            try:
                previous.close()
            except Exception:
                pass


class CompareStudio(QWidget):
    """Two independent PDF panes with optional page-number synchronization."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._language = "en"
        self.setObjectName("compare_studio")
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(8)

        top = QHBoxLayout()
        intro = QVBoxLayout()
        self.heading = QLabel()
        self.heading.setStyleSheet("font-size:18pt;font-weight:750;")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setProperty("role", "muted")
        intro.addWidget(self.heading)
        intro.addWidget(self.subtitle)
        top.addLayout(intro, 1)
        self.compare_text_button = QPushButton()
        self.compare_text_button.clicked.connect(self.compare_current_page_text)
        top.addWidget(self.compare_text_button)
        self.sync_checkbox = QCheckBox()
        self.sync_checkbox.setChecked(True)
        self.sync_checkbox.toggled.connect(self._set_sync_enabled)
        top.addWidget(self.sync_checkbox)
        root.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        self.left_pane = ComparePane("left", splitter)
        self.right_pane = ComparePane("right", splitter)
        splitter.addWidget(self.left_pane)
        splitter.addWidget(self.right_pane)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)
        self.splitter = splitter

        self.status_label = QLabel()
        self.status_label.setProperty("role", "muted")
        root.addWidget(self.status_label)
        self.diff_summary = QLabel()
        self.diff_summary.setProperty("role", "muted")
        root.addWidget(self.diff_summary)
        self.diff_editor = QPlainTextEdit(self)
        self.diff_editor.setReadOnly(True)
        self.diff_editor.setMaximumHeight(160)
        self.diff_editor.setObjectName("compare_text_diff")
        self.diff_editor.hide()
        root.addWidget(self.diff_editor)

        self.left_pane.pageChanged.connect(
            lambda page: self._on_page_changed("left", page)
        )
        self.right_pane.pageChanged.connect(
            lambda page: self._on_page_changed("right", page)
        )
        self.left_pane.documentLoaded.connect(
            lambda _path, _count: self._on_document_loaded("left")
        )
        self.right_pane.documentLoaded.connect(
            lambda _path, _count: self._on_document_loaded("right")
        )
        self.set_language("en")

    def set_language(self, language: str) -> None:
        self._language = language if language in _LABELS else "en"
        labels = _LABELS[self._language]
        self.heading.setText(labels["title"])
        self.subtitle.setText(labels["subtitle"])
        self.sync_checkbox.setText(labels["sync"])
        self.compare_text_button.setText(labels["compare_text"])
        self.left_pane.set_language(self._language)
        self.right_pane.set_language(self._language)
        self._update_status()

    def load_document(
        self,
        side: str,
        file_path: str,
        report_errors: bool = True,
    ) -> bool:
        if side not in ("left", "right"):
            raise ValueError("Compare side must be 'left' or 'right'.")
        pane = self.left_pane if side == "left" else self.right_pane
        loaded = pane.load_document(file_path, report_errors=report_errors)
        if loaded and self.sync_checkbox.isChecked():
            if side == "left" and self.right_pane.document is not None:
                self.left_pane.set_page(self.right_pane.current_page, emit=False)
            elif side == "right" and self.left_pane.document is not None:
                self.right_pane.set_page(self.left_pane.current_page, emit=False)
        self._update_status()
        return loaded

    def _on_page_changed(self, side: str, page: int) -> None:
        if self.sync_checkbox.isChecked():
            other = self.right_pane if side == "left" else self.left_pane
            if other.document is not None:
                other.set_page(page, emit=False)
        self._update_status()

    def _on_document_loaded(self, side: str) -> None:
        if not self.sync_checkbox.isChecked():
            self._update_status()
            return
        if side == "left" and self.right_pane.document is not None:
            self.left_pane.set_page(self.right_pane.current_page, emit=False)
        elif side == "right" and self.left_pane.document is not None:
            self.right_pane.set_page(self.left_pane.current_page, emit=False)
        self._update_status()

    def _set_sync_enabled(self, enabled: bool) -> None:
        if enabled:
            source = self.left_pane if self.left_pane.document is not None else self.right_pane
            other = self.right_pane if source is self.left_pane else self.left_pane
            if source.document is not None and other.document is not None:
                other.set_page(source.current_page, emit=False)
        self._update_status()

    def _update_status(self) -> None:
        labels = _LABELS[self._language]
        left = self.left_pane.document.page_count if self.left_pane.document else 0
        right = self.right_pane.document.page_count if self.right_pane.document else 0
        self.status_label.setText(
            f"{labels['left']}: {left}    ·    {labels['right']}: {right}"
        )
        self.compare_text_button.setEnabled(bool(left and right))

    def compare_current_page_text(self) -> bool:
        """Render a bounded unified diff for the two currently selected pages."""
        labels = _LABELS[self._language]
        if self.left_pane.document is None or self.right_pane.document is None:
            self.diff_editor.setPlainText(labels["need_both"])
            self.diff_editor.show()
            self.diff_summary.setText("")
            return False
        try:
            left_page = self.left_pane.document.load_page(self.left_pane.current_page - 1)
            right_page = self.right_pane.document.load_page(self.right_pane.current_page - 1)
            left_text = left_page.get_text("text")
            right_text = right_page.get_text("text")
            max_chars = 120_000
            max_lines = 1_500
            truncated = len(left_text) > max_chars or len(right_text) > max_chars
            left_lines = left_text[:max_chars].splitlines()[:max_lines]
            right_lines = right_text[:max_chars].splitlines()[:max_lines]
            if len(left_text.splitlines()) > max_lines or len(right_text.splitlines()) > max_lines:
                truncated = True

            diff_lines = list(
                difflib.unified_diff(
                    left_lines,
                    right_lines,
                    fromfile=f"Left · page {self.left_pane.current_page}",
                    tofile=f"Right · page {self.right_pane.current_page}",
                    lineterm="",
                    n=2,
                )
            )
            added = sum(
                1 for line in diff_lines
                if line.startswith("+") and not line.startswith("+++")
            )
            removed = sum(
                1 for line in diff_lines
                if line.startswith("-") and not line.startswith("---")
            )
            if not diff_lines:
                output = labels["no_diff"]
                summary = labels["no_diff"]
            else:
                output = "\n".join(diff_lines[:400])
                if len(diff_lines) > 400:
                    output += "\n…"
                    truncated = True
                summary = labels["diff_counts"].format(added=added, removed=removed)
            if truncated:
                output += "\n\n" + labels["diff_truncated"]
            self.diff_editor.setPlainText(output)
            self.diff_summary.setText(summary)
            self.diff_editor.show()
            return True
        except Exception as exc:
            self.diff_editor.setPlainText(str(exc))
            self.diff_summary.setText(labels["render_error"])
            self.diff_editor.show()
            return False

    def close_documents(self) -> None:
        self.left_pane.close_document()
        self.right_pane.close_document()
        self._update_status()
