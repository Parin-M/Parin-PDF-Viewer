"""Private, local persistence for per-PDF research notes and references."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ResearchStoreError(RuntimeError):
    """Raised when research data cannot be read or safely persisted."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_document_path(document_path: str | os.PathLike[str]) -> str:
    raw = os.fspath(document_path).strip()
    if not raw:
        raise ValueError("A document path is required for research notes.")
    return os.path.normcase(os.path.realpath(os.path.abspath(os.path.expanduser(raw))))


class ResearchStore:
    """Stores notes in one atomic JSON file per local PDF document.

    No document bytes or note contents are uploaded. The caller supplies the
    application's private data directory; this class never guesses a path.
    """

    SCHEMA_VERSION = 1
    MAX_NOTE_LENGTH = 20_000

    def __init__(self, storage_directory: str | os.PathLike[str]) -> None:
        self.storage_directory = Path(storage_directory).expanduser()
        try:
            self.storage_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ResearchStoreError(f"Cannot create research storage: {exc}") from exc

    def path_for_document(self, document_path: str | os.PathLike[str]) -> Path:
        canonical = canonical_document_path(document_path)
        key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self.storage_directory / f"{key}.json"

    def _read(self, document_path: str | os.PathLike[str]) -> dict[str, Any]:
        canonical = canonical_document_path(document_path)
        path = self.path_for_document(canonical)
        if not path.exists():
            return {
                "version": self.SCHEMA_VERSION,
                "document": canonical,
                "notes": [],
            }
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ResearchStoreError(f"Cannot read research notes: {exc}") from exc
        if not isinstance(payload, dict) or payload.get("version") != self.SCHEMA_VERSION:
            raise ResearchStoreError("Research notes have an unsupported format.")
        if payload.get("document") != canonical or not isinstance(payload.get("notes"), list):
            raise ResearchStoreError("Research notes do not match this PDF document.")
        valid_notes = []
        for note in payload["notes"]:
            if not isinstance(note, dict):
                continue
            note_id = note.get("id")
            page = note.get("page")
            text = note.get("text")
            if (
                isinstance(note_id, str)
                and isinstance(page, int)
                and page >= 1
                and isinstance(text, str)
            ):
                valid_notes.append({
                    "id": note_id,
                    "page": page,
                    "text": text[: self.MAX_NOTE_LENGTH],
                    "created_at": str(note.get("created_at", "")),
                    "updated_at": str(note.get("updated_at", "")),
                })
        return {
            "version": self.SCHEMA_VERSION,
            "document": canonical,
            "notes": valid_notes,
        }

    def _write(self, document_path: str | os.PathLike[str], payload: dict[str, Any]) -> None:
        path = self.path_for_document(document_path)
        temporary_path: str | None = None
        try:
            fd, temporary_path = tempfile.mkstemp(
                prefix=".research-", suffix=".tmp", dir=self.storage_directory
            )
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
        except (OSError, TypeError, ValueError) as exc:
            raise ResearchStoreError(f"Cannot save research notes: {exc}") from exc
        finally:
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass

    def list_notes(self, document_path: str | os.PathLike[str]) -> list[dict[str, Any]]:
        payload = self._read(document_path)
        notes = [dict(note) for note in payload["notes"]]
        notes.sort(key=lambda note: (note["updated_at"], note["created_at"]), reverse=True)
        return notes

    def add_note(
        self,
        document_path: str | os.PathLike[str],
        page: int,
        text: str,
    ) -> dict[str, Any]:
        if type(page) is not int or page < 1:
            raise ValueError("Page number must be a positive integer.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("A research note cannot be empty.")
        if len(text) > self.MAX_NOTE_LENGTH:
            raise ValueError(f"Research notes are limited to {self.MAX_NOTE_LENGTH} characters.")
        payload = self._read(document_path)
        now = _timestamp()
        note = {
            "id": uuid.uuid4().hex,
            "page": page,
            "text": text.strip(),
            "created_at": now,
            "updated_at": now,
        }
        payload["notes"].append(note)
        self._write(document_path, payload)
        return dict(note)

    def update_note(
        self,
        document_path: str | os.PathLike[str],
        note_id: str,
        page: int,
        text: str,
    ) -> dict[str, Any]:
        if type(page) is not int or page < 1:
            raise ValueError("Page number must be a positive integer.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("A research note cannot be empty.")
        if len(text) > self.MAX_NOTE_LENGTH:
            raise ValueError(f"Research notes are limited to {self.MAX_NOTE_LENGTH} characters.")
        payload = self._read(document_path)
        for note in payload["notes"]:
            if note["id"] == note_id:
                note["page"] = page
                note["text"] = text.strip()
                note["updated_at"] = _timestamp()
                self._write(document_path, payload)
                return dict(note)
        raise KeyError(f"Research note not found: {note_id}")

    def delete_note(
        self,
        document_path: str | os.PathLike[str],
        note_id: str,
    ) -> bool:
        payload = self._read(document_path)
        remaining = [note for note in payload["notes"] if note["id"] != note_id]
        if len(remaining) == len(payload["notes"]):
            return False
        payload["notes"] = remaining
        self._write(document_path, payload)
        return True

    def copy_document_notes(
        self,
        source_path: str | os.PathLike[str],
        destination_path: str | os.PathLike[str],
    ) -> int:
        """Copy sidecar notes on Save As while retaining the source document's notes."""
        source = canonical_document_path(source_path)
        destination = canonical_document_path(destination_path)
        if source == destination:
            return len(self.list_notes(source))
        payload = self._read(source)
        copied = {
            "version": self.SCHEMA_VERSION,
            "document": destination,
            "notes": [dict(note) for note in payload["notes"]],
        }
        self._write(destination, copied)
        return len(copied["notes"])


def extract_pdf_highlights(document: object | None) -> list[dict[str, Any]]:
    """Collect PDF text highlights and Parin's translucent ink-highlighter strokes."""
    if document is None or getattr(document, "is_closed", False):
        return []
    results: list[dict[str, Any]] = []
    try:
        page_count = int(getattr(document, "page_count", 0) or 0)
    except (TypeError, ValueError):
        return []
    for page_index in range(max(0, page_count)):
        try:
            page = document.load_page(page_index)
            annotations = page.annots()
            if annotations is None:
                continue
            for annot in annotations:
                try:
                    annot_type = str((getattr(annot, "type", (0, "Annotation")) or (0, "Annotation"))[1])
                    type_key = annot_type.casefold()
                    opacity = float(getattr(annot, "opacity", 1.0) or 1.0)
                    is_markup_highlight = "highlight" in type_key
                    is_parin_highlighter = type_key == "ink" and opacity <= 0.55
                    if not (is_markup_highlight or is_parin_highlighter):
                        continue
                    info = getattr(annot, "info", None) or {}
                    rect = getattr(annot, "rect", None)
                    excerpt = ""
                    if rect is not None:
                        try:
                            excerpt = " ".join(page.get_textbox(rect).split())[:240]
                        except Exception:
                            pass
                    results.append({
                        "page": page_index + 1,
                        "type": annot_type,
                        "content": str(info.get("content") or ""),
                        "author": str(info.get("title") or ""),
                        "excerpt": excerpt,
                    })
                except Exception:
                    continue
        except Exception:
            continue
    return results
