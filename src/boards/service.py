from pathlib import Path

from sqlalchemy.orm import Session

from src.boards import models
from src.posts.models import Post, Image


def get_all_boards(session: Session) -> list[models.Board]:
    return session.query(models.Board).all()


def create_board(session: Session, name: str, description: str | None) -> models.Board:
    board = models.Board(name=name, description=description)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


def get_board(session: Session, board_id: int) -> models.Board | None:
    return session.get(models.Board, board_id)


def delete_board_cascade(session: Session, board: models.Board) -> None:
    posts = session.query(Post).filter(Post.board_id == board.id).all()
    for post in posts:
        for image in post.images:
            Path("uploads", image.filename).unlink(missing_ok=True)
            session.delete(image)
        session.delete(post)
    session.delete(board)
    session.commit()
