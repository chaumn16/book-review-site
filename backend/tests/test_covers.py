"""Tests for app/covers.py's find_cover_url(). httpx.get is monkeypatched so
these never make a real network call."""

import httpx

from app.covers import find_cover_url


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def _fake_get(open_library=None, google_books=None):
    """Route based on which host is being requested, so tests can control
    each source independently. Each arg is a _FakeResponse or an exception
    instance to raise; None means "empty result" for that source."""

    def get(url, **kwargs):
        if "openlibrary.org" in url:
            if isinstance(open_library, Exception):
                raise open_library
            return open_library if open_library is not None else _FakeResponse({"docs": []})
        if "googleapis.com" in url:
            if isinstance(google_books, Exception):
                raise google_books
            return google_books if google_books is not None else _FakeResponse({"items": []})
        raise AssertionError(f"unexpected URL: {url}")

    return get


def test_returns_open_library_cover_when_found(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(open_library=_FakeResponse({"docs": [{"cover_i": 12345}]})))
    assert find_cover_url("Dune", "Frank Herbert") == "https://covers.openlibrary.org/b/id/12345-M.jpg"


def test_does_not_call_google_books_when_open_library_succeeds(monkeypatch):
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        if "openlibrary.org" in url:
            return _FakeResponse({"docs": [{"cover_i": 12345}]})
        return _FakeResponse({"items": []})

    monkeypatch.setattr(httpx, "get", get)
    find_cover_url("Dune", "Frank Herbert")
    assert all("openlibrary.org" in u for u in calls)  # never reached Google Books


def test_falls_back_to_google_books_when_open_library_has_no_cover(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        _fake_get(
            open_library=_FakeResponse({"docs": [{}]}),  # matched, but no cover_i
            google_books=_FakeResponse({"items": [{"volumeInfo": {"imageLinks": {"thumbnail": "http://books.example.com/x.jpg"}}}]}),
        ),
    )
    assert find_cover_url("Some Book", "Some Author") == "https://books.example.com/x.jpg"


def test_returns_none_when_neither_source_has_a_match(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())  # both empty
    assert find_cover_url("Some Obscure Book", "Nobody") is None


def test_returns_none_when_open_library_errors_and_google_books_has_nothing(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(open_library=httpx.ConnectError("no network")))
    assert find_cover_url("Dune", "Frank Herbert") is None


def test_falls_back_to_google_books_when_open_library_raises(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        _fake_get(
            open_library=httpx.ConnectError("no network"),
            google_books=_FakeResponse({"items": [{"volumeInfo": {"imageLinks": {"thumbnail": "http://books.example.com/y.jpg"}}}]}),
        ),
    )
    assert find_cover_url("Dune", "Frank Herbert") == "https://books.example.com/y.jpg"


def test_returns_none_when_google_books_also_errors(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        _fake_get(open_library=_FakeResponse({"docs": []}), google_books=RuntimeError("rate limited")),
    )
    assert find_cover_url("Dune", "Frank Herbert") is None
