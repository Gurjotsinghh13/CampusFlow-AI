"""
Usage:
    python scripts/create_admin_hash.py "YourPasswordHere"

Copy the printed hash into ADMIN_PASSWORD_HASH in your .env file.
"""

import sys

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_admin_hash.py <password>")
        sys.exit(1)
    print(pwd_context.hash(sys.argv[1]))
