# Bookish — AI-summarized book review site

A quick prototype: add a popular book by title/author, an LLM generates a whole-book
summary and per-chapter highlights, and readers can leave comments that are
auto-screened by a second LLM call before they ever appear.

## Stack

- **Backend**: Python, FastAPI + SQLAlchemy + SQLite (zero setup) + Anthropic API,
  tested with `pytest`
- **Frontend**: React + Vite + React Router, tested with `vitest` + React Testing Library

## How generation & moderation work

- `POST /api/books` saves the book as `pending`, calls Claude (`claude-sonnet-5`) to
  write a ~250-word summary and 6–15 chapter/section highlights from its general
  knowledge of the book, then marks it `ready` (or `failed` if generation errors —
  retry via `POST /api/books/{id}/regenerate`, wired to a Retry button on the book page).
- `POST /api/books/{id}/comments` sends the comment body to Claude
  (`claude-haiku-4-5-20251001`) for a fast allowed/not-allowed classification
  (harassment, hate speech, threats, doxxing, spam, severe abuse → blocked; ordinary
  negative opinions are allowed) **before** it's ever shown. Blocked comments are
  stored with `status='removed'` and a reason, but never returned by the list endpoint.
  If the moderation call itself errors, the comment is held back rather than published
  unmoderated (fails closed).

## Setup

You'll need [Node.js](https://nodejs.org/) for the frontend (this environment didn't
have it, so that scaffold was hand-written rather than `npm create vite`'d — structure
is standard, `npm install` works normally) and Python 3.9+ for the backend.

### 1. Backend

```bash
cd backend
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 4000
```

Runs on `http://localhost:4000`. SQLite file (`data.sqlite`) is created automatically
on first run — no separate DB setup needed.

**Tests** (no API key needed — the LLM calls are mocked):

```bash
cd backend
source .venv/bin/activate
pytest -v
```

13 tests cover book generation success/failure/retry, comment posting, and — the
important one — that a comment flagged by moderation is blocked and never appears in
the public list. Verified passing in this environment.

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
states, form submission, retry-after-failure, and the moderation-blocked comment flow.
Not run in this environment (no Node.js available here) but written against the exact
component markup, so they should pass as-is; run `npm test` locally to confirm.

## Notes / things to harden before this is "real"

- **No auth** — comments are posted with a free-text name, no accounts. Fine for a
  prototype, not for production (add auth + rate limiting before opening this up
  publicly).
- **Copyright**: summaries are generated from the model's general knowledge, not by
  reproducing licensed text — that's the intended, safer design for a review site.
  Still spot-check outputs for accuracy, since the model can be wrong about details
  for lesser-known books.
- **SQLite** is great for a prototype; move to Postgres (just change `DATABASE_URL`,
  SQLAlchemy handles the rest) before multiple people write concurrently in production.
