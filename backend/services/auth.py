"""
services/auth.py – user signup/login and JWT token handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from db.models import User


class AuthService:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 720,
    ):
        self._session_factory = session_factory
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        # Prefer pbkdf2_sha256 for stable cross-platform behavior.
        # Keep bcrypt in verify list for compatibility with any existing hashes.
        self._pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt"],
            deprecated="auto",
        )

    async def create_user(self, name: str, email: str, password: str) -> User:
        email_norm = email.strip().lower()
        async with self._session_factory() as session:
            existing = await session.execute(select(User).where(User.email == email_norm))
            if existing.scalars().first():
                raise ValueError("Email already registered")

            user = User(
                name=name.strip(),
                email=email_norm,
                password_hash=self._pwd_context.hash(password),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        email_norm = email.strip().lower()
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.email == email_norm))
            user = result.scalars().first()
            if not user:
                return None
            if not self._pwd_context.verify(password, user.password_hash):
                return None
            return user

    def create_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self._access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    async def get_user_from_token(self, token: str) -> Optional[User]:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            user_id = int(payload.get("sub", "0"))
            if user_id <= 0:
                return None
        except (JWTError, ValueError):
            return None

        async with self._session_factory() as session:
            return await session.get(User, user_id)

    async def update_google_oauth(
        self,
        user_id: int,
        google_email: str,
        refresh_token: Optional[str] = None,
    ) -> Optional[User]:
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                return None
            user.google_email = (google_email or "").strip().lower()
            if refresh_token:
                user.google_refresh_token = refresh_token
            user.google_connected_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(user)
            return user
