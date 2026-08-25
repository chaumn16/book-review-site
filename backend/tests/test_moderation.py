"""Tests for app/moderation.py's review_pending_comments().

These never touch the real `claude` CLI -- `classify` is injected as a plain
callable, same pattern as mock_llm for app/llm.py. make_cli_classifier()'s
subprocess plumbing itself is intentionally thin and left to be exercised by
actually running scripts/review_comments.py, since mocking `subprocess.run`
to fake `claude`'s output wouldn't prove the real CLI integration works.
"""

import pytest

from app import models
from app.moderation import review_pending_comments


@pytest.fixture()
def db():
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_book(db):
    book = models.Book(title="Dune", author="Frank Herbert", status="ready", summary="A summary.")
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def _add_comment(db, book_id, body, author="Someone"):
    comment = models.Comment(book_id=book_id, author_name=author, body=body, status="visible", reviewed=False)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def test_review_approves_clean_comments(db):
    book = _make_book(db)
    comment = _add_comment(db, book.id, "I loved this book!")

    summary = review_pending_comments(db, classify=lambda body: {"allowed": True, "reason": None})
    db.refresh(comment)

    assert summary == {"total_pending": 1, "approved": 1, "blocked": 0, "errors": 0}
    assert comment.reviewed is True
    assert comment.status == "visible"


def test_review_removes_flagged_comments(db):
    book = _make_book(db)
    comment = _add_comment(db, book.id, "you are all idiots and should die")

    summary = review_pending_comments(db, classify=lambda body: {"allowed": False, "reason": "harassment"})
    db.refresh(comment)

    assert summary == {"total_pending": 1, "approved": 0, "blocked": 1, "errors": 0}
    assert comment.reviewed is True
    assert comment.status == "removed"
    assert comment.moderation_reason == "harassment"


def test_removed_comments_drop_out_of_the_public_list(db):
    book = _make_book(db)
    _add_comment(db, book.id, "spam spam buy my crypto")

    review_pending_comments(db, classify=lambda body: {"allowed": False, "reason": "spam"})

    still_visible = (
        db.query(models.Comment)
        .filter(models.Comment.book_id == book.id, models.Comment.status == "visible")
        .all()
    )
    assert still_visible == []


def test_review_leaves_classification_errors_pending_for_retry(db):
    book = _make_book(db)
    comment = _add_comment(db, book.id, "some comment")

    def boom(body):
        raise RuntimeError("claude CLI timed out")

    summary = review_pending_comments(db, classify=boom)
    db.refresh(comment)

    assert summary == {"total_pending": 1, "approved": 0, "blocked": 0, "errors": 1}
    assert comment.reviewed is False  # untouched -- will be picked up again next run
    assert comment.status == "visible"


def test_review_skips_already_reviewed_comments_on_a_second_run(db):
    book = _make_book(db)
    _add_comment(db, book.id, "first")

    calls = []

    def fake_classify(body):
        calls.append(body)
        return {"allowed": True, "reason": None}

    first_summary = review_pending_comments(db, classify=fake_classify)
    second_summary = review_pending_comments(db, classify=fake_classify)

    assert first_summary["total_pending"] == 1
    assert second_summary == {"total_pending": 0, "approved": 0, "blocked": 0, "errors": 0}
    assert len(calls) == 1  # classify was only ever called once, not re-run on the 2nd pass


def test_review_handles_multiple_pending_comments_independently(db):
    book = _make_book(db)
    good = _add_comment(db, book.id, "great read", author="A")
    bad = _add_comment(db, book.id, "you are trash", author="B")

    def fake_classify(body):
        return {"allowed": "trash" not in body, "reason": "insult" if "trash" in body else None}

    summary = review_pending_comments(db, classify=fake_classify)
    db.refresh(good)
    db.refresh(bad)

    assert summary == {"total_pending": 2, "approved": 1, "blocked": 1, "errors": 0}
    assert good.status == "visible"
    assert bad.status == "removed"
