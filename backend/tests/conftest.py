import os

# Must be set before `app.main` (and therefore `app.database`) is imported,
# so the app's own engine points at a shared in-memory SQLite DB for the
# whole test run.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient

from app import covers
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
def mock_covers(monkeypatch):
    """Replace the real Open Library/Google Books cover lookup with a
    deterministic fake so tests don't need network access. This is the only
    external call POST /api/books still makes synchronously -- book
    generation itself is async now (see app/generation.py,
    tests/test_generation.py) and isn't called from the router at all.
    """

    def fake_find_cover_url(title, author):
        return f"https://covers.example.com/{title.lower().replace(' ', '-')}.jpg"

    monkeypatch.setattr(covers, "find_cover_url", fake_find_cover_url)
    return covers
