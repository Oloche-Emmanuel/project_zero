from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from rentalapp.core.exceptions import AuthError, ForbiddenError
from rentalapp.core.security import decode_access_token
from rentalapp.database import get_db
from rentalapp.modules.users.models import User, UserRole
from rentalapp.modules.users.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError("Could not validate credentials")
    user = UserRepository(db).get(int(user_id))
    if user is None or not user.is_active:
        raise AuthError("Could not validate credentials")
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory for role-based access control.

    Usage: `current_user: User = Depends(require_roles(UserRole.ADMIN))`.
    New modules reuse this rather than re-implementing authorization.
    """

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"Requires one of roles: {[r.value for r in roles]}")
        return user

    return checker
