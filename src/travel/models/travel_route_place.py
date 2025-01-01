from datetime import datetime
from typing import Annotated, Optional

from sqlmodel import Field, Relationship, SQLModel

from sqlalchemy import Column, JSON, DateTime
from src.travel.models.enums import ThemeEnum, RegionEnum
from src.travel.models.base import BaseDatetime, kst
from src.user.models.models import User


class TravelRoute(BaseDatetime, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(..., foreign_key="users.id")
    regions: list[RegionEnum] = Field(sa_type=JSON)
    themes: list[ThemeEnum] = Field(sa_type=JSON)
    breakfast: bool
    morning: int
    lunch: bool
    afternoon: int
    dinner: bool
    travel_route_places: list["TravelRoutePlace"] = Relationship(back_populates="travel_route")
    user: User = Relationship(back_populates="travel_route")


class TravelRoutePlace(BaseDatetime, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    travel_route_id: int | None = Field(default=None, foreign_key="travelroute.id")
    place_id: int = Field(..., foreign_key="place.id")
    priority: int
    route_time: datetime
    distance: float
    travel_route: "TravelRoute" = Relationship(back_populates="travel_route_places")


