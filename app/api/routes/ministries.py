import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_approved, require_roles
from app.db.session import get_db
from app.models.ministry import Ministry, MinistryMembership
from app.models.person import Person, Role
from app.schemas.ministry import (
    MinistryCreate,
    MinistryMembershipCreate,
    MinistryMembershipOut,
    MinistryOut,
)

router = APIRouter(prefix="/api/ministries", tags=["ministries"])

MANAGE = require_roles(Role.ADMIN, Role.HEAD_PASTOR)


@router.get("", response_model=list[MinistryOut])
def list_ministries(db: Session = Depends(get_db), _: Person = Depends(require_approved)):
    return db.execute(select(Ministry).order_by(Ministry.name)).scalars().all()


@router.post("", response_model=MinistryOut, status_code=status.HTTP_201_CREATED)
def create_ministry(
    payload: MinistryCreate, db: Session = Depends(get_db), _: Person = Depends(MANAGE)
):
    ministry = Ministry(**payload.model_dump())
    db.add(ministry)
    db.commit()
    db.refresh(ministry)
    return ministry


@router.get("/{ministry_id}/members", response_model=list[MinistryMembershipOut])
def list_members(
    ministry_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(require_approved)
):
    return (
        db.execute(select(MinistryMembership).where(MinistryMembership.ministry_id == ministry_id))
        .scalars()
        .all()
    )


@router.post(
    "/{ministry_id}/members",
    response_model=MinistryMembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    ministry_id: uuid.UUID,
    payload: MinistryMembershipCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE),
):
    # Any approved member can be assigned as director of THIS ministry —
    # directorship is scoped per-ministry, not a global role.
    if db.get(Ministry, ministry_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministry not found")
    membership = MinistryMembership(ministry_id=ministry_id, **payload.model_dump())
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.delete("/{ministry_id}/members/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    ministry_id: uuid.UUID,
    person_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE),
):
    membership = db.execute(
        select(MinistryMembership).where(
            MinistryMembership.ministry_id == ministry_id,
            MinistryMembership.person_id == person_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    db.delete(membership)
    db.commit()
