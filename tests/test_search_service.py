import unittest

import pymupdf as fitz

from parin_ui.search_service import SearchMatch, find_next_match


class SearchServiceTests(unittest.TestCase):
    def setUp(self):
        self.document = fitz.open()

    def tearDown(self):
        self.document.close()

    def _add_page(self, lines):
        page = self.document.new_page(width=400, height=500)
        for index, line in enumerate(lines):
            page.insert_text((40, 50 + index * 35), line)
        return page

    def test_finds_match_on_a_later_page(self):
        self._add_page(["First page has no target"])
        self._add_page(["The target phrase is here"])

        match = find_next_match(self.document, "target phrase", start_page=0)

        self.assertIsInstance(match, SearchMatch)
        self.assertEqual(match.page_index, 1)
        self.assertEqual(match.match_index, 0)
        self.assertEqual(match.page_match_count, 1)
        self.assertEqual(len(match.rect), 4)
        self.assertGreater(match.rect[2], match.rect[0])

    def test_advances_through_multiple_matches_on_the_same_page(self):
        self._add_page([
            "Parin search service",
            "Another Parin search service result",
            "A final Parin search service result",
        ])

        first = find_next_match(self.document, "Parin search service")
        second = find_next_match(
            self.document,
            "Parin search service",
            start_page=first.page_index,
            start_match_index=first.match_index + 1,
        )
        third = find_next_match(
            self.document,
            "Parin search service",
            start_page=second.page_index,
            start_match_index=second.match_index + 1,
        )

        self.assertEqual(first.page_index, 0)
        self.assertEqual(second.match_index, 1)
        self.assertEqual(third.match_index, 2)
        self.assertEqual(first.page_match_count, 3)
        self.assertLess(first.rect[1], second.rect[1])
        self.assertLess(second.rect[1], third.rect[1])

    def test_search_is_case_insensitive(self):
        self._add_page(["Parin PDF Viewer"])

        match = find_next_match(self.document, "parin pdf viewer")

        self.assertIsNotNone(match)
        self.assertEqual(match.page_index, 0)

    def test_wraps_to_earlier_pages(self):
        self._add_page(["The target is on page one"])
        self._add_page(["No match on this page"])

        match = find_next_match(self.document, "target", start_page=1)

        self.assertIsNotNone(match)
        self.assertEqual(match.page_index, 0)

    def test_returns_none_for_empty_query_or_no_match(self):
        self._add_page(["Some unrelated text"])

        self.assertIsNone(find_next_match(self.document, "   "))
        self.assertIsNone(find_next_match(self.document, "missing phrase"))

    def test_returns_none_for_an_empty_document(self):
        self.assertIsNone(find_next_match(self.document, "anything"))

    def test_rejects_invalid_start_positions(self):
        self._add_page(["Content"])

        for start_page in (-1, 1, True, 0.5):
            with self.subTest(start_page=start_page):
                with self.assertRaises(ValueError):
                    find_next_match(self.document, "Content", start_page=start_page)

        for start_match_index in (-1, True, 1.5):
            with self.subTest(start_match_index=start_match_index):
                with self.assertRaises(ValueError):
                    find_next_match(
                        self.document,
                        "Content",
                        start_match_index=start_match_index,
                    )

    def test_rejects_non_string_query(self):
        self._add_page(["Content"])

        with self.assertRaises(TypeError):
            find_next_match(self.document, None)
