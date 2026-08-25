import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AddBook from "./AddBook.jsx";
import { api } from "../api.js";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../api.js", () => ({
  api: { addBook: vi.fn() },
}));

describe("AddBook", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("submits the form and navigates to the new book on success", async () => {
    api.addBook.mockResolvedValue({ id: 42 });
    const user = userEvent.setup();
    render(<AddBook />);

    await user.type(screen.getByLabelText(/title/i), "Dune");
    await user.type(screen.getByLabelText(/author/i), "Frank Herbert");
    await user.click(screen.getByRole("button", { name: /add book/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/books/42"));
    expect(api.addBook).toHaveBeenCalledWith("Dune", "Frank Herbert");
  });

  it("shows an error message and does not navigate when the request fails", async () => {
    // Posting only fails for validation errors now -- generation itself is
    // async and can't fail this request (see app/generation.py instead).
    api.addBook.mockRejectedValue(new Error("Network error"));
    const user = userEvent.setup();
    render(<AddBook />);

    await user.type(screen.getByLabelText(/title/i), "Dune");
    await user.type(screen.getByLabelText(/author/i), "Frank Herbert");
    await user.click(screen.getByRole("button", { name: /add book/i }));

    expect(await screen.findByText("Network error")).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
