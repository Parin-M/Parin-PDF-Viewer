"""Bounded snapshot history for PDF document undo and redo.

The history manager owns snapshot storage and state transitions only. The
application remains responsible for serializing its live PDF and restoring a
snapshot into the active reader UI.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Literal


HistoryOutcome = Literal["empty", "unavailable", "restored", "failed"]


class DocumentHistory:
    """Manage bounded undo/redo snapshots without owning a PDF document."""

    def __init__(
        self,
        max_snapshot_bytes: int = 16 * 1024 * 1024,
        max_undo_steps: int = 5,
    ) -> None:
        if max_snapshot_bytes < 1:
            raise ValueError("max_snapshot_bytes must be positive")
        if max_undo_steps < 1:
            raise ValueError("max_undo_steps must be positive")
        self.max_snapshot_bytes = int(max_snapshot_bytes)
        self.max_undo_steps = int(max_undo_steps)
        self.undo_stack: list[bytes] = []
        self.redo_stack: list[bytes] = []
        self.disabled = False

    @property
    def can_undo(self) -> bool:
        return not self.disabled and bool(self.undo_stack)

    @property
    def can_redo(self) -> bool:
        return not self.disabled and bool(self.redo_stack)

    def reset(self) -> None:
        """Clear all snapshots and re-enable history for a newly opened PDF."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.disabled = False

    def disable(self) -> None:
        """Disable history after an unsafe or unavailable snapshot."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.disabled = True

    def capture_snapshot(
        self,
        document,
        *,
        file_path: str | None = None,
        encrypted: bool = False,
        encryption_keep=None,
    ) -> bytes | None:
        """Serialize a bounded snapshot, preserving encryption when requested."""
        if self.disabled or document is None:
            return None
        try:
            if (
                file_path
                and os.path.isfile(file_path)
                and os.path.getsize(file_path) > self.max_snapshot_bytes
            ):
                return None
            options = {"garbage": 0, "deflate": True}
            if encrypted and encryption_keep is not None:
                options["encryption"] = encryption_keep
            snapshot = bytes(document.tobytes(**options))
            return (
                snapshot
                if 0 < len(snapshot) <= self.max_snapshot_bytes
                else None
            )
        except Exception:
            return None

    def record(self, snapshot: bytes | None) -> bool:
        """Push an undo checkpoint and invalidate the redo branch."""
        if self.disabled:
            return False
        if snapshot is None or len(snapshot) > self.max_snapshot_bytes:
            self.disable()
            return False
        self.undo_stack.append(bytes(snapshot))
        del self.undo_stack[:-self.max_undo_steps]
        self.redo_stack.clear()
        return True

    def undo(
        self,
        current_snapshot: bytes | None,
        restore: Callable[[bytes, str], bool],
    ) -> HistoryOutcome:
        """Restore the latest undo checkpoint and move current state to redo."""
        if self.disabled or not self.undo_stack:
            return "empty"
        if current_snapshot is None or len(current_snapshot) > self.max_snapshot_bytes:
            self.disable()
            return "unavailable"
        target = self.undo_stack[-1]
        try:
            restored = bool(restore(target, "Undo"))
        except Exception:
            restored = False
        if not restored:
            return "failed"
        self.undo_stack.pop()
        self.redo_stack.append(bytes(current_snapshot))
        return "restored"

    def redo(
        self,
        current_snapshot: bytes | None,
        restore: Callable[[bytes, str], bool],
    ) -> HistoryOutcome:
        """Restore the latest redo checkpoint and preserve the undo limit."""
        if self.disabled or not self.redo_stack:
            return "empty"
        if current_snapshot is None or len(current_snapshot) > self.max_snapshot_bytes:
            self.disable()
            return "unavailable"
        target = self.redo_stack[-1]
        try:
            restored = bool(restore(target, "Redo"))
        except Exception:
            restored = False
        if not restored:
            return "failed"
        self.redo_stack.pop()
        self.undo_stack.append(bytes(current_snapshot))
        del self.undo_stack[:-self.max_undo_steps]
        return "restored"


__all__ = ["DocumentHistory", "HistoryOutcome"]
