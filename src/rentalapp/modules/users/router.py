from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from rentalapp.core.deps import get_current_user, require_roles
from rentalapp.database import get_db
from rentalapp.modules.users.models import User, UserRole
from rentalapp.modules.users.schemas import Token, UserCreate, UserRead, UserUpdate
from rentalapp.modules.users.service import UserService

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.post("/auth/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    return UserService(db).register(data)


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    token = UserService(db).authenticate(form_data.username, form_data.password)
    return Token(access_token=token)


@router.get("/users/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[User]:
    return UserService(db).list()


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    return UserService(db).get(user_id)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    return UserService(db).update(user_id, data)
