"""Generate content for any book awaiting it (status='pending') -- both
brand-new books (added via the site) and ones queued for regeneration via
the book page's Retry button end up here.

Uses the `claude` Code CLI under YOUR Claude account/subscription -- this
script never imports the `anthropic` SDK and never needs ANTHROPIC_API_KEY.
A book posts immediately with a 'pending' status and doesn't show up in the
public list until this actually runs and gets it to 'ready'.

Run it whenever you want to catch up (there's no scheduler here --
intentional, you're the one running it):

    python scripts/generate_books.py
    python scripts/generate_books.py --model haiku   # optional override

If you'd rather it ran on a cadence instead of by hand, wire this same
command into cron/launchd yourself -- same as scripts/review_comments.py.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.generation import ClaudeCliError, generate_pending_books, make_cli_generator  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Generate content for pending books via the `claude` CLI.")
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override, passed through as `claude -p ... --model <value>`. "
        "Omit to use whatever model your `claude` CLI defaults to.",
    )
    args = parser.parse_args()

    try:
        generate = make_cli_generator(model=args.model)
    except ClaudeCliError as exc:
        print(f"error: {exc}")
        sys.exit(1)

    db = SessionLocal()
    try:
        summary = generate_pending_books(db, generate=generate)
    finally:
        db.close()

    if summary["total_pending"] == 0:
        print("Nothing pending -- all books already generated.")
        return

    print(
        f"Processed {summary['total_pending']} pending book(s): "
        f"{summary['ready']} generated, {summary['failed']} failed "
        "(use the Retry button on the book page, or POST /api/books/{id}/regenerate, "
        "to queue them again)."
    )


if __name__ == "__main__":
    main()
