import { api } from "./api.js";

function mockFetchOnce(status, body) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: "Error",
    json: async () => body,
  });
}

describe("api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("listBooks defaults to the ready catalog", async () => {
    mockFetchOnce(200, [{ id: 1, title: "Dune" }]);
    const result = await api.listBooks();
    expect(global.fetch).toHaveBeenCalledWith("/api/books?status=ready");
    expect(result).toEqual([{ id: 1, title: "Dune" }]);
  });

  it("listBooks passes through an explicit status", async () => {
    mockFetchOnce(200, [{ id: 2, title: "Still Cooking" }]);
    const result = await api.listBooks("pending");
    expect(global.fetch).toHaveBeenCalledWith("/api/books?status=pending");
    expect(result).toEqual([{ id: 2, title: "Still Cooking" }]);
  });

  it("addBook posts JSON and returns the created book", async () => {
    mockFetchOnce(201, { id: 1, title: "Dune", author: "Frank Herbert" });
    const result = await api.addBook("Dune", "Frank Herbert");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/books",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "Dune", author: "Frank Herbert" }),
      })
    );
    expect(result.id).toBe(1);
  });

  it("addComment sends rating: null by default, or the given rating", async () => {
    mockFetchOnce(201, { id: 1, author_name: "Alice", body: "Great!", rating: null });
    await api.addComment(1, "Alice", "Great!");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/books/1/comments",
      expect.objectContaining({
        body: JSON.stringify({ author_name: "Alice", body: "Great!", rating: null }),
      })
    );

    await api.addComment(1, "Alice", "Great!", 5);
    expect(global.fetch).toHaveBeenLastCalledWith(
      "/api/books/1/comments",
      expect.objectContaining({
        body: JSON.stringify({ author_name: "Alice", body: "Great!", rating: 5 }),
      })
    );
  });

  it("throws an Error carrying the server-provided message on failure", async () => {
    mockFetchOnce(404, { error: "Book not found" });
    await expect(api.getBook(999)).rejects.toThrow("Book not found");
  });

  it("attaches status and body to thrown errors", async () => {
    mockFetchOnce(422, { error: "Comment removed by moderation", reason: "spam" });
    await expect(api.addComment(1, "Bob", "buy my crypto now")).rejects.toMatchObject({
      status: 422,
      body: { error: "Comment removed by moderation", reason: "spam" },
    });
  });

  it("deleteBook resolves to null on a 204 No Content response", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 204 });
    const result = await api.deleteBook(1);
    expect(result).toBeNull();
  });
});
