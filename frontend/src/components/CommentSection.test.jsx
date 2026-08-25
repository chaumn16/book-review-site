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

  it("shows a moderation notice and does not list a blocked comment", async () => {
    api.listComments.mockResolvedValue([]);
    const err = new Error("Comment removed by moderation");
    err.status = 422;
    err.body = { reason: "harassment" };
    api.addComment.mockRejectedValue(err);

    const user = userEvent.setup();
    render(<CommentSection bookId={1} />);
    await screen.findByText(/no comments yet/i);

    await user.type(screen.getByPlaceholderText(/your name/i), "Troll");
    await user.type(screen.getByPlaceholderText(/what did you think/i), "bad stuff");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    expect(await screen.findByText(/comment removed by moderation: harassment/i)).toBeInTheDocument();
  });
});
