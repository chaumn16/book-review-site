"""Tests for the postgres:// -> postgresql:// URL normalization in
app/database.py (some providers, e.g. Render, hand out the old scheme, which
SQLAlchemy 1.4+ rejects). Runs the module's logic in isolation via a fresh
subprocess so it doesn't fight with the already-imported app.database module
(which is fixed to the test suite's sqlite:///:memory: for the whole run).
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _normalized_url(database_url: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", "import os; os.environ['ANTHROPIC_API_KEY']='test'; from app.database import DATABASE_URL; print(DATABASE_URL)"],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": database_url, "PYTHONPATH": str(BACKEND_DIR)},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_postgres_scheme_is_rewritten_to_postgresql():
    assert _normalized_url("postgres://user:pass@host/db") == "postgresql://user:pass@host/db"


def test_postgresql_scheme_is_left_alone():
    url = "postgresql://user:pass@host/db?sslmode=require"
    assert _normalized_url(url) == url


def test_sqlite_url_is_left_alone():
    # In-memory on purpose -- a file-based URL here would create a stray
    # .sqlite file as a side effect of running this test.
    assert _normalized_url("sqlite:///:memory:") == "sqlite:///:memory:"
