import pytest
from main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client: yield client

def test_flask_nosql_crud_and_pagination(client):
    book = {"title": "Flask Architecture", "release_year": 2026, "author_id": 77}
    res = client.post("/books", json=book)
    assert res.status_code == 201
    created = res.get_json()
    assert "_id" in created

    res = client.get("/books?limit=1&offset=0")
    assert res.status_code == 200
    assert len(res.get_json()) == 1

    book_id = created["_id"]
    res = client.get(f"/books/{book_id}")
    assert res.status_code == 200

    res = client.delete(f"/books/{book_id}")
    assert res.status_code == 204
