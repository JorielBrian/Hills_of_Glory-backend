import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.person import AccountStatus, MemberType, Role


class PersonCreate(BaseModel):
    """Used by staff to create a person record with no login (kid, walk-in visitor)."""

    full_name: str
    birthdate: date | None = None
    contact_number: str | None = None
    facebook_url: str | None = None
    member_type: MemberType = MemberType.ADULT
    guardian_id: uuid.UUID | None = None
    role: Role = Role.VISITOR


class PersonUpdate(BaseModel):
    full_name: str | None = None
    birthdate: date | None = None
    contact_number: str | None = None
    facebook_url: str | None = None
    member_type: MemberType | None = None
    guardian_id: uuid.UUID | None = None


class PersonRoleUpdate(BaseModel):
    role: Role


class PersonStatusUpdate(BaseModel):
    status: AccountStatus


class PersonOut(BaseModel):
    id: uuid.UUID
    full_name: str
    username: str | None
    email: str | None
    birthdate: date | None
    contact_number: str | None
    facebook_url: str | None
    role: Role
    member_type: MemberType
    status: AccountStatus
    guardian_id: uuid.UUID | None
    qr_code: str
    created_at: datetime

    model_config = {"from_attributes": True}
