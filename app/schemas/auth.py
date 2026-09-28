import uuid
from datetime import date

from pydantic import BaseModel, EmailStr

from app.models.person import AccountStatus, Role


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    birthdate: date | None = None
    contact_number: str | None = None
    facebook_url: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: Role
    status: AccountStatus

    model_config = {"from_attributes": True}
