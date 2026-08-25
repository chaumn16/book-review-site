"""Tests for app/llm.py's generate_book_content() -- specifically the
verdict normalization logic. The Anthropic client is faked via get_client();
these never make a real API call.
"""

import json
from types import SimpleNamespace

import pytest

from app import llm


class _FakeMessages:
    def __init__(self, text):
        self._text = text

    def create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class _FakeClient:
    def __init__(self, text):
        self.messages = _FakeMessages(text)


def _fake_response(monkeypatch, payload: dict):
    monkeypatch.setattr(llm, "get_client", lambda: _FakeClient(json.dumps(payload)))


def test_returns_the_models_verdict_when_present_and_valid(monkeypatch):
    _fake_response(
        monkeypatch,
        {
            "summary": "A summary.",
            "chapters": [{"chapter_number": 1, "highlight": "x"}],
            "verdict": {"label": "skip", "reason": "Not recommended for most readers."},
        },
    )
    result = llm.generate_book_content("Some Book", "Some Author")
    assert result["verdict"] == {"label": "skip", "reason": "Not recommended for most readers."}


def test_defaults_verdict_to_depends_when_missing_entirely(monkeypatch):
    _fake_response(
        monkeypatch,
        {
            "summary": "A summary.",
            "chapters": [{"chapter_number": 1, "highlight": "x"}],
            # no "verdict" key at all
        },
    )
    result = llm.generate_book_content("Some Book", "Some Author")
    assert result["verdict"]["label"] == "depends"


def test_defaults_verdict_when_label_is_not_one_of_the_three_allowed_values(monkeypatch):
    _fake_response(
        monkeypatch,
        {
            "summary": "A summary.",
            "chapters": [{"chapter_number": 1, "highlight": "x"}],
            "verdict": {"label": "amazing!!!", "reason": "great"},
        },
    )
    result = llm.generate_book_content("Some Book", "Some Author")
    assert result["verdict"]["label"] == "depends"


def test_raises_when_summary_or_chapters_are_missing(monkeypatch):
    _fake_response(monkeypatch, {"summary": "", "chapters": []})
    with pytest.raises(ValueError):
        llm.generate_book_content("Some Book", "Some Author")
