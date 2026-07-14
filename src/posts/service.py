import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.posts import models


def get_post(session: Session, post_id: int) -> models.Post | None:
    return session.get(models.Post, post_id)


def get_threads(session: Session, board_id: int) -> list[models.Post]:
    return (
        session.query(models.Post)
        .filter(
            models.Post.board_id == board_id,
            models.Post.parent_id.is_(None),
            models.Post.deleted == False,
        )
        .all()
    )


def get_replies(session: Session, thread_id: int) -> list[models.Post]:
    return (
        session.query(models.Post)
        .filter(
            models.Post.thread_id == thread_id,
            models.Post.id != thread_id,
            models.Post.deleted == False,
        )
        .order_by(models.Post.created_at)
        .all()
    )


def create_post(
    session: Session,
    board_id: int,
    token: str,
    title: str,
    body: str,
    name: str | None,
    files: list[UploadFile] | None,
) -> models.Post:
    db_post = models.Post(
        board_id=board_id,
        title=title,
        body=body,
        name=name or None,
        poster_token=token,
    )
    session.add(db_post)
    session.flush()
    db_post.thread_id = db_post.id
    db_post.display_id = _compute_display_id(token, db_post.id)
    _save_files(session, db_post, files)
    session.commit()
    session.refresh(db_post)
    return db_post


def create_reply(
    session: Session,
    board_id: int,
    parent_id: int,
    thread_id: int,
    token: str,
    body: str,
    name: str | None,
    files: list[UploadFile] | None,
) -> models.Post:
    db_post = models.Post(
        board_id=board_id,
        parent_id=parent_id,
        title=None,
        body=body,
        name=name or None,
        poster_token=token,
        thread_id=thread_id,
        display_id=_compute_display_id(token, thread_id),
    )
    session.add(db_post)
    session.flush()
    _save_files(session, db_post, files)
    session.commit()
    session.refresh(db_post)
    return db_post


def apply_soft_delete(
    session: Session, post: models.Post, deleted_by: str
) -> bool:
    post.deleted = True
    post.deleted_by = deleted_by
    was_thread_op = post.parent_id is None
    if was_thread_op:
        for reply in (
            session.query(models.Post)
            .filter(models.Post.thread_id == post.id)
            .all()
        ):
            reply.deleted = True
            reply.deleted_by = deleted_by
    return was_thread_op


def _compute_display_id(token: str, thread_id: int) -> str:
    return hashlib.sha256(f"{token}:{thread_id}".encode()).hexdigest()[:10]


def _save_files(
    session: Session, post: models.Post, files: list[UploadFile] | None
) -> None:
    for file in files or []:
        if not file.filename:
            continue
        ext = Path(file.filename).suffix
        unique_name = f"{uuid4()}{ext}"
        content = file.file.read()
        Path("uploads").mkdir(exist_ok=True)
        Path("uploads", unique_name).write_bytes(content)
        session.add(
            models.Image(
                post_id=post.id, filename=unique_name, original_name=file.filename
            )
        )
