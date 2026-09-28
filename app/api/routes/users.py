import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_approved, require_roles
from app.db.session import get_db
from app.models.person import AccountStatus, Person, Role
from app.schemas.person import (
    PersonCreate,
    PersonOut,
    PersonRoleUpdate,
    PersonStatusUpdate,
    PersonUpdate,
)

router = APIRouter(prefix="/api/users", tags=["users"])

MANAGE_USERS = require_roles(Role.ADMIN, Role.HEAD_PASTOR)


@router.get("", response_model=list[PersonOut])
def list_people(
    status_filter: AccountStatus | None = None,
    role_filter: Role | None = None,
    db: Session = Depends(get_db),
    _: Person = Depends(require_approved),
):
    query = select(Person)
    if status_filter is not None:
        query = query.where(Person.status == status_filter)
    if role_filter is not None:
        query = query.where(Person.role == role_filter)
    return db.execute(query.order_by(Person.created_at.desc())).scalars().all()


@router.get("/pending", response_model=list[PersonOut])
def list_pending(db: Session = Depends(get_db), _: Person = Depends(MANAGE_USERS)):
    return (
        db.execute(select(Person).where(Person.status == AccountStatus.PENDING))
        .scalars()
        .all()
    )


@router.post("", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
def create_person(
    payload: PersonCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_USERS),
):
    """Staff-created record with no login: kids, walk-in visitors, etc."""
    person = Person(status=AccountStatus.APPROVED, **payload.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(
    person_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(require_approved)
):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


@router.patch("/{person_id}", response_model=PersonOut)
def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_USERS),
):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    db.commit()
    db.refresh(person)
    return person


@router.patch("/{person_id}/status", response_model=PersonOut)
def update_status(
    person_id: uuid.UUID,
    payload: PersonStatusUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_USERS),
):
    """Approve or reject a pending registration."""
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    person.status = payload.status
    db.commit()
    db.refresh(person)
    return person


@router.patch("/{person_id}/role", response_model=PersonOut)
def update_role(
    person_id: uuid.UUID,
    payload: PersonRoleUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_USERS),
):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    person.role = payload.role
    db.commit()
    db.refresh(person)
    return person
