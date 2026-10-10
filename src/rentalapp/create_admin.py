"""Create (or promote) an admin account from the command line.

Public sign-up cannot create admins, so the first admin is made here:

    python -m rentalapp.create_admin admin@example.com "Full Name"

The password is prompted for (not passed as an argument, so it never lands
in shell history). Runs against DATABASE_URL, so it works locally or, with
the production URL set in the environment, against the live database.
"""

import argparse
import getpass
import sys

from rentalapp.core.security import hash_password
from rentalapp.database import SessionLocal
from rentalapp.migrate import upgrade_database
from rentalapp.modules.users.models import User, UserRole
from rentalapp.modules.users.repository import UserRepository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("full_name", nargs="?", default="Administrator")
    args = parser.parse_args(argv)

    upgrade_database()
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        existing = repo.get_by_email(args.email)
        if existing:
            existing.role = UserRole.ADMIN
            db.commit()
            print(f"Promoted existing user {args.email} to admin.")
            return 0

        password = getpass.getpass("Password for new admin: ")
        if len(password) < 8 or password != getpass.getpass("Repeat password: "):
            print("Passwords must match and be at least 8 characters.", file=sys.stderr)
            return 1
        repo.add(User(email=args.email, hashed_password=hash_password(password), full_name=args.full_name, role=UserRole.ADMIN))
        print(f"Created admin {args.email}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
