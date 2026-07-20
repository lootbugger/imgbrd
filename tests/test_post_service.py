from io import BytesIO

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.posts.service import (
    get_post,
    get_threads,
    get_replies,
    create_post,
    create_reply,
    apply_soft_delete,
)
from src.posts.models import Post, Image
from src.boards.models import Board


class TestGetPost:
    def test_found(self, db_session: Session, sample_post: Post):
        post = get_post(db_session, sample_post.id)
        assert post is not None
        assert post.id == sample_post.id

    def test_not_found(self, db_session: Session):
        assert get_post(db_session, 999) is None


class TestGetThreads:
    def test_returns_threads(self, db_session: Session, sample_post: Post):
        threads = get_threads(db_session, sample_post.board_id)
        assert len(threads) == 1
        assert threads[0].id == sample_post.id

    def test_excludes_replies(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="reply",
            poster_token="r1",
        )
        db_session.add(reply)
        db_session.commit()

        threads = get_threads(db_session, sample_board.id)
        assert len(threads) == 1

    def test_excludes_deleted(self, db_session: Session, sample_board: Board):
        post = Post(
            board_id=sample_board.id,
            title="del",
            body="body",
            poster_token="t",
            deleted=True,
        )
        db_session.add(post)
        db_session.commit()

        assert get_threads(db_session, sample_board.id) == []

    def test_empty_board(self, db_session: Session, sample_board: Board):
        assert get_threads(db_session, sample_board.id) == []


class TestGetReplies:
    def test_returns_replies(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="reply",
            poster_token="r1",
        )
        db_session.add(reply)
        db_session.commit()

        replies = get_replies(db_session, sample_post.id)
        assert len(replies) == 1
        assert replies[0].body == "reply"

    def test_excludes_op(self, db_session: Session, sample_post: Post):
        replies = get_replies(db_session, sample_post.id)
        assert replies == []

    def test_excludes_deleted(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="gone",
            poster_token="r1",
            deleted=True,
        )
        db_session.add(reply)
        db_session.commit()

        assert get_replies(db_session, sample_post.id) == []

    def test_ordered_by_created_at(self, db_session: Session, sample_board: Board, sample_post: Post):
        import datetime
        r1 = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="first",
            poster_token="r1",
            created_at=datetime.datetime(2024, 1, 1),
        )
        r2 = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="second",
            poster_token="r2",
            created_at=datetime.datetime(2024, 1, 2),
        )
        r3 = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="third",
            poster_token="r3",
            created_at=datetime.datetime(2024, 1, 3),
        )
        db_session.add_all([r2, r3, r1])
        db_session.commit()

        replies = get_replies(db_session, sample_post.id)
        assert [r.body for r in replies] == ["first", "second", "third"]


class TestCreatePost:
    def test_creates_thread(self, db_session: Session, sample_board: Board):
        post = create_post(db_session, sample_board.id, "token1", "Title", "Body", None, None)
        assert post.board_id == sample_board.id
        assert post.title == "Title"
        assert post.body == "Body"
        assert post.name is None
        assert post.parent_id is None
        assert post.thread_id == post.id
        assert post.display_id is not None
        assert post.id is not None

    def test_with_name(self, db_session: Session, sample_board: Board):
        post = create_post(db_session, sample_board.id, "token1", "T", "B", "Anonymous", None)
        assert post.name == "Anonymous"

    def test_with_files(self, db_session: Session, sample_board: Board):
        files = [UploadFile(filename="test.txt", file=BytesIO(b"hello world"))]
        post = create_post(db_session, sample_board.id, "t", "T", "B", None, files)
        assert len(post.images) == 1
        assert post.images[0].original_name == "test.txt"

    def test_without_files(self, db_session: Session, sample_board: Board):
        post = create_post(db_session, sample_board.id, "t", "T", "B", None, None)
        assert post.images == []


class TestCreateReply:
    def test_creates_reply(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = create_reply(
            db_session, sample_board.id, sample_post.id, sample_post.id,
            "token2", "Reply body", None, None,
        )
        assert reply.parent_id == sample_post.id
        assert reply.thread_id == sample_post.id
        assert reply.board_id == sample_board.id
        assert reply.title is None
        assert reply.body == "Reply body"
        assert reply.display_id is not None

    def test_with_files(self, db_session: Session, sample_board: Board, sample_post: Post):
        files = [UploadFile(filename="img.png", file=BytesIO(b"png data"))]
        reply = create_reply(
            db_session, sample_board.id, sample_post.id, sample_post.id,
            "t", "body", None, files,
        )
        assert len(reply.images) == 1


class TestApplySoftDelete:
    def test_reply_marked_deleted(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="reply",
            poster_token="r1",
        )
        db_session.add(reply)
        db_session.commit()

        was_op = apply_soft_delete(db_session, reply, "author")
        assert reply.deleted is True
        assert reply.deleted_by == "author"
        assert was_op is False

    def test_op_cascades_to_replies(self, db_session: Session, sample_board: Board, sample_post: Post):
        reply = Post(
            board_id=sample_board.id,
            parent_id=sample_post.id,
            thread_id=sample_post.id,
            body="reply",
            poster_token="r1",
        )
        db_session.add(reply)
        db_session.commit()

        was_op = apply_soft_delete(db_session, sample_post, "author")
        assert sample_post.deleted is True
        assert reply.deleted is True
        assert reply.deleted_by == "author"
        assert was_op is True

    def test_op_returns_true(self, db_session: Session, sample_post: Post):
        assert apply_soft_delete(db_session, sample_post, "x") is True
