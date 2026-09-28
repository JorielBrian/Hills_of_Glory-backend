import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MinistryMemberRole(str, enum.Enum):
    MEMBER = "member"
    DIRECTOR = "director"  # scoped to this ministry only, not a global role


class Ministry(Base):
    __tablename__ = "ministries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["MinistryMembership"]] = relationship(
        back_populates="ministry", cascade="all, delete-orphan"
    )


class MinistryMembership(Base):
    __tablename__ = "ministry_memberships"
    __table_args__ = (UniqueConstraint("ministry_id", "person_id", name="uq_ministry_person"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ministry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ministries.id", ondelete="CASCADE"))
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    role: Mapped[MinistryMemberRole] = mapped_column(
        Enum(MinistryMemberRole, name="ministry_member_role"), default=MinistryMemberRole.MEMBER
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ministry: Mapped["Ministry"] = relationship(back_populates="memberships")
    person: Mapped["Person"] = relationship()
