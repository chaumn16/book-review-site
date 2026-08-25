import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

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
          <h3>{b.title}</h3>
          <p className="author">by {b.author}</p>
          <p className="meta">
            <span className={`status status-${b.status}`}>{b.status}</span>
            {" · "}
            {b.comment_count} comment{b.comment_count === 1 ? "" : "s"}
          </p>
        </Link>
      ))}
    </div>
  );
}
