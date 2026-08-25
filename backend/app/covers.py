"""Book cover lookup: Open Library first, Google Books as a fallback.

Both free, no key required. Best-effort and non-blocking by design: each
helper swallows its own network/parsing errors and returns None rather than
raising, so a cover lookup failure never blocks adding or viewing a book --
and Google Books being unavailable (e.g. rate-limited) just means we fall
back to a placeholder, same as today, not an error.

Open Library is tried first because it returns cleaner, source-agnostic
results; Google Books tends to have better coverage for very recent
releases, which is exactly where Open Library comes up empty.
"""

from typing import Optional

import httpx

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER_TEMPLATE = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


def _from_open_library(title: str, author: str, timeout: float) -> Optional[str]:
    try:
        response = httpx.get(
            OPEN_LIBRARY_SEARCH_URL,
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
        return OPEN_LIBRARY_COVER_TEMPLATE.format(cover_id=cover_id)
    except Exception:
        return None


def _from_google_books(title: str, author: str, timeout: float) -> Optional[str]:
    try:
        response = httpx.get(
            GOOGLE_BOOKS_URL,
            params={"q": f"{title} {author}", "maxResults": 1},
            timeout=timeout,
            headers={"User-Agent": "book-review-site-prototype/1.0"},
        )
        response.raise_for_status()
        items = response.json().get("items") or []
        if not items:
            return None
        image_links = items[0].get("volumeInfo", {}).get("imageLinks") or {}
        url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if not url:
            return None
        return url.replace("http://", "https://")  # avoid mixed-content warnings
    except Exception:
        return None


def find_cover_url(title: str, author: str, timeout: float = 5.0) -> Optional[str]:
    return _from_open_library(title, author, timeout) or _from_google_books(title, author, timeout)
