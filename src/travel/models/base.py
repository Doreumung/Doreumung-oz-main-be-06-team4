from datetime import datetime, timedelta, timezone
from typing import Annotated

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

kst = timezone(timedelta(hours=9))

'''
sa_column을 사용한 클래스를 상속받아서 사용했더니 created_at, updated_at 필드가 두번씩 생성되어 오류가 발생했다...
그래서 sa_type으로 변경하고 onupdate는 sa_column_kwargs를 사용하여 해결함
'''
class BaseDatetime(SQLModel):
    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(kst), sa_type=DateTime(timezone=True))
    ]
    updated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(kst),
            sa_type=DateTime(timezone=True), sa_column_kwargs={
                "onupdate": lambda: datetime.now(kst)
            } # sqlalchemy 문법사용
        ),
    ]
