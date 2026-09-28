import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_person, require_roles
from app.db.session import get_db
from app.models.announcement import Announcement, AnnouncementVisibility
from app.models.person import AccountStatus, Person, Role
from app.schemas.announcement import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

MANAGE = require_roles(Role.ADMIN, Role.HEAD_PASTOR)


@router.get("/public", response_model=list[AnnouncementOut])
def list_public(db: Session = Depends(get_db)):
    """No auth required — this is what the public marketing site renders."""
    return (
        db.execute(
            select(Announcement)
            .where(
                Announcement.visibility == AnnouncementVisibility.PUBLIC,
                Announcement.is_published.is_(True),
            )
            .order_by(Announcement.created_at.desc())
        )
        .scalars()
        .all()
    )


@router.get("", response_model=list[AnnouncementOut])
def list_all(db: Session = Depends(get_db), current: Person = Depends(get_current_person)):
    """All announcements, including members-only ones, for logged-in + approved users."""
    if current.status != AccountStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not approved")
    return db.execute(select(Announcement).order_by(Announcement.created_at.desc())).scalars().all()


@router.post("", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate, db: Session = Depends(get_db), current: Person = Depends(MANAGE)
):
    announcement = Announcement(created_by_id=current.id, **payload.model_dump())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.patch("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: uuid.UUID,
    payload: AnnouncementUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE),
):
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(announcement, field, value)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(MANAGE)
):
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    db.delete(announcement)
    db.commit()
