from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/books/{book_id}/comments", tags=["comments"])


@router.get("", response_model=list[schemas.CommentOut])
def list_comments(book_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Comment)
        .filter(models.Comment.book_id == book_id, models.Comment.status == "visible")
        .order_by(models.Comment.created_at.desc())
        .all()
    )


@router.post("", response_model=schemas.CommentOut, status_code=201)
def add_comment(book_id: int, payload: schemas.CommentCreate, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # No moderation call here. The comment is visible right away;
    # scripts/review_comments.py screens it asynchronously (via the `claude`
    # CLI, run under your own account) and flips status to 'removed' if
    # flagged. See app/moderation.py.
    comment = models.Comment(
        book_id=book_id,
        author_name=payload.author_name.strip(),
        body=payload.body.strip(),
        status="visible",
        reviewed=False,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
