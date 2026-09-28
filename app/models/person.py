import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    HEAD_PASTOR = "head_pastor"
    NETWORK_LEADER = "network_leader"
    LIFE_GUIDE = "life_guide"
    MEMBER = "member"
    VISITOR = "visitor"


class MemberType(str, enum.Enum):
    ADULT = "adult"
    KID = "kid"


class AccountStatus(str, enum.Enum):
    # Only meaningful for people who registered for dashboard/login access.
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Person(Base):
    """
    Every human tracked by the system: staff/leaders who log in, adult
    members, kids (no login), and visitors. Login fields are nullable
    because kids and walk-in visitors are created by staff without
    credentials but still need a QR code for attendance.
    """

    __tablename__ = "people"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.VISITOR, nullable=False)
    member_type: Mapped[MemberType] = mapped_column(
        Enum(MemberType, name="member_type"), default=MemberType.ADULT, nullable=False
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status"), default=AccountStatus.PENDING, nullable=False
    )

    # Kids link to a parent/guardian's Person record.
    guardian_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    guardian: Mapped["Person | None"] = relationship(remote_side="Person.id")

    # Permanent unique badge code, generated once, used for every QR scan.
    qr_code: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def has_login(self) -> bool:
        return self.email is not None and self.password_hash is not None
