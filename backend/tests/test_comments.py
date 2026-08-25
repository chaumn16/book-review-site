def _make_book(client):
    return client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()


def test_allowed_comment_is_posted_and_listed(client, mock_llm):
    book = _make_book(client)
    resp = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "Alice", "body": "Great book!"})
    assert resp.status_code == 201
    assert resp.json()["body"] == "Great book!"

    listed = client.get(f"/api/books/{book['id']}/comments").json()
    assert len(listed) == 1
    assert listed[0]["author_name"] == "Alice"


def test_flagged_comment_is_blocked_and_never_listed(client, mock_llm):
    book = _make_book(client)
    resp = client.post(
        f"/api/books/{book['id']}/comments",
        json={"author_name": "Troll", "body": "this has badword in it"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["reason"] == "contains flagged language"

    listed = client.get(f"/api/books/{book['id']}/comments").json()
    assert listed == []


def test_comment_on_missing_book_404s(client):
    resp = client.post("/api/books/999/comments", json={"author_name": "Alice", "body": "hi"})
    assert resp.status_code == 404


def test_comment_missing_fields_is_rejected(client, mock_llm):
    book = _make_book(client)
    resp = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "", "body": ""})
    assert resp.status_code == 422


def test_moderation_call_failure_holds_comment_for_review(client, mock_llm, monkeypatch):
    from app import llm

    book = _make_book(client)

    def boom(body):
        raise RuntimeError("moderation service down")

    monkeypatch.setattr(llm, "moderate_comment", boom)

    resp = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "Alice", "body": "hello"})
    assert resp.status_code == 422  # held for review, not published

    listed = client.get(f"/api/books/{book['id']}/comments").json()
    assert listed == []
