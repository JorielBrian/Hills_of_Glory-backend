from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_approved
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.models.event import EventInstance
from app.models.ministry import Ministry
from app.models.person import AccountStatus, Person

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: Person = Depends(require_approved)):
    """Feeds the dashboard Overview cards: attendance (last 30 days),
    pending users, and active ministry count."""
    since = date.today() - timedelta(days=30)

    attendance_count = db.execute(
        select(func.count(AttendanceRecord.id))
        .join(EventInstance, AttendanceRecord.event_instance_id == EventInstance.id)
        .where(EventInstance.date >= since)
    ).scalar_one()

    pending_users = db.execute(
        select(func.count(Person.id)).where(Person.status == AccountStatus.PENDING)
    ).scalar_one()

    ministry_count = db.execute(select(func.count(Ministry.id))).scalar_one()

    return {
        "attendance_last_30_days": attendance_count,
        "pending_users": pending_users,
        "active_ministries": ministry_count,
    }


@router.get("/attendance-trend")
def attendance_trend(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    _: Person = Depends(require_approved),
):
    """Daily attendance counts between start and end, for charting."""
    rows = db.execute(
        select(EventInstance.date, func.count(AttendanceRecord.id))
        .join(AttendanceRecord, AttendanceRecord.event_instance_id == EventInstance.id)
        .where(EventInstance.date >= start, EventInstance.date <= end)
        .group_by(EventInstance.date)
        .order_by(EventInstance.date)
    ).all()
    return [{"date": str(d), "count": c} for d, c in rows]
