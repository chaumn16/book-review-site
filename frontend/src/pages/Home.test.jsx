import { render, screen } from "@testing-library/react";
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

  it("renders each book once loaded", async () => {
    api.listBooks.mockResolvedValue([
      { id: 1, title: "Dune", author: "Frank Herbert", status: "ready", comment_count: 2 },
    ]);
    renderHome();

    expect(await screen.findByText("Dune")).toBeInTheDocument();
    expect(screen.getByText("by Frank Herbert")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    // Text is split across sibling nodes ("2", "comment", "s"), so match on
    // the containing element's full text content instead of an exact string.
    expect(
      screen.getByText((_, node) => node?.className === "meta" && node.textContent.includes("2 comments"))
    ).toBeInTheDocument();
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
});
