import unittest

import pymupdf as fitz

from parin_ui.annotation_service import (
    add_ink_annotation,
    add_text_annotation,
    erase_annotations_at_point,
)


class AnnotationServiceTests(unittest.TestCase):
    def setUp(self):
        self.document = fitz.open()
        self.page = self.document.new_page(width=300, height=400)

    def tearDown(self):
        self.document.close()

    def _annotations(self):
        return list(self.page.annots() or ())

    def test_adds_pen_ink_annotation_with_requested_color(self):
        annotation = add_ink_annotation(
            self.page,
            [(30, 30), (80, 70), (120, 60)],
            (0.2, 0.4, 0.8),
            tool="pen",
        )
        self.assertEqual(annotation.type[1], "Ink")
        self.assertEqual(len(self._annotations()), 1)
        for actual, expected in zip(annotation.colors["stroke"], (0.2, 0.4, 0.8)):
            self.assertAlmostEqual(actual, expected, places=6)
        self.assertAlmostEqual(annotation.border["width"], 2.0)

    def test_adds_highlighter_with_translucent_wide_stroke(self):
        annotation = add_ink_annotation(
            self.page,
            [(20, 100), (80, 100), (150, 100)],
            (1.0, 0.8, 0.1),
            tool="highlight",
        )
        self.assertEqual(annotation.type[1], "Ink")
        self.assertAlmostEqual(annotation.border["width"], 14.0)
        self.assertAlmostEqual(annotation.opacity, 0.35)

    def test_adds_text_annotation_and_clamps_it_to_page(self):
        annotation = add_text_annotation(
            self.page,
            "Parin annotation",
            (295, 395),
            font_size=14,
            font_name="helv",
            text_color=(0.1, 0.3, 0.5),
        )
        self.assertEqual(annotation.type[1], "FreeText")
        rect = annotation.rect
        self.assertGreaterEqual(rect.x0, self.page.rect.x0)
        self.assertGreaterEqual(rect.y0, self.page.rect.y0)
        self.assertLessEqual(rect.x1, self.page.rect.x1)
        self.assertLessEqual(rect.y1, self.page.rect.y1)
        self.assertEqual(annotation.info["content"], "Parin annotation")

    def test_text_annotation_accepts_point_tuple(self):
        annotation = add_text_annotation(self.page, "Tuple point", (15, 25))
        self.assertEqual(annotation.type[1], "FreeText")
        self.assertGreaterEqual(annotation.rect.x0, 15)

    def test_eraser_deletes_only_intersecting_annotations(self):
        close_annotation = self.page.add_rect_annot(fitz.Rect(40, 40, 70, 70))
        far_annotation = self.page.add_rect_annot(fitz.Rect(220, 300, 260, 340))
        close_xref = close_annotation.xref
        far_xref = far_annotation.xref
        removed = erase_annotations_at_point(
            self.page,
            fitz.Point(55, 55),
            zoom_factor=1.0,
        )
        remaining = self._annotations()
        self.assertEqual(removed, 1)
        self.assertEqual([annotation.xref for annotation in remaining], [far_xref])
        self.assertNotIn(close_xref, [annotation.xref for annotation in remaining])

    def test_eraser_radius_scales_with_zoom(self):
        self.page.add_rect_annot(fitz.Rect(30, 30, 35, 35))
        removed = erase_annotations_at_point(
            self.page,
            fitz.Point(0, 0),
            zoom_factor=2.0,
            base_radius=20,
        )
        self.assertEqual(removed, 0)
        self.assertEqual(len(self._annotations()), 1)

    def test_invalid_strokes_colors_and_tools_are_rejected(self):
        invalid_calls = (
            lambda: add_ink_annotation(self.page, [(1, 1)], (0, 0, 0)),
            lambda: add_ink_annotation(self.page, [(1, 1), (2, 2)], (0, 0, 2)),
            lambda: add_ink_annotation(self.page, [(1, 1), (2, 2)], (0, 0, 0), tool="eraser"),
        )
        for callback in invalid_calls:
            with self.subTest(callback=callback):
                with self.assertRaises(ValueError):
                    callback()
        self.assertEqual(len(self._annotations()), 0)

    def test_many_text_and_ink_annotations_can_be_saved_and_reopened(self):
        for index in range(120):
            y = 20 + (index % 20) * 18
            add_ink_annotation(
                self.page,
                [(10, y), (60, y + 2), (110, y)],
                (0.2, 0.5, 0.8),
                tool="highlight" if index % 2 else "pen",
            )
            add_text_annotation(
                self.page,
                f"Note {index}",
                (130, y),
                font_size=8,
            )

        snapshot = self.document.tobytes(deflate=True)
        reopened = fitz.open(stream=snapshot, filetype="pdf")
        try:
            reopened_page = reopened.load_page(0)
            annotation_types = [
                annotation.type[1]
                for annotation in (reopened_page.annots() or ())
            ]
            self.assertEqual(len(annotation_types), 240)
            self.assertEqual(annotation_types.count("FreeText"), 120)
        finally:
            reopened.close()

    def test_invalid_text_and_eraser_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            add_text_annotation(self.page, "  ", (10, 10))
        with self.assertRaises(ValueError):
            add_text_annotation(self.page, "Text", (10, 10), font_size=0)
        with self.assertRaises(ValueError):
            erase_annotations_at_point(self.page, (10, 10), zoom_factor=0)
        self.assertEqual(len(self._annotations()), 0)


if __name__ == "__main__":
    unittest.main()
