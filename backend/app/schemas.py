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
    id: int
    title: str
    author: str
    status: str
    created_at: datetime
    comment_count: int

    model_config = ConfigDict(from_attributes=True)


class BookDetail(BaseModel):
    id: int
    title: str
    author: str
    summary: Optional[str] = None
    status: str
    created_at: datetime
    chapters: List[ChapterHighlightOut] = []

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    author_name: str = Field(min_length=1)
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: int
    author_name: str
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
