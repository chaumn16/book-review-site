import { render, screen, fireEvent } from "@testing-library/react";
import BookCover from "./BookCover.jsx";

describe("BookCover", () => {
  it("renders the image when a src is given", () => {
    render(<BookCover src="https://covers.example.com/dune.jpg" title="Dune" />);
    const img = screen.getByRole("img", { name: "Cover of Dune" });
    expect(img).toHaveAttribute("src", "https://covers.example.com/dune.jpg");
  });

  it("renders the placeholder when there's no src at all", () => {
    render(<BookCover src={null} title="Dune" />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("📖")).toBeInTheDocument();
  });

  it("falls back to the placeholder if the image fails to load at runtime", () => {
    render(<BookCover src="https://covers.example.com/broken.jpg" title="Dune" />);
    const img = screen.getByRole("img", { name: "Cover of Dune" });

    fireEvent.error(img);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("📖")).toBeInTheDocument();
  });
});
