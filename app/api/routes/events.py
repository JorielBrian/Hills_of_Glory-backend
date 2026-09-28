import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_approved, require_roles
from app.db.session import get_db
from app.models.event import EventInstance, EventTemplate, InstanceStatus
from app.models.person import Person, Role
from app.schemas.event import (
    EventInstanceCreate,
    EventInstanceOut,
    EventInstanceUpdate,
    EventTemplateCreate,
    EventTemplateOut,
)

router = APIRouter(prefix="/api/events", tags=["events"])

MANAGE = require_roles(Role.ADMIN, Role.HEAD_PASTOR, Role.NETWORK_LEADER)


def _week_bounds(d: date) -> tuple[date, date]:
    monday = d - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=6)


def _apply_suppression(db: Session, new_instance: EventInstance) -> None:
    """
    If the new instance's template suppresses another template (e.g. Prayer &
    Fasting suppresses Prayer Encounter), cancel that template's scheduled
    instance for the same calendar week, if one exists.
    """
    if new_instance.template_id is None:
        return
    template = db.get(EventTemplate, new_instance.template_id)
    if template is None or template.suppresses_template_id is None:
        return

    week_start, week_end = _week_bounds(new_instance.date)
    to_suppress = db.execute(
        select(EventInstance).where(
            EventInstance.template_id == template.suppresses_template_id,
            EventInstance.date >= week_start,
            EventInstance.date <= week_end,
            EventInstance.status == InstanceStatus.SCHEDULED,
        )
    ).scalars().all()
    for instance in to_suppress:
        instance.status = InstanceStatus.CANCELLED
        instance.suppressed_by_instance_id = new_instance.id


# --- Templates -------------------------------------------------------------


@router.get("/templates", response_model=list[EventTemplateOut])
def list_templates(db: Session = Depends(get_db), _: Person = Depends(require_approved)):
    return db.execute(select(EventTemplate)).scalars().all()


@router.post("/templates", response_model=EventTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: EventTemplateCreate, db: Session = Depends(get_db), _: Person = Depends(MANAGE)
):
    template = EventTemplate(**payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


# --- Instances ---------------------------------------------------------------


@router.get("/instances", response_model=list[EventInstanceOut])
def list_instances(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    _: Person = Depends(require_approved),
):
    """Returns the effective calendar for a range: cancelled/suppressed instances
    are included with status=cancelled so the UI can grey them out with a reason."""
    query = select(EventInstance)
    if start is not None:
        query = query.where(EventInstance.date >= start)
    if end is not None:
        query = query.where(EventInstance.date <= end)
    return db.execute(query.order_by(EventInstance.date, EventInstance.start_time)).scalars().all()


@router.post("/instances", response_model=EventInstanceOut, status_code=status.HTTP_201_CREATED)
def create_instance(
    payload: EventInstanceCreate, db: Session = Depends(get_db), _: Person = Depends(MANAGE)
):
    instance = EventInstance(**payload.model_dump())
    db.add(instance)
    db.flush()  # get instance.id without committing yet
    _apply_suppression(db, instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.patch("/instances/{instance_id}", response_model=EventInstanceOut)
def update_instance(
    instance_id: uuid.UUID,
    payload: EventInstanceUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE),
):
    """Reschedule (date/time/location) or cancel a single instance without
    touching the recurring template — for one-off schedule changes."""
    instance = db.get(EventInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event instance not found")

    updates = payload.model_dump(exclude_unset=True)
    date_or_time_changed = "date" in updates or "start_time" in updates or "end_time" in updates
    for field, value in updates.items():
        setattr(instance, field, value)
    if date_or_time_changed and "status" not in updates:
        instance.status = InstanceStatus.RESCHEDULED

    db.commit()
    db.refresh(instance)
    return instance
