import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

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

    def test_main_window_starts_on_welcome_page_and_can_switch_to_dark(self):
        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            dialog = None
            try:
                self.assertIs(viewer.workspace_stack.currentWidget(), viewer.welcome_page)
                self.assertIsNotNone(viewer.welcome_open_button)
                self.assertIsNotNone(viewer.recent_grid)

                dialog = SettingsDialog(viewer)
                dialog.appearance_mode.setCurrentIndex(1)
                self.assertEqual(dialog.collect()["appearance_mode"], "dark")

                dialog.apply_changes()
                self.assertEqual(viewer.app_settings["appearance_mode"], "dark")
                self.assertIn("background:#111827", viewer.styleSheet())
            finally:
                if dialog is not None:
                    dialog.close()
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
