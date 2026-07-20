from io import BytesIO
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.boards.models import Board
from src.posts.models import Post


class TestCreatePost:
    def test_creates_thread_and_redirects(self, client: TestClient, sample_board: Board):
        resp = client.post(
            f"/boards/{sample_board.id}/posts",
            data={"title": "Test", "body": "Body"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"].startswith(f"/boards/{sample_board.id}/posts/")

    def test_with_file(self, client: TestClient, sample_board: Board):
        resp = client.post(
            f"/boards/{sample_board.id}/posts",
            data={"title": "With file", "body": "Body"},
            files={"files": ("test.txt", b"hello world", "text/plain")},
            follow_redirects=False,
        )

    def test_requires_board(self, client: TestClient):
        resp = client.post("/boards/999/posts", data={"title": "T", "body": "B"})
        assert resp.status_code == 404


class TestGetThreads:
    def test_returns_html(self, client: TestClient, sample_board: Board, sample_post: Post):
        resp = client.get(f"/boards/{sample_board.id}/posts")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")


class TestGetThread:
    def test_returns_html(self, client: TestClient, sample_board: Board, sample_post: Post):
        resp = client.get(f"/boards/{sample_board.id}/posts/{sample_post.id}")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")

    def test_deleted_thread_returns_404(self, client: TestClient, db_session: Session, sample_board: Board, sample_post: Post):
        sample_post.deleted = True
        sample_post.deleted_by = "author"
        db_session.commit()

        resp = client.get(f"/boards/{sample_board.id}/posts/{sample_post.id}")
        assert resp.status_code == 404

    def test_not_found(self, client: TestClient, sample_board: Board):
        resp = client.get(f"/boards/{sample_board.id}/posts/999")
        assert resp.status_code == 404


class TestReply:
    def test_returns_html_fragment(self, client: TestClient, sample_board: Board, sample_post: Post):
        resp = client.post(
            f"/boards/{sample_board.id}/posts/{sample_post.id}/reply",
            data={"body": "A reply"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")

    def test_not_found(self, client: TestClient, sample_board: Board):
        resp = client.post(f"/boards/{sample_board.id}/posts/999/reply", data={"body": "X"})
        assert resp.status_code == 404


class TestDeletePost:
    def test_requires_matching_token(self, client: TestClient, sample_board: Board, sample_post: Post):
        resp = client.delete(
            f"/boards/{sample_board.id}/posts/{sample_post.id}",
            cookies={"poster_token": "wrong_token"},
        )
        assert resp.status_code == 403

    def test_deletes_thread_op_returns_json(self, client: TestClient, db_session: Session, sample_board: Board, sample_post: Post):
        resp = client.delete(
            f"/boards/{sample_board.id}/posts/{sample_post.id}",
            cookies={"poster_token": "abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert resp.headers.get("hx-redirect") is not None

    def test_deletes_reply(self, client: TestClient, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="reply to delete",
            poster_token="reply_token",
        )
        db_session.add(reply)
        db_session.commit()
        db_session.refresh(reply)

        resp = client.delete(
            f"/boards/{sample_board.id}/posts/{reply.id}",
            cookies={"poster_token": "reply_token"},
        )
        assert resp.status_code == 200
