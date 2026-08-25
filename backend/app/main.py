import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .database import Base, engine  # noqa: E402  (must load .env first)
from .routers import books, comments  # noqa: E402

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Book Review API")

# Comma-separated list of allowed origins, e.g.
# "https://your-frontend.vercel.app,https://yourdomain.com"
# Defaults to "*" for local dev; set FRONTEND_ORIGINS explicitly in production
# so the API isn't open to every origin on the internet.
_origins_env = os.getenv("FRONTEND_ORIGINS")
_allow_origins = [o.strip() for o in _origins_env.split(",")] if _origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(comments.router)


@app.get("/api/health")
def health():
    # No API key to report on anymore: book generation and comment
    # moderation both run out-of-band via scripts/*.py using the `claude`
    # CLI, not this process. This server never calls an LLM directly.
    return {"ok": True}
