import datetime

from src.boards.schemas import BoardIn, BoardOut
from src.posts.schemas import PostIn, PostOut, ImageOut
from src.boards.models import Board
from src.posts.models import Post, Image


class TestBoardIn:
    def test_valid(self):
        d = BoardIn.model_validate({"name": "tech", "description": "tech board"})
        assert d.name == "tech"
        assert d.description == "tech board"

    def test_minimal(self):
        d = BoardIn.model_validate({"name": "tech"})
        assert d.name == "tech"
        assert d.description is None


class TestBoardOut:
    def test_from_orm(self):
        board = Board(id=1, name="test", description="desc")
        out = BoardOut.model_validate(board)
        assert out.id == 1
        assert out.name == "test"
        assert out.description == "desc"


class TestImageOut:
    def test_url_computed(self):
        img = Image(id=1, post_id=1, filename="abc.jpg", original_name="photo.jpg")
        out = ImageOut.model_validate(img)
        assert out.url == "/uploads/abc.jpg"


class TestPostIn:
    def test_defaults(self):
        d = PostIn.model_validate({"body": "hello"})
        assert d.body == "hello"
        assert d.title is None
        assert d.name is None

    def test_full(self):
        d = PostIn.model_validate({"title": "T", "body": "B", "name": "Anonymous"})
        assert d.title == "T"
        assert d.name == "Anonymous"


class TestPostOut:
    def test_redact_if_deleted(self):
        post = Post(
            id=1, board_id=1, title="Original", body="Secret",
            deleted=True, deleted_by="author",
            created_at=datetime.datetime(2024, 1, 1),
            display_id="abc123",
        )
        out = PostOut.model_validate(post)
        assert "Secret" not in out.body
        assert "[post was deleted by author]" in out.body
        assert out.title is None

    def test_not_deleted(self):
        post = Post(
            id=1, board_id=1, title="Visible", body="Content",
            deleted=False,
            created_at=datetime.datetime(2024, 1, 1),
            display_id="abc123",
        )
        out = PostOut.model_validate(post)
        assert out.body == "Content"
        assert out.title == "Visible"

    def test_display_id_preserved(self):
        post = Post(
            id=1, board_id=1, body="test",
            deleted=False,
            created_at=datetime.datetime(2024, 1, 1),
            display_id="xyz789",
        )
        out = PostOut.model_validate(post)
        assert out.display_id == "xyz789"
