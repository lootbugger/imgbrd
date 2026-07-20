import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.database import Base, get_session
from src.main import app
from src.boards.models import Board
from src.posts.models import Post, Image


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session):
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_board(db_session: Session) -> Board:
    board = Board(name="test", description="test board")
    db_session.add(board)
    db_session.commit()
    db_session.refresh(board)
    return board


@pytest.fixture
def sample_post(db_session: Session, sample_board: Board) -> Post:
    post = Post(
        board_id=sample_board.id,
        title="Test thread",
        body="Test body",
        poster_token="abc123",
    )
    db_session.add(post)
    db_session.flush()
    post.thread_id = post.id
    post.display_id = "abcdef1234"
    db_session.commit()
    db_session.refresh(post)
    return post
