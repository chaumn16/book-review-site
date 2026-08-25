import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Home from "./Home.jsx";
import { api } from "../api.js";

vi.mock("../api.js", () => ({
  api: { listBooks: vi.fn() },
}));

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>
  );
}

describe("Home", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("shows a loading state before the books arrive", () => {
    api.listBooks.mockReturnValue(new Promise(() => {})); // never resolves
    renderHome();
    expect(screen.getByText(/loading books/i)).toBeInTheDocument();
  });

  it("renders each book once loaded, with no status badge", async () => {
    // The API only ever lists ready books now, so there's nothing to
    // display -- listBooks() responses don't even carry a `status` field.
    api.listBooks.mockResolvedValue([{ id: 1, title: "Dune", author: "Frank Herbert", comment_count: 2 }]);
    renderHome();

    expect(await screen.findByText("Dune")).toBeInTheDocument();
    expect(screen.getByText("by Frank Herbert")).toBeInTheDocument();
    expect(screen.queryByText("ready")).not.toBeInTheDocument();
    // Text is split across sibling nodes ("2", "comment", "s"), so match on
    // the containing element's full text content instead of an exact string.
    expect(
      screen.getByText((_, node) => node?.className === "meta" && node.textContent.includes("2 comments"))
    ).toBeInTheDocument();
  });

  it("renders a cover image when the book has one", async () => {
    api.listBooks.mockResolvedValue([
      { id: 1, title: "Dune", author: "Frank Herbert", comment_count: 0, cover_url: "https://covers.example.com/dune.jpg" },
    ]);
    renderHome();

    const img = await screen.findByRole("img", { name: "Cover of Dune" });
    expect(img).toHaveAttribute("src", "https://covers.example.com/dune.jpg");
  });

  it("shows a placeholder instead of an image when the book has no cover", async () => {
    api.listBooks.mockResolvedValue([{ id: 1, title: "Dune", author: "Frank Herbert", comment_count: 0 }]);
    renderHome();

    await screen.findByText("Dune");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("📖")).toBeInTheDocument();
  });

  it("shows the verdict pill and average rating when present", async () => {
    api.listBooks.mockResolvedValue([
      {
        id: 1,
        title: "Dune",
        author: "Frank Herbert",
        comment_count: 3,
        verdict_label: "worth_it",
        average_rating: 4.5,
        rating_count: 2,
      },
    ]);
    renderHome();

    expect(await screen.findByText(/worth it/i)).toBeInTheDocument();
    expect(screen.getByText("4.5 (2)")).toBeInTheDocument();
  });

  it("renders no verdict pill or rating when the book has neither", async () => {
    api.listBooks.mockResolvedValue([{ id: 1, title: "Dune", author: "Frank Herbert", comment_count: 0 }]);
    renderHome();

    await screen.findByText("Dune");
    expect(screen.queryByText(/worth it|depends|skip/i)).not.toBeInTheDocument();
  });

  it("shows an empty state with a link to add the first book", async () => {
    api.listBooks.mockResolvedValue([]);
    renderHome();
    expect(await screen.findByText(/no books yet/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /add the first one/i })).toHaveAttribute("href", "/add");
  });

  it("shows an error message when the fetch fails", async () => {
    api.listBooks.mockRejectedValue(new Error("network down"));
    renderHome();
    expect(await screen.findByText(/failed to load books: network down/i)).toBeInTheDocument();
  });

  it("fetches the ready catalog by default", async () => {
    api.listBooks.mockResolvedValue([]);
    renderHome();
    await screen.findByText(/no books yet/i);
    expect(api.listBooks).toHaveBeenCalledWith("ready");
  });

  it("switches to the Just Added tab and fetches pending books", async () => {
    api.listBooks
      .mockResolvedValueOnce([{ id: 1, title: "Dune", author: "Frank Herbert", comment_count: 0 }]) // ready
      .mockResolvedValueOnce([{ id: 2, title: "Still Cooking", author: "Someone", comment_count: 0 }]); // pending

    const user = userEvent.setup();
    renderHome();
    await screen.findByText("Dune");

    await user.click(screen.getByRole("tab", { name: /just added/i }));

    expect(await screen.findByText("Still Cooking")).toBeInTheDocument();
    expect(api.listBooks).toHaveBeenLastCalledWith("pending");
    // Pending cards show a waiting notice instead of verdict/rating/comments.
    expect(screen.getByText(/waiting to be generated/i)).toBeInTheDocument();
    expect(screen.queryByText(/comment/)).not.toBeInTheDocument();
  });

  it("shows a pending-specific empty state on the Just Added tab", async () => {
    api.listBooks.mockResolvedValueOnce([]).mockResolvedValueOnce([]);

    const user = userEvent.setup();
    renderHome();
    await screen.findByText(/no books yet/i);

    await user.click(screen.getByRole("tab", { name: /just added/i }));

    expect(await screen.findByText(/nothing pending/i)).toBeInTheDocument();
  });
});
