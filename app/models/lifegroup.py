import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LifegroupMemberRole(str, enum.Enum):
    MEMBER = "member"
    LEADER = "leader"


class Network(Base):
    """A network is overseen by a Network Leader and groups several lifegroups."""

    __tablename__ = "networks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    leader: Mapped["Person | None"] = relationship()

    lifegroups: Mapped[list["Lifegroup"]] = relationship(back_populates="network")


class Lifegroup(Base):
    __tablename__ = "lifegroups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    network_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("networks.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    network: Mapped["Network | None"] = relationship(back_populates="lifegroups")
    memberships: Mapped[list["LifegroupMembership"]] = relationship(
        back_populates="lifegroup", cascade="all, delete-orphan"
    )


class LifegroupMembership(Base):
    __tablename__ = "lifegroup_memberships"
    __table_args__ = (UniqueConstraint("lifegroup_id", "person_id", name="uq_lifegroup_person"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lifegroup_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lifegroups.id", ondelete="CASCADE"))
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    role: Mapped[LifegroupMemberRole] = mapped_column(
        Enum(LifegroupMemberRole, name="lifegroup_member_role"), default=LifegroupMemberRole.MEMBER
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lifegroup: Mapped["Lifegroup"] = relationship(back_populates="memberships")
    person: Mapped["Person"] = relationship()
