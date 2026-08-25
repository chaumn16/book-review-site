import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BookDetail from "./BookDetail.jsx";
import { api } from "../api.js";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useParams: () => ({ id: "1" }) };
});

vi.mock("../api.js", () => ({
  api: {
    getBook: vi.fn(),
    regenerateBook: vi.fn(),
    listComments: vi.fn(),
    addComment: vi.fn(),
  },
}));

const readyBook = {
  id: 1,
  title: "Dune",
  author: "Frank Herbert",
  status: "ready",
  summary: "A desert planet epic.",
  chapters: [{ chapter_number: 1, chapter_title: "Arrival", highlight: "The Atreides arrive on Arrakis." }],
};

describe("BookDetail", () => {
  beforeEach(() => {
    api.listComments.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state before the book arrives", () => {
    api.getBook.mockReturnValue(new Promise(() => {}));
    render(<BookDetail />);
    expect(screen.getByText(/loading…/i)).toBeInTheDocument();
  });

  it("renders the summary and chapter highlights once ready", async () => {
    api.getBook.mockResolvedValue(readyBook);
    render(<BookDetail />);

    expect(await screen.findByText("Dune")).toBeInTheDocument();
    expect(screen.getByText("A desert planet epic.")).toBeInTheDocument();
    expect(screen.getByText("The Atreides arrive on Arrakis.")).toBeInTheDocument();
  });

  it("shows a pending notice while generation is still running", async () => {
    api.getBook.mockResolvedValue({ ...readyBook, status: "pending", summary: null, chapters: [] });
    render(<BookDetail />);
    expect(await screen.findByText(/generating summary/i)).toBeInTheDocument();
  });

  it("shows an error message when the book fails to load", async () => {
    api.getBook.mockRejectedValue(new Error("Book not found"));
    render(<BookDetail />);
    expect(await screen.findByText("Book not found")).toBeInTheDocument();
  });

  it("retries generation and reloads the book on success", async () => {
    api.getBook
      .mockResolvedValueOnce({ ...readyBook, status: "failed", summary: null, chapters: [] })
      .mockResolvedValueOnce(readyBook);
    api.regenerateBook.mockResolvedValue(readyBook);

    const user = userEvent.setup();
    render(<BookDetail />);

    const retryButton = await screen.findByRole("button", { name: /retry/i });
    await user.click(retryButton);

    expect(api.regenerateBook).toHaveBeenCalledWith("1");
    expect(await screen.findByText("A desert planet epic.")).toBeInTheDocument();
  });
});
