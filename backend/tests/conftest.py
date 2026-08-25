import os

# Must be set before `app.main` (and therefore `app.database`) is imported,
# so the app's own engine points at a shared in-memory SQLite DB and no real
# API key / .env file is required to run the test suite.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from app import covers, llm
from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    """Give every test a clean database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def mock_llm(monkeypatch):
    """Replace the real Anthropic call for book generation, and the real
    Open Library cover lookup, with deterministic fakes so tests don't need
    network access or a real API key.

    (Comment moderation is no longer part of `app.llm` -- see
    app/moderation.py and tests/test_moderation.py, which use a plain
    injected `classify` callable instead of monkeypatching anything.)
    """

    def fake_generate_book_content(title, author):
        return {
            "summary": f"A test summary of {title} by {author}.",
            "chapters": [
                {"chapter_number": 1, "chapter_title": "The Beginning", "highlight": "Things start."},
                {"chapter_number": 2, "chapter_title": "The Middle", "highlight": "Things happen."},
            ],
            "verdict": {"label": "worth_it", "reason": "A solid, well-made example of its genre."},
        }

    def fake_find_cover_url(title, author):
        return f"https://covers.example.com/{title.lower().replace(' ', '-')}.jpg"

    monkeypatch.setattr(llm, "generate_book_content", fake_generate_book_content)
    monkeypatch.setattr(covers, "find_cover_url", fake_find_cover_url)
    return llm
