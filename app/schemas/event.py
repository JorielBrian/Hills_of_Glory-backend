import uuid
from datetime import date as date_
from datetime import datetime, time

from pydantic import BaseModel

from app.models.event import InstanceStatus, RecurrenceType


class EventTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    recurrence_type: RecurrenceType
    recurrence_config: dict = {}
    default_start_time: time | None = None
    default_end_time: time | None = None
    default_location: str | None = None
    suppresses_template_id: uuid.UUID | None = None


class EventTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    recurrence_type: RecurrenceType
    recurrence_config: dict
    default_start_time: time | None
    default_end_time: time | None
    default_location: str | None
    is_active: bool
    suppresses_template_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class EventInstanceCreate(BaseModel):
    """Create a standalone instance, or override one generated from a template."""

    template_id: uuid.UUID | None = None
    title: str | None = None
    date: date_
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    notes: str | None = None


class EventInstanceUpdate(BaseModel):
    """Used for one-off reschedules: change date and/or time independent of the template."""

    title: str | None = None
    date: date_ | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    status: InstanceStatus | None = None
    notes: str | None = None


class EventInstanceOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID | None
    title: str | None
    date: date_
    start_time: time | None
    end_time: time | None
    location: str | None
    status: InstanceStatus
    suppressed_by_instance_id: uuid.UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
