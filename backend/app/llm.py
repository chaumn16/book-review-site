"""Thin wrapper around the Anthropic API for the two LLM jobs this app needs:
generating book content, and moderating comments.

Kept as plain functions (not a class) so tests can monkeypatch
`generate_book_content` / `moderate_comment` directly without touching the
Anthropic client at all.
"""

import json
import re
from typing import Any, Optional

import anthropic

SUMMARY_MODEL = "claude-sonnet-5"
MODERATION_MODEL = "claude-haiku-4-5-20251001"

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def _extract_json(text: str) -> Any:
    """Pull the first {...} or [...] JSON block out of a model response."""
    match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if not match:
        raise ValueError(f"No JSON found in model response: {text[:200]}")
    return json.loads(match.group(0))


def _text_of(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def generate_book_content(title: str, author: str) -> dict:
    """Generate a whole-book summary plus per-chapter highlights from the
    model's general knowledge of the book. Best-effort: for lesser-known
    books the model may need to infer a reasonable chapter breakdown.
    """
    prompt = f"""You are a book-review editor. For the book "{title}" by {author}, write:

1. "summary": a spoiler-aware but informative 200-300 word overview of the whole book (premise, key ideas or plot arc, why it matters). If it's fiction, avoid revealing the ending twist explicitly; you may hint at themes.
2. "chapters": an array of chapter/section highlights covering the book's real structure as best you know it (if you don't know the exact chapter count, use its major parts/sections instead). Aim for 6-15 entries. Each entry has:
   - "chapter_number": integer, sequential starting at 1
   - "chapter_title": the chapter's title if known, otherwise a short descriptive label
   - "highlight": 2-4 sentence summary of what happens / what's covered in that chapter, no filler

Respond with ONLY a single JSON object of the exact shape:
{{"summary": "...", "chapters": [{{"chapter_number": 1, "chapter_title": "...", "highlight": "..."}}]}}

If you genuinely do not recognize this book at all, still respond with your best good-faith synthesis based on the title/author/genre conventions, and keep the summary honest about being a general overview rather than inventing specific plot points you're unsure of."""

    response = get_client().messages.create(
        model=SUMMARY_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    parsed = _extract_json(_text_of(response))

    if not parsed.get("summary") or not isinstance(parsed.get("chapters"), list):
        raise ValueError("Model response missing summary/chapters")
    return parsed


def moderate_comment(body: str) -> dict:
    """Classify a comment for harmful/inappropriate content before it's
    stored. Returns {"allowed": bool, "reason": str | None}.
    """
    prompt = f"""Classify the following user comment left on a book review site. Flag it if it contains: harassment, hate speech, threats, sexual content involving minors, doxxing/personal info, spam/scams, or severe profanity/abuse. Ordinary negative opinions, mild criticism, or strong-but-civil disagreement about the book are ALLOWED.

Comment:
\"\"\"{body}\"\"\"

Respond with ONLY this JSON object: {{"allowed": true|false, "reason": "short reason if not allowed, else null"}}"""

    response = get_client().messages.create(
        model=MODERATION_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    parsed = _extract_json(_text_of(response))
    return {"allowed": bool(parsed.get("allowed")), "reason": parsed.get("reason")}
