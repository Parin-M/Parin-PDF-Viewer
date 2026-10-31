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


    def test_light_theme_keeps_header_action_text_on_dark_header(self):
        stylesheet = ThemeEngine("light").stylesheet
        self.assertIn("QFrame#parin_header QPushButton", stylesheet)
        self.assertIn("color: #FFFFFF;", stylesheet)
        self.assertIn("QLineEdit, QComboBox, QSpinBox", stylesheet)

    def test_text_editors_use_theme_surface_and_selection_tokens(self):
        for mode in ("dark", "light"):
            engine = ThemeEngine(mode)
            stylesheet = engine.stylesheet
            self.assertIn("QTextEdit, QPlainTextEdit", stylesheet)
            self.assertIn(engine.tokens.surface, stylesheet)
            self.assertIn(engine.tokens.selection_background, stylesheet)
            self.assertIn(engine.tokens.selection_text, stylesheet)
            self.assertIn(engine.tokens.accent, stylesheet)
            self.assertIn("QTextEdit:disabled, QPlainTextEdit:disabled", stylesheet)

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


    def test_shell_localizes_workspace_and_context_labels(self):
        shell = ParinWorkspaceShell()
        try:
            shell.set_language("fa")
            shell.set_active_workspace("focus")
            self.assertEqual(shell.workspace_heading.text(), "فضاهای کاری")
            self.assertEqual(shell.workspace_title.text(), "حالت تمرکز")
            self.assertEqual(shell.focus_exit_button.text(), "خروج از تمرکز")
            self.assertEqual(shell.command_button.text(), "جست‌وجوی فرمان‌ها    Ctrl+K")

            shell.set_language("de")
            self.assertEqual(shell.inspector_heading.text(), "DOKUMENT-INSPEKTOR")
            self.assertEqual(shell.workspace_title.text(), "Focus Studio")
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


    def test_document_hub_reuses_recent_documents_and_preserves_reader(self):
        from parin_pdf_viewer import ParinPDFViewer
        from unittest.mock import patch

        class DummyDocument:
            def close(self):
                pass

        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                viewer.doc = DummyDocument()
                viewer.v10_shell.set_active_workspace("hub")
                self.assertEqual(viewer.v10_shell.workspace_title.text(), "Document Hub")
                self.assertIs(viewer.v10_shell._workspace_widget, viewer.workspace_stack)
                self.assertIs(viewer.workspace_stack.currentWidget(), viewer.welcome_page)

                viewer.v10_shell.set_active_workspace("reader")
                self.assertIs(viewer.workspace_stack.currentWidget(), viewer.scroll_area)
                self.assertIs(viewer.doc.__class__, DummyDocument)
            finally:
                viewer.close()
                self.app.processEvents()


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




class ResearchStoreTests(unittest.TestCase):
    def test_notes_are_saved_updated_deleted_and_isolated_by_document(self):
        import tempfile
        from pathlib import Path
        from parin_ui.research_store import ResearchStore

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first_pdf = root / "first.pdf"
            second_pdf = root / "second.pdf"
            first_pdf.write_bytes(b"%PDF-1.7")
            second_pdf.write_bytes(b"%PDF-1.7")
            store = ResearchStore(root / "research")

            note = store.add_note(str(first_pdf), 3, "Check equation on this page")
            self.assertEqual(store.list_notes(str(first_pdf))[0]["text"], "Check equation on this page")
            updated = store.update_note(str(first_pdf), note["id"], 4, "Verified source on page four")
            self.assertEqual(updated["page"], 4)
            self.assertEqual(store.list_notes(str(second_pdf)), [])
            self.assertTrue(store.delete_note(str(first_pdf), note["id"]))
            self.assertEqual(store.list_notes(str(first_pdf)), [])

    def test_invalid_page_and_empty_note_are_rejected(self):
        import tempfile
        from pathlib import Path
        from parin_ui.research_store import ResearchStore

        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder) / "sample.pdf"
            pdf.write_bytes(b"%PDF-1.7")
            store = ResearchStore(Path(folder) / "research")
            with self.assertRaises(ValueError):
                store.add_note(str(pdf), 0, "invalid page")
            with self.assertRaises(ValueError):
                store.add_note(str(pdf), 1, "   ")

    def test_save_as_copies_notes_without_deleting_source_notes(self):
        import tempfile
        from pathlib import Path
        from parin_ui.research_store import ResearchStore

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.pdf"
            destination = root / "copy.pdf"
            source.write_bytes(b"%PDF-1.7")
            destination.write_bytes(b"%PDF-1.7")
            store = ResearchStore(root / "research")
            store.add_note(str(source), 2, "A source note")
            self.assertEqual(store.copy_document_notes(str(source), str(destination)), 1)
            self.assertEqual(len(store.list_notes(str(source))), 1)
            self.assertEqual(len(store.list_notes(str(destination))), 1)


class ResearchStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_notes_persist_and_activation_navigates_to_referenced_page(self):
        import tempfile
        from pathlib import Path
        import pymupdf as fitz
        from parin_ui.research_store import ResearchStore
        from parin_ui.research_studio import ResearchStudio

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "research.pdf"
            document = fitz.open()
            document.new_page()
            document.new_page()
            document.save(str(path))
            document.close()
            document = fitz.open(str(path))
            store = ResearchStore(Path(folder) / "research-data")
            studio = ResearchStudio(store)
            try:
                studio.set_document(str(path), document, 1)
                studio.page_spin.setValue(2)
                studio.note_editor.setPlainText("Compare this definition with section 4.")
                self.assertTrue(studio.save_note())
                self.assertEqual(len(studio.notes), 1)
                self.assertEqual(studio.notes[0]["page"], 2)

                restarted = ResearchStudio(store)
                restarted.set_document(str(path), document, 0)
                self.assertEqual(len(restarted.notes), 1)
                self.assertIn("Compare this definition", restarted.notes[0]["text"])

                navigated = []
                studio.navigateRequested.connect(navigated.append)
                item = studio.notes_list.item(0)
                studio._activate_note(item)
                self.assertEqual(navigated, [2])
                restarted.close()
            finally:
                studio.close()
                document.close()

    def test_highlight_extractor_finds_pdf_highlight_annotations(self):
        import pymupdf as fitz
        from parin_ui.research_store import extract_pdf_highlights

        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Research evidence text")
        highlight = page.add_highlight_annot(fitz.Rect(70, 55, 180, 78))
        highlight.set_info(content="Key source passage")
        highlight.update()
        items = extract_pdf_highlights(document)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["page"], 1)
        self.assertIn("Highlight", items[0]["type"])
        self.assertEqual(items[0]["content"], "Key source passage")
        document.close()

    def test_research_studio_handles_missing_document(self):
        import tempfile
        from pathlib import Path
        from parin_ui.research_store import ResearchStore
        from parin_ui.research_studio import ResearchStudio

        with tempfile.TemporaryDirectory() as folder:
            studio = ResearchStudio(ResearchStore(Path(folder)))
            self.assertEqual(studio.notes, ())
            self.assertFalse(studio.save_button.isEnabled())
            self.assertEqual(studio.document, None)
            studio.close()


    def test_research_workspace_is_mounted_and_empty_state_is_safe(self):
        from unittest.mock import patch
        from parin_pdf_viewer import ParinPDFViewer
        from parin_ui.research_studio import ResearchStudio

        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                viewer.v10_shell.set_active_workspace("research")
                self.assertIsInstance(viewer.v10_shell._workspace_widget, ResearchStudio)
                self.assertIs(viewer.research_studio.document, None)
                self.assertFalse(viewer.research_studio.save_button.isEnabled())
                self.assertEqual(viewer.v10_shell.active_workspace, "research")
            finally:
                viewer.close()
                self.app.processEvents()




class CompareStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_pdf(self, path, page_count):
        import pymupdf as fitz
        document = fitz.open()
        for index in range(page_count):
            page = document.new_page()
            page.insert_text((72, 72), f"Comparison page {index + 1}")
        document.save(str(path))
        document.close()

    def test_two_pdfs_load_independently_and_sync_pages(self):
        import tempfile
        from pathlib import Path
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "left.pdf"
            right = root / "right.pdf"
            self._make_pdf(left, 4)
            self._make_pdf(right, 2)
            studio = CompareStudio()
            try:
                self.assertTrue(studio.load_document("left", str(left), report_errors=False))
                self.assertTrue(studio.load_document("right", str(right), report_errors=False))
                studio.left_pane.set_page(2)
                self.assertEqual(studio.right_pane.current_page, 2)
                studio.left_pane.set_page(4)
                self.assertEqual(studio.right_pane.current_page, 2)
                self.assertEqual(studio.left_pane.document.page_count, 4)
                self.assertEqual(studio.right_pane.document.page_count, 2)
            finally:
                studio.close_documents()
                studio.close()

    def test_previews_are_rendered_for_both_loaded_documents(self):
        import tempfile
        from pathlib import Path
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "left.pdf"
            right = root / "right.pdf"
            self._make_pdf(left, 1)
            self._make_pdf(right, 1)
            studio = CompareStudio()
            try:
                self.assertTrue(studio.load_document("left", str(left), report_errors=False))
                self.assertTrue(studio.load_document("right", str(right), report_errors=False))
                self.assertIsNotNone(studio.left_pane.page_image.pixmap())
                self.assertIsNotNone(studio.right_pane.page_image.pixmap())
            finally:
                studio.close_documents()
                studio.close()

    def test_sync_can_be_disabled_and_reenabled(self):
        import tempfile
        from pathlib import Path
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "left.pdf"
            right = root / "right.pdf"
            self._make_pdf(left, 3)
            self._make_pdf(right, 3)
            studio = CompareStudio()
            try:
                studio.load_document("left", str(left), report_errors=False)
                studio.load_document("right", str(right), report_errors=False)
                studio.sync_checkbox.setChecked(False)
                studio.left_pane.set_page(3)
                self.assertEqual(studio.right_pane.current_page, 1)
                studio.sync_checkbox.setChecked(True)
                self.assertEqual(studio.right_pane.current_page, 3)
            finally:
                studio.close_documents()
                studio.close()

    def test_page_text_diff_reports_additions_and_removals(self):
        import tempfile
        from pathlib import Path
        import pymupdf as fitz
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "left.pdf"
            right = root / "right.pdf"
            left_doc = fitz.open()
            left_page = left_doc.new_page()
            left_page.insert_text((72, 72), "Shared statement")
            left_page.insert_text((72, 100), "Old wording")
            left_doc.save(str(left))
            left_doc.close()

            right_doc = fitz.open()
            right_page = right_doc.new_page()
            right_page.insert_text((72, 72), "Shared statement")
            right_page.insert_text((72, 100), "New wording")
            right_doc.save(str(right))
            right_doc.close()

            studio = CompareStudio()
            try:
                self.assertTrue(studio.load_document("left", str(left), report_errors=False))
                self.assertTrue(studio.load_document("right", str(right), report_errors=False))
                self.assertTrue(studio.compare_current_page_text())
                output = studio.diff_editor.toPlainText()
                self.assertIn("-Old wording", output)
                self.assertIn("+New wording", output)
                self.assertIn("1 added", studio.diff_summary.text())
                self.assertIn("1 removed", studio.diff_summary.text())
            finally:
                studio.close_documents()
                studio.close()

    def test_equal_page_text_has_explicit_no_difference_state(self):
        import tempfile
        from pathlib import Path
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left = root / "left.pdf"
            right = root / "right.pdf"
            self._make_pdf(left, 1)
            self._make_pdf(right, 1)
            studio = CompareStudio()
            try:
                studio.load_document("left", str(left), report_errors=False)
                studio.load_document("right", str(right), report_errors=False)
                self.assertTrue(studio.compare_current_page_text())
                self.assertIn("No text differences", studio.diff_summary.text())
            finally:
                studio.close_documents()
                studio.close()

    def test_failed_replacement_preserves_loaded_document(self):
        import tempfile
        from pathlib import Path
        from parin_ui.compare_studio import CompareStudio

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            good = root / "good.pdf"
            bad = root / "bad.pdf"
            self._make_pdf(good, 1)
            bad.write_text("not a PDF", encoding="utf-8")
            studio = CompareStudio()
            try:
                self.assertTrue(studio.load_document("left", str(good), report_errors=False))
                previous = studio.left_pane.document
                self.assertFalse(studio.load_document("left", str(bad), report_errors=False))
                self.assertIs(studio.left_pane.document, previous)
                self.assertEqual(studio.left_pane.document_path, str(good.resolve()))
            finally:
                studio.close_documents()
                studio.close()

    def test_compare_workspace_is_mounted_and_localized(self):
        from unittest.mock import patch
        from parin_pdf_viewer import ParinPDFViewer
        from parin_ui.compare_studio import CompareStudio

        with patch("parin_pdf_viewer.QSettings", _MemorySettings):
            viewer = ParinPDFViewer()
            try:
                viewer.apply_language("fa")
                viewer.v10_shell.set_active_workspace("compare")
                self.assertIsInstance(viewer.v10_shell._workspace_widget, CompareStudio)
                self.assertEqual(viewer.compare_studio.heading.text(), "محیط مقایسه")
            finally:
                viewer.close()
                self.app.processEvents()


class PageOrganizerDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_document(self, labels=("Page one", "Page two", "Page three")):
        import pymupdf as fitz
        document = fitz.open()
        for label in labels:
            page = document.new_page()
            page.insert_text((72, 72), label)
        return document

    def _make_viewer(self, document):
        class Viewer(QWidget):
            def __init__(self, doc):
                super().__init__()
                self.doc = doc
                self.current_page = 0
                self.file_path = ""
                self.undo_records = 0
                self.structure_updates = 0
                self.undo_calls = 0

            def _record_undo(self):
                self.undo_records += 1

            def _after_document_structure_change(self):
                self.structure_updates += 1

            def undo_edit(self):
                self.undo_calls += 1

        return Viewer(document)

    def test_reorder_pages_is_applied_transactionally_and_updates_current_page(self):
        from PySide6.QtCore import Qt
        from parin_ui.page_organizer import PageOrganizerDialog

        document = self._make_document()
        viewer = self._make_viewer(document)
        viewer.current_page = 1
        dialog = PageOrganizerDialog(viewer)
        try:
            moved = dialog.pages.takeItem(1)
            dialog.pages.insertItem(0, moved)
            dialog.apply_changes()
            self.assertIn("Page two", document.load_page(0).get_text())
            self.assertEqual(viewer.current_page, 0)
            self.assertEqual(viewer.undo_records, 1)
            self.assertEqual(viewer.structure_updates, 1)
            self.assertEqual(viewer.undo_calls, 0)
        finally:
            dialog.close()
            viewer.close()
            document.close()

    def test_rotation_is_staged_until_apply(self):
        from unittest.mock import patch
        from parin_ui.page_organizer import PageOrganizerDialog

        document = self._make_document(("Rotate me",))
        viewer = self._make_viewer(document)
        dialog = PageOrganizerDialog(viewer)
        try:
            dialog.pages.item(0).setSelected(True)
            dialog.rotate_selected()
            self.assertEqual(dialog.rotations[0], 90)
            self.assertEqual(document.load_page(0).rotation, 0)
            with patch("parin_ui.page_organizer.QMessageBox.critical") as critical:
                dialog.apply_changes()
            critical.assert_not_called()
            self.assertEqual(document.load_page(0).rotation, 90)
            self.assertEqual(viewer.undo_records, 1)
        finally:
            dialog.close()
            viewer.close()
            document.close()

    def test_empty_page_list_is_rejected_without_mutating_document(self):
        from unittest.mock import patch
        from parin_ui.page_organizer import PageOrganizerDialog

        document = self._make_document(("Keep one", "Keep two"))
        viewer = self._make_viewer(document)
        dialog = PageOrganizerDialog(viewer)
        try:
            for row in range(dialog.pages.count()):
                dialog.pages.item(row).setSelected(True)
            dialog.remove_selected()
            self.assertEqual(dialog.pages.count(), 0)
            with patch("parin_ui.page_organizer.QMessageBox.warning") as warning:
                dialog.apply_changes()
            warning.assert_called_once()
            self.assertEqual(document.page_count, 2)
            self.assertEqual(viewer.undo_records, 0)
            self.assertEqual(viewer.structure_updates, 0)
        finally:
            dialog.close()
            viewer.close()
            document.close()

    def test_main_module_keeps_page_organizer_import_compatible(self):
        from parin_pdf_viewer import PageOrganizerDialog as MainPageOrganizerDialog
        from parin_ui.page_organizer import PageOrganizerDialog

        self.assertIs(MainPageOrganizerDialog, PageOrganizerDialog)


class SettingsDialogModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _resources(self):
        import parin_pdf_viewer as legacy
        from parin_ui.settings_dialog import SettingsDialogResources

        return SettingsDialogResources(
            settings_i18n=legacy.SETTINGS_I18N,
            color_themes=tuple(legacy.COLOR_THEMES),
            theme_accents=legacy.THEME_ACCENTS,
            theme_stylesheet=legacy._theme_stylesheet,
            app_version=legacy.APP_VERSION,
            about_attribution=legacy.ABOUT_ATTRIBUTION,
            make_app_icon=legacy.make_app_icon,
            card_frame=legacy.card_frame,
        )

    def _viewer(self):
        resources = self._resources()

        class SettingsViewer(QWidget):
            def __init__(self):
                super().__init__()
                self.current_lang = "en"
                self.app_settings = {
                    "appearance_mode": "light",
                    "theme": "Arctic Glass",
                    "accent": "Theme default",
                }
                self.language_changes = []
                self.apply_count = 0

            def apply_language(self, code):
                self.current_lang = code
                self.language_changes.append(code)

            def apply_app_settings(self):
                self.apply_count += 1

            def _settings_dialog_resources(self):
                return resources

        return SettingsViewer()

    def test_settings_dialog_uses_injected_resources_and_localizes(self):
        from parin_ui.settings_dialog import SettingsDialog

        viewer = self._viewer()
        dialog = SettingsDialog(viewer)
        try:
            self.assertIn("Parin", dialog.title.text())
            dialog._language_from_settings(1)
            self.assertEqual(viewer.language_changes, ["fa"])
            self.assertIn("پرین", dialog.title.text())
            self.assertEqual(dialog.lang, "fa")
        finally:
            dialog.close()
            viewer.close()

    def test_settings_dialog_collect_and_apply_preserve_preferences(self):
        from parin_ui.settings_dialog import SettingsDialog

        viewer = self._viewer()
        dialog = SettingsDialog(viewer, self._resources())
        try:
            dialog.appearance_mode.setCurrentIndex(1)
            dialog.remember_last.setChecked(False)
            dialog.volume.setValue(37)
            result = dialog.collect()
            self.assertEqual(result["appearance_mode"], "dark")
            self.assertFalse(result["remember_last"])
            self.assertEqual(result["volume"], 37)

            dialog.apply_changes()
            self.assertEqual(viewer.app_settings["appearance_mode"], "dark")
            self.assertFalse(viewer.app_settings["remember_last"])
            self.assertEqual(viewer.app_settings["volume"], 37)
            self.assertEqual(viewer.apply_count, 1)
        finally:
            dialog.close()
            viewer.close()

    def test_main_module_preserves_settings_dialog_import_compatibility(self):
        from parin_pdf_viewer import SettingsDialog as MainSettingsDialog
        from parin_ui.settings_dialog import SettingsDialog

        self.assertIs(MainSettingsDialog, SettingsDialog)



class SettingsLocalizationTests(unittest.TestCase):
    def test_settings_locales_include_farsi_and_german(self):
        from parin_ui.settings_i18n import SETTINGS_I18N

        self.assertIn("تنظیمات", SETTINGS_I18N["fa"]["title"])
        self.assertIn("Übersicht", SETTINGS_I18N["de"]["overview"])
        self.assertEqual(SETTINGS_I18N["fa"]["appearance_mode"], "حالت ظاهری")
        self.assertEqual(SETTINGS_I18N["en"]["appearance_mode"], "Appearance mode")

    def test_settings_labels_are_normalized_without_decorative_emoji(self):
        from parin_ui.settings_i18n import SETTINGS_I18N

        for language in SETTINGS_I18N.values():
            for value in language.values():
                self.assertNotRegex(value, r"[\U0001F300-\U0001FAFF]")
                self.assertEqual(value, " ".join(value.split()))

    def test_settings_localization_module_has_no_qt_dependency(self):
        from pathlib import Path

        source = Path("src/parin_ui/settings_i18n.py").read_text(encoding="utf-8")
        self.assertNotIn("PySide6", source)
        self.assertIn("SETTINGS_I18N", source)



