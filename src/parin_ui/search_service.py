"""Qt-independent PDF text search operations.

The Reader owns navigation, match highlighting and status presentation. This
module owns only the document-level search traversal and match coordinates.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchMatch:
    """One search hit, with a page-local zero-based match index."""

    page_index: int
    rect: tuple[float, float, float, float]
    match_index: int
    page_match_count: int


def find_next_match(document, query, start_page=0, start_match_index=0):
    """Find the next occurrence, scanning forward and wrapping across pages.

    The start page is searched from start_match_index onward. Later pages are
    searched from their first match. The current page is not rescanned before
    the supplied start index, matching the Reader's existing next-match flow.
    """
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    query = query.strip()
    if not query:
        return None

    page_count = document.page_count
    if page_count <= 0:
        return None

    if isinstance(start_page, bool) or not isinstance(start_page, int):
        raise ValueError("start_page must be an integer page index")
    if not 0 <= start_page < page_count:
        raise ValueError("start_page is outside the document")
    if isinstance(start_match_index, bool) or not isinstance(start_match_index, int):
        raise ValueError("start_match_index must be a non-negative integer")
    if start_match_index < 0:
        raise ValueError("start_match_index must be a non-negative integer")

    for offset in range(page_count):
        page_index = (start_page + offset) % page_count
        page = document.load_page(page_index)
        matches = page.search_for(query)
        match_index = start_match_index if offset == 0 else 0
        if match_index >= len(matches):
            continue

        rect = matches[match_index]
        return SearchMatch(
            page_index=page_index,
            rect=(float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)),
            match_index=match_index,
            page_match_count=len(matches),
        )

    return None
