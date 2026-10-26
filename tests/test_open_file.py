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

    def test_opened_pdf_renders_a_visible_page_bitmap(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "visible-page.pdf"
            document = fitz.open()
            page = document.new_page()
            page.draw_rect(fitz.Rect(100, 100, 400, 600), color=(1, 0, 0), fill=(1, 0, 0))
            document.save(str(path))
            document.close()

            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                try:
                    viewer.resize(1280, 850)
                    viewer.show()
                    self.app.processEvents()
                    viewer.open_file(str(path))
                    self.app.processEvents()

                    pixmap = viewer.page_label.pixmap()
                    self.assertIsNotNone(pixmap)
                    self.assertFalse(pixmap.isNull(), "PDF renderer must create an image")
                    self.assertGreater(pixmap.width(), 300, "fit-width rendering should use the available canvas")
                    self.assertEqual(viewer.page_label.size(), pixmap.size())
                    self.assertIs(viewer.workspace_stack.currentWidget(), viewer.scroll_area)

                    rendered = pixmap.toImage()
                    x = max(1, min(pixmap.width() - 1, int(250 * viewer.zoom_factor)))
                    y = max(1, min(pixmap.height() - 1, int(250 * viewer.zoom_factor)))
                    color = rendered.pixelColor(x, y)
                    self.assertGreater(color.red(), 200, f"Expected red page content at ({x}, {y}), got {color.name()}")
                    self.assertLess(color.green(), 100, f"Expected red page content at ({x}, {y}), got {color.name()}")
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
