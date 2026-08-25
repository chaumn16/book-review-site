"""Thin wrapper around the Anthropic API for book-content generation.

Comment moderation is *not* here anymore -- see app/moderation.py, which
shells out to the `claude` Code CLI under your own Claude account instead of
calling this SDK/API-key path. This module stays scoped to the one job that
still uses ANTHROPIC_API_KEY directly: generating book summaries/highlights.
"""

import json
import re
from typing import Any, Optional

import anthropic

SUMMARY_MODEL = "claude-sonnet-5"

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
3. "verdict": your own honest, differentiated judgment of whether it's worth reading -- don't default to praising everything. An object with:
   - "label": exactly one of "worth_it", "depends", or "skip"
   - "reason": 1-2 sentences on who it's for (or not for) and why -- specific enough to be useful, not generic praise

Respond with ONLY a single JSON object of the exact shape:
{{"summary": "...", "chapters": [{{"chapter_number": 1, "chapter_title": "...", "highlight": "..."}}], "verdict": {{"label": "worth_it", "reason": "..."}}}}

If you genuinely do not recognize this book at all, still respond with your best good-faith synthesis based on the title/author/genre conventions, and keep the summary honest about being a general overview rather than inventing specific plot points you're unsure of."""

    response = get_client().messages.create(
        model=SUMMARY_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    parsed = _extract_json(_text_of(response))

    if not parsed.get("summary") or not isinstance(parsed.get("chapters"), list):
        raise ValueError("Model response missing summary/chapters")

    verdict = parsed.get("verdict") or {}
    if verdict.get("label") not in ("worth_it", "depends", "skip"):
        verdict = {"label": "depends", "reason": verdict.get("reason") or "No clear verdict was generated."}
    parsed["verdict"] = verdict
    return parsed
