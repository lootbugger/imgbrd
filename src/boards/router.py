from fastapi import APIRouter, Request

from src.database import SessionDep
from src.boards.service import get_all_boards, create_board, delete_board_cascade
from src.boards.dependencies import get_board_or_404
from src.boards.schemas import BoardIn, BoardOut
from src.templates import templates

router = APIRouter()


@router.get("/boards")
def get_boards(request: Request, session: SessionDep):
    boards = get_all_boards(session)
    return templates.TemplateResponse(request, "boards.html", {"boards": boards})


@router.post("/boards", response_model=BoardOut)
def create_board_route(board: BoardIn, session: SessionDep):
    return create_board(session, board.name, board.description)


@router.delete("/boards/{board_id}")
def delete_board_route(board_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    delete_board_cascade(session, board)
    return {"ok": True}
