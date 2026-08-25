def test_list_books_empty(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_book_success(client, mock_llm):
    resp = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    assert resp.status_code == 201

    body = resp.json()
    assert body["status"] == "ready"
    assert body["summary"].startswith("A test summary")
    assert len(body["chapters"]) == 2
    assert body["chapters"][0] == {
        "chapter_number": 1,
        "chapter_title": "The Beginning",
        "highlight": "Things start.",
    }


def test_add_book_missing_fields_is_rejected(client):
    resp = client.post("/api/books", json={"title": "", "author": "Someone"})
    assert resp.status_code == 422


def test_get_book_not_found(client):
    resp = client.get("/api/books/999")
    assert resp.status_code == 404


def test_add_book_generation_failure_marks_book_failed(client, monkeypatch):
    from app import llm

    def boom(title, author):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(llm, "generate_book_content", boom)

    resp = client.post("/api/books", json={"title": "Ghost Book", "author": "Nobody"})
    assert resp.status_code == 502

    books = client.get("/api/books").json()
    assert len(books) == 1
    assert books[0]["status"] == "failed"


def test_regenerate_recovers_a_failed_book(client, monkeypatch, mock_llm):
    from app import llm

    # Captured now, while mock_llm's fake is still active, so we can restore
    # it after temporarily swapping in a failing version below.
    working_generate = llm.generate_book_content

    def boom(title, author):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(llm, "generate_book_content", boom)
    created_resp = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    assert created_resp.status_code == 502
    book_id = client.get("/api/books").json()[0]["id"]

    monkeypatch.setattr(llm, "generate_book_content", working_generate)
    resp = client.post(f"/api/books/{book_id}/regenerate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_delete_book(client, mock_llm):
    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    resp = client.delete(f"/api/books/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/books/{created['id']}").status_code == 404


def test_book_list_reflects_visible_comment_count(client, mock_llm):
    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    client.post(f"/api/books/{created['id']}/comments", json={"author_name": "Alice", "body": "Loved it!"})
    client.post(f"/api/books/{created['id']}/comments", json={"author_name": "Bob", "body": "this has badword in it"})

    books = client.get("/api/books").json()
    # Only the allowed comment should count; the blocked one shouldn't.
    assert books[0]["comment_count"] == 1
