from pydantic import BaseModel


class BoardIn(BaseModel):
    name: str
    description: str | None = None


class BoardOut(BoardIn):
    id: int

    model_config = {"from_attributes": True}
