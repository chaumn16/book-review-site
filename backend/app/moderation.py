"""Async comment moderation.

Unlike app/llm.py, this module never imports the `anthropic` SDK and never
touches ANTHROPIC_API_KEY. It shells out to the `claude` Code CLI instead --
i.e. it runs under *your* logged-in Claude account/subscription, the same way
typing a prompt into Claude Code would. There is no API billing path here.

Nothing in the request/response cycle (see app/routers/comments.py) calls
this module. A comment is written with reviewed=False and shown immediately;
review_pending_comments() is meant to be invoked out-of-band, on your own
schedule, by scripts/review_comments.py.
"""

import shutil
import subprocess
from typing import Callable, Optional

from . import models
from .llm import _extract_json

Classifier = Callable[[str], dict]


class ClaudeCliError(RuntimeError):
    """Raised when the `claude` CLI is missing, errors, or returns something
    we can't parse. Callers decide what to do with it (the CLI entry point
    treats it as fatal; review_pending_comments treats a per-comment failure
    as "leave it pending, try again next run")."""


def _build_prompt(body: str) -> str:
    return (
        "Classify the following user comment left on a book review site. Flag it if it "
        "contains: harassment, hate speech, threats, sexual content involving minors, "
        "doxxing/personal info, spam/scams, or severe profanity/abuse. Ordinary negative "
        "opinions, mild criticism, or strong-but-civil disagreement about the book are "
        "ALLOWED.\n\n"
        f'Comment:\n"""{body}"""\n\n'
        "Respond with ONLY this JSON object, nothing else, no markdown fences: "
        '{"allowed": true|false, "reason": "short reason if not allowed, else null"}'
    )


def make_cli_classifier(model: Optional[str] = None) -> Classifier:
    """Build a classifier function that runs `claude -p <prompt>` (headless,
    non-interactive Claude Code) for a single comment and parses the JSON it
    prints. Raises ClaudeCliError immediately if `claude` isn't on PATH, so
    callers can fail fast instead of retrying per-comment.
    """
    if shutil.which("claude") is None:
        raise ClaudeCliError(
            "`claude` CLI not found on PATH. Install Claude Code "
            "(https://docs.claude.com/claude-code) and make sure you're logged in "
            "with your Claude account (run `claude` once interactively if you haven't), "
            "then re-run this script."
        )

    def classify(body: str) -> dict:
        cmd = ["claude", "-p", _build_prompt(body)]
        if model:
            cmd += ["--model", model]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired as exc:
            raise ClaudeCliError("`claude` CLI timed out after 120s") from exc

        if result.returncode != 0:
            raise ClaudeCliError(
                f"`claude` CLI exited {result.returncode}: {result.stderr.strip() or '(no stderr)'}"
            )
        return _extract_json(result.stdout)

    return classify


def review_pending_comments(db, classify: Classifier) -> dict:
    """Classify every comment with reviewed=False using `classify`, and
    persist the result: allowed -> status stays 'visible', reviewed=True;
    not allowed -> status='removed' (drops out of the public list), with a
    reason recorded. A classification error leaves the comment untouched
    (reviewed=False) so the next run retries it, rather than either exposing
    or removing it on a guess.
    """
    pending = db.query(models.Comment).filter(models.Comment.reviewed.is_(False)).all()
    approved = blocked = errors = 0

    for comment in pending:
        try:
            result = classify(comment.body)
            allowed = bool(result.get("allowed"))
            reason = result.get("reason")
        except Exception as exc:
            errors += 1
            print(f"  ! comment {comment.id}: classification failed ({exc}); left pending for retry")
            continue

        comment.reviewed = True
        if allowed:
            comment.status = "visible"
            approved += 1
        else:
            comment.status = "removed"
            comment.moderation_reason = reason
            blocked += 1
        db.commit()

    return {"total_pending": len(pending), "approved": approved, "blocked": blocked, "errors": errors}
