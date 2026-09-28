import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ministry import MinistryMemberRole


class MinistryCreate(BaseModel):
    name: str
    description: str | None = None


class MinistryOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MinistryMembershipCreate(BaseModel):
    person_id: uuid.UUID
    role: MinistryMemberRole = MinistryMemberRole.MEMBER


class MinistryMembershipOut(BaseModel):
    id: uuid.UUID
    ministry_id: uuid.UUID
    person_id: uuid.UUID
    role: MinistryMemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}
