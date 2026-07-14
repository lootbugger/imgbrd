from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.database import SessionDep
from src.boards.dependencies import get_board_or_404
from src.posts.dependencies import get_post_or_404
from src.posts.service import (
    get_threads,
    get_replies,
    create_post,
    create_reply,
    apply_soft_delete,
)
from src.templates import templates

router = APIRouter()


@router.post("/boards/{board_id}/posts")
def create_post_route(
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
    post = create_post(session, board_id, token, title, body, name, files)
    return RedirectResponse(url=f"/boards/{board_id}/posts/{post.id}", status_code=303)


@router.get("/boards/{board_id}/posts")
def get_posts_route(request: Request, board_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    posts = get_threads(session, board_id)
    return templates.TemplateResponse(
        request, "board_posts.html", {"board": board, "posts": posts}
    )


@router.get("/boards/{board_id}/posts/{post_id}")
def get_thread_route(request: Request, board_id: int, post_id: int, session: SessionDep):
    board = get_board_or_404(session, board_id)
    post = get_post_or_404(session, post_id)
    if post.deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    replies = get_replies(session, post_id)
    return templates.TemplateResponse(
        request, "thread.html", {"board": board, "post": post, "replies": replies}
    )


@router.post("/boards/{board_id}/posts/{post_id}/reply")
def reply_to_post_route(
    board_id: int,
    post_id: int,
    body: Annotated[str, Form()],
    session: SessionDep,
    request: Request,
    name: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    get_board_or_404(session, board_id)
    parent = get_post_or_404(session, post_id)
    token = request.cookies.get("poster_token") or uuid4().hex
    thread_id = parent.thread_id or post_id
    post = create_reply(session, board_id, post_id, thread_id, token, body, name, files)
    return templates.TemplateResponse(request, "_post.html", {"post": post})


@router.delete("/boards/{board_id}/posts/{post_id}")
def delete_post_route(
    board_id: int,
    post_id: int,
    session: SessionDep,
    request: Request,
    deleted_by: str = "author",
):
    get_board_or_404(session, board_id)
    post = get_post_or_404(session, post_id)
    token = request.cookies.get("poster_token")
    if not token or token != post.poster_token:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    was_thread_op = apply_soft_delete(session, post, deleted_by)
    if was_thread_op:
        session.commit()
        resp = JSONResponse({"ok": True})
        resp.headers["HX-Redirect"] = f"/boards/{board_id}/posts"
        return resp
    session.commit()
    session.refresh(post)
    return templates.TemplateResponse(request, "_post.html", {"post": post})
