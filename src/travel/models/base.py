from datetime import datetime, timedelta, timezone
from typing import Annotated

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

kst = timezone(timedelta(hours=9))


class BaseDatetime(SQLModel):
    __tablename__ = None

    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(kst), sa_column=Column(DateTime(timezone=True)))
    ]
    updated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(kst),
            sa_column=Column(DateTime(timezone=True), onupdate=lambda: datetime.now(kst)),  # sqlalchemy 문법사용
        ),
    ]
