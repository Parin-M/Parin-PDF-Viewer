"""Tiny offline assistant for stabilizing handwritten PDF ink.

This deliberately does not pretend to perform handwriting-to-text OCR. It
uses the geometry of the current stroke to reduce small jitter while retaining
the stroke's endpoints and stronger direction changes. It has no cloud calls
or model download and can be replaced by a trained local recognizer later.
"""
from __future__ import annotations

from math import hypot
from typing import Iterable, Sequence

Point = tuple[float, float]


class SmartInkAssistant:
    """Adaptive, low-cost smoothing for stylus/mouse input in PDF coordinates."""

    def __init__(self, strength: float = 0.38) -> None:
        self.strength = max(0.0, min(0.75, float(strength)))

    @staticmethod
    def _point(value: Sequence[float]) -> Point:
        if len(value) < 2:
            raise ValueError("A stroke point must contain x and y.")
        return float(value[0]), float(value[1])

    def smooth_points(self, points: Iterable[Sequence[float]]) -> list[Point]:
        """Return adaptive smoothed points while preserving both endpoints."""
        source = [self._point(point) for point in points]
        if len(source) < 3 or self.strength <= 0:
            return source

        result: list[Point] = [source[0]]
        for index in range(1, len(source) - 1):
            previous = source[index - 1]
            current = source[index]
            following = source[index + 1]

            incoming = (current[0] - previous[0], current[1] - previous[1])
            outgoing = (following[0] - current[0], following[1] - current[1])
            incoming_len = hypot(*incoming)
            outgoing_len = hypot(*outgoing)
            local_scale = max(1.0, incoming_len, outgoing_len)

            midpoint = ((previous[0] + following[0]) / 2.0,
                        (previous[1] + following[1]) / 2.0)
            deviation = hypot(current[0] - midpoint[0], current[1] - midpoint[1])
            avg_segment = max(1.0, (incoming_len + outgoing_len) / 2.0)
            curvature = min(1.0, deviation / max(1.0, avg_segment * 0.35))

            # Very sharp direction changes are likely intentional corners or
            # letter joins. Keep them more faithfully than small wobbles.
            if incoming_len < 0.01 or outgoing_len < 0.01:
                corner_score = 0.0
            else:
                cosine = (incoming[0] * outgoing[0] + incoming[1] * outgoing[1]) / (incoming_len * outgoing_len)
                cosine = max(-1.0, min(1.0, cosine))
                turn_score = (1.0 - cosine) / 2.0
                corner_score = min(1.0, max(0.0, (turn_score - 0.12) / 0.72))

            adaptive_strength = self.strength * (0.25 + 0.75 * curvature) * (1.0 - 0.78 * corner_score)
            adaptive_strength = max(0.0, min(0.75, adaptive_strength))
            result.append((
                current[0] * (1.0 - adaptive_strength) + midpoint[0] * adaptive_strength,
                current[1] * (1.0 - adaptive_strength) + midpoint[1] * adaptive_strength,
            ))

        result.append(source[-1])
        return result

    def describe_style(self, points: Iterable[Sequence[float]]) -> str:
        """A small stroke-shape heuristic for UI feedback, not text recognition."""
        source = [self._point(point) for point in points]
        if len(source) < 3:
            return "short"
        turns = []
        for a, b, c in zip(source, source[1:], source[2:]):
            first = (b[0] - a[0], b[1] - a[1])
            second = (c[0] - b[0], c[1] - b[1])
            first_len, second_len = hypot(*first), hypot(*second)
            if first_len < 0.5 or second_len < 0.5:
                continue
            cosine = (first[0] * second[0] + first[1] * second[1]) / (first_len * second_len)
            turns.append((1.0 - max(-1.0, min(1.0, cosine))) / 2.0)
        if not turns:
            return "steady"
        average_turn = sum(turns) / len(turns)
        if average_turn < 0.12:
            return "steady"
        if average_turn > 0.68:
            return "expressive"
        return "mixed"
