import unittest

from parin_handwriting_assist import SmartInkAssistant


class SmartInkAssistantTests(unittest.TestCase):
    def setUp(self):
        self.assistant = SmartInkAssistant(strength=0.45)

    def test_short_strokes_are_returned_unchanged(self):
        self.assertEqual(self.assistant.smooth_points([]), [])
        self.assertEqual(self.assistant.smooth_points([(2, 3)]), [(2.0, 3.0)])
        self.assertEqual(self.assistant.smooth_points([(2, 3), (4, 5)]), [(2.0, 3.0), (4.0, 5.0)])

    def test_endpoints_are_preserved(self):
        stroke = [(0, 0), (1, 1), (2, -1), (3, 1), (4, -1), (5, 0)]
        result = self.assistant.smooth_points(stroke)
        self.assertEqual(result[0], (0.0, 0.0))
        self.assertEqual(result[-1], (5.0, 0.0))
        self.assertEqual(len(result), len(stroke))

    def test_adaptive_filter_reduces_small_jitter(self):
        stroke = [(0, 0), (1, 1), (2, -1), (3, 1), (4, -1), (5, 0)]
        result = self.assistant.smooth_points(stroke)
        original_deviation = sum(abs(float(point[1])) for point in stroke[1:-1])
        filtered_deviation = sum(abs(point[1]) for point in result[1:-1])
        self.assertLess(filtered_deviation, original_deviation)

    def test_style_summary_handles_steady_and_expressive_strokes(self):
        steady = [(0, 0), (1, 0.02), (2, -0.01), (3, 0.01), (4, 0)]
        expressive = [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0)]
        self.assertEqual(self.assistant.describe_style(steady), "steady")
        self.assertEqual(self.assistant.describe_style(expressive), "expressive")


if __name__ == "__main__":
    unittest.main()
