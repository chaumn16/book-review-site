from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import llm, models, schemas
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


@router.get("", response_model=list[schemas.BookListItem])
def list_books(db: Session = Depends(get_db)):
    books = db.query(models.Book).order_by(models.Book.created_at.desc()).all()
    return [
        schemas.BookListItem(
            id=b.id,
            title=b.title,
            author=b.author,
            status=b.status,
            created_at=b.created_at,
            comment_count=(
                db.query(func.count(models.Comment.id))
                .filter(models.Comment.book_id == b.id, models.Comment.status == "visible")
                .scalar()
            ),
        )
        for b in books
    ]


@router.get("/{book_id}", response_model=schemas.BookDetail)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


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
    db.commit()
    db.refresh(book)
    return book


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
    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
