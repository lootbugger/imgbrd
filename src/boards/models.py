from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(nullable=True)
