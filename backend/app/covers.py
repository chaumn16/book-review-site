"""Book cover lookup via the Open Library API -- free, no key required.

Best-effort and non-blocking by design: find_cover_url() swallows any
network/parsing error and returns None rather than raising, so a cover
lookup failure never blocks adding or viewing a book.
"""

from typing import Optional

import httpx

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL_TEMPLATE = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"


def find_cover_url(title: str, author: str, timeout: float = 5.0) -> Optional[str]:
    try:
        response = httpx.get(
            SEARCH_URL,
            params={"title": title, "author": author, "limit": 1, "fields": "cover_i"},
            timeout=timeout,
            headers={"User-Agent": "book-review-site-prototype/1.0"},
        )
        response.raise_for_status()
        docs = response.json().get("docs") or []
        if not docs:
            return None
        cover_id = docs[0].get("cover_i")
        if not cover_id:
            return None
        return COVER_URL_TEMPLATE.format(cover_id=cover_id)
    except Exception:
        return None
