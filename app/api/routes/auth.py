from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_person
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.person import AccountStatus, MemberType, Person, Role
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        select(Person).where(
            (Person.email == payload.email) | (Person.username == payload.username)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email or username already exists",
        )

    person = Person(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        birthdate=payload.birthdate,
        contact_number=payload.contact_number,
        facebook_url=payload.facebook_url,
        role=Role.VISITOR,
        member_type=MemberType.ADULT,
        status=AccountStatus.PENDING,  # requires admin/head pastor approval before login works
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    person = db.execute(select(Person).where(Person.email == payload.email)).scalar_one_or_none()

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
    )
    if person is None or person.password_hash is None:
        raise invalid_credentials
    if not verify_password(payload.password, person.password_hash):
        raise invalid_credentials

    if person.status == AccountStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is still awaiting approval",
        )
    if person.status == AccountStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Your registration was not approved"
        )

    token = create_access_token(subject=str(person.id), extra_claims={"role": person.role.value})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(current: Person = Depends(get_current_person)):
    return current
