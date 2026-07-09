import hashlib
from pathlib import Path
from uuid import uuid4
from typing import Annotated

from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import SessionDep
import models
from schemas import BoardIn, BoardOut, PostOut


app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.middleware("http")
async def ensure_poster_token(request: Request, call_next):
    response = await call_next(request)
    if "poster_token" not in request.cookies:
        response.set_cookie("poster_token", uuid4().hex, max_age=365 * 24 * 3600, httponly=True)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "404.html", {"detail": exc.detail}, status_code=404
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def get_board_or_404(session: SessionDep, board_id: int) -> models.Board:
    board = session.get(models.Board, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


def compute_display_id(token: str, thread_id: int) -> str:
    return hashlib.sha256(f"{token}:{thread_id}".encode()).hexdigest()[:10]


async def save_files(
    session: SessionDep, post: models.Post, files: list[UploadFile] | None
) -> None:
    for file in files or []:
        if not file.filename:
            continue
        ext = Path(file.filename).suffix
        unique_name = f"{uuid4()}{ext}"
        content = await file.read()
        Path("uploads").mkdir(exist_ok=True)
        Path("uploads", unique_name).write_bytes(content)
        session.add(
            models.Image(
                post_id=post.id, filename=unique_name, original_name=file.filename
            )
        )


@app.get("/")
def get_status():
    return {"status": "ok"}


@app.get("/boards")
def get_boards(request: Request, session: SessionDep):
    boards = session.query(models.Board).all()
    return templates.TemplateResponse(request, "boards.html", {"boards": boards})


@app.post("/boards", response_model=BoardOut)
def create_board(board: BoardIn, session: SessionDep):
    db_board = models.Board(name=board.name, description=board.description)
    session.add(db_board)
    session.commit()
    session.refresh(db_board)
    return db_board


@app.delete("/boards/{board_id}")
def delete_board(board_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    posts = session.query(models.Post).filter(models.Post.board_id == board_id).all()
    for post in posts:
        for image in post.images:
            Path("uploads", image.filename).unlink(missing_ok=True)
            session.delete(image)
        session.delete(post)
    session.delete(board)
    session.commit()
    return {"ok": True}


@app.post("/boards/{board_id}/posts")
async def create_post(
    board_id: int,
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
    session: SessionDep,
    request: Request,
    name: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    get_board_or_404(session, board_id)
    token = request.cookies.get("poster_token") or uuid4().hex
    db_post = models.Post(
        board_id=board_id, title=title, body=body, name=name or None, poster_token=token
    )
    session.add(db_post)
    session.flush()
    db_post.thread_id = db_post.id
    db_post.display_id = compute_display_id(token, db_post.id)
    await save_files(session, db_post, files)
    session.commit()
    session.refresh(db_post)
    return RedirectResponse(
        url=f"/boards/{board_id}/posts/{db_post.id}", status_code=303
    )


@app.get("/boards/{board_id}/posts")
def get_posts(request: Request, board_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    posts = (
        session.query(models.Post)
        .filter(
            models.Post.board_id == board_id,
            models.Post.parent_id.is_(None),
            models.Post.deleted == False,
        )
        .all()
    )
    return templates.TemplateResponse(
        request, "board_posts.html", {"board": board, "posts": posts}
    )


@app.get("/boards/{board_id}/posts/{post_id}")
def get_thread(request: Request, board_id: int, post_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    post = session.get(models.Post, post_id)
    if not post or post.deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    replies = (
        session.query(models.Post)
        .filter(
            models.Post.thread_id == post_id,
            models.Post.id != post_id,
            models.Post.deleted == False,
        )
        .order_by(models.Post.created_at)
        .all()
    )
    return templates.TemplateResponse(
        request, "thread.html", {"board": board, "post": post, "replies": replies}
    )


@app.post("/boards/{board_id}/posts/{post_id}/reply")
async def reply_to_post(
    board_id: int,
    post_id: int,
    body: Annotated[str, Form()],
    session: SessionDep,
    request: Request,
    name: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    get_board_or_404(session, board_id)
    parent = session.get(models.Post, post_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Post not found")
    token = request.cookies.get("poster_token") or uuid4().hex
    thread_id = parent.thread_id or post_id
    db_post = models.Post(
        board_id=board_id,
        parent_id=post_id,
        title=None,
        body=body,
        name=name or None,
        poster_token=token,
        thread_id=thread_id,
        display_id=compute_display_id(token, thread_id),
    )
    session.add(db_post)
    session.flush()
    await save_files(session, db_post, files)
    session.commit()
    session.refresh(db_post)
    return templates.TemplateResponse(request, "_post.html", {"post": db_post})


@app.delete("/boards/{board_id}/posts/{post_id}")
def delete_post(
    board_id: int,
    post_id: int,
    session: SessionDep,
    request: Request,
    deleted_by: str = "author",
):
    get_board_or_404(session, board_id)
    post = session.get(models.Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    token = request.cookies.get("poster_token")
    if not token or token != post.poster_token:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    post.deleted = True
    post.deleted_by = deleted_by
    if post.parent_id is None:
        for reply in session.query(models.Post).filter(models.Post.thread_id == post_id).all():
            reply.deleted = True
            reply.deleted_by = deleted_by
        session.commit()
        resp = JSONResponse({"ok": True})
        resp.headers["HX-Redirect"] = f"/boards/{board_id}/posts"
        return resp
    session.commit()
    session.refresh(post)
    return templates.TemplateResponse(request, "_post.html", {"post": post})
