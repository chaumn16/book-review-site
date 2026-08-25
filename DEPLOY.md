# Deploying Bookish

Three pieces, three destinations:

| Piece | Where | Why |
|---|---|---|
| Frontend (static build) | [Vercel](https://vercel.com) | Free tier, connects straight to your GitHub repo, auto-deploys on push |
| Backend (FastAPI) | [Render](https://render.com) | Free/cheap tier that runs a real Python process |
| Database | [Neon](https://neon.tech) (Postgres) | Free tier, reachable from anywhere -- including your laptop, which matters below |

**`scripts/generate_books.py` and `scripts/review_comments.py` both still run on your own machine**, not on Render — they shell out to your locally-authenticated `claude` CLI, and your Claude account credentials shouldn't live on a cloud server. This is exactly why Postgres (not SQLite) matters here: your laptop needs to reach the same database the deployed backend writes to, over the network, and SQLite can't do that. The deployed backend itself never calls an LLM at all -- no API key involved anywhere in this deployment.

## 1. Create the Postgres database (Neon)

1. Sign up at [neon.tech](https://neon.tech), create a project.
2. Copy the connection string it gives you (looks like `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require`). You'll use this exact string in two places below.

## 2. Deploy the backend (Render)

1. Push this repo to GitHub if you haven't (it already is, per your earlier setup).
2. On [render.com](https://render.com): New → Web Service → connect the `book-review-site` repo.
3. Settings:
   - **Root directory**: `backend`
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables (Render's dashboard → Environment):
   - `DATABASE_URL` — the Neon connection string from step 1
   - `FRONTEND_ORIGINS` — leave this blank for now, you'll fill it in after step 3 once you know your Vercel URL

   No API key needed — this server never calls an LLM.
5. Deploy. Note the URL Render gives you, e.g. `https://book-review-site.onrender.com`.
6. Sanity check: `curl https://book-review-site.onrender.com/api/health` should return `{"ok":true}`.

## 3. Deploy the frontend (Vercel)

1. On [vercel.com](https://vercel.com): New Project → same repo.
2. Settings:
   - **Root directory**: `frontend`
   - **Build command**: `npm run build` (default)
   - **Output directory**: `dist` (default for Vite)
3. Environment variable:
   - `VITE_API_BASE_URL` = `https://book-review-site.onrender.com/api` (your Render URL from step 2, + `/api`)
4. Deploy. Note the URL Vercel gives you, e.g. `https://bookish.vercel.app`.

## 4. Close the loop: lock down CORS

Back in Render's environment variables, set:
```
FRONTEND_ORIGINS=https://bookish.vercel.app
```
Redeploy the backend so it picks up the change. Without this it defaults to `*` (any origin can call your API) — fine while testing, worth tightening once you have a real frontend URL.

## 5. Seed the deployed database

From your own machine, point the seed script at the *same* Neon URL instead of your local SQLite file:

```bash
cd backend
source .venv/bin/activate
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require" python scripts/seed_top10_2025.py
```

This inserts the 10 books (with their verdicts and covers already baked in) directly into the production database. Same idempotent behavior as before — safe to re-run.

## 6. Running the generation and moderation scripts against production

Same idea — point either at the same `DATABASE_URL`:

```bash
cd backend
source .venv/bin/activate
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require" python scripts/generate_books.py
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require" python scripts/review_comments.py
```

Run these by hand whenever you want to catch up on books added or comments posted on
the live site. (If you'd rather not retype the connection string every time, put it in
`backend/.env` locally — `python-dotenv` already loads it automatically, and this file
is gitignored.)

Full usage details (options, example output, what counts as a retry vs. a failure) are
in [backend/scripts/README.md](backend/scripts/README.md).

## Costs

All three tiers above have a free option as of writing: Neon's free tier, Vercel's free/hobby tier, and Render's free web service tier (which does spin down after inactivity and takes ~30s to wake back up on the next request — fine for a low-traffic personal site, worth upgrading to a paid tier if that cold-start delay bothers you or real users start hitting it).
