"""Review any comments awaiting moderation.

Uses the `claude` Code CLI under YOUR Claude account/subscription -- this
script never imports the `anthropic` SDK and never needs ANTHROPIC_API_KEY.
Every comment posts and shows up immediately; running this is what actually
screens them and takes down anything flagged.

Run it whenever you want to catch up (there's no scheduler here -- that's
intentional, you're the one running it):

    python scripts/review_comments.py
    python scripts/review_comments.py --model haiku   # optional override

If you'd rather it ran on a cadence instead of by hand, wire this same
command into cron/launchd yourself; nothing about the script assumes either.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.moderation import ClaudeCliError, make_cli_classifier, review_pending_comments  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Review pending comments via the `claude` CLI.")
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override, passed through as `claude -p ... --model <value>`. "
        "Omit to use whatever model your `claude` CLI defaults to.",
    )
    args = parser.parse_args()

    try:
        classify = make_cli_classifier(model=args.model)
    except ClaudeCliError as exc:
        print(f"error: {exc}")
        sys.exit(1)

    db = SessionLocal()
    try:
        summary = review_pending_comments(db, classify=classify)
    finally:
        db.close()

    if summary["total_pending"] == 0:
        print("Nothing pending -- all comments already reviewed.")
        return

    print(
        f"Reviewed {summary['total_pending']} pending comment(s): "
        f"{summary['approved']} approved, {summary['blocked']} blocked, "
        f"{summary['errors']} left pending (classification errors, will retry next run)."
    )


if __name__ == "__main__":
    main()
