from fastapi.testclient import TestClient
from src.boards.models import Board


class TestGetBoards:
    def test_returns_html(self, client: TestClient, sample_board: Board):
        resp = client.get("/boards")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert "test" in resp.text


class TestCreateBoard:
    def test_returns_json(self, client: TestClient):
        resp = client.post("/boards", json={"name": "tech", "description": "tech board"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "tech"
        assert data["description"] == "tech board"
        assert "id" in data

    def test_minimal(self, client: TestClient):
        resp = client.post("/boards", json={"name": "tech"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "tech"
        assert data["description"] is None


class TestDeleteBoard:
    def test_deletes_board(self, client: TestClient, sample_board: Board):
        resp = client.delete(f"/boards/{sample_board.id}")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_not_found(self, client: TestClient):
        resp = client.delete("/boards/999")
        assert resp.status_code == 404
