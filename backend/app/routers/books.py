from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import covers, llm, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/books", tags=["books"])


def _save_chapters(db: Session, book_id: int, chapters: list[dict]) -> None:
    for ch in chapters:
        db.add(
            models.ChapterHighlight(
                book_id=book_id,
                chapter_number=ch["chapter_number"],
                chapter_title=ch.get("chapter_title"),
                highlight=ch["highlight"],
            )
        )


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
def list_books(db: Session = Depends(get_db)):
    # Only fully-generated books are ever listed publicly -- a book stuck in
    # 'pending' or 'failed' is only reachable directly by id (e.g. to retry
    # generation), not surfaced here.
    books = (
        db.query(models.Book)
        .filter(models.Book.status == "ready")
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
    book = models.Book(title=payload.title.strip(), author=payload.author.strip(), status="pending")
    db.add(book)
    db.commit()
    db.refresh(book)

    try:
        content = llm.generate_book_content(book.title, book.author)
    except Exception as exc:
        book.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Generation failed, book saved as 'failed'.",
                "book_id": book.id,
                "retry_endpoint": f"/api/books/{book.id}/regenerate",
            },
        ) from exc

    _save_chapters(db, book.id, content["chapters"])
    book.summary = content["summary"]
    book.status = "ready"
    book.verdict_label = content["verdict"]["label"]
    book.verdict_reason = content["verdict"]["reason"]
    # Best-effort; find_cover_url() never raises, so this can't fail the request.
    book.cover_url = covers.find_cover_url(book.title, book.author)
    db.commit()
    db.refresh(book)
    return _to_detail(db, book)


@router.post("/{book_id}/regenerate", response_model=schemas.BookDetail)
def regenerate_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        content = llm.generate_book_content(book.title, book.author)
    except Exception as exc:
        book.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Generation failed again.") from exc

    db.query(models.ChapterHighlight).filter(models.ChapterHighlight.book_id == book.id).delete()
    _save_chapters(db, book.id, content["chapters"])
    book.summary = content["summary"]
    book.status = "ready"
    book.verdict_label = content["verdict"]["label"]
    book.verdict_reason = content["verdict"]["reason"]
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
