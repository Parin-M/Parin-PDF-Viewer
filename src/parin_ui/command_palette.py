"""Searchable command registry and compact Ctrl+K palette."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme_engine import ThemeEngine


CommandCallback = Callable[[], object]


@dataclass(frozen=True, slots=True)
class Command:
    command_id: str
    title: str
    category: str
    callback: CommandCallback = field(compare=False, repr=False)
    keywords: tuple[str, ...] = ()
    shortcut: str = ""


class CommandRegistry:
    """Stores commands and ranks results without coupling them to the UI."""

    def __init__(self, commands: Iterable[Command] = ()) -> None:
        self._commands: dict[str, Command] = {}
        for command in commands:
            self.register(command)

    def register(self, command: Command) -> None:
        if not command.command_id.strip():
            raise ValueError("A command id cannot be empty.")
        if command.command_id in self._commands:
            raise ValueError(f"Duplicate command id: {command.command_id}")
        self._commands[command.command_id] = command

    def unregister(self, command_id: str) -> None:
        self._commands.pop(command_id, None)

    def get(self, command_id: str) -> Command | None:
        return self._commands.get(command_id)

    def all_commands(self) -> tuple[Command, ...]:
        return tuple(self._commands.values())

    def search(self, query: str = "") -> tuple[Command, ...]:
        terms = tuple(part.casefold() for part in query.split() if part)
        if not terms:
            return self.all_commands()

        ranked: list[tuple[int, int, Command]] = []
        for index, command in enumerate(self._commands.values()):
            title = command.title.casefold()
            category = command.category.casefold()
            keywords = " ".join(command.keywords).casefold()
            searchable = " ".join((title, category, keywords, command.shortcut.casefold()))
            if not all(term in searchable for term in terms):
                continue

            score = 0
            if title.startswith(" ".join(terms)):
                score += 100
            elif all(term in title for term in terms):
                score += 60
            if all(term in category for term in terms):
                score += 20
            if all(term in keywords for term in terms):
                score += 10
            ranked.append((score, -index, command))

        ranked.sort(reverse=True, key=lambda item: (item[0], item[1]))
        return tuple(item[2] for item in ranked)


class CommandPaletteDialog(QDialog):
    """Keyboard-friendly command picker with live filtering."""

    def __init__(
        self,
        registry: CommandRegistry,
        theme: ThemeEngine | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.registry = registry
        self.theme = theme or ThemeEngine("dark")
        self.setObjectName("command_palette")
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.resize(620, 420)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(10)

        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("command_search")
        self.search_input.setPlaceholderText("Search commands…")
        self.search_input.setClearButtonEnabled(True)
        root.addWidget(self.search_input)

        self.results = QListWidget(self)
        self.results.setObjectName("command_results")
        self.results.setSpacing(2)
        root.addWidget(self.results, 1)

        footer = QHBoxLayout()
        self.hint = QLabel("↑ ↓ Navigate    Enter Run    Esc Close", self)
        self.hint.setProperty("role", "muted")
        footer.addWidget(self.hint)
        footer.addStretch(1)
        self.count_label = QLabel(self)
        self.count_label.setProperty("role", "muted")
        footer.addWidget(self.count_label)
        root.addLayout(footer)

        self.search_input.textChanged.connect(self._refresh_results)
        self.search_input.returnPressed.connect(self._run_current)
        self.results.itemActivated.connect(self._run_item)
        self.results.itemClicked.connect(self._select_item)
        self.theme.apply(self)
        self._refresh_results("")
        self.search_input.setFocus()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.search_input.setFocus()

    def _refresh_results(self, query: str) -> None:
        commands = self.registry.search(query)
        self.results.clear()
        for command in commands:
            label = command.title
            if command.shortcut:
                label = f"{label}    ·    {command.shortcut}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, command.command_id)
            item.setToolTip(f"{command.category} — {command.title}")
            self.results.addItem(item)
        self.count_label.setText(str(len(commands)))
        if self.results.count():
            self.results.setCurrentRow(0)

    def _select_item(self, item: QListWidgetItem) -> None:
        self.results.setCurrentItem(item)

    def _run_current(self) -> None:
        item = self.results.currentItem()
        if item is not None:
            self._run_item(item)

    def _run_item(self, item: QListWidgetItem) -> None:
        command = self.registry.get(item.data(Qt.ItemDataRole.UserRole))
        if command is None:
            return
        self.accept()
        command.callback()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.results.setFocus()
            super().keyPressEvent(event)
            return
        if self.results.hasFocus() and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self._run_current()
            return
        super().keyPressEvent(event)
