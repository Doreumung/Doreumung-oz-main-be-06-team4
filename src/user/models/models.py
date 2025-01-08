import random
import string
import uuid
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from pydantic import EmailStr, ValidationError
from sqlalchemy import Date, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlmodel import Field, Relationship, SQLModel

from src.reviews.models.models import Comment, Like, Review


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class SocialProvider(StrEnum):
    KAKAO = "kakao"
    GOOGLE = "google"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String(36))  # type: ignore
    email: str = Field(sa_type=String(50), unique=True, nullable=False, index=True)  # type: ignore
    password: str = Field(sa_type=String(255), nullable=False)  # type: ignore
    nickname: Optional[str] = Field(sa_type=String(30), nullable=False)  # type: ignore
    birthday: Optional[date] = Field(sa_type=Date, nullable=True)
    gender: Optional[Gender] = Field(sa_type=SqlEnum(Gender), nullable=True)  # type: ignore
    oauth_id: Optional[str] = Field(sa_type=String(100), nullable=True)  # type: ignore
    is_superuser: Optional[bool] = Field(default=False, nullable=True)
    social_provider: Optional[SocialProvider] = Field(sa_type=SqlEnum(SocialProvider), nullable=True)  # type: ignore
    is_deleted: Optional[bool] = Field(default=False, nullable=True)
    deleted_at: Optional[datetime] = Field(nullable=True)
    created_at: datetime = Field(default_factory=func.now, nullable=False, sa_type=DateTime)
    updated_at: datetime = Field(
        default_factory=func.now, nullable=False, sa_type=DateTime, sa_column_kwargs={"onupdate": func.now()}
    )
    travel_routes: list["TravelRoute"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})  # type: ignore
    likes: list["Like"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )
    comments: list["Comment"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )
    review: Optional["Review"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )

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
        gender: Optional[Gender],
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
        return self.is_deleted and self.deleted_at is not None  # type: ignore

    def is_ready_for_hard_delete(self) -> bool:
        """삭제 예약 시간이 경과했는지 확인"""
        if self.is_deleted and self.deleted_at:
            deleted_at_datetime = self.deleted_at
            if isinstance(deleted_at_datetime, datetime):
                return datetime.now(timezone(timedelta(hours=9))) > deleted_at_datetime
        return False
