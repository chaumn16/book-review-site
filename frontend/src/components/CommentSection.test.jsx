import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CommentSection from "./CommentSection.jsx";
import { api } from "../api.js";

vi.mock("../api.js", () => ({
  api: { listComments: vi.fn(), addComment: vi.fn() },
}));

describe("CommentSection", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("lists existing visible comments", async () => {
    api.listComments.mockResolvedValue([
      { id: 1, author_name: "Alice", body: "Loved it", created_at: "2024-01-01T00:00:00Z" },
    ]);
    render(<CommentSection bookId={1} />);

    expect(await screen.findByText("Loved it")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("shows a comment's star rating when it has one, nothing when it doesn't", async () => {
    api.listComments.mockResolvedValue([
      { id: 1, author_name: "Alice", body: "Loved it", rating: 4, created_at: "2024-01-01T00:00:00Z" },
      { id: 2, author_name: "Bob", body: "It was ok", rating: null, created_at: "2024-01-02T00:00:00Z" },
    ]);
    render(<CommentSection bookId={1} />);

    const aliceRating = await screen.findByLabelText("Rated 4 out of 5");
    expect(aliceRating).toHaveTextContent("★★★★☆");
    // Only Alice's comment has a rating -- Bob's has none.
    expect(screen.getAllByLabelText(/rated .* out of 5/i)).toHaveLength(1);
  });

  it("shows an empty state when there are no comments", async () => {
    api.listComments.mockResolvedValue([]);
    render(<CommentSection bookId={1} />);
    expect(await screen.findByText(/no comments yet/i)).toBeInTheDocument();
  });

  it("posts a comment and refreshes the visible list", async () => {
    api.listComments
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: 2, author_name: "Bob", body: "Great read", created_at: "2024-01-02T00:00:00Z" },
      ]);
    api.addComment.mockResolvedValue({ id: 2, author_name: "Bob", body: "Great read" });

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.type(screen.getByPlaceholderText(/your name/i), "Bob");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "Great read");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(await screen.findByText("Comment posted.")).toBeInTheDocument();
    expect(api.addComment).toHaveBeenCalledWith(1, "Bob", "Great read", null);
    expect(await screen.findByText("Great read")).toBeInTheDocument();
    expect(api.listComments).toHaveBeenCalledTimes(2);
  });

  it("includes a selected star rating when posting", async () => {
    api.listComments.mockResolvedValue([]);
    api.addComment.mockResolvedValue({ id: 4, author_name: "Cara", body: "Loved it", rating: 5 });

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.type(screen.getByPlaceholderText(/your name/i), "Cara");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "Loved it");
    await user.click(screen.getByRole("radio", { name: "5 stars" }));
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(api.addComment).toHaveBeenCalledWith(1, "Cara", "Loved it", 5);
  });

  it("clicking a selected star again clears the rating", async () => {
    api.listComments.mockResolvedValue([]);
    api.addComment.mockResolvedValue({ id: 5, author_name: "Cara", body: "hi" });

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.click(screen.getByRole("radio", { name: "3 stars" }));
    expect(screen.getByRole("radio", { name: "3 stars" })).toHaveAttribute("aria-checked", "true");

    await user.click(screen.getByRole("radio", { name: "3 stars" }));
    expect(screen.getByRole("radio", { name: "3 stars" })).toHaveAttribute("aria-checked", "false");

    await user.type(screen.getByPlaceholderText(/your name/i), "Cara");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "hi");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(api.addComment).toHaveBeenCalledWith(1, "Cara", "hi", null);
  });

  it("posts even harsh-sounding content immediately -- moderation isn't synchronous", async () => {
    // There's no inline moderation call anymore: posting only fails for
    // validation errors or a missing book, never because of content.
    api.listComments
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: 3, author_name: "Troll", body: "this book was trash", created_at: "2024-01-03T00:00:00Z" },
      ]);
    api.addComment.mockResolvedValue({ id: 3, author_name: "Troll", body: "this book was trash" });

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.type(screen.getByPlaceholderText(/your name/i), "Troll");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "this book was trash");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(await screen.findByText("Comment posted.")).toBeInTheDocument();
    expect(await screen.findByText("this book was trash")).toBeInTheDocument();
  });

  it("shows a generic error notice when posting fails", async () => {
    api.listComments.mockResolvedValue([]);
    api.addComment.mockRejectedValue(new Error("Book not found"));

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.type(screen.getByPlaceholderText(/your name/i), "Alice");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "hello");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(await screen.findByText("Book not found")).toBeInTheDocument();
  });
});
