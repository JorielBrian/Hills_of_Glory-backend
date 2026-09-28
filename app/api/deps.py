import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.person import AccountStatus, Person, Role

# tokenUrl is only used for the OpenAPI docs "Authorize" button; the
# frontend gets its token from POST /api/auth/login and sends it as a
# Bearer header (see apps/web/services/api-client.ts).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_current_person(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Person:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_error

    person = db.get(Person, uuid.UUID(payload["sub"]))
    if person is None:
        raise credentials_error
    return person


def require_approved(person: Person = Depends(get_current_person)) -> Person:
    if person.status != AccountStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not approved yet",
        )
    return person


def require_roles(*allowed_roles: Role):
    """Usage: Depends(require_roles(Role.ADMIN, Role.HEAD_PASTOR))"""

    def dependency(person: Person = Depends(require_approved)) -> Person:
        if person.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return person

    return dependency
