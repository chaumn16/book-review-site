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


def test_returns_cover_url_when_a_matching_doc_has_a_cover(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse({"docs": [{"cover_i": 12345}]}))
    assert find_cover_url("Dune", "Frank Herbert") == "https://covers.openlibrary.org/b/id/12345-M.jpg"


def test_returns_none_when_no_docs_match(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse({"docs": []}))
    assert find_cover_url("Some Obscure Book", "Nobody") is None


def test_returns_none_when_matching_doc_has_no_cover_id(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse({"docs": [{}]}))
    assert find_cover_url("Some Book", "Someone") is None


def test_returns_none_on_network_error_rather_than_raising(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(httpx, "get", boom)
    assert find_cover_url("Dune", "Frank Herbert") is None


def test_returns_none_on_http_error_status(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse({}, status_code=500))
    assert find_cover_url("Dune", "Frank Herbert") is None
