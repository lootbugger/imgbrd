from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.posts import models
from src.posts.service import get_post


def get_post_or_404(session: Session, post_id: int) -> models.Post:
    post = get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
