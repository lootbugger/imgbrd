from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.boards import models
from src.boards.service import get_board


def get_board_or_404(session: Session, board_id: int) -> models.Board:
    board = get_board(session, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board
