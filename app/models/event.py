import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
    Time,
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecurrenceType(str, enum.Enum):
    WEEKLY = "weekly"  # e.g. Prayer Encounter, every Sunday
    MONTHLY_NTH_WEEKDAY = "monthly_nth_weekday"  # e.g. Prayer & Fasting, 1st Saturday
    ONE_OFF = "one_off"  # standalone events with no recurrence


class InstanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"  # date/time overridden from the recurrence default
    CANCELLED = "cancelled"  # e.g. a Prayer Encounter suppressed by Prayer & Fasting


class EventTemplate(Base):
    """
    A recurring event definition (e.g. Sunday Service, Prayer Encounter,
    Prayer & Fasting). Concrete calendar entries live in EventInstance.
    """

    __tablename__ = "event_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    recurrence_type: Mapped[RecurrenceType] = mapped_column(
        Enum(RecurrenceType, name="recurrence_type"), nullable=False
    )
    # WEEKLY: {"weekday": 6}  (Mon=0 ... Sun=6)
    # MONTHLY_NTH_WEEKDAY: {"nth": 1, "weekday": 5}  (1st Saturday)
    recurrence_config: Mapped[dict] = mapped_column(JSON, default=dict)

    default_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    default_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    default_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # If set, an instance of THIS template occurring in a given week/month
    # cancels the corresponding instance of the referenced template for
    # that same period. e.g. Prayer & Fasting.suppresses_template_id = Prayer Encounter.id
    suppresses_template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_templates.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instances: Mapped[list["EventInstance"]] = relationship(
        back_populates="template", foreign_keys="EventInstance.template_id"
    )


class EventInstance(Base):
    """A single concrete occurrence on the calendar, generated from a template or standalone."""

    __tablename__ = "event_instances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=True
    )
    # Standalone/one-off events skip the template and just set these directly.
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[InstanceStatus] = mapped_column(
        Enum(InstanceStatus, name="instance_status"), default=InstanceStatus.SCHEDULED
    )
    # Points to the instance that suppressed this one (e.g. this Prayer Encounter
    # instance was cancelled because of a Prayer & Fasting instance that week).
    suppressed_by_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_instances.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    template: Mapped["EventTemplate | None"] = relationship(
        back_populates="instances", foreign_keys=[template_id]
    )
