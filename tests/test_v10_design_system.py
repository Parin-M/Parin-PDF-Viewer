import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QWidget

from parin_ui.command_palette import Command, CommandRegistry
from parin_ui.layout import get_layout_metrics
from parin_ui.theme_engine import ThemeEngine
from parin_ui.theme_tokens import available_theme_modes, get_theme_tokens
from parin_ui.workspace_shell import ParinWorkspaceShell


class _MemorySettings:
    """Isolated QSettings stand-in for the main-window integration smoke test."""

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


class ThemeTokenTests(unittest.TestCase):
    def test_dark_and_light_tokens_are_distinct(self):
        dark = get_theme_tokens("dark")
        light = get_theme_tokens("light")
        self.assertNotEqual(dark.app_background, light.app_background)
        self.assertEqual(dark.header_text, "#F7FAFF")
        self.assertEqual(light.header_text, "#FFFFFF")
        self.assertEqual(available_theme_modes(), ("dark", "light"))

    def test_unknown_theme_is_rejected(self):
        with self.assertRaises(ValueError):
            get_theme_tokens("blue")

    def test_stylesheet_uses_semantic_tokens(self):
        engine = ThemeEngine("light")
        self.assertIn(engine.tokens.accent, engine.stylesheet)
        self.assertIn("QFrame#navigation_panel", engine.stylesheet)
        engine.set_mode("dark")
        self.assertIn(engine.tokens.canvas_background, engine.stylesheet)

    def test_theme_engine_rejects_non_widget_objects(self):
        with self.assertRaises(TypeError):
            ThemeEngine().apply(object())


class LayoutMetricTests(unittest.TestCase):
    def test_high_density_matches_hybrid_pro_spec(self):
        metrics = get_layout_metrics("high")
        self.assertEqual(metrics.header_height, 54)
        self.assertEqual(metrics.toolbar_height, 50)
        self.assertEqual(metrics.context_toolbar_height, 40)
        self.assertEqual(metrics.sidebar_width, 224)
        self.assertEqual(metrics.inspector_width, 288)
        self.assertEqual(metrics.statusbar_height, 28)

    def test_all_density_profiles_are_available(self):
        self.assertGreater(get_layout_metrics("comfortable").control_height,
                           get_layout_metrics("high").control_height)
        self.assertGreater(get_layout_metrics("high").control_height,
                           get_layout_metrics("compact").control_height)

    def test_unknown_density_is_rejected(self):
        with self.assertRaises(ValueError):
            get_layout_metrics("ultra")


class CommandRegistryTests(unittest.TestCase):
    def setUp(self):
        self.called = []
        self.registry = CommandRegistry(
            [
                Command("open", "Open PDF", "File", lambda: self.called.append("open"),
                        ("document", "browse"), "Ctrl+O"),
                Command("search", "Find in document", "Document",
                        lambda: self.called.append("search"), ("text", "lookup"), "Ctrl+F"),
                Command("focus", "Switch to Focus Studio", "Workspace",
                        lambda: self.called.append("focus"), ("focus", "workspace")),
            ]
        )

    def test_search_matches_titles_categories_and_keywords(self):
        self.assertEqual(self.registry.search("open")[0].command_id, "open")
        self.assertEqual(self.registry.search("lookup")[0].command_id, "search")
        self.assertEqual(self.registry.search("workspace focus")[0].command_id, "focus")

    def test_search_returns_no_false_positive_for_missing_term(self):
        self.assertEqual(self.registry.search("nonexistent"), ())

    def test_duplicate_command_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register(
                Command("open", "Another Open", "File", lambda: None)
            )

    def test_unregister_removes_command(self):
        self.registry.unregister("open")
        self.assertIsNone(self.registry.get("open"))


class WorkspaceShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_shell_builds_all_five_hybrid_pro_zones(self):
        shell = ParinWorkspaceShell(theme_mode="dark", density="high")
        try:
            self.assertIsNotNone(shell.findChild(QWidget, "parin_header"))
            self.assertIsNotNone(shell.findChild(QWidget, "toolbar"))
            self.assertIsNotNone(shell.findChild(QWidget, "context_toolbar"))
            self.assertIsNotNone(shell.findChild(QWidget, "navigation_panel"))
            self.assertIsNotNone(shell.findChild(QWidget, "inspector_panel"))
            self.assertEqual(shell.active_workspace, "reader")
            self.assertEqual(shell.command_registry.get("file.open").shortcut, "Ctrl+O")
        finally:
            shell.close()

    def test_workspace_switch_updates_context_and_emits_signal(self):
        shell = ParinWorkspaceShell()
        observed = []
        shell.workspaceChanged.connect(observed.append)
        try:
            shell.set_active_workspace("research")
            self.assertEqual(shell.active_workspace, "research")
            self.assertEqual(shell.workspace_title.text(), "Research Studio")
            self.assertEqual(observed, ["research"])
        finally:
            shell.close()

    def test_workspace_widget_can_replace_placeholder(self):
        shell = ParinWorkspaceShell()
        widget = QLabel("PDF viewport")
        try:
            shell.set_workspace_widget(widget)
            self.assertIs(shell.workspace_stack.currentWidget(), widget)
            self.assertEqual(shell.workspace_stack.count(), 2)
        finally:
            shell.close()


    def test_focus_mode_hides_panels_and_restores_responsive_layout(self):
        shell = ParinWorkspaceShell()
        try:
            shell.set_focus_mode(True)
            self.assertTrue(shell._focus_mode)
            self.assertTrue(shell.toolbar_frame.isHidden())
            self.assertTrue(shell.navigation_panel.isHidden())
            self.assertTrue(shell.inspector_panel.isHidden())
            self.assertFalse(shell.focus_exit_button.isHidden())

            shell.set_focus_mode(False)
            self.assertFalse(shell._focus_mode)
            self.assertFalse(shell.toolbar_frame.isHidden())
            self.assertTrue(shell.focus_exit_button.isHidden())
        finally:
            shell.close()

    def test_invalid_workspace_is_rejected(self):
        shell = ParinWorkspaceShell()
        try:
            with self.assertRaises(ValueError):
                shell.set_active_workspace("unknown")
        finally:
            shell.close()




