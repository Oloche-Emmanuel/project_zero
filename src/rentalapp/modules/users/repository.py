from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.users.models import User


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalars(stmt).first()
