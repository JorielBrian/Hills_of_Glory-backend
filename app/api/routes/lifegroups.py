import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_approved, require_roles
from app.db.session import get_db
from app.models.lifegroup import Lifegroup, LifegroupMembership, Network
from app.models.person import Person, Role
from app.schemas.lifegroup import (
    LifegroupCreate,
    LifegroupMembershipCreate,
    LifegroupMembershipOut,
    LifegroupOut,
    NetworkCreate,
    NetworkOut,
)

router = APIRouter(prefix="/api/lifegroups", tags=["lifegroups"])

# Network Leaders manage leaders + members; Admin/Head Pastor manage everything.
MANAGE_NETWORKS = require_roles(Role.ADMIN, Role.HEAD_PASTOR)
MANAGE_GROUPS = require_roles(Role.ADMIN, Role.HEAD_PASTOR, Role.NETWORK_LEADER)


@router.get("/networks", response_model=list[NetworkOut])
def list_networks(db: Session = Depends(get_db), _: Person = Depends(require_approved)):
    return db.execute(select(Network).order_by(Network.name)).scalars().all()


@router.post("/networks", response_model=NetworkOut, status_code=status.HTTP_201_CREATED)
def create_network(
    payload: NetworkCreate, db: Session = Depends(get_db), _: Person = Depends(MANAGE_NETWORKS)
):
    network = Network(**payload.model_dump())
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@router.get("", response_model=list[LifegroupOut])
def list_lifegroups(db: Session = Depends(get_db), _: Person = Depends(require_approved)):
    return db.execute(select(Lifegroup).order_by(Lifegroup.name)).scalars().all()


@router.post("", response_model=LifegroupOut, status_code=status.HTTP_201_CREATED)
def create_lifegroup(
    payload: LifegroupCreate, db: Session = Depends(get_db), _: Person = Depends(MANAGE_GROUPS)
):
    lifegroup = Lifegroup(**payload.model_dump())
    db.add(lifegroup)
    db.commit()
    db.refresh(lifegroup)
    return lifegroup


@router.get("/{lifegroup_id}/members", response_model=list[LifegroupMembershipOut])
def list_members(
    lifegroup_id: uuid.UUID, db: Session = Depends(get_db), _: Person = Depends(require_approved)
):
    return (
        db.execute(
            select(LifegroupMembership).where(LifegroupMembership.lifegroup_id == lifegroup_id)
        )
        .scalars()
        .all()
    )


@router.post(
    "/{lifegroup_id}/members",
    response_model=LifegroupMembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    lifegroup_id: uuid.UUID,
    payload: LifegroupMembershipCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_GROUPS),
):
    if db.get(Lifegroup, lifegroup_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lifegroup not found")
    membership = LifegroupMembership(lifegroup_id=lifegroup_id, **payload.model_dump())
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.delete("/{lifegroup_id}/members/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    lifegroup_id: uuid.UUID,
    person_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Person = Depends(MANAGE_GROUPS),
):
    membership = db.execute(
        select(LifegroupMembership).where(
            LifegroupMembership.lifegroup_id == lifegroup_id,
            LifegroupMembership.person_id == person_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    db.delete(membership)
    db.commit()