class LegacyCommandPaletteBridgeTests(unittest.TestCase):
    def test_bridge_registers_available_viewer_actions(self):
        from types import SimpleNamespace
        from parin_ui.legacy_bridge import build_legacy_command_registry

        called = []
        viewer = SimpleNamespace(
            open_file=lambda: called.append("open"),
            save_file=lambda: called.append("save"),
            toggle_tool=lambda tool: called.append(tool),
        )
        registry = build_legacy_command_registry(viewer)

        self.assertIsNotNone(registry.get("file.open"))
        self.assertIsNotNone(registry.get("file.save"))
        self.assertIsNotNone(registry.get("annotation.pen"))
        self.assertIsNone(registry.get("settings.open"))
        registry.get("file.open").callback()
        registry.get("annotation.pen").callback()
        self.assertEqual(called, ["open", "pen"])

    def test_bridge_does_not_register_duplicate_shortcut_records(self):
        from types import SimpleNamespace
        from parin_ui.legacy_bridge import build_legacy_command_registry

        viewer = SimpleNamespace(
            zoom_in=lambda: None,
            zoom_out=lambda: None,
            search_pdf=lambda: None,
        )
        registry = build_legacy_command_registry(viewer)
        ids = [command.command_id for command in registry.all_commands()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(registry.get("document.find").shortcut, "Ctrl+F")




class ReaderInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_inspector_shows_document_metadata_and_page_dimensions(self):
        from types import SimpleNamespace
        from parin_ui.reader_inspector import ReaderInspector

        class FakeDocument:
            page_count = 12
            metadata = {"title": "Quarterly report", "author": "Parin", "subject": "Finance"}

            def load_page(self, index):
                return SimpleNamespace(rect=SimpleNamespace(width=595.0, height=842.0))

        inspector = ReaderInspector()
        inspector.update_document(FakeDocument(), "/tmp/report.pdf", 4, 1.25, True)
        self.assertEqual(inspector.file_name.text(), "report.pdf")
        self.assertEqual(inspector.pages_value.text(), "12")
        self.assertEqual(inspector.page_value.text(), "5 / 12")
        self.assertEqual(inspector.size_value.text(), "595 × 842 pt")
        self.assertEqual(inspector.title_value.text(), "Quarterly report")
        self.assertEqual(inspector.author_value.text(), "Parin")
        self.assertTrue(inspector.find_button.isEnabled())

    def test_inspector_localizes_and_clears_document(self):
        from parin_ui.reader_inspector import ReaderInspector

        inspector = ReaderInspector()
        inspector.set_language("fa")
        self.assertEqual(inspector.document_heading.text(), "مشخصات سند")
        self.assertEqual(inspector.file_name.text(), "سندی باز نیست")
        self.assertFalse(inspector.find_button.isEnabled())


class IntegratedV10ShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_viewer_hosts_existing_reader_in_v10_shell(self):
        from unittest.mock import patch
        from parin_pdf_viewer import ParinPDFViewer

        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                self.assertIs(viewer.centralWidget(), viewer.v10_shell)
                self.assertIs(viewer.v10_shell._workspace_widget, viewer.workspace_stack)
                self.assertIs(viewer.v10_shell.toolbar_frame, viewer.tool_area)
                self.assertIs(viewer.reader_inspector.parent(), viewer.v10_shell.inspector_panel)
                self.assertEqual(viewer.v10_shell.active_workspace, "reader")
                self.assertIs(viewer.v10_shell.navigation_panel.layout().count() > 5, True)
            finally:
                viewer.close()
                self.app.processEvents()

    def test_future_studios_are_clearly_marked_as_in_development(self):
        from parin_ui.studio_pages import StudioLanding

        page = StudioLanding("research")
        self.assertEqual(page.workspace_id, "research")
        self.assertEqual(page.status.text(), "IN DEVELOPMENT")


    def test_focus_studio_keeps_pdf_widget_and_can_return_to_reader(self):
        from parin_pdf_viewer import ParinPDFViewer
        from unittest.mock import patch

        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                viewer.v10_shell.set_active_workspace("focus")
                self.assertTrue(viewer.v10_shell._focus_mode)
                self.assertIs(viewer.v10_shell._workspace_widget, viewer.workspace_stack)
                self.assertTrue(viewer.v10_shell.toolbar_frame.isHidden())
                self.assertTrue(viewer.v10_shell.navigation_panel.isHidden())
                self.assertTrue(viewer.v10_shell.inspector_panel.isHidden())
                self.assertFalse(viewer.v10_shell.focus_exit_button.isHidden())

                viewer.v10_shell.focus_exit_button.click()
                self.assertEqual(viewer.v10_shell.active_workspace, "reader")
                self.assertFalse(viewer.v10_shell._focus_mode)
                self.assertIs(viewer.v10_shell._workspace_widget, viewer.workspace_stack)
            finally:
                viewer.close()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
