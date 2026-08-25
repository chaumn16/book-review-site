from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import covers, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/books", tags=["books"])


def _comment_count(db: Session, book_id: int) -> int:
    return (
        db.query(func.count(models.Comment.id))
        .filter(models.Comment.book_id == book_id, models.Comment.status == "visible")
        .scalar()
    )


def _rating_stats(db: Session, book_id: int) -> tuple[float | None, int]:
    """Average + count of ratings from visible, rated comments."""
    avg, count = (
        db.query(func.avg(models.Comment.rating), func.count(models.Comment.rating))
        .filter(
            models.Comment.book_id == book_id,
            models.Comment.status == "visible",
            models.Comment.rating.isnot(None),
        )
        .one()
    )
    return (round(avg, 1) if avg is not None else None, count or 0)


def _to_list_item(db: Session, b: models.Book) -> schemas.BookListItem:
    average_rating, rating_count = _rating_stats(db, b.id)
    return schemas.BookListItem(
        id=b.id,
        title=b.title,
        author=b.author,
        cover_url=b.cover_url,
        verdict_label=b.verdict_label,
        verdict_reason=b.verdict_reason,
        average_rating=average_rating,
        rating_count=rating_count,
        created_at=b.created_at,
        comment_count=_comment_count(db, b.id),
    )


def _to_detail(db: Session, b: models.Book) -> schemas.BookDetail:
    average_rating, rating_count = _rating_stats(db, b.id)
    return schemas.BookDetail(
        id=b.id,
        title=b.title,
        author=b.author,
        summary=b.summary,
        status=b.status,
        cover_url=b.cover_url,
        verdict_label=b.verdict_label,
        verdict_reason=b.verdict_reason,
        average_rating=average_rating,
        rating_count=rating_count,
        created_at=b.created_at,
        chapters=b.chapters,
    )


@router.get("", response_model=list[schemas.BookListItem])
def list_books(status: str = "ready", db: Session = Depends(get_db)):
    # Defaults to the public catalog (fully-generated books). Pass
    # ?status=pending for the "just added" tab -- books waiting on
    # scripts/generate_books.py. 'failed' isn't exposed here; those are
    # only reachable directly by id, via the Retry button.
    if status not in ("ready", "pending"):
        raise HTTPException(status_code=400, detail="status must be 'ready' or 'pending'")
    books = (
        db.query(models.Book)
        .filter(models.Book.status == status)
        .order_by(models.Book.created_at.desc())
        .all()
    )
    return [_to_list_item(db, b) for b in books]


@router.get("/{book_id}", response_model=schemas.BookDetail)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return _to_detail(db, book)


@router.post("", response_model=schemas.BookDetail, status_code=201)
def add_book(payload: schemas.BookCreate, db: Session = Depends(get_db)):
    # No generation call here. The book is saved as 'pending' and returned
    # immediately; scripts/generate_books.py fills in the summary, chapter
    # highlights, and verdict asynchronously (via the `claude` CLI, run
    # under your own account) and flips status to 'ready'. See
    # app/generation.py. Cover lookup is unrelated (not an LLM call, just a
    # free public API) so it still happens synchronously, right here.
    book = models.Book(
        title=payload.title.strip(),
        author=payload.author.strip(),
        status="pending",
        cover_url=covers.find_cover_url(payload.title.strip(), payload.author.strip()),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return _to_detail(db, book)


@router.post("/{book_id}/regenerate", response_model=schemas.BookDetail)
def regenerate_book(book_id: int, db: Session = Depends(get_db)):
    """Queue a book for (re)generation -- doesn't generate anything itself.
    Existing summary/chapters/verdict are left as-is until
    scripts/generate_books.py actually overwrites them; only the status
    flips, which is what makes the book page show "Generating..." again.
    """
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.status = "pending"
    if not book.cover_url:
        book.cover_url = covers.find_cover_url(book.title, book.author)
    db.commit()
    db.refresh(book)
    return _to_detail(db, book)


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
