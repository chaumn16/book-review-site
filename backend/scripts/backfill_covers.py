"""One-off: backfill cover_url for existing books that don't have one yet
(e.g. books added before the cover-lookup feature existed). New books get
this automatically at creation time -- see app/routers/books.py.

Run from the backend/ directory with the venv active:
    python scripts/backfill_covers.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.covers import find_cover_url  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Book  # noqa: E402


def main():
    db = SessionLocal()
    found = missing = 0
    try:
        books = db.query(Book).filter(Book.cover_url.is_(None)).all()
        for book in books:
            url = find_cover_url(book.title, book.author)
            if url:
                book.cover_url = url
                db.commit()
                found += 1
                print(f"found cover: {book.title!r} -> {url}")
            else:
                missing += 1
                print(f"no cover found: {book.title!r} by {book.author}")
    finally:
        db.close()

    print(f"\nDone. {found} cover(s) found, {missing} not found.")


if __name__ == "__main__":
    main()
