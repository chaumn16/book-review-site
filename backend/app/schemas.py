from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChapterHighlightOut(BaseModel):
    chapter_number: int
    chapter_title: Optional[str] = None
    highlight: str

    model_config = ConfigDict(from_attributes=True)


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)


class BookListItem(BaseModel):
    # No `status` here: the list endpoint only ever returns ready books, so
    # there's nothing to display. BookDetail below still carries status --
    # the book page needs it for the pending/failed/retry UI.
    id: int
    title: str
    author: str
    cover_url: Optional[str] = None
    verdict_label: Optional[str] = None  # worth_it | depends | skip
    verdict_reason: Optional[str] = None
    average_rating: Optional[float] = None  # None when no ratings yet
    rating_count: int = 0
    created_at: datetime
    comment_count: int

    model_config = ConfigDict(from_attributes=True)


class BookDetail(BaseModel):
    id: int
    title: str
    author: str
    summary: Optional[str] = None
    status: str
    cover_url: Optional[str] = None
    verdict_label: Optional[str] = None
    verdict_reason: Optional[str] = None
    average_rating: Optional[float] = None
    rating_count: int = 0
    created_at: datetime
    chapters: List[ChapterHighlightOut] = []

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    author_name: str = Field(min_length=1)
    body: str = Field(min_length=1)
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class CommentOut(BaseModel):
    id: int
    author_name: str
    body: str
    rating: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
