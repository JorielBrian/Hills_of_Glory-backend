import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.announcement import AnnouncementVisibility


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    image_url: str | None = None
    visibility: AnnouncementVisibility = AnnouncementVisibility.PUBLIC
    is_published: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    image_url: str | None = None
    visibility: AnnouncementVisibility | None = None
    is_published: bool | None = None


class AnnouncementOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    image_url: str | None
    visibility: AnnouncementVisibility
    is_published: bool
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
