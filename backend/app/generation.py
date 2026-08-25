"""Async book-content generation (summary, chapter highlights, verdict).

This module never imports the `anthropic` SDK and never touches
ANTHROPIC_API_KEY. It shells out to the `claude` Code CLI instead -- i.e. it
runs under *your* logged-in Claude account/subscription, the same way typing
a prompt into Claude Code would. There is no API billing path here. (Same
pattern as app/moderation.py, applied here to book generation instead of
comment moderation.)

Nothing in the request/response cycle (see app/routers/books.py) calls this
module. A book is written with status='pending' and shown in the grid only
once status='ready'; generate_pending_books() is meant to be invoked
out-of-band, on your own schedule, by scripts/generate_books.py.

Cover lookup (app/covers.py) is unrelated to this -- it's a free public API,
not an LLM call, so it stays synchronous in the router.
"""

import shutil
import subprocess
from typing import Callable, Optional

from . import models
from .util import extract_json

Generator = Callable[[str, str], dict]  # (title, author) -> content dict


class ClaudeCliError(RuntimeError):
    """Raised when the `claude` CLI is missing, errors, or returns something
    we can't parse. Callers decide what to do with it (the CLI entry point
    treats it as fatal; generate_pending_books marks the book 'failed' so a
    human decides whether to retry, via the existing Retry button)."""


def _build_prompt(title: str, author: str) -> str:
    return (
        f'You are a book-review editor. For the book "{title}" by {author}, write:\n\n'
        '1. "summary": a spoiler-aware but informative 200-300 word overview of the whole '
        "book (premise, key ideas or plot arc, why it matters). If it's fiction, avoid "
        "revealing the ending twist explicitly; you may hint at themes.\n"
        '2. "chapters": an array of chapter/section highlights covering the book\'s real '
        "structure as best you know it (if you don't know the exact chapter count, use its "
        "major parts/sections instead). Aim for 6-15 entries. Each entry has:\n"
        '   - "chapter_number": integer, sequential starting at 1\n'
        '   - "chapter_title": the chapter\'s title if known, otherwise a short descriptive label\n'
        '   - "highlight": 2-4 sentence summary of what happens / what\'s covered in that '
        "chapter, no filler\n"
        '3. "verdict": your own honest, differentiated judgment of whether it\'s worth '
        "reading -- don't default to praising everything. An object with:\n"
        '   - "label": exactly one of "worth_it", "depends", or "skip"\n'
        '   - "reason": 1-2 sentences on who it\'s for (or not for) and why -- specific '
        "enough to be useful, not generic praise\n\n"
        "Respond with ONLY a single JSON object of the exact shape:\n"
        '{"summary": "...", "chapters": [{"chapter_number": 1, "chapter_title": "...", '
        '"highlight": "..."}], "verdict": {"label": "worth_it", "reason": "..."}}\n\n'
        "If you genuinely do not recognize this book at all, still respond with your best "
        "good-faith synthesis based on the title/author/genre conventions, and keep the "
        "summary honest about being a general overview rather than inventing specific plot "
        "points you're unsure of."
    )


def make_cli_generator(model: Optional[str] = None) -> Generator:
    """Build a generator function that runs `claude -p <prompt>` (headless,
    non-interactive Claude Code) for a single book and parses the JSON it
    prints. Raises ClaudeCliError immediately if `claude` isn't on PATH, so
    callers can fail fast instead of retrying per-book.
    """
    if shutil.which("claude") is None:
        raise ClaudeCliError(
            "`claude` CLI not found on PATH. Install Claude Code "
            "(https://docs.claude.com/claude-code) and make sure you're logged in "
            "with your Claude account (run `claude` once interactively if you haven't), "
            "then re-run this script."
        )

    def generate(title: str, author: str) -> dict:
        cmd = ["claude", "-p", _build_prompt(title, author)]
        if model:
            cmd += ["--model", model]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired as exc:
            raise ClaudeCliError("`claude` CLI timed out after 180s") from exc

        if result.returncode != 0:
            raise ClaudeCliError(
                f"`claude` CLI exited {result.returncode}: {result.stderr.strip() or '(no stderr)'}"
            )

        parsed = extract_json(result.stdout)
        if not parsed.get("summary") or not isinstance(parsed.get("chapters"), list):
            raise ClaudeCliError("Model response missing summary/chapters")

        verdict = parsed.get("verdict") or {}
        if verdict.get("label") not in ("worth_it", "depends", "skip"):
            verdict = {"label": "depends", "reason": verdict.get("reason") or "No clear verdict was generated."}
        parsed["verdict"] = verdict
        return parsed

    return generate


def generate_pending_books(db, generate: Generator, find_cover=None) -> dict:
    """Generate content for every book with status='pending' -- both
    brand-new books and ones queued for regeneration via the Retry button
    end up here. On success: summary/chapters/verdict are (re)written and
    status becomes 'ready'. On failure: status becomes 'failed', matching
    the existing Retry-button UX rather than silently retrying forever.

    `find_cover` is optional (defaults to app.covers.find_cover_url) so
    tests can inject a fake without patching a module-level import.
    """
    if find_cover is None:
        from .covers import find_cover_url as find_cover

    pending = db.query(models.Book).filter(models.Book.status == "pending").all()
    ready = failed = 0

    for book in pending:
        try:
            content = generate(book.title, book.author)
        except Exception as exc:
            book.status = "failed"
            db.commit()
            failed += 1
            print(f"  ! book {book.id} ({book.title!r}): generation failed ({exc}); marked failed")
            continue

        db.query(models.ChapterHighlight).filter(models.ChapterHighlight.book_id == book.id).delete()
        for ch in content["chapters"]:
            db.add(
                models.ChapterHighlight(
                    book_id=book.id,
                    chapter_number=ch["chapter_number"],
                    chapter_title=ch.get("chapter_title"),
                    highlight=ch["highlight"],
                )
            )
        book.summary = content["summary"]
        book.verdict_label = content["verdict"]["label"]
        book.verdict_reason = content["verdict"]["reason"]
        if not book.cover_url:
            book.cover_url = find_cover(book.title, book.author)
        book.status = "ready"
        db.commit()
        ready += 1

    return {"total_pending": len(pending), "ready": ready, "failed": failed}
