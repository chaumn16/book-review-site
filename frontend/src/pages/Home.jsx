import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { VerdictPill } from "../components/VerdictBadge.jsx";
import StarRating from "../components/StarRating.jsx";
import BookCover from "../components/BookCover.jsx";

const TABS = [
  { key: "ready", label: "Library" },
  { key: "pending", label: "Just Added" },
];

export default function Home() {
  const [tab, setTab] = useState("ready");
  const [books, setBooks] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setBooks(null);
    setError(null);
    api.listBooks(tab).then(setBooks).catch((e) => setError(e.message));
  }, [tab]);

  let body;
  if (error) {
    body = <p className="error">Failed to load books: {error}</p>;
  } else if (!books) {
    body = <p>Loading books…</p>;
  } else if (books.length === 0) {
    body =
      tab === "pending" ? (
        <p>Nothing pending — every added book has already been generated.</p>
      ) : (
        <p>
          No books yet. <Link to="/add">Add the first one</Link>.
        </p>
      );
  } else {
    body = (
      <div className="book-grid">
        {books.map((b) => (
          <Link to={`/books/${b.id}`} key={b.id} className="book-card">
            <BookCover src={b.cover_url} title={b.title} />
            {tab === "ready" && <VerdictPill label={b.verdict_label} />}
            <h3>{b.title}</h3>
            <p className="author">by {b.author}</p>
            {tab === "ready" ? (
              <>
                <StarRating average={b.average_rating} count={b.rating_count} />
                <p className="meta">
                  {b.comment_count} comment{b.comment_count === 1 ? "" : "s"}
                </p>
              </>
            ) : (
              <p className="notice">⏳ Waiting to be generated</p>
            )}
          </Link>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className={tab === t.key ? "tab tab-active" : "tab"}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {body}
    </div>
  );
}
