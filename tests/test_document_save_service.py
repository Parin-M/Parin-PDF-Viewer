import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from parin_ui.document_save_service import save_pdf_document


class DocumentSaveServiceTests(unittest.TestCase):
    @staticmethod
    def _make_document(page_count=3):
        document = fitz.open()
        for index in range(page_count):
            page = document.new_page()
            page.insert_text((72, 72), f"Original page {index + 1}")
        return document

    def test_saves_validated_output_and_keeps_source_open(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "saved.pdf"
            source = self._make_document()
            try:
                saved = save_pdf_document(source, target, page_index=1)
                try:
                    self.assertTrue(target.is_file())
                    self.assertEqual(saved.file_path, str(target))
                    self.assertEqual(saved.page_index, 1)
                    self.assertEqual(saved.document.page_count, 3)
                    self.assertIn("Original page 2", saved.document.load_page(1).get_text())
                    self.assertFalse(source.is_closed)
                finally:
                    saved.document.close()
            finally:
                source.close()

    def test_page_index_is_clamped_to_available_range(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._make_document(2)
            try:
                saved = save_pdf_document(source, Path(folder) / "clamped.pdf", page_index=99)
                try:
                    self.assertEqual(saved.page_index, 1)
                finally:
                    saved.document.close()
            finally:
                source.close()

    def test_preserves_encryption_with_empty_user_password(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "encrypted-source.pdf"
            target = Path(folder) / "encrypted-copy.pdf"
            source = self._make_document(1)
            source.save(
                str(source_path),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner-secret",
                user_pw="",
            )
            source.close()
            source = fitz.open(str(source_path))
            self.assertGreater(source.authenticate(""), 0)
            try:
                saved = save_pdf_document(source, target, encrypted=True, source_password="")
                try:
                    self.assertTrue(saved.encrypted)
                    self.assertEqual(saved.password, "")
                    self.assertTrue(saved.document.authenticate("") > 0)
                    self.assertTrue((saved.document.metadata or {}).get("encryption"))
                finally:
                    saved.document.close()
            finally:
                source.close()

    def test_explicit_options_can_remove_encryption(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "encrypted-source.pdf"
            target = Path(folder) / "unlocked.pdf"
            source = self._make_document(1)
            source.save(
                str(source_path),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner-secret",
                user_pw="reader-secret",
            )
            source.close()
            source = fitz.open(str(source_path))
            self.assertGreater(source.authenticate("reader-secret"), 0)
            try:
                saved = save_pdf_document(
                    source,
                    target,
                    encrypted=True,
                    source_password="reader-secret",
                    password_after="",
                    save_options={"encryption": fitz.PDF_ENCRYPT_NONE},
                )
                try:
                    self.assertFalse(saved.encrypted)
                    self.assertEqual(saved.password, "")
                    self.assertFalse((saved.document.metadata or {}).get("encryption"))
                    self.assertEqual(saved.document.page_count, 1)
                finally:
                    saved.document.close()
            finally:
                source.close()

    def test_explicit_options_can_add_a_password(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._make_document(1)
            target = Path(folder) / "protected.pdf"
            try:
                saved = save_pdf_document(
                    source,
                    target,
                    save_options={
                        "encryption": fitz.PDF_ENCRYPT_AES_256,
                        "user_pw": "new-reader-password",
                        "owner_pw": "new-owner-password",
                    },
                    password_after="new-reader-password",
                )
                try:
                    self.assertTrue(saved.encrypted)
                    self.assertEqual(saved.password, "new-reader-password")
                    self.assertGreater(saved.document.authenticate("new-reader-password"), 0)
                finally:
                    saved.document.close()
            finally:
                source.close()

    def test_failed_replacement_preserves_existing_target_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "existing.pdf"
            target.write_bytes(b"original destination bytes")
            source = self._make_document(1)
            try:
                with patch("parin_ui.document_save_service.os.replace", side_effect=OSError("replace denied")):
                    with self.assertRaises(OSError):
                        save_pdf_document(source, target)
                self.assertEqual(target.read_bytes(), b"original destination bytes")
                self.assertFalse(source.is_closed)
                self.assertEqual(
                    sorted(path.name for path in Path(folder).iterdir()),
                    ["existing.pdf"],
                )
            finally:
                source.close()

    def test_missing_output_directory_fails_without_closing_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._make_document(1)
            missing_target = Path(folder) / "missing" / "output.pdf"
            try:
                with self.assertRaises(FileNotFoundError):
                    save_pdf_document(source, missing_target)
                self.assertFalse(source.is_closed)
            finally:
                source.close()

    def test_closed_source_is_rejected(self):
        source = self._make_document(1)
        source.close()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                save_pdf_document(source, Path(folder) / "closed.pdf")


if __name__ == "__main__":
    unittest.main()
