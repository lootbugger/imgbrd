from sqlalchemy.orm import Session

from src.boards.service import get_all_boards, create_board, get_board, delete_board_cascade
from src.boards.models import Board
from src.posts.models import Post, Image


class TestGetAllBoards:
    def test_empty(self, db_session: Session):
        assert get_all_boards(db_session) == []

    def test_returns_boards(self, db_session: Session, sample_board: Board):
        boards = get_all_boards(db_session)
        assert len(boards) == 1
        assert boards[0].id == sample_board.id
        assert boards[0].name == "test"


class TestCreateBoard:
    def test_with_description(self, db_session: Session):
        board = create_board(db_session, "test", "a board")
        assert board.name == "test"
        assert board.description == "a board"
        assert board.id is not None

    def test_minimal(self, db_session: Session):
        board = create_board(db_session, "test", None)
        assert board.name == "test"
        assert board.description is None


class TestGetBoard:
    def test_found(self, db_session: Session, sample_board: Board):
        board = get_board(db_session, sample_board.id)
        assert board is not None
        assert board.id == sample_board.id

    def test_not_found(self, db_session: Session):
        assert get_board(db_session, 999) is None


class TestDeleteBoardCascade:
    def test_deletes_board_and_posts(self, db_session: Session, sample_board: Board):
        post1 = Post(board_id=sample_board.id, title="t1", body="b1", poster_token="t1")
        post2 = Post(board_id=sample_board.id, title="t2", body="b2", poster_token="t2")
        db_session.add_all([post1, post2])
        db_session.commit()

        delete_board_cascade(db_session, sample_board)

        assert get_board(db_session, sample_board.id) is None
        assert db_session.query(Post).count() == 0

    def test_deletes_post_images(self, db_session: Session, sample_board: Board):
        post = Post(board_id=sample_board.id, title="t", body="b", poster_token="t")
        db_session.add(post)
        db_session.flush()
        image = Image(post_id=post.id, filename="test.jpg", original_name="test.jpg")
        db_session.add(image)
        db_session.commit()
        db_session.refresh(post)

        delete_board_cascade(db_session, sample_board)

        assert db_session.query(Image).count() == 0
