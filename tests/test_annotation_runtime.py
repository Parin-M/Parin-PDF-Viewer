import unittest

from parin_ui.annotation_runtime import (
    MAX_PREVIEW_POINTS,
    MAX_STROKE_POINTS,
    PageRenderCache,
    append_stroke_sample,
    preview_stroke_points,
)


class StrokeBufferTests(unittest.TestCase):
    def test_appends_pdf_and_view_points_in_lockstep(self):
        pdf_points = [(0.0, 0.0)]
        view_points = [(0.0, 0.0)]

        added = append_stroke_sample(
            pdf_points, view_points, (3, 4), (3, 4)
        )

        self.assertTrue(added)
        self.assertEqual(len(pdf_points), 2)
        self.assertEqual(len(view_points), 2)

    def test_drops_near_duplicate_samples(self):
        pdf_points = [(0.0, 0.0)]
        view_points = [(10.0, 10.0)]

        added = append_stroke_sample(
            pdf_points, view_points, (0.2, 0.2), (10.5, 10.5)
        )

        self.assertFalse(added)
        self.assertEqual(len(pdf_points), 1)
        self.assertEqual(len(view_points), 1)

    def test_long_stroke_compaction_preserves_endpoints_and_alignment(self):
        pdf_points = [(0.0, 0.0)]
        view_points = [(0.0, 0.0)]
        for index in range(1, 100_001):
            append_stroke_sample(
                pdf_points,
                view_points,
                (index, index * 0.5),
                (index * 2, index),
                minimum_distance_px=0,
            )

        self.assertLessEqual(len(pdf_points), MAX_STROKE_POINTS)
        self.assertEqual(len(pdf_points), len(view_points))
        self.assertEqual(pdf_points[0], (0.0, 0.0))
        self.assertEqual(pdf_points[-1], (100_000.0, 50_000.0))
        self.assertEqual(view_points[-1], (200_000.0, 100_000.0))

    def test_preview_is_bounded_and_keeps_endpoints(self):
        points = [(float(index), float(index * 2)) for index in range(20_000)]

        preview = preview_stroke_points(points)

        self.assertLessEqual(len(preview), MAX_PREVIEW_POINTS)
        self.assertEqual(preview[0], points[0])
        self.assertEqual(preview[-1], points[-1])

    def test_invalid_buffers_and_points_are_rejected(self):
        with self.assertRaises(ValueError):
            append_stroke_sample([], [(0, 0)], (1, 1), (1, 1))
        with self.assertRaises(ValueError):
            append_stroke_sample([(0, 0)], [(0, 0)], (float("nan"), 1), (1, 1))


class PageRenderCacheTests(unittest.TestCase):
    def test_cache_hits_promote_entries_to_most_recent(self):
        cache = PageRenderCache(max_bytes=10)
        first, second, third = object(), object(), object()
        cache.put(("doc", 0, 1.0, 0, 0), first, 4)
        cache.put(("doc", 1, 1.0, 0, 0), second, 4)
        self.assertIs(cache.get(("doc", 0, 1.0, 0, 0)), first)
        cache.put(("doc", 2, 1.0, 0, 0), third, 4)

        self.assertIsNone(cache.get(("doc", 1, 1.0, 0, 0)))
        self.assertIs(cache.get(("doc", 0, 1.0, 0, 0)), first)
        self.assertIs(cache.get(("doc", 2, 1.0, 0, 0)), third)
        self.assertEqual(cache.current_bytes, 8)

    def test_cache_never_exceeds_byte_budget(self):
        cache = PageRenderCache(max_bytes=8)
        cache.put(("doc", 0), object(), 8)
        self.assertFalse(cache.put(("doc", 1), object(), 9))
        self.assertLessEqual(cache.current_bytes, cache.max_bytes)
        self.assertEqual(len(cache), 1)
        self.assertIsNotNone(cache.get(("doc", 0)))

    def test_invalidating_a_page_is_scoped_to_document(self):
        cache = PageRenderCache(max_bytes=20)
        left = object()
        right = object()
        cache.put(("left", 3, 1.0), left, 4)
        cache.put(("right", 3, 1.0), right, 4)

        removed = cache.invalidate_page(3, document_token="left")

        self.assertEqual(removed, 1)
        self.assertIsNone(cache.get(("left", 3, 1.0)))
        self.assertIs(cache.get(("right", 3, 1.0)), right)

    def test_clear_releases_all_cached_bytes(self):
        cache = PageRenderCache(max_bytes=20)
        cache.put(("doc", 0), object(), 7)
        cache.clear()
        self.assertEqual(len(cache), 0)
        self.assertEqual(cache.current_bytes, 0)


if __name__ == "__main__":
    unittest.main()
