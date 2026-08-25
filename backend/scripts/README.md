# scripts/

Five scripts. Two are the **async LLM processes** referenced throughout the main
[README](../../README.md) — you run these regularly, by hand, whenever you want to catch
up on work waiting in the database. The other three are one-off/seed scripts, run once
(or occasionally) to load data, not part of the app's normal operation.

All of them assume the same setup:

```bash
cd backend                    # scripts insert their own path, but run from here anyway
source .venv/bin/activate
python scripts/<script>.py
```

They all connect via `DATABASE_URL` the same way the app does (defaulting to the local
`sqlite:///./data.sqlite` if unset) — see the main README's `.env.example` notes. To run
one against a deployed database instead of your local file, prefix the command:

```bash
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require" python scripts/generate_books.py
```

---

## The async processes

Both of these:
- Use the **`claude` Code CLI** (`claude -p "<prompt>"`, headless) — **your own logged-in
  Claude account**, not the Anthropic API. No `ANTHROPIC_API_KEY` is used anywhere.
- **Fail fast** with a clear message if `claude` isn't found on `PATH`, rather than
  silently skipping work.
- Have **no built-in scheduler** — that's intentional. Running them is a manual choice.
  If you want a cadence instead, wire the same command into `cron`/`launchd` yourself.
- Accept an optional `--model <value>`, passed straight through to `claude -p ... --model
  <value>`. Omit it to use whatever your `claude` CLI defaults to.

### `generate_books.py` — write summaries, chapter highlights, and verdicts

**What it's for:** every book you add via the site (or queue via the book page's
**Retry** button) sits with `status='pending'` — no title/author-only placeholder is
ever shown as a real book — until this runs.

```bash
python scripts/generate_books.py
python scripts/generate_books.py --model haiku   # optional
```

**What happens:** finds every book with `status='pending'`, and for each one asks Claude
for a ~250-word summary, 6–15 chapter/section highlights, and a `worth_it` / `depends` /
`skip` verdict with reasoning (explicitly instructed not to default to praise). On
success: `status` becomes `ready` and the book shows up on the home page. On failure
(bad/unparseable output, CLI error, timeout): `status` becomes `failed` — it is **not**
retried automatically; visit the book page and hit **Retry** (or call
`POST /api/books/{id}/regenerate`) to queue it again. The book detail page polls every
8 seconds while `pending`, so it'll pick up the result on its own once you've run this.

**Example output:**
```
Processed 1 pending book(s): 1 generated, 0 failed (use the Retry button on the book
page, or POST /api/books/{id}/regenerate, to queue them again).
```

Logic lives in [`app/generation.py`](../app/generation.py); tests in
[`tests/test_generation.py`](../tests/test_generation.py) (all mocked/injected — no real
`claude` calls in the test suite).

### `review_comments.py` — screen comments for harmful content

**What it's for:** every posted comment shows up on the site **immediately** — posting
never waits on this. This is what actually screens it.

```bash
python scripts/review_comments.py
python scripts/review_comments.py --model haiku   # optional
```

**What happens:** finds every comment with `reviewed=false`, and for each one asks
Claude to classify it (harassment, hate speech, threats, doxxing, spam, and severe abuse
get flagged; ordinary negative opinions are allowed). Allowed comments get
`reviewed=true` and stay visible. Flagged comments get `status='removed'` (they drop out
of the public list and the book's average-rating calculation on the next fetch) plus a
recorded reason. A CLI failure for a given comment leaves it `reviewed=false` so the
*next* run retries it automatically — unlike book generation, there's no separate
"retry" action needed here.

**Example output:**
```
Reviewed 2 pending comment(s): 1 approved, 1 blocked, 0 left pending (classification
errors, will retry next run).
```

Logic lives in [`app/moderation.py`](../app/moderation.py); tests in
[`tests/test_moderation.py`](../tests/test_moderation.py) (same mocked/injected pattern).

**Known tradeoff for both scripts:** there's a window between something posting and you
running the relevant script where it's live but not yet processed. For books, that just
means the book isn't listed yet — nothing wrong is shown. For comments, it means
unmoderated content is briefly public. Reasonable for a low-traffic site you're actively
watching; shorten your cadence (or add a scheduled job) if that's not true anymore.

---

## One-off / seed scripts

These don't use the `claude` CLI at all — either no LLM is involved, or (for the seed
data) the content was already hand-written once and is just being inserted.

### `seed_top10_2025.py`

Seeds the database with the New York Times' "10 Best Books of 2025" — title, author,
summary, chapter highlights, verdict, and cover URL, all hand-written/researched ahead
of time (see the file for sourcing notes) rather than generated at runtime. **Idempotent
in two ways:** skips a book entirely if it's already present with a verdict, but will
backfill just the verdict and/or cover_url into an existing row if either is missing
(e.g. from before those fields existed) — safe to re-run any time.

```bash
python scripts/seed_top10_2025.py
```

### `backfill_covers.py`

For any book missing `cover_url` (regardless of source — new books already get this
automatically at creation time via `app/covers.py`), looks one up via Open Library, then
Google Books as a fallback. Free public APIs, no `claude` CLI involved.

```bash
python scripts/backfill_covers.py
```

### `seed_sample_comments.py`

Inserts 3 hand-written reader comments (each with a 1–5 rating) per book — 30 total —
so the average-rating display has real data to show. Inserted directly as
`reviewed=true`/`visible` since the content is already known-clean; doesn't go through
`review_comments.py`. Skips any book that already has at least one comment, so it's safe
to re-run without duplicating.

```bash
python scripts/seed_sample_comments.py
```
