import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

from parin_ui.page_operations import (
    apply_page_edit_plan,
    create_page_edit_candidate,
    create_page_edit_plan,
    extract_pdf_pages,
    insert_pdf_pages,
)


class PageOperationsTests(unittest.TestCase):
    @staticmethod
    def _make_document(labels):
        document = fitz.open()
        for label in labels:
            page = document.new_page()
            page.insert_text((72, 72), label)
        return document

    def test_plan_reorders_removes_and_rotates_selected_pages(self):
        document = self._make_document(["Page Alpha", "Page Beta", "Page Gamma"])
        try:
            plan = create_page_edit_plan(
                document.page_count,
                [2, 0],
                {0: 90, 1: 180, 2: 270},
            )
            self.assertTrue(plan.has_changes)
            self.assertEqual(plan.order, (2, 0))
            self.assertEqual(plan.rotations, ((0, 90), (2, 270)))
            apply_page_edit_plan(document, plan)

            self.assertEqual(document.page_count, 2)
            self.assertIn("Page Gamma", document.load_page(0).get_text())
            self.assertIn("Page Alpha", document.load_page(1).get_text())
            self.assertEqual(document.load_page(0).rotation, 270)
            self.assertEqual(document.load_page(1).rotation, 90)
        finally:
            document.close()

    def test_noop_plan_has_no_changes(self):
        plan = create_page_edit_plan(3, [0, 1, 2], {})
        self.assertFalse(plan.has_changes)

    def test_rejects_empty_duplicate_and_out_of_range_orders(self):
        for order in ([], [0, 0], [0, 2], [-1]):
            with self.subTest(order=order):
                with self.assertRaises(ValueError):
                    create_page_edit_plan(2, order)

    def test_rejects_invalid_rotation_delta(self):
        with self.assertRaises(ValueError):
            create_page_edit_plan(2, [0, 1], {0: 45})

    def test_rejects_plan_for_a_different_document_size_before_mutation(self):
        document = self._make_document(["One", "Two"])
        try:
            plan = create_page_edit_plan(3, [2, 0])
            with self.assertRaises(ValueError):
                apply_page_edit_plan(document, plan)
            self.assertEqual(document.page_count, 2)
            self.assertIn("One", document.load_page(0).get_text())
        finally:
            document.close()

    def test_page_edit_candidate_isolated_from_live_document(self):
        document = self._make_document(["First", "Second", "Third"])
        candidate = None
        try:
            plan = create_page_edit_plan(3, [2, 0])
            candidate = create_page_edit_candidate(document, plan)
            self.assertEqual(document.page_count, 3)
            self.assertIn("First", document.load_page(0).get_text())
            self.assertEqual(candidate.page_count, 2)
            self.assertIn("Third", candidate.load_page(0).get_text())
            self.assertIn("First", candidate.load_page(1).get_text())
        finally:
            if candidate is not None:
                candidate.close()
            document.close()

    def test_encrypted_page_edit_candidate_preserves_encryption(self):
        document = fitz.open()
        document.new_page()
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "encrypted-source.pdf"
            document.save(
                str(source_path),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner-secret",
                user_pw="",
            )
            document.close()
            source = fitz.open(str(source_path))
            if getattr(source, "needs_pass", False):
                self.assertGreater(source.authenticate(""), 0)
            candidate = None
            try:
                plan = create_page_edit_plan(source.page_count, [0])
                candidate = create_page_edit_candidate(source, plan, password="")
                encryption = (candidate.metadata or {}).get("encryption")
                self.assertTrue(
                    encryption and str(encryption).strip().lower() not in ("none", "null")
                )
                self.assertGreater(candidate.authenticate(""), 0)
            finally:
                if candidate is not None:
                    candidate.close()
                source.close()

    def test_inserts_source_pdf_at_the_requested_position(self):
        target = self._make_document(["Target one", "Target two"])
        source = self._make_document(["Inserted one", "Inserted two"])
        try:
            count = insert_pdf_pages(target, source, start_at=1)
            self.assertEqual(count, 2)
            self.assertEqual(target.page_count, 4)
            texts = [target.load_page(i).get_text() for i in range(target.page_count)]
            self.assertIn("Target one", texts[0])
            self.assertIn("Inserted one", texts[1])
            self.assertIn("Inserted two", texts[2])
            self.assertIn("Target two", texts[3])
        finally:
            target.close()
            source.close()

    def test_rejects_invalid_insertion_position_without_mutation(self):
        target = self._make_document(["Destination"])
        source = self._make_document(["Source"])
        try:
            with self.assertRaises(ValueError):
                insert_pdf_pages(target, source, start_at=2)
            self.assertEqual(target.page_count, 1)
            self.assertEqual(source.page_count, 1)
        finally:
            target.close()
            source.close()

    def test_extracts_pages_in_requested_order_through_atomic_save(self):
        source = self._make_document(["Extract first", "Skip this", "Extract last"])
        try:
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / "selected-pages.pdf"
                result = extract_pdf_pages(source, [2, 0], target)
                self.assertEqual(result.file_path, str(target))
                self.assertEqual(result.page_count, 2)
                extracted = fitz.open(str(target))
                try:
                    self.assertEqual(extracted.page_count, 2)
                    self.assertIn("Extract last", extracted.load_page(0).get_text())
                    self.assertIn("Extract first", extracted.load_page(1).get_text())
                finally:
                    extracted.close()
                self.assertEqual(source.page_count, 3)
        finally:
            source.close()

    def test_extraction_rejects_duplicate_or_invalid_pages_without_output(self):
        source = self._make_document(["One", "Two"])
        try:
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / "not-created.pdf"
                for indexes in ([0, 0], [2], []):
                    with self.subTest(indexes=indexes):
                        with self.assertRaises(ValueError):
                            extract_pdf_pages(source, indexes, target)
                self.assertFalse(target.exists())
        finally:
            source.close()


if __name__ == "__main__":
    unittest.main()