class NavigationLocalizationTests(unittest.TestCase):
    def test_navigation_locales_share_required_labels(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N

        required = {
            "dock", "outline", "pages", "page", "nav_action",
            "recent", "no_recent", "clear_recent", "no_outline",
        }
        self.assertIn("fa", NAVIGATION_I18N)
        self.assertIn("de", NAVIGATION_I18N)
        for language, labels in NAVIGATION_I18N.items():
            with self.subTest(language=language):
                self.assertTrue(required.issubset(labels))

    def test_navigation_page_labels_preserve_page_number_placeholder(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N

        for language, labels in NAVIGATION_I18N.items():
            with self.subTest(language=language):
                self.assertIn("{n}", labels["page"])
                self.assertEqual(labels["page"].format(n=7).count("7"), 1)

    def test_navigation_localization_module_is_qt_independent(self):
        from pathlib import Path

        source = Path("src/parin_ui/navigation_i18n.py").read_text(encoding="utf-8")
        self.assertNotIn("PySide6", source)
        self.assertIn("NAVIGATION_I18N", source)



class NavigationPanelControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_viewer(self):
        import pymupdf as fitz
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMainWindow, QMenu

        class Viewer(QMainWindow):
            def __init__(self, document):
                super().__init__()
                self.doc = document
                self.current_page = 0
                self.current_lang = "en"
                self.visited_pages = []
                self.navigation_action = QAction("Navigation", self)
                self.recent_menu = QMenu(self)

            def _navigate_outline_item(self, item, column=0):
                page_index = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(page_index, int):
                    self.go_to_page(page_index + 1)

            def _navigate_page_list(self, row):
                if self.doc and 0 <= row < self.doc.page_count and row != self.current_page:
                    self.go_to_page(row + 1)

            def go_to_page(self, page_number):
                self.visited_pages.append(page_number)
                self.current_page = page_number - 1

        document = fitz.open()
        document.new_page().insert_text((72, 72), "First page")
        document.new_page().insert_text((72, 72), "Second page")
        document.set_toc([[1, "Chapter One", 1], [2, "Section Two", 2]])
        return Viewer(document), document

    def test_controller_builds_navigation_widgets_and_projects_pdf_outline(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N
        from parin_ui.navigation_panel import NavigationPanelController

        viewer, document = self._make_viewer()
        controller = NavigationPanelController(viewer, NAVIGATION_I18N)
        try:
            viewer.show()
            controller.dock.show()
            self.app.processEvents()
            controller.refresh()
            self.assertEqual(controller.page_list.count(), 2)
            self.assertEqual(controller.page_list.item(0).text(), "Page 1")
            self.assertEqual(controller.outline_tree.topLevelItemCount(), 1)
            chapter = controller.outline_tree.topLevelItem(0)
            self.assertEqual(chapter.text(0), "Chapter One")
            self.assertEqual(chapter.childCount(), 1)
        finally:
            viewer.close()
            document.close()

    def test_page_and_outline_selection_route_to_reader_navigation(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N
        from parin_ui.navigation_panel import NavigationPanelController

        viewer, document = self._make_viewer()
        controller = NavigationPanelController(viewer, NAVIGATION_I18N)
        try:
            viewer.show()
            controller.dock.show()
            self.app.processEvents()
            controller.refresh()
            controller.page_list.setCurrentRow(1)
            self.assertEqual(viewer.visited_pages, [2])
            chapter = controller.outline_tree.topLevelItem(0)
            section = chapter.child(0)
            controller.outline_tree.itemActivated.emit(section, 0)
            self.assertEqual(viewer.visited_pages[-1], 2)
        finally:
            viewer.close()
            document.close()

    def test_translation_and_current_page_sync_are_owned_by_controller(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N
        from parin_ui.navigation_panel import NavigationPanelController

        viewer, document = self._make_viewer()
        controller = NavigationPanelController(viewer, NAVIGATION_I18N)
        try:
            viewer.show()
            controller.dock.show()
            self.app.processEvents()
            controller.refresh()
            self.assertEqual(controller.nav_text("page", n=4), "Page 4")
            viewer.current_lang = "fa"
            controller.retranslate()
            self.assertEqual(controller.tabs.tabText(0), "فهرست")
            self.assertEqual(controller.nav_text("page", n=4), "صفحهٔ 4")

            viewer._navigation_needs_refresh = False
            viewer.current_page = 1
            controller.sync_current_page()
            self.assertEqual(controller.page_list.currentRow(), 1)
        finally:
            viewer.close()
            document.close()

    def test_visible_page_thumbnails_are_cached_with_a_bounded_lru(self):
        from parin_ui.navigation_i18n import NAVIGATION_I18N
        from parin_ui.navigation_panel import NavigationPanelController

        viewer, document = self._make_viewer()
        controller = NavigationPanelController(viewer, NAVIGATION_I18N)
        try:
            viewer.show()
            controller.dock.show()
            self.app.processEvents()
            controller.refresh()
            controller.load_visible_thumbnails()
            self.assertGreater(len(controller.thumbnail_cache), 0)
            self.assertLessEqual(len(controller.thumbnail_cache), 40)
        finally:
            viewer.close()
            document.close()



if __name__ == "__main__":
    unittest.main()
