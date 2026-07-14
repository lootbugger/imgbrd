import datetime
from sqlalchemy import ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(nullable=True)
    body: Mapped[str]
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    name: Mapped[str | None] = mapped_column(nullable=True)
    display_id: Mapped[str | None] = mapped_column(nullable=True)
    poster_token: Mapped[str | None] = mapped_column(nullable=True)
    thread_id: Mapped[int | None] = mapped_column(nullable=True)
    deleted: Mapped[bool] = mapped_column(default=False)
    deleted_by: Mapped[str | None] = mapped_column(nullable=True)

    images: Mapped[list["Image"]] = relationship(back_populates="post")


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    filename: Mapped[str]
    original_name: Mapped[str]

    post: Mapped[Post] = relationship(back_populates="images")
