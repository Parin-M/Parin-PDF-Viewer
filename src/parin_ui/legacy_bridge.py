"""Command palette adapters for the current Parin PDF Viewer window."""

from __future__ import annotations

from .command_palette import Command, CommandRegistry


def build_legacy_command_registry(viewer: object) -> CommandRegistry:
    """Expose existing viewer operations to the v10 command palette.

    Missing optional methods are skipped, allowing the palette to remain safe
    while legacy functionality is moved into the v10 modules incrementally.
    """
    registry = CommandRegistry()

    def add_method(
        command_id: str,
        title: str,
        category: str,
        method_name: str,
        keywords: tuple[str, ...] = (),
        shortcut: str = "",
        args: tuple[object, ...] = (),
    ) -> None:
        method = getattr(viewer, method_name, None)
        if callable(method):
            registry.register(
                Command(
                    command_id=command_id,
                    title=title,
                    category=category,
                    callback=lambda method=method, args=args: method(*args),
                    keywords=keywords,
                    shortcut=shortcut,
                )
            )

    methods = (
        ("file.open", "Open PDF", "File", "open_file", ("open", "document"), "Ctrl+O"),
        ("file.save", "Save PDF", "File", "save_file", ("save", "document"), "Ctrl+S"),
        ("file.print", "Print document", "File", "print_document", ("print", "paper"), ""),
        ("document.find", "Find in document", "Document", "search_pdf", ("search", "find", "text"), "Ctrl+F"),
        ("document.organize", "Organize pages", "Document", "open_page_organizer", ("pages", "reorder", "organize"), ""),
        ("document.undo", "Undo", "Document", "undo_edit", ("history", "back"), "Ctrl+Z"),
        ("document.redo", "Redo", "Document", "redo_edit", ("history", "forward"), "Ctrl+Y"),
        ("view.zoom_in", "Zoom in", "View", "zoom_in", ("zoom", "larger"), "Ctrl++"),
        ("view.zoom_out", "Zoom out", "View", "zoom_out", ("zoom", "smaller"), "Ctrl+-"),
        ("view.fit_width", "Fit page width", "View", "fit_width", ("fit", "width"), "Ctrl+W"),
        ("view.fit_page", "Fit full page", "View", "fit_page", ("fit", "page"), "Ctrl+Shift+W"),
        ("view.reset_zoom", "Reset zoom to 100%", "View", "reset_zoom", ("zoom", "actual size"), "Ctrl+0"),
        ("view.fullscreen", "Toggle fullscreen", "View", "toggle_fullscreen", ("screen", "presentation"), "F11"),
        ("navigation.previous", "Previous page", "Navigation", "prev_page", ("page", "back"), "Left"),
        ("navigation.next", "Next page", "Navigation", "next_page", ("page", "forward"), "Right"),
        ("navigation.panel", "Toggle page navigation", "Navigation", "toggle_navigation_panel", ("outline", "thumbnails"), ""),
        ("settings.open", "Open settings", "Settings", "open_settings", ("preferences", "appearance"), ""),
        ("security.add_password", "Protect PDF with password", "Security", "add_password", ("password", "encrypt", "protect"), ""),
        ("security.remove_password", "Remove PDF password", "Security", "remove_password", ("password", "unlock"), ""),
    )
    for command_id, title, category, method_name, keywords, shortcut in methods:
        add_method(command_id, title, category, method_name, keywords, shortcut)

    for tool, title, keywords in (
        ("pen", "Toggle pen tool", ("annotate", "draw", "ink")),
        ("highlight", "Toggle highlighter", ("annotate", "mark", "color")),
        ("eraser", "Toggle eraser", ("annotate", "remove", "ink")),
        ("text", "Add text annotation", ("annotate", "type", "note")),
    ):
        toggle = getattr(viewer, "toggle_tool", None)
        if callable(toggle):
            registry.register(
                Command(
                    f"annotation.{tool}",
                    title,
                    "Annotation",
                    lambda toggle=toggle, tool=tool: toggle(tool),
                    keywords,
                )
            )

    rotate = getattr(viewer, "rotate", None)
    if callable(rotate):
        registry.register(
            Command("view.rotate_left", "Rotate left", "View",
                    lambda: rotate(-90), ("rotate", "orientation", "counterclockwise"))
        )
        registry.register(
            Command("view.rotate_right", "Rotate right", "View",
                    lambda: rotate(90), ("rotate", "orientation", "clockwise"))
        )

    return registry
