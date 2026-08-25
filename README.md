# Bookish — AI-summarized book review site

A quick prototype: add a popular book by title/author, and its summary, chapter
highlights, and a "worth reading?" verdict get generated shortly after. Readers can
leave comments (with an optional star rating), which also post and appear immediately,
then get screened shortly after. Neither of those "shortly after" steps happens
automatically — you run them yourself.

## Stack

- **Backend**: Python, FastAPI + SQLAlchemy + SQLite (zero setup), tested with `pytest`
- **Frontend**: React + Vite + React Router, tested with `vitest` + React Testing Library
- **LLM**: entirely via **your own `claude` Code CLI login** — this server never imports
  the `anthropic` SDK and never needs `ANTHROPIC_API_KEY`. There is no API billing path
  in this app at all; both jobs below run as scripts you invoke yourself, under your own
  Claude account.

Both book generation and comment moderation follow the exact same shape:

1. **The action is instant.** Adding a book or posting a comment just writes a row and
   returns — no LLM call, no waiting.
2. **You process the queue on your own schedule** by running a script that shells out to
   the `claude` CLI (headless, `claude -p "<prompt>"`) for everything waiting.

There's no scheduler built into either — running them is a manual choice, by design. If
you want a cadence instead, wire the same commands into `cron`/`launchd` yourself.

## How book generation works (async, via your Claude account)

1. `POST /api/books` ([app/routers/books.py](backend/app/routers/books.py)) saves the
   book as `status='pending'` and returns immediately — summary, chapters, and verdict
   are all `null`/empty at this point. (Cover art lookup is the one exception: it's a
   free public API call, not an LLM call, so it still happens synchronously here.) A
   `pending` book isn't listed on the home page yet — see `test_only_ready_books_are_listed`.
2. **You generate on your own schedule** by running:
   ```bash
   cd backend
   source .venv/bin/activate
   python scripts/generate_books.py
   ```
   This finds every book with `status='pending'`, and for each one shells out to the
   `claude` CLI to write a ~250-word summary, 6–15 chapter/section highlights, and a
   `worth_it`/`depends`/`skip` verdict with reasoning (explicitly told not to default to
   praise). See [app/generation.py](backend/app/generation.py).

   Success sets `status='ready'` and the book shows up on the home page. Failure sets
   `status='failed'` — visit the book page directly and hit **Retry** (or
   `POST /api/books/{id}/regenerate`) to queue it again; failures aren't silently
   retried forever. The book detail page polls automatically every 8s while `pending`,
   so it picks up the result without a manual reload once you've run the script.

## How comment moderation works (async, via your Claude account)

1. **Posting is instant.** `POST /api/books/{id}/comments`
   ([app/routers/comments.py](backend/app/routers/comments.py)) just writes the comment
   with `status='visible', reviewed=false` and returns — it shows up immediately.
2. **You review on your own schedule** by running:
   ```bash
   cd backend
   source .venv/bin/activate
   python scripts/review_comments.py
   ```
   This finds every comment with `reviewed=false` and shells out to the `claude` CLI to
   classify it. See [app/moderation.py](backend/app/moderation.py).

   Allowed comments get `reviewed=true` and stay `visible`. Flagged comments (harassment,
   hate speech, threats, doxxing, spam, severe abuse) get `status='removed'` and a
   recorded reason — they drop out of the public list on the next fetch. A CLI failure
   for a given comment leaves it `reviewed=false` for the next run, rather than guessing.

   **Known tradeoff:** there's a window between a comment posting and you running the
   review script where bad content is publicly visible. Reasonable for a low-traffic
   prototype you're actively watching; worth reconsidering (shorter cadence, or a
   scheduled job) if traffic picks up.

**Prerequisite for both scripts:** [Claude Code](https://docs.claude.com/claude-code)
installed and logged in (`claude` on your `PATH`; if it prompts to log in the first time
you run it interactively, do that once). Both scripts fail fast with a clear message if
`claude` isn't found — they won't silently skip the work.

See [backend/scripts/README.md](backend/scripts/README.md) for full usage details on
these two (options, example output, failure/retry behavior) plus the one-off seed
scripts in that same directory.

## Setup

You'll need [Node.js](https://nodejs.org/) for the frontend, Python 3.9+ for the
backend, and [Claude Code](https://docs.claude.com/claude-code) on your `PATH` to run
either of the two scripts above.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 4000
```

No `.env` file is required to run the app itself — there's no API key needed anywhere in
this server. (`.env.example` documents `DATABASE_URL`/`FRONTEND_ORIGINS`, which matter
once you deploy — see below — but both have working local defaults.)

Runs on `http://localhost:4000`. SQLite file (`data.sqlite`) is created automatically
on first run — no separate DB setup needed.

**Tests** (no `claude` CLI or network access needed — both are injected/mocked):

```bash
cd backend
source .venv/bin/activate
pytest -v
```

39 tests. The important ones: `test_generation.py` covers `generate_pending_books()`
generating content, skipping already-generated books, clearing stale chapters on
regeneration, and marking (not silently retrying) failures; `test_moderation.py` covers
the equivalent for comments. Verified passing in this environment, including live smoke
tests against the real `claude` CLI for both scripts (added a book and a comment, ran
both scripts for real, confirmed generation *and* a harassing-comment takedown actually
happened with real Claude output — not mocked).

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api/*` to the backend.

**Tests:**

```bash
cd frontend
npm install
npm test
```

Covers `api.js`'s fetch wrapper, and the pages/components (`Home`, `AddBook`,
`BookDetail`, `CommentSection`) — loading/empty/error states, form submission, the
pending-book polling behavior, and comments posting immediately without blocking. Not
run in this environment (no Node.js available here) but written against the exact
component markup, so they should pass as-is; run `npm test` locally to confirm.

## Deploying

See [DEPLOY.md](DEPLOY.md) for the full walkthrough (Vercel + Render + Neon Postgres,
with both scripts above still run from your own machine against the deployed database —
your Claude login shouldn't live on a server). `DATABASE_URL` and `FRONTEND_ORIGINS` are
already wired up via environment variables for exactly this; no code changes needed to
go from local SQLite to a deployed Postgres instance.

## Notes / things to harden before this is "real"

- **No auth** — comments are posted with a free-text name, no accounts. Fine for a
  prototype, not for production (add auth + rate limiting before opening this up
  publicly).
- **Exposure/visibility windows** — see "Known tradeoff" above for comments; the
  equivalent for books is just a `pending` book sitting unlisted until you run the
  generation script, which is lower-stakes (nothing wrong is shown, it's just not there
  yet).
- **Copyright**: summaries are generated from the model's general knowledge, not by
  reproducing licensed text — that's the intended, safer design for a review site.
  Still spot-check outputs for accuracy, since the model can be wrong about details
  for lesser-known books.
- **SQLite** is great for a prototype; move to Postgres (just change `DATABASE_URL`,
  SQLAlchemy handles the rest) before multiple people write concurrently in production.
