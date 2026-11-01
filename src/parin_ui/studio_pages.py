"""Honest landing states for workspaces that are not implemented yet."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


STUDIO_DETAILS = {
    "focus": (
        "Focus Studio",
        "A distraction-reduced reading mode with typography, spacing and focus controls.",
    ),
    "research": (
        "Research Studio",
        "A structured workspace for highlights, notes, references and document insights.",
    ),
    "compare": (
        "Compare Studio",
        "A side-by-side document workspace for reviewing two PDFs together.",
    ),
    "hub": (
        "Document Hub",
        "A central library for recent documents, collections and document organization.",
    ),
}


class StudioLanding(QWidget):
    """Clearly marked development state for a workspace awaiting implementation."""

    def __init__(self, workspace_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if workspace_id not in STUDIO_DETAILS:
            raise ValueError(f"Unknown future studio: {workspace_id}")
        title, description = STUDIO_DETAILS[workspace_id]
        self.workspace_id = workspace_id
        self.setObjectName(f"{workspace_id}_studio_landing")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        self.status = QLabel("IN DEVELOPMENT", self)
        self.status.setObjectName("studio_status")
        self.status.setProperty("role", "muted")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title = QLabel(title, self)
        self.title.setObjectName("studio_title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:20pt;font-weight:750;")
        layout.addWidget(self.title)

        self.description = QLabel(description, self)
        self.description.setObjectName("studio_description")
        self.description.setWordWrap(True)
        self.description.setMaximumWidth(560)
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description.setProperty("role", "muted")
        layout.addWidget(self.description, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        self.return_hint = QLabel("Your existing PDF remains open in Reader Studio.", self)
        self.return_hint.setProperty("role", "muted")
        self.return_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.return_hint)
        layout.addStretch(1)
