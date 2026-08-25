def test_list_books_empty(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.json() == []


def test_only_ready_books_are_listed(client):
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    db.add(models.Book(title="Still Cooking", author="Someone", status="pending"))
    db.add(models.Book(title="Broke", author="Someone Else", status="failed"))
    db.add(models.Book(title="Done", author="A Third Person", status="ready", summary="A summary."))
    db.commit()
    db.close()

    books = client.get("/api/books").json()
    assert [b["title"] for b in books] == ["Done"]
    assert "status" not in books[0]


def test_add_book_success(client, mock_llm):
    resp = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    assert resp.status_code == 201

    body = resp.json()
    assert body["status"] == "ready"
    assert body["summary"].startswith("A test summary")
    assert body["cover_url"] == "https://covers.example.com/dune.jpg"
    assert body["verdict_label"] == "worth_it"
    assert body["verdict_reason"] == "A solid, well-made example of its genre."
    assert body["average_rating"] is None
    assert body["rating_count"] == 0
    assert len(body["chapters"]) == 2
    assert body["chapters"][0] == {
        "chapter_number": 1,
        "chapter_title": "The Beginning",
        "highlight": "Things start.",
    }


def test_book_list_and_detail_reflect_average_rating(client, mock_llm):
    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    book_id = created["id"]

    client.post(f"/api/books/{book_id}/comments", json={"author_name": "Alice", "body": "Loved it!", "rating": 5})
    client.post(f"/api/books/{book_id}/comments", json={"author_name": "Bob", "body": "It was fine.", "rating": 3})
    client.post(f"/api/books/{book_id}/comments", json={"author_name": "Cara", "body": "No rating from me."})

    books = client.get("/api/books").json()
    assert books[0]["average_rating"] == 4.0
    assert books[0]["rating_count"] == 2

    detail = client.get(f"/api/books/{book_id}").json()
    assert detail["average_rating"] == 4.0
    assert detail["rating_count"] == 2


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
    book_id = resp.json()["detail"]["book_id"]

    # A failed book is never listed publicly -- only reachable by id.
    assert client.get("/api/books").json() == []
    assert client.get(f"/api/books/{book_id}").json()["status"] == "failed"


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
    book_id = created_resp.json()["detail"]["book_id"]

    monkeypatch.setattr(llm, "generate_book_content", working_generate)
    resp = client.post(f"/api/books/{book_id}/regenerate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_delete_book(client, mock_llm):
    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    resp = client.delete(f"/api/books/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/books/{created['id']}").status_code == 404


def test_book_list_comment_count_is_immediate_then_drops_after_moderation(client, mock_llm):
    from app.database import SessionLocal
    from app.moderation import review_pending_comments

    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    client.post(f"/api/books/{created['id']}/comments", json={"author_name": "Alice", "body": "Loved it!"})
    client.post(f"/api/books/{created['id']}/comments", json={"author_name": "Bob", "body": "this has badword in it"})

    # Both comments count right away -- moderation is async, not on-submit.
    books = client.get("/api/books").json()
    assert books[0]["comment_count"] == 2

    # Once the review process (scripts/review_comments.py, tested in
    # isolation in test_moderation.py) runs and flags Bob's comment...
    def fake_classify(body):
        flagged = "badword" in body.lower()
        return {"allowed": not flagged, "reason": "flagged language" if flagged else None}

    db = SessionLocal()
    review_pending_comments(db, classify=fake_classify)
    db.close()

    # ...it drops out of the visible count.
    books = client.get("/api/books").json()
    assert books[0]["comment_count"] == 1


def test_a_removed_comments_rating_does_not_count_toward_the_average(client, mock_llm):
    from app.database import SessionLocal
    from app.moderation import review_pending_comments

    created = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
    book_id = created["id"]
    client.post(f"/api/books/{book_id}/comments", json={"author_name": "Alice", "body": "Loved it!", "rating": 5})
    client.post(f"/api/books/{book_id}/comments", json={"author_name": "Troll", "body": "you are trash", "rating": 1})

    # Both ratings count before moderation runs.
    assert client.get("/api/books").json()[0]["average_rating"] == 3.0

    db = SessionLocal()
    review_pending_comments(db, classify=lambda body: {"allowed": "trash" not in body, "reason": "insult"})
    db.close()

    # Troll's 1-star rating is gone along with the removed comment.
    books = client.get("/api/books").json()
    assert books[0]["average_rating"] == 5.0
    assert books[0]["rating_count"] == 1
