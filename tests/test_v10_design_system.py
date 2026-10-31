import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QWidget

from parin_ui.command_palette import Command, CommandRegistry
from parin_ui.layout import get_layout_metrics
from parin_ui.theme_engine import ThemeEngine
from parin_ui.theme_tokens import available_theme_modes, get_theme_tokens
from parin_ui.workspace_shell import ParinWorkspaceShell


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

    def test_invalid_workspace_is_rejected(self):
        shell = ParinWorkspaceShell()
        try:
            with self.assertRaises(ValueError):
                shell.set_active_workspace("unknown")
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main()
