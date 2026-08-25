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

  it("renders the verdict callout with its reasoning", async () => {
    api.getBook.mockResolvedValue({
      ...readyBook,
      verdict_label: "depends",
      verdict_reason: "Great if you like slow-burn plots, not if you want action.",
    });
    render(<BookDetail />);

    expect(await screen.findByText(/depends/i)).toBeInTheDocument();
    expect(screen.getByText("Great if you like slow-burn plots, not if you want action.")).toBeInTheDocument();
  });

  it("renders no verdict callout when the book has none", async () => {
    api.getBook.mockResolvedValue(readyBook);
    render(<BookDetail />);

    await screen.findByText("Dune");
    expect(screen.queryByText(/worth it|depends|skip/i)).not.toBeInTheDocument();
  });

  it("renders the average rating in the header when present", async () => {
    api.getBook.mockResolvedValue({ ...readyBook, average_rating: 3.7, rating_count: 9 });
    render(<BookDetail />);

    expect(await screen.findByText("3.7 (9)")).toBeInTheDocument();
  });

  it("renders a cover image when the book has one, a placeholder otherwise", async () => {
    api.getBook.mockResolvedValue({ ...readyBook, cover_url: "https://covers.example.com/dune.jpg" });
    render(<BookDetail />);

    const img = await screen.findByRole("img", { name: "Cover of Dune" });
    expect(img).toHaveAttribute("src", "https://covers.example.com/dune.jpg");
  });

  it("shows a pending notice while generation is still running", async () => {
    api.getBook.mockResolvedValue({ ...readyBook, status: "pending", summary: null, chapters: [] });
    render(<BookDetail />);
    expect(await screen.findByText(/waiting to be generated/i)).toBeInTheDocument();
  });

  it("polls while pending and picks up the book once it's ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api.getBook
      .mockResolvedValueOnce({ ...readyBook, status: "pending", summary: null, chapters: [] })
      .mockResolvedValueOnce(readyBook);

    render(<BookDetail />);
    await screen.findByText(/waiting to be generated/i);
    expect(api.getBook).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(8000);

    expect(api.getBook).toHaveBeenCalledTimes(2);
    expect(await screen.findByText("A desert planet epic.")).toBeInTheDocument();

    vi.useRealTimers();
  });

  it("stops polling once the book is no longer pending", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api.getBook.mockResolvedValue(readyBook);

    render(<BookDetail />);
    await screen.findByText("A desert planet epic.");
    expect(api.getBook).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(20000);
    expect(api.getBook).toHaveBeenCalledTimes(1); // no extra polling once ready

    vi.useRealTimers();
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
