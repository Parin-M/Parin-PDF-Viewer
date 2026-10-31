import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf as fitz

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette

from parin_pdf_viewer import (
    COLOR_THEMES,
    ParinPDFViewer,
    SettingsDialog,
    _theme_stylesheet,
)


class _MemorySettings:
    """Isolated QSettings substitute so GUI smoke tests never touch user prefs."""
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


class InterfaceThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_light_and_dark_stylesheets_are_distinct(self):
        light = _theme_stylesheet("Arctic Glass", "light")
        dark = _theme_stylesheet("Arctic Glass", "dark")

        self.assertTrue(COLOR_THEMES)
        self.assertIn("background:#F8FBFF", light)
        self.assertIn("background:#111827", dark)
        self.assertIn("#3A8DFF", dark)
        self.assertIn("QLabel{color:#182338;background:transparent;}", light)

    def test_main_window_starts_on_welcome_page_and_can_switch_to_dark(self):
        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            dialog = None
            try:
                self.assertIs(viewer.workspace_stack.currentWidget(), viewer.welcome_page)
                self.assertIsNotNone(viewer.welcome_open_button)
                self.assertIsNotNone(viewer.recent_grid)
                self.assertEqual(viewer.palette().color(QPalette.WindowText).name(), "#20324a")
                self.assertIn("color:#20324A", viewer.styleSheet())
                self.assertIn("background-color:#10243F", viewer.header.styleSheet())
                self.assertIn("color:#FFFFFF", viewer.brand_title.styleSheet())

                dialog = SettingsDialog(viewer)
                self.assertEqual(dialog.card_titles[0].styleSheet(), "")
                dialog.appearance_mode.setCurrentIndex(1)
                self.assertEqual(dialog.collect()["appearance_mode"], "dark")

                dialog.apply_changes()
                self.assertEqual(viewer.app_settings["appearance_mode"], "dark")
                self.assertIn("background:#111827", viewer.styleSheet())
                self.assertEqual(viewer.palette().color(QPalette.WindowText).name(), "#eaf1fa")
            finally:
                if dialog is not None:
                    dialog.close()
                viewer.close()
                self.app.processEvents()


    def test_reset_defaults_updates_every_settings_widget(self):
        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            dialog = None
            try:
                dialog = SettingsDialog(viewer)
                dialog.remember_last.setChecked(False)
                dialog.single_page.setChecked(False)
                dialog.status.setChecked(False)
                dialog.show_icons.setChecked(False)
                dialog.low_memory.setChecked(True)
                dialog.audio_enabled.setChecked(False)
                dialog.fit.setCurrentText("100%")
                dialog.volume.setValue(7)

                dialog.reset_defaults()
                settings = dialog.collect()
                self.assertTrue(settings["remember_last"])
                self.assertTrue(settings["single_page"])
                self.assertTrue(settings["status_bar"])
                self.assertTrue(settings["show_toolbar_text"])
                self.assertFalse(settings["low_memory"])
                self.assertTrue(settings["audio_enabled"])
                self.assertEqual(settings["fit_mode"], "Fit Width")
                self.assertEqual(settings["volume"], 50)
                self.assertTrue(settings["preload_pages"])
            finally:
                if dialog is not None:
                    dialog.close()
                viewer.close()
                self.app.processEvents()

    def test_settings_apply_100_percent_mode_and_rotation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fit-mode.pdf"
            document = fitz.open()
            document.new_page()
            document.save(str(path))
            document.close()

            with patch("parin_pdf_viewer.QSettings", _MemorySettings):
                viewer = ParinPDFViewer()
                dialog = None
                try:
                    viewer.open_file(str(path))
                    dialog = SettingsDialog(viewer)
                    dialog.fit.setCurrentText("Fit Page")
                    dialog.apply_changes()
                    self.assertEqual(viewer.fit_mode, "page")

                    dialog.fit.setCurrentText("100%")
                    dialog.rotation.setCurrentText("90°")
                    dialog.apply_changes()
                    self.assertIsNone(viewer.fit_mode)
                    self.assertEqual(viewer.zoom_factor, 1.0)
                    self.assertEqual(viewer.rotation, 90)
                finally:
                    if dialog is not None:
                        dialog.close()
                    viewer.close()
                    self.app.processEvents()

    def test_workspace_uses_consistent_surface_and_action_styles(self):
        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                stylesheet = viewer.styleSheet()
                self.assertEqual(viewer.btn_open.objectName(), "primary_action")
                self.assertEqual(viewer.btn_save.objectName(), "secondary_action")
                self.assertIn("QFrame#tool_group", stylesheet)
                self.assertIn("QFrame#welcome_hero", stylesheet)
                self.assertIn("QToolButton#recent_file_card", stylesheet)
                self.assertIn("QPushButton#primary_action", stylesheet)
                self.assertIn("QListWidget::item:selected", stylesheet)
                self.assertIsNotNone(viewer._welcome_refresh_timer)
            finally:
                viewer.close()
                self.app.processEvents()

    def test_text_font_size_and_smart_ink_controls(self):
        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                self.assertEqual(viewer.font_selector.count(), 3)
                viewer.font_selector.setCurrentIndex(2)
                viewer.font_size.setValue(26)
                self.assertEqual(viewer.font_selector.currentData(), "cour")
                self.assertEqual(viewer.font_size.value(), 26)

                viewer.toggle_smart_ink(False)
                self.assertFalse(viewer.app_settings["smart_ink"])
                self.assertFalse(viewer.settings_store.value("smart_ink", True))
                viewer.toggle_smart_ink(True)
                self.assertTrue(viewer.app_settings["smart_ink"])
            finally:
                viewer.close()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
