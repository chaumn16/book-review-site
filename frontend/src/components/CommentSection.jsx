import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function CommentSection({ bookId }) {
  const [comments, setComments] = useState(null);
  const [name, setName] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  function refresh() {
    api.listComments(bookId).then(setComments).catch(() => setComments([]));
  }

  useEffect(refresh, [bookId]);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      await api.addComment(bookId, name, body);
      setBody("");
      setNotice({ type: "ok", text: "Comment posted." });
      refresh();
    } catch (err) {
      // Posting itself no longer runs moderation -- it only fails for
      // validation errors (empty fields) or the book not existing.
      setNotice({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="comments">
      <h2>Comments</h2>

      <form onSubmit={onSubmit} className="comment-form">
        <input
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <textarea
          placeholder="What did you think of this book?"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={3}
        />
        {notice && <p className={`notice notice-${notice.type}`}>{notice.text}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Posting…" : "Post comment"}
        </button>
        <p className="hint">
          Comments appear right away. They're screened shortly after by the site owner's
          review process — anything that breaks the guidelines gets taken down.
        </p>
      </form>

      {comments === null && <p>Loading comments…</p>}
      {comments?.length === 0 && <p>No comments yet — be the first.</p>}
      <ul className="comment-list">
        {comments?.map((c) => (
          <li key={c.id}>
            <strong>{c.author_name}</strong>
            <span className="comment-date">{new Date(c.created_at).toLocaleDateString()}</span>
            <p>{c.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
