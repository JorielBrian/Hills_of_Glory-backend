import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnnouncementVisibility(str, enum.Enum):
    PUBLIC = "public"  # shown on the public site to visitors
    MEMBERS_ONLY = "members_only"  # shown only in the dashboard


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visibility: Mapped[AnnouncementVisibility] = mapped_column(
        Enum(AnnouncementVisibility, name="announcement_visibility"),
        default=AnnouncementVisibility.PUBLIC,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped["Person | None"] = relationship()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
