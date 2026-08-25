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
    expect(api.addComment).toHaveBeenCalledWith(1, "Bob", "Great read");
    expect(await screen.findByText("Great read")).toBeInTheDocument();
    expect(api.listComments).toHaveBeenCalledTimes(2);
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
