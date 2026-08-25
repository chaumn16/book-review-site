from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | ready | failed
    created_at = Column(DateTime, default=utcnow, nullable=False)

    chapters = relationship(
        "ChapterHighlight",
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="ChapterHighlight.chapter_number",
    )
    comments = relationship("Comment", back_populates="book", cascade="all, delete-orphan")


class ChapterHighlight(Base):
    __tablename__ = "chapter_highlights"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    chapter_title = Column(String, nullable=True)
    highlight = Column(Text, nullable=False)

    book = relationship("Book", back_populates="chapters")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="visible")  # visible | removed
    moderation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    book = relationship("Book", back_populates="comments")
