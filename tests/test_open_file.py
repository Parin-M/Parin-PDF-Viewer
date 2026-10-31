import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf as fitz
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QWheelEvent
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



    def test_727_page_document_renders_page_one_into_visible_viewport(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large-page-count.pdf"
            document = fitz.open()
            for index in range(727):
                page = document.new_page(width=595, height=842)
                if index == 0:
                    page.draw_rect(
                        fitz.Rect(80, 80, 515, 760),
                        color=(0.1, 0.2, 0.8),
                        fill=(0.1, 0.2, 0.8),
                    )
                    page.insert_text((110, 140), "Visible first page", fontsize=24, color=(1, 1, 1))
            document.save(str(path), garbage=3, deflate=True)
            document.close()

            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                try:
                    viewer.resize(1480, 900)
                    viewer.show()
                    self.app.processEvents()
                    viewer.open_file(str(path))
                    for _ in range(8):
                        self.app.processEvents()

                    self.assertEqual(viewer.doc.page_count, 727)
                    self.assertEqual(viewer.current_page, 0)
                    pixmap = viewer.page_label.pixmap()
                    self.assertIsNotNone(pixmap)
                    self.assertFalse(pixmap.isNull())
                    self.assertGreater(pixmap.width(), 500)
                    self.assertGreater(pixmap.height(), 700)

                    viewport_image = viewer.scroll_area.viewport().grab().toImage()
                    visible_blue = False
                    for y in range(20, viewport_image.height(), 25):
                        for x in range(20, viewport_image.width(), 25):
                            color = viewport_image.pixelColor(x, y)
                            if color.blue() > 100 and color.blue() > color.red() + 45:
                                visible_blue = True
                                break
                        if visible_blue:
                            break
                    self.assertTrue(visible_blue, "page-one pixels must be painted in the visible PDF viewport")
                finally:
                    viewer.close()
                    self.app.processEvents()

    def test_next_and_previous_page_render_the_selected_page(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "navigation-colors.pdf"
            document = fitz.open()
            colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
            for color in colors:
                page = document.new_page(width=595, height=842)
                page.draw_rect(fitz.Rect(50, 50, 545, 792), color=color, fill=color)
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
                    self.assertEqual(viewer.current_page, 0)

                    def center_pixel():
                        pixmap = viewer.page_label.pixmap()
                        self.assertIsNotNone(pixmap)
                        self.assertFalse(pixmap.isNull())
                        image = pixmap.toImage()
                        x = min(pixmap.width() - 1, max(1, int(250 * viewer.zoom_factor)))
                        y = min(pixmap.height() - 1, max(1, int(300 * viewer.zoom_factor)))
                        return image.pixelColor(x, y)

                    first = center_pixel()
                    self.assertGreater(first.red(), first.green() + 100)

                    viewer.next_page()
                    self.app.processEvents()
                    second = center_pixel()
                    self.assertEqual(viewer.current_page, 1)
                    self.assertGreater(second.green(), second.red() + 100)

                    viewer.go_to_page(3)
                    self.app.processEvents()
                    third = center_pixel()
                    self.assertEqual(viewer.current_page, 2)
                    self.assertGreater(third.blue(), third.red() + 100)

                    viewer.prev_page()
                    self.app.processEvents()
                    returned = center_pixel()
                    self.assertEqual(viewer.current_page, 1)
                    self.assertGreater(returned.green(), returned.red() + 100)
                finally:
                    viewer.close()
                    self.app.processEvents()

    def test_large_page_rendering_is_limited_to_safe_raster_size(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large-page.pdf"
            document = fitz.open()
            page = document.new_page(width=10000, height=10000)
            page.insert_text((500, 500), "Large page", fontsize=120)
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
                    viewer.zoom_factor = 8.0
                    viewer.render_page()
                    pixmap = viewer.page_label.pixmap()
                    self.assertIsNotNone(pixmap)
                    self.assertFalse(pixmap.isNull())
                    self.assertLess(viewer.zoom_factor, 8.0)
                    self.assertLessEqual(pixmap.width() * pixmap.height(), 16_000_000)
                    self.assertLessEqual(max(pixmap.width(), pixmap.height()), 12_000)
                finally:
                    viewer.close()
                    self.app.processEvents()

    def test_mouse_wheel_scrolls_and_crosses_pages_without_blank_canvas(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "long-document.pdf"
            document = fitz.open()
            for index in range(3):
                page = document.new_page(width=595, height=1200)
                page.insert_text((72, 90), f"Visible content on page {index + 1}", fontsize=24)
                page.draw_rect(fitz.Rect(60, 120, 500, 1100), color=(0, 0.4, 0.8), fill=(0, 0.4, 0.8), width=3)
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
                    self.app.processEvents()

                    bar = viewer.scroll_area.verticalScrollBar()
                    self.assertGreater(bar.maximum(), 0, "a tall page must have a vertical scroll range")
                    start = bar.value()
                    event = QWheelEvent(
                        QPointF(30, 30), QPointF(30, 30), QPoint(0, 0), QPoint(0, -120),
                        Qt.NoButton, Qt.NoModifier, Qt.ScrollPhase.ScrollUpdate, False,
                    )
                    self.app.sendEvent(viewer.page_label, event)
                    self.app.processEvents()
                    self.assertGreater(bar.value(), start, "wheel-down must move the PDF canvas down")

                    # Reaching the bottom and scrolling again should enter the next page.
                    bar.setValue(bar.maximum())
                    event = QWheelEvent(
                        QPointF(30, 30), QPointF(30, 30), QPoint(0, 0), QPoint(0, -120),
                        Qt.NoButton, Qt.NoModifier, Qt.ScrollPhase.ScrollUpdate, False,
                    )
                    self.app.sendEvent(viewer.page_label, event)
                    self.app.processEvents()
                    self.app.processEvents()
                    self.assertEqual(viewer.current_page, 1)
                    self.assertFalse(viewer.page_label.pixmap().isNull())
                    self.assertLess(bar.value(), bar.maximum(), "the next page should continue from its top")

                    # Wheel events on the viewport (for example, over page margins)
                    # must use the same page-transition logic as events on the label.
                    bar.setValue(bar.maximum())
                    event = QWheelEvent(
                        QPointF(4, 4), QPointF(4, 4), QPoint(0, 0), QPoint(0, -120),
                        Qt.NoButton, Qt.NoModifier, Qt.ScrollPhase.ScrollUpdate, False,
                    )
                    self.app.sendEvent(viewer.scroll_area.viewport(), event)
                    for _ in range(5):
                        self.app.processEvents()
                    self.assertEqual(viewer.current_page, 2, "viewport wheel must advance the page")
                    self.assertFalse(viewer.page_label.pixmap().isNull())
                    image = viewer.scroll_area.viewport().grab().toImage()
                    sample = image.pixelColor(image.width() // 2, image.height() // 2)
                    self.assertGreater(sample.blue(), sample.red() + 30, "rendered page content must remain visible after viewport scrolling")

                    # Scrolling upward from the top of page 3 returns to page 2 near its bottom.
                    bar.setValue(bar.minimum())
                    event = QWheelEvent(
                        QPointF(4, 4), QPointF(4, 4), QPoint(0, 0), QPoint(0, 120),
                        Qt.NoButton, Qt.NoModifier, Qt.ScrollPhase.ScrollUpdate, False,
                    )
                    self.app.sendEvent(viewer.scroll_area.viewport(), event)
                    for _ in range(5):
                        self.app.processEvents()
                    self.assertEqual(viewer.current_page, 1, "upward viewport scrolling must return to the previous page")
                    self.assertGreater(bar.value(), 0, "the previous page should resume near its bottom")

                    # Ctrl+wheel remains zoom, not document scrolling.
                    previous_zoom = viewer.zoom_factor
                    event = QWheelEvent(
                        QPointF(4, 4), QPointF(4, 4), QPoint(0, 0), QPoint(0, 120),
                        Qt.NoButton, Qt.ControlModifier, Qt.ScrollPhase.ScrollUpdate, False,
                    )
                    self.app.sendEvent(viewer.scroll_area.viewport(), event)
                    self.app.processEvents()
                    self.assertGreater(viewer.zoom_factor, previous_zoom, "Ctrl+wheel-up must zoom in")
                finally:
                    viewer.close()
                    self.app.processEvents()

    def test_empty_password_encryption_is_preserved_when_saving(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "blank-user-password.pdf"
            output_path = Path(folder) / "saved-encrypted.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Encrypted but open with an empty user password")
            document.save(
                str(source_path),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner-secret",
                user_pw="",
            )
            document.close()

            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                saved = None
                try:
                    viewer.open_file(str(source_path))
                    self.assertIsNotNone(viewer.doc)
                    self.assertTrue(viewer._document_encrypted)
                    self.assertEqual(viewer._document_password, "")
                    self.assertTrue(viewer._save_to_path(str(output_path)))

                    saved = fitz.open(str(output_path))
                    encryption = (saved.metadata or {}).get("encryption")
                    self.assertTrue(
                        encryption and str(encryption).strip().lower() not in ("none", "null"),
                        f"the saved PDF must retain encryption metadata, got {encryption!r}",
                    )
                    self.assertGreater(
                        saved.authenticate(""), 0,
                        "the empty user password must still authenticate the saved PDF",
                    )
                    page_text = saved.load_page(0).get_text().strip()
                    self.assertIn("Encrypted but open", page_text)
                finally:
                    if saved is not None:
                        saved.close()
                    viewer.close()
                    self.app.processEvents()

    def test_failed_save_keeps_the_open_document_usable(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "source.pdf"
            self._make_pdf(source_path)
            bad_output = Path(folder) / "missing-directory" / "output.pdf"
            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                try:
                    viewer.open_file(str(source_path))
                    original_doc = viewer.doc
                    with patch.object(QMessageBox, "critical"):
                        self.assertFalse(viewer._save_to_path(str(bad_output)))
                    self.assertIs(viewer.doc, original_doc)
                    self.assertEqual(viewer.doc.page_count, 1)
                    self.assertGreater(viewer.doc.load_page(0).rect.width, 0)
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
