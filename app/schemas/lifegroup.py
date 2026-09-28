import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.lifegroup import LifegroupMemberRole


class NetworkCreate(BaseModel):
    name: str
    leader_id: uuid.UUID | None = None


class NetworkOut(BaseModel):
    id: uuid.UUID
    name: str
    leader_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class LifegroupCreate(BaseModel):
    name: str
    description: str | None = None
    network_id: uuid.UUID | None = None


class LifegroupOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    network_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LifegroupMembershipCreate(BaseModel):
    person_id: uuid.UUID
    role: LifegroupMemberRole = LifegroupMemberRole.MEMBER


class LifegroupMembershipOut(BaseModel):
    id: uuid.UUID
    lifegroup_id: uuid.UUID
    person_id: uuid.UUID
    role: LifegroupMemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}
