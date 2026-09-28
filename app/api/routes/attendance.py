import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.models.event import EventInstance
from app.models.person import Person, Role
from app.schemas.attendance import AttendanceRecordOut, AttendanceScanRequest

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

# Whoever is allowed to operate the door scanner. Adjust as needed.
SCAN = require_roles(Role.ADMIN, Role.HEAD_PASTOR, Role.NETWORK_LEADER, Role.LIFE_GUIDE)


@router.post("/scan", response_model=AttendanceRecordOut, status_code=status.HTTP_201_CREATED)
def scan(
    payload: AttendanceScanRequest,
    db: Session = Depends(get_db),
    operator: Person = Depends(SCAN),
):
    person = db.execute(select(Person).where(Person.qr_code == payload.qr_code)).scalar_one_or_none()
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not recognized")

    instance = db.get(EventInstance, payload.event_instance_id)
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event instance not found")

    record = AttendanceRecord(
        event_instance_id=instance.id,
        person_id=person.id,
        scanned_by_id=operator.id,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Unique constraint on (event_instance_id, person_id) caught a duplicate scan.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{person.full_name} has already been scanned in for this event",
        )
    db.refresh(record)
    return record


@router.get("/instances/{instance_id}", response_model=list[AttendanceRecordOut])
def list_for_instance(
    instance_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(SCAN)
):
    return (
        db.execute(select(AttendanceRecord).where(AttendanceRecord.event_instance_id == instance_id))
        .scalars()
        .all()
    )


@router.get("/people/{person_id}", response_model=list[AttendanceRecordOut])
def list_for_person(
    person_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(SCAN)
):
    return (
        db.execute(select(AttendanceRecord).where(AttendanceRecord.person_id == person_id))
        .scalars()
        .all()
    )
