import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("event_instance_id", "person_id", name="uq_attendance_instance_person"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("event_instances.id", ondelete="CASCADE")
    )
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))

    # Staff member who operated the scanner, for accountability. Nullable for
    # future self-scan kiosk flows.
    scanned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event_instance: Mapped["EventInstance"] = relationship()
    person: Mapped["Person"] = relationship(foreign_keys=[person_id])
    scanned_by: Mapped["Person | None"] = relationship(foreign_keys=[scanned_by_id])
