import random
import string
import uuid
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Optional

from pydantic import EmailStr, ValidationError
from sqlalchemy import Boolean, Date, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.orm import Base


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class SocialProvider(StrEnum):
    KAKAO = "kakao"
    GOOGLE = "google"


class User(Base):  # type: ignore
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 난수 uuid
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False)
    birthday: Mapped[Date] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(SqlEnum(Gender), nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    social_provider: Mapped[Optional[SocialProvider | None]] = mapped_column(SqlEnum(SocialProvider), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 추가 문자열로 처리하여 순환 참조 방지
    likes = relationship("Like", back_populates="user")
    comments = relationship("Comment", back_populates="user")

    @staticmethod
    def _is_bcrypt_pattern(password: str) -> bool:
        from src.user.services.authentication import is_bcrypt_pattern

        return is_bcrypt_pattern(password)

    @classmethod
    def create(
        cls,
        email: EmailStr,
        password: str,
        nickname: str,
        birthday: date,
        gender: Gender,
    ) -> "User":
        from src.user.services.authentication import hash_password

        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(plain_text=password)
        return cls(
            email=email,
            password=hashed_password,
            nickname=nickname,
            birthday=birthday,
            gender=gender,
        )

    @classmethod
    def social_signup(cls, social_provider: SocialProvider, subject: str, email: EmailStr, nickname: str) -> "User":
        from src.user.services.authentication import hash_password

        unique_id = uuid.uuid4().hex[:6]
        oauth_id: str = f"{social_provider[:3]}#{subject[:8]}_{unique_id}"
        password: str = "".join(random.choices(string.ascii_letters, k=16))
        hashed_password = hash_password(plain_text=password)
        return cls(
            oauth_id=oauth_id,
            email=email,
            nickname=nickname,
            password=hashed_password,
            social_provider=social_provider,
        )

    def update_password(self, password: str) -> None:
        from src.user.services.authentication import hash_password

        if self._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        hashed_password = hash_password(plain_text=password)
        self.password = hashed_password

    def update_email(self, email: EmailStr) -> None:
        # email type validation
        try:
            email = str(email)
            self.email = str(email)
        except ValidationError:
            raise ValueError("Invalid email format")

    def mark_as_deleted(self) -> None:
        """사용자를 소프트 삭제로 설정"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone(timedelta(hours=9)))

    def restore(self) -> None:
        """소프트 삭제된 사용자 복원"""
        self.is_deleted = False
        self.deleted_at = None

    def is_deletion_scheduled(self) -> bool:
        """삭제 예약이 되었는지 확인"""
        return self.is_deleted and self.deleted_at is not None

    def is_ready_for_hard_delete(self) -> bool:
        """삭제 예약 시간이 경과했는지 확인"""
        if self.is_deleted and self.deleted_at:
            deleted_at_datetime = self.deleted_at
            if isinstance(deleted_at_datetime, datetime):
                return datetime.now(timezone(timedelta(hours=9))) > deleted_at_datetime
        return False
