import pytest

class TestBooks:
    def test_get_books_empty(self, client):
        assert client.get("/api/books").get_json() == []

    def test_create_book(self, client):
        response = client.post("/api/books", json={
            "title": "Clean Code",
            "genre": "Education",
            "year_published": 2008,
            "created_by": "Ilya Sender"
        })
        assert response.status_code == 201
        assert response.get_json()["title"] == "Clean Code"

    def test_create_book_without_title(self, client):
        response = client.post("/api/books", json={"created_by": "Ilya"})
        assert response.status_code == 400

    def test_create_book_without_created_by(self, client):
        response = client.post("/api/books", json={"title": "No Author"})
        assert response.status_code == 400

    def test_create_book_with_author(self, client):
        a = client.post("/api/authors", json={"name": "Robert Martin"}).get_json()
        response = client.post("/api/books", json={
            "title": "Clean Architecture",
            "author_id": a["id"],
            "created_by": "Ilya Sender"
        })
        assert response.status_code == 201
        assert response.get_json()["author_id"] == a["id"]

    def test_create_book_with_nonexistent_author(self, client):
        response = client.post("/api/books", json={
            "title": "Ghost Book",
            "author_id": 999,
            "created_by": "Ilya"
        })
        assert response.status_code == 400

    def test_get_book_by_id(self, client):
        b = client.post("/api/books", json={"title": "T1", "created_by": "I"}).get_json()
        response = client.get(f"/api/books/{b['id']}")
        assert response.status_code == 200
        assert response.get_json()["title"] == "T1"

    def test_get_book_not_found(self, client):
        assert client.get("/api/books/999").status_code == 404

    def test_delete_book(self, client):
        b = client.post("/api/books", json={"title": "To Delete", "created_by": "I"}).get_json()
        assert client.delete(f"/api/books/{b['id']}").status_code == 204
        assert client.get(f"/api/books/{b['id']}").status_code == 404

    def test_final_check_for_pr(self, client):
        """Цей тест ми додаємо спеціально для Pull Request"""
        response = client.post("/api/books", json={
            "title": "PR Verification Book",
            "created_by": "Ilya684"
        })
        assert response.status_code == 201

class TestBooksFilter:
    def test_filter_by_genre(self, client):
        client.post("/api/books", json={"title": "Poem", "genre": "poetry", "created_by": "I"})
        client.post("/api/books", json={"title": "Novel", "genre": "fiction", "created_by": "I"})
        response = client.get("/api/books?genre=poetry")
        assert len(response.get_json()) == 1

    def test_filter_by_author_id(self, client):
        a = client.post("/api/authors", json={"name": "Ilya"}).get_json()
        client.post("/api/books", json={"title": "B1", "author_id": a["id"], "created_by": "I"})
        response = client.get(f"/api/books?author_id={a['id']}")
        assert len(response.get_json()) == 1

    def test_search_by_title(self, client):
        client.post("/api/books", json={"title": "Kobzar", "created_by": "I"})
        response = client.get("/api/books?q=kobzar")
        assert len(response.get_json()) == 1

    def test_filter_no_results(self, client):
        client.post("/api/books", json={"title": "T", "genre": "G", "created_by": "I"})
        response = client.get("/api/books?genre=nonexistent")
        assert response.get_json() == []
