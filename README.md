# Bookish — AI-summarized book review site

A quick prototype: add a popular book by title/author, an LLM generates a whole-book
summary and per-chapter highlights, and readers can leave comments. Comments post and
appear immediately; a separate review process you run yourself screens them shortly
after and takes down anything that breaks the guidelines.

## Stack

- **Backend**: Python, FastAPI + SQLAlchemy + SQLite (zero setup), tested with `pytest`
- **Frontend**: React + Vite + React Router, tested with `vitest` + React Testing Library
- **LLM**: two *different* integration paths, deliberately —
  - Book generation calls the **Anthropic API directly** (`ANTHROPIC_API_KEY`, billed API usage).
  - Comment moderation runs through **your own `claude` Code CLI login** instead — no
    API key, no separate billing, and the backend server never talks to Claude for this
    at all. See below.

## How book generation works

`POST /api/books` saves the book as `pending`, calls Claude (`claude-sonnet-5` via the
Anthropic SDK, [app/llm.py](backend/app/llm.py)) to write a ~250-word summary and 6–15
chapter/section highlights from its general knowledge of the book, then marks it
`ready` (or `failed` if generation errors — retry via `POST /api/books/{id}/regenerate`,
wired to a Retry button on the book page).

## How comment moderation works (async, via your Claude account)

This is **not** the usual "call the API on every request" pattern. It's two decoupled
steps:

1. **Posting is instant.** `POST /api/books/{id}/comments` ([app/routers/comments.py](backend/app/routers/comments.py))
   just writes the comment with `status='visible', reviewed=false` and returns —
   no LLM call, no waiting. It shows up in the list immediately.
2. **You review on your own schedule** by running:
   ```bash
   cd backend
   source .venv/bin/activate
   python scripts/review_comments.py
   ```
   This finds every comment with `reviewed=false`, and for each one shells out to the
   **`claude` Code CLI** (`claude -p "<prompt>"`, headless/non-interactive) — the same
   CLI you're using right now, authenticated with *your* Claude account. It's not the
   Anthropic API: no `ANTHROPIC_API_KEY` involved, no per-call billing outside your
   normal Claude usage. See [app/moderation.py](backend/app/moderation.py).

   Allowed comments get `reviewed=true` and stay `visible`. Flagged comments (harassment,
   hate speech, threats, doxxing, spam, severe abuse) get `status='removed'` and a
   recorded reason — they drop out of the public list on the next fetch. If the CLI call
   itself fails for a given comment (timeout, bad output), that comment is left
   `reviewed=false` and just gets retried the next time you run the script.

   **Prerequisite:** [Claude Code](https://docs.claude.com/claude-code) installed and
   logged in (`claude` on your `PATH`; if it prompts to log in the first time you run it
   interactively, do that once). The script fails fast with a clear message if `claude`
   isn't found — it won't silently skip moderation.

   There's no scheduler built in — running it is a manual choice, by design. If you want
   a cadence instead, wire the same command into `cron` or `launchd` yourself.

   **Known tradeoff:** there's a window between a comment posting and you running the
   review script where bad content is publicly visible. That's the cost of this
   architecture vs. the synchronous alternative — reasonable for a low-traffic prototype
   you're actively watching, worth reconsidering (e.g. shorter review cadence, or a
   scheduled job) if traffic picks up.

## Setup

You'll need [Node.js](https://nodejs.org/) for the frontend, Python 3.9+ for the
backend, and [Claude Code](https://docs.claude.com/claude-code) on your `PATH` if you
want to run the comment reviewer.

### 1. Backend

```bash
cd backend
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...  (only needed for book generation)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 4000
```

Runs on `http://localhost:4000`. SQLite file (`data.sqlite`) is created automatically
on first run — no separate DB setup needed.

**Tests** (no API key or `claude` CLI needed — both are mocked/injected):

```bash
cd backend
source .venv/bin/activate
pytest -v
```

18 tests cover book generation success/failure/retry, comments posting and appearing
immediately, and — the important ones, in `test_moderation.py` — that
`review_pending_comments()` approves clean comments, removes flagged ones, retries
classification errors instead of guessing, and skips already-reviewed comments on a
second run. Verified passing in this environment, including a live smoke test against
the real `claude` CLI (posted a comment, ran `scripts/review_comments.py` for real, and
confirmed a harassing comment actually got taken down with a real reason).

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

Covers `api.js`'s fetch wrapper (including error propagation) and the four pages/
components (`Home`, `AddBook`, `BookDetail`, `CommentSection`) — loading/empty/error
states, form submission, retry-after-failure, and comments posting immediately without
blocking. Not run in this environment (no Node.js available here) but written against
the exact component markup, so they should pass as-is; run `npm test` locally to confirm.

## Deploying

See [DEPLOY.md](DEPLOY.md) for the full walkthrough (Vercel + Render + Neon Postgres,
with `scripts/review_comments.py` still run from your own machine against the deployed
database). `DATABASE_URL` and `FRONTEND_ORIGINS` are already wired up via environment
variables for exactly this; no code changes needed to go from local SQLite to a
deployed Postgres instance.

## Notes / things to harden before this is "real"

- **No auth** — comments are posted with a free-text name, no accounts. Fine for a
  prototype, not for production (add auth + rate limiting before opening this up
  publicly).
- **Comment exposure window** — see "Known tradeoff" above; async moderation means a
  brief window of public visibility before anything bad gets removed.
- **Copyright**: summaries are generated from the model's general knowledge, not by
  reproducing licensed text — that's the intended, safer design for a review site.
  Still spot-check outputs for accuracy, since the model can be wrong about details
  for lesser-known books.
- **SQLite** is great for a prototype; move to Postgres (just change `DATABASE_URL`,
  SQLAlchemy handles the rest) before multiple people write concurrently in production.
