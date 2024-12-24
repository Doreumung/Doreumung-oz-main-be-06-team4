import random
import string
import uuid
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column

from pydantic import ValidationError
from pydantic.v1 import EmailStr
from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, func

from src.config.orm import Base
from src.user.services.authentication import hash_password, is_bcrypt_pattern


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class SocialProvider(StrEnum):
    KAKAO = "kakao"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    birthday: Mapped[Date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(SqlEnum(Gender), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    oauth_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    social_provider: Mapped[SocialProvider | None] = mapped_column(SqlEnum(SocialProvider), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @staticmethod
    def _is_bcrypt_pattern(password: str) -> bool:
        return is_bcrypt_pattern(password)

    @classmethod
    def create(cls, email: str, password: str):
        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(plain_text=password)
        return cls(email=email, password=hashed_password)

    @classmethod
    def social_signup(cls, social_provider: SocialProvider, subject: str, email: str):
        unique_id = uuid.uuid4().hex[:6]
        username: str = f"{social_provider[:3]}#{subject[:8]}_{unique_id}"
        password: str = "".join(random.choices(string.ascii_letters, k=16))
        hashed_password = hash_password(plain_text=password)
        return cls(
            username=username,
            email=email,
            password=hashed_password,
            social_login=social_provider,
        )

    def update_password(self, password: str):
        if self._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        hashed_password = hash_password(plain_text=password)
        self.password = hashed_password

    def update_email(self, email: str):
        # email type validation
        try:
            email = EmailStr(email)
            self.email = str(email)
        except ValidationError:
            raise ValueError("Invalid email format")
