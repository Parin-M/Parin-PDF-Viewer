import os
import unittest
from pathlib import Path

from parin_pdf_helpers import (
    APP_VERSION,
    add_recent_file,
    clamp_zoom,
    ensure_pdf_extension,
    normalize_recent_files,
    same_path,
)


class RecentFilesTests(unittest.TestCase):
    def test_newest_path_is_first_and_duplicates_are_removed(self):
        recent = normalize_recent_files(["docs/a.pdf", "docs/b.pdf", "docs/a.pdf"])
        self.assertEqual(recent[0], os.path.abspath("docs/a.pdf"))
        self.assertEqual(recent[1], os.path.abspath("docs/b.pdf"))
        self.assertEqual(len(recent), 2)

    def test_add_recent_moves_existing_path_to_front(self):
        first = os.path.abspath("one.pdf")
        second = os.path.abspath("two.pdf")
        self.assertEqual(add_recent_file([first, second], second), [second, first])

    def test_normalization_ignores_blank_values_and_limits_items(self):
        got = normalize_recent_files(["", None, "one.pdf", "two.pdf", "three.pdf"], limit=2)
        self.assertEqual(got, [os.path.abspath("one.pdf"), os.path.abspath("two.pdf")])

    def test_string_input_is_treated_as_one_path_not_characters(self):
        self.assertEqual(normalize_recent_files("single.pdf"), [os.path.abspath("single.pdf")])


class PdfPathTests(unittest.TestCase):
    def test_extension_is_added_when_missing(self):
        self.assertEqual(ensure_pdf_extension("report"), "report.pdf")

    def test_pdf_extension_is_case_insensitive(self):
        self.assertEqual(ensure_pdf_extension("report.PDF"), "report.PDF")

    def test_empty_path_is_rejected(self):
        with self.assertRaises(ValueError):
            ensure_pdf_extension("  ")

    def test_relative_and_absolute_paths_compare_equal(self):
        self.assertTrue(same_path("folder/../file.pdf", os.path.abspath("file.pdf")))


class ZoomTests(unittest.TestCase):
    def test_zoom_is_clamped_to_supported_bounds(self):
        self.assertEqual(clamp_zoom(-50), 0.1)
        self.assertEqual(clamp_zoom(99), 8.0)
        self.assertEqual(clamp_zoom(1.25), 1.25)

    def test_invalid_zoom_values_fall_back_to_one(self):
        self.assertEqual(clamp_zoom("not-a-number"), 1.0)
        self.assertEqual(clamp_zoom(float("nan")), 1.0)
        self.assertEqual(clamp_zoom(float("inf")), 1.0)


class VersionTests(unittest.TestCase):
    def test_version_is_890(self):
        self.assertEqual(APP_VERSION, "8.9.0")


if __name__ == "__main__":
    unittest.main()
