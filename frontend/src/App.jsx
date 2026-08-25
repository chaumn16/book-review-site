import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home.jsx";
import BookDetail from "./pages/BookDetail.jsx";
import AddBook from "./pages/AddBook.jsx";

export default function App() {
  return (
    <div className="app">
      <header className="site-header">
        <Link to="/" className="brand">📚 Bookish</Link>
        <Link to="/add" className="add-link">+ Add a book</Link>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/books/:id" element={<BookDetail />} />
          <Route path="/add" element={<AddBook />} />
        </Routes>
      </main>
    </div>
  );
}
