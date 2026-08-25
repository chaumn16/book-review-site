import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { VerdictPill } from "../components/VerdictBadge.jsx";
import StarRating from "../components/StarRating.jsx";
import BookCover from "../components/BookCover.jsx";

export default function Home() {
  const [books, setBooks] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listBooks().then(setBooks).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">Failed to load books: {error}</p>;
  if (!books) return <p>Loading books…</p>;
  if (books.length === 0) {
    return (
      <p>
        No books yet. <Link to="/add">Add the first one</Link>.
      </p>
    );
  }

  return (
    <div className="book-grid">
      {books.map((b) => (
        <Link to={`/books/${b.id}`} key={b.id} className="book-card">
          <BookCover src={b.cover_url} title={b.title} />
          <VerdictPill label={b.verdict_label} />
          <h3>{b.title}</h3>
          <p className="author">by {b.author}</p>
          <StarRating average={b.average_rating} count={b.rating_count} />
          <p className="meta">
            {b.comment_count} comment{b.comment_count === 1 ? "" : "s"}
          </p>
        </Link>
      ))}
    </div>
  );
}
