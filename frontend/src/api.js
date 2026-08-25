// In dev, "/api" is proxied to the backend by vite.config.js. In production,
// the frontend and backend are typically on different domains (e.g. Vercel +
// Render), so set VITE_API_BASE_URL at build time to the deployed backend's
// full URL, e.g. "https://your-backend.onrender.com/api".
const BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function handle(res) {
  if (!res.ok) {
    let body;
    try {
      body = await res.json();
    } catch {
      body = { error: res.statusText };
    }
    const err = new Error(body.error || "Request failed");
    err.status = res.status;
    err.body = body;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listBooks: (status = "ready") => fetch(`${BASE}/books?status=${status}`).then(handle),
  getBook: (id) => fetch(`${BASE}/books/${id}`).then(handle),
  addBook: (title, author) =>
    fetch(`${BASE}/books`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, author }),
    }).then(handle),
  regenerateBook: (id) => fetch(`${BASE}/books/${id}/regenerate`, { method: "POST" }).then(handle),
  deleteBook: (id) => fetch(`${BASE}/books/${id}`, { method: "DELETE" }).then(handle),
  listComments: (bookId) => fetch(`${BASE}/books/${bookId}/comments`).then(handle),
  addComment: (bookId, author_name, body, rating = null) =>
    fetch(`${BASE}/books/${bookId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ author_name, body, rating }),
    }).then(handle),
};
