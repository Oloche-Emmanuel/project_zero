from sqlalchemy.orm import Session

from rentalapp.core.exceptions import AuthError, ConflictError, NotFoundError
from rentalapp.core.security import create_access_token, hash_password, verify_password
from rentalapp.modules.users.models import User
from rentalapp.modules.users.repository import UserRepository
from rentalapp.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def register(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ConflictError(f"A user with email '{data.email}' already exists")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        return self.repo.add(user)

    def authenticate(self, email: str, password: str) -> str:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("User account is inactive")
        return create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})

    def get(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def list(self, offset: int = 0, limit: int = 100) -> list[User]:
        return self.repo.list(offset=offset, limit=limit)

    def update(self, user_id: int, data: UserUpdate) -> User:
        user = self.get(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.repo.db.commit()
        self.repo.db.refresh(user)
        return user
