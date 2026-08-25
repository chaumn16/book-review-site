import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api.js";
import CommentSection from "../components/CommentSection.jsx";

export default function BookDetail() {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [error, setError] = useState(null);
  const [retrying, setRetrying] = useState(false);

  function load() {
    api.getBook(id).then(setBook).catch((e) => setError(e.message));
  }

  useEffect(load, [id]);

  async function retry() {
    setRetrying(true);
    try {
      await api.regenerateBook(id);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setRetrying(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!book) return <p>Loading…</p>;

  return (
    <article className="book-detail">
      <h1>{book.title}</h1>
      <p className="author">by {book.author}</p>

      {book.status === "failed" && (
        <div className="notice notice-error">
          Generation failed.{" "}
          <button onClick={retry} disabled={retrying}>
            {retrying ? "Retrying…" : "Retry"}
          </button>
        </div>
      )}
      {book.status === "pending" && <p className="notice">Generating summary…</p>}

      {book.summary && (
        <section>
          <h2>Summary</h2>
          <p className="summary">{book.summary}</p>
        </section>
      )}

      {book.chapters?.length > 0 && (
        <section>
          <h2>Chapter highlights</h2>
          <ol className="chapters">
            {book.chapters.map((c) => (
              <li key={c.chapter_number}>
                <strong>
                  Ch. {c.chapter_number}
                  {c.chapter_title ? ` — ${c.chapter_title}` : ""}
                </strong>
                <p>{c.highlight}</p>
              </li>
            ))}
          </ol>
        </section>
      )}

      <CommentSection bookId={book.id} />
    </article>
  );
}
