from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from src.travel.models.base import BaseDatetime
from src.travel.models.enums import RegionEnum, ThemeEnum


class Place(BaseDatetime, table=True):
    __tablename__ = "place"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=100)  # varchar(255)로 설정됨 이름중복 x
    theme: ThemeEnum
    region: RegionEnum
    latitude: float
    longitude: float
    travel_route_places: list["TravelRoutePlace"] = Relationship(  # type: ignore
        back_populates="place", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class PlaceUpdate(SQLModel):
    name: str | None = None
    theme: ThemeEnum | None = None
    region: RegionEnum | None = None
    latitude: float | None = None
    longitude: float | None = None
