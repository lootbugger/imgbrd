import datetime
from pydantic import BaseModel, computed_field, model_validator


class ImageOut(BaseModel):
    id: int
    post_id: int
    filename: str
    original_name: str

    @computed_field(return_type=str)
    @property
    def url(self):
        return f"/uploads/{self.filename}"

    model_config = {"from_attributes": True}


class PostIn(BaseModel):
    title: str | None = None
    body: str = ""
    name: str | None = None


class PostOut(PostIn):
    id: int
    board_id: int
    parent_id: int | None = None
    created_at: datetime.datetime
    images: list[ImageOut]
    deleted: bool = False
    deleted_by: str | None = None
    display_id: str

    @model_validator(mode="after")
    def redact_if_deleted(self):
        if self.deleted:
            self.body = f"[post was deleted by {self.deleted_by or 'unknown'}]"
            self.title = None
        return self

    model_config = {"from_attributes": True}
