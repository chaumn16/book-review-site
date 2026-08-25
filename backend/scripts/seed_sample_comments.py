"""Seed 3 sample reader comments (each with a rating) per book, so the
average rating shown on the home page has real data instead of "no ratings
yet".

Hand-written per book (not generated at runtime), inserted directly with
reviewed=True / status='visible' -- these are known-clean, so they skip
scripts/review_comments.py rather than faking a review pass for content
that's already fine.

Run from the backend/ directory with the venv active:
    python scripts/seed_sample_comments.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import Book, Comment  # noqa: E402

# title -> [(author_name, rating, body), ...]
SAMPLE_COMMENTS = {
    "Angel Down": [
        ("Marcus R.", 5, "Genuinely unlike anything else I've read this year -- the trench warfare horror is brutal but the celestial mystery kept me hooked start to finish."),
        ("Priya K.", 2, "Too bleak for me. I get what it's going for but there's only so much misery I can take before it stops feeling meaningful and starts feeling gratuitous."),
        ("Devon W.", 4, "Kraus nails the atmosphere. Loses a star for a middle section that drags, but the ending sticks with you."),
    ],
    "The Director": [
        ("Helena B.", 5, "Chilling in a very quiet way. You watch a smart man talk himself into every single compromise and by the end you understand exactly how it happens."),
        ("Tom Fischer", 5, "Best historical fiction I've read in years. Doesn't lecture you, just shows you the machinery of complicity one small decision at a time."),
        ("Sarah L.", 4, "Dense in places if you don't already know who Pabst was, but worth the effort."),
    ],
    "The Loneliness of Sonia and Sunny": [
        ("Anjali M.", 5, "Desai writes longing better than almost anyone. Took me a while to get through but I didn't want it to end."),
        ("Ravi D.", 4, "Beautiful sentences, slow plot. If you loved The Inheritance of Loss you'll know what you're signing up for."),
        ("Claire O.", 5, "Devastating in the best way. The way it handles distance and timing between the two leads felt painfully real."),
    ],
    "The Sisters": [
        ("Nina S.", 4, "The structure is a lot to keep straight at first but it pays off -- by the third sister's account I was completely hooked."),
        ("Erik L.", 3, "Admired it more than I enjoyed it, if that makes sense. Clever but a bit of a slog in the middle third."),
        ("Malin K.", 5, "One of those books where you immediately want to reread it once you know how it all connects."),
    ],
    "Stone Yard Devotional": [
        ("Grace T.", 5, "Quiet, spare, and completely absorbing if you let it be. Not for readers who need plot, but I found it deeply moving."),
        ("James H.", 2, "I understand the acclaim but nothing really happens for 250 pages. Beautifully written, tested my patience."),
        ("Wendy A.", 4, "The mouse plague as a backdrop to all that grief and guilt is such a strange, effective choice. Stuck with me."),
    ],
    "A Marriage at Sea: A True Story of Love, Obsession, and Shipwreck": [
        ("Kevin P.", 5, "Couldn't put it down. Reads like a thriller even though you sort of know how it ends."),
        ("Louise M.", 5, "Expected a survival story, got a genuinely unflinching look at a marriage too. Elmhirst doesn't flinch from the ugly parts."),
        ("Ahmed R.", 4, "Great pacing, though I wanted a bit more from the 'after' section -- the rescue felt like it wrapped up too fast."),
    ],
    "Mother Emanuel": [
        ("Denise W.", 5, "Essential reading. Sack does the hard work of giving you two hundred years of context most coverage of the shooting never bothered with."),
        ("Michael C.", 5, "Heavy, obviously, but so meticulously reported. This is what long-form journalism should look like."),
        ("Patricia G.", 4, "Thorough to a fault at times -- some of the historical sections could've been tightened -- but the reporting on the victims is unforgettable."),
    ],
    "Mother Mary Comes to Me": [
        ("Divya N.", 4, "Roy's prose is as sharp as ever. The mother-daughter dynamic is messy and honest in a way a lot of memoirs shy away from."),
        ("Ben K.", 5, "As good as I hoped. You can trace a direct line from Mary Roy's fights to everything Arundhati later became."),
        ("Fatima S.", 4, "Beautifully written but emotionally exhausting in places -- Mary Roy is a genuinely difficult person to spend 300 pages with."),
    ],
    "There Is No Place for Us: Working and Homeless in America": [
        ("Chris B.", 5, "This should be required reading. Completely reframed how I think about who 'homeless' even describes."),
        ("Angela F.", 5, "Goldstone treats these families with so much dignity. Rigorous reporting without ever feeling exploitative."),
        ("Marcus J.", 4, "The policy chapters are dense but necessary -- this isn't just misery for its own sake, it's building an actual argument."),
    ],
    "Wild Thing: A Life of Paul Gauguin": [
        ("Oliver T.", 4, "Doesn't let Gauguin off the hook, which I appreciated. Meticulously researched even if it's a lot of biography to get through."),
        ("Isabelle V.", 3, "Well written but I wanted more art criticism and less day-to-day biographical detail."),
        ("Grant D.", 5, "The best Gauguin biography I've read. Prideaux is clear-eyed about the colonial stuff in a way older biographies weren't."),
    ],
}


def main():
    db = SessionLocal()
    added, skipped = 0, 0
    try:
        for title, comments in SAMPLE_COMMENTS.items():
            book = db.query(Book).filter(Book.title == title).first()
            if not book:
                print(f"book not found, skipping: {title!r}")
                continue

            existing_count = db.query(Comment).filter(Comment.book_id == book.id).count()
            if existing_count > 0:
                print(f"skip (already has {existing_count} comment(s)): {title!r}")
                skipped += len(comments)
                continue

            for author_name, rating, body in comments:
                db.add(
                    Comment(
                        book_id=book.id,
                        author_name=author_name,
                        body=body,
                        rating=rating,
                        status="visible",
                        reviewed=True,
                    )
                )
            db.commit()
            print(f"added {len(comments)} comments to {title!r}")
            added += len(comments)
    finally:
        db.close()

    print(f"\nDone. {added} comment(s) added, {skipped} skipped (book already had comments).")


if __name__ == "__main__":
    main()
