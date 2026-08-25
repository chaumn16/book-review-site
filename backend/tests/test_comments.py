def _make_book(client):
    return client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"}).json()


def test_comment_is_posted_and_visible_immediately(client, mock_llm):
    book = _make_book(client)
    resp = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "Alice", "body": "Great book!"})
    assert resp.status_code == 201
    assert resp.json()["body"] == "Great book!"

    listed = client.get(f"/api/books/{book['id']}/comments").json()
    assert len(listed) == 1
    assert listed[0]["author_name"] == "Alice"


def test_posting_never_blocks_on_moderation(client, mock_llm):
    # There's no synchronous moderation call anymore: even obviously bad
    # content posts successfully and stays visible until
    # scripts/review_comments.py (tested separately) reviews it.
    book = _make_book(client)
    resp = client.post(
        f"/api/books/{book['id']}/comments",
        json={"author_name": "Troll", "body": "this is clearly harassment"},
    )
    assert resp.status_code == 201

    listed = client.get(f"/api/books/{book['id']}/comments").json()
    assert len(listed) == 1


def test_comment_on_missing_book_404s(client):
    resp = client.post("/api/books/999/comments", json={"author_name": "Alice", "body": "hi"})
    assert resp.status_code == 404


def test_comment_missing_fields_is_rejected(client, mock_llm):
    book = _make_book(client)
    resp = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "", "body": ""})
    assert resp.status_code == 422


def test_comment_rating_is_optional_and_stored(client, mock_llm):
    book = _make_book(client)
    resp = client.post(
        f"/api/books/{book['id']}/comments",
        json={"author_name": "Alice", "body": "Great book!", "rating": 5},
    )
    assert resp.status_code == 201
    assert resp.json()["rating"] == 5

    unrated = client.post(f"/api/books/{book['id']}/comments", json={"author_name": "Bob", "body": "No rating."})
    assert unrated.json()["rating"] is None


def test_comment_rating_out_of_range_is_rejected(client, mock_llm):
    book = _make_book(client)
    resp = client.post(
        f"/api/books/{book['id']}/comments",
        json={"author_name": "Alice", "body": "Great book!", "rating": 6},
    )
    assert resp.status_code == 422
