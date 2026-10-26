import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf as fitz
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMessageBox

from parin_pdf_viewer import ParinPDFViewer, _startup_pdf_path


class _MemorySettings:
    """Isolated QSettings replacement for file-open integration tests."""
    def __init__(self, *args, **kwargs):
        self.values = {}

    def value(self, key, defaultValue=None, type=None):
        value = self.values.get(key, defaultValue)
        if type is not None and value is not None:
            try:
                return type(value)
            except (TypeError, ValueError):
                return defaultValue
        return value

    def setValue(self, key, value):
        self.values[key] = value


class PdfOpenRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _make_pdf(path):
        document = fitz.open()
        document.new_page()
        document.save(str(path))
        document.close()

    def test_desktop_file_url_and_uppercase_extension_are_resolved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Résumé.PDF"
            self._make_pdf(path)

            self.assertEqual(_startup_pdf_path(str(path)), str(path))
            url = QUrl.fromLocalFile(str(path)).toString()
            self.assertEqual(_startup_pdf_path(url), str(path))

    def test_startup_argument_rejects_remote_urls_and_options(self):
        self.assertIsNone(_startup_pdf_path("https://example.com/file.pdf"))
        self.assertIsNone(_startup_pdf_path("--help"))
        self.assertIsNone(_startup_pdf_path("/path/that/does/not/exist.pdf"))

    def test_open_file_loads_document_and_switches_to_pdf_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "opened.PDF"
            self._make_pdf(path)
            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                try:
                    viewer.open_file(str(path))
                    self.assertIsNotNone(viewer.doc)
                    self.assertEqual(viewer.doc.page_count, 1)
                    self.assertEqual(viewer.file_path, str(path))
                    self.assertIs(viewer.workspace_stack.currentWidget(), viewer.scroll_area)
                finally:
                    viewer.close()
                    self.app.processEvents()

    def test_failed_open_keeps_current_document_available(self):
        with tempfile.TemporaryDirectory() as folder:
            good_path = Path(folder) / "good.pdf"
            bad_path = Path(folder) / "not-a-pdf.pdf"
            self._make_pdf(good_path)
            bad_path.write_text("not a PDF", encoding="utf-8")
            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                try:
                    viewer.open_file(str(good_path))
                    original_doc = viewer.doc
                    with patch.object(QMessageBox, "critical"):
                        viewer.open_file(str(bad_path))
                    self.assertIs(viewer.doc, original_doc)
                    self.assertEqual(viewer.file_path, str(good_path))
                    self.assertEqual(viewer.doc.page_count, 1)
                finally:
                    viewer.close()
                    self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
