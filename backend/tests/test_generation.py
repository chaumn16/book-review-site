"""Tests for app/generation.py's generate_pending_books().

These never touch the real `claude` CLI -- `generate` is injected as a
plain callable, same pattern as tests/test_moderation.py. make_cli_generator()'s
subprocess plumbing itself is intentionally thin and left to be exercised by
actually running scripts/generate_books.py, since mocking `subprocess.run`
to fake `claude`'s output wouldn't prove the real CLI integration works.
"""

import pytest

from app import models
from app.generation import generate_pending_books


@pytest.fixture()
def db():
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _add_pending_book(db, title="Dune", author="Frank Herbert", status="pending", **kwargs):
    book = models.Book(title=title, author=author, status=status, **kwargs)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


FAKE_CONTENT = {
    "summary": "A test summary.",
    "chapters": [
        {"chapter_number": 1, "chapter_title": "The Beginning", "highlight": "Things start."},
        {"chapter_number": 2, "chapter_title": "The Middle", "highlight": "Things happen."},
    ],
    "verdict": {"label": "worth_it", "reason": "A solid example of its genre."},
}


def test_generates_content_for_a_pending_book(db):
    book = _add_pending_book(db)

    summary = generate_pending_books(db, generate=lambda title, author: FAKE_CONTENT, find_cover=lambda t, a: None)
    db.refresh(book)

    assert summary == {"total_pending": 1, "ready": 1, "failed": 0}
    assert book.status == "ready"
    assert book.summary == "A test summary."
    assert book.verdict_label == "worth_it"
    assert [c.highlight for c in book.chapters] == ["Things start.", "Things happen."]


def test_fetches_a_cover_only_if_not_already_set(db):
    with_cover = _add_pending_book(db, title="Has Cover", cover_url="https://covers.example.com/existing.jpg")
    without_cover = _add_pending_book(db, title="No Cover")

    calls = []

    def fake_find_cover(title, author):
        calls.append(title)
        return "https://covers.example.com/new.jpg"

    generate_pending_books(db, generate=lambda title, author: FAKE_CONTENT, find_cover=fake_find_cover)
    db.refresh(with_cover)
    db.refresh(without_cover)

    assert with_cover.cover_url == "https://covers.example.com/existing.jpg"  # untouched
    assert without_cover.cover_url == "https://covers.example.com/new.jpg"  # fetched
    assert calls == ["No Cover"]  # never looked up for the book that already had one


def test_generation_failure_marks_the_book_failed_not_left_pending(db):
    book = _add_pending_book(db)

    def boom(title, author):
        raise RuntimeError("claude CLI timed out")

    summary = generate_pending_books(db, generate=boom, find_cover=lambda t, a: None)
    db.refresh(book)

    assert summary == {"total_pending": 1, "ready": 0, "failed": 1}
    assert book.status == "failed"  # not silently retried -- needs the Retry button / regenerate call


def test_regenerating_a_failed_book_clears_old_chapters(db):
    book = _add_pending_book(db)
    # Simulate a book that previously generated, then got queued again via
    # the regenerate endpoint (which flips status back to 'pending' but
    # leaves old chapters in place until overwritten).
    db.add(models.ChapterHighlight(book_id=book.id, chapter_number=1, chapter_title="Old", highlight="stale"))
    db.commit()

    generate_pending_books(db, generate=lambda title, author: FAKE_CONTENT, find_cover=lambda t, a: None)
    db.refresh(book)

    highlights = [c.highlight for c in book.chapters]
    assert "stale" not in highlights
    assert highlights == ["Things start.", "Things happen."]


def test_only_processes_pending_books(db):
    ready_book = _add_pending_book(db, title="Already Ready", status="ready", summary="Existing summary")

    calls = []

    def fake_generate(title, author):
        calls.append(title)
        return FAKE_CONTENT

    summary = generate_pending_books(db, generate=fake_generate, find_cover=lambda t, a: None)

    assert summary == {"total_pending": 0, "ready": 0, "failed": 0}
    assert calls == []
    db.refresh(ready_book)
    assert ready_book.summary == "Existing summary"  # untouched
