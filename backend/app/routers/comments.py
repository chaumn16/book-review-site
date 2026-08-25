from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import llm, models, schemas
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

    try:
        result = llm.moderate_comment(payload.body)
        allowed, reason = result["allowed"], result.get("reason")
    except Exception:
        # Fail closed: if moderation itself errors, hold the comment for
        # review rather than silently publishing unmoderated content.
        allowed, reason = False, "Moderation check failed; held for review."

    comment = models.Comment(
        book_id=book_id,
        author_name=payload.author_name.strip(),
        body=payload.body.strip(),
        status="visible" if allowed else "removed",
        moderation_reason=reason,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    if not allowed:
        raise HTTPException(
            status_code=422,
            detail={"error": "Comment removed by moderation", "reason": reason},
        )

    return comment
