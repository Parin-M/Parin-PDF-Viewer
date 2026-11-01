import math
import unittest

from parin_ui.print_service import safe_print_scale


class SafePrintScaleTests(unittest.TestCase):
    def test_standard_page_uses_target_print_resolution(self):
        scale = safe_print_scale(595, 842)
        self.assertAlmostEqual(scale, 2.5)

    def test_oversized_page_is_bounded_by_pixel_and_edge_limits(self):
        scale = safe_print_scale(10_000, 10_000)
        self.assertLess(scale, 2.5)
        self.assertLessEqual(10_000 * scale, 12_000)
        self.assertLessEqual((10_000 * scale) ** 2, 16_000_000)

    def test_asymmetric_page_is_bounded_by_long_edge(self):
        scale = safe_print_scale(30_000, 1_000)
        self.assertLessEqual(30_000 * scale, 12_000)
        self.assertLessEqual(30_000 * 1_000 * scale * scale, 16_000_000)

    def test_invalid_dimensions_and_limits_are_rejected(self):
        for width, height in ((0, 10), (-1, 10), (math.inf, 10), (10, math.nan)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    safe_print_scale(width, height)
        with self.assertRaises(ValueError):
            safe_print_scale(10, 10, max_pixels=0)


if __name__ == "__main__":
    unittest.main()
