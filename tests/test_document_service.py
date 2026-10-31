import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from parin_ui.document_service import (
    IncorrectPasswordError,
    PasswordRequiredError,
    is_document_encrypted,
    open_pdf_document,
    preflight_pdf_page,
)


class DocumentServiceTests(unittest.TestCase):
    @staticmethod
    def _make_pdf(path, *, password=None):
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Parin document service")
        options = {}
        if password is not None:
            options.update(
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner-secret",
                user_pw=password,
            )
        document.save(str(path), **options)
        document.close()

    def test_opens_and_preflights_a_valid_pdf(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "valid.pdf"
            self._make_pdf(path)
            opened = open_pdf_document(path)
            try:
                self.assertEqual(opened.file_path, str(path))
                self.assertEqual(opened.file_size, path.stat().st_size)
                self.assertEqual(opened.document.page_count, 1)
                self.assertFalse(opened.encrypted)
                self.assertEqual(opened.password, "")
            finally:
                opened.document.close()

    def test_missing_file_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.pdf"
            with self.assertRaises(FileNotFoundError):
                open_pdf_document(missing)

    def test_malformed_pdf_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.pdf"
            path.write_bytes(b"not a PDF document")
            with self.assertRaises(Exception):
                open_pdf_document(path)

    def test_encrypted_pdf_requests_password_and_closes_failed_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "locked.pdf"
            self._make_pdf(path, password="reader-secret")
            with self.assertRaises(PasswordRequiredError):
                open_pdf_document(path)
            with self.assertRaises(IncorrectPasswordError):
                open_pdf_document(path, password="wrong-password")

            opened = open_pdf_document(path, password="reader-secret")
            try:
                self.assertTrue(opened.encrypted)
                self.assertEqual(opened.password, "reader-secret")
                self.assertEqual(opened.document.page_count, 1)
            finally:
                opened.document.close()

    def test_encrypted_pdf_with_empty_user_password_opens_without_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty-user-password.pdf"
            self._make_pdf(path, password="")
            opened = open_pdf_document(path)
            try:
                self.assertTrue(opened.encrypted)
                self.assertEqual(opened.password, "")
                self.assertTrue(is_document_encrypted(opened.document))
                self.assertEqual(opened.document.page_count, 1)
            finally:
                opened.document.close()

    def test_preflight_rejects_page_outside_document(self):
        document = fitz.open()
        document.new_page()
        try:
            with self.assertRaises(ValueError):
                preflight_pdf_page(document, 1)
        finally:
            document.close()

    def test_candidate_is_closed_when_preflight_fails(self):
        class FakeDocument:
            page_count = 1
            is_closed = False
            metadata = {"encryption": None}
            is_encrypted = False

            def load_page(self, index):
                raise RuntimeError("broken page")

            def close(self):
                self.is_closed = True

        fake = FakeDocument()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "candidate.pdf"
            path.write_bytes(b"placeholder")
            with patch("parin_ui.document_service.fitz.open", return_value=fake):
                with self.assertRaises(RuntimeError):
                    open_pdf_document(path)
        self.assertTrue(fake.is_closed)


if __name__ == "__main__":
    unittest.main()
