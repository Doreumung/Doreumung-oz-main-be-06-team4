from typing import Annotated, Optional
from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship
from src.travel.models.base import BaseDatetime
from src.travel.models.enums import ThemeEnum, RegionEnum
from src.travel.models.travel_route_place import TravelRoutePlace


class TravelRoute(BaseDatetime, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(..., foreign_key="users.id")
    regions: list[RegionEnum] = Field(sa_column=Column(JSON))
    themes: list[ThemeEnum] = Field(sa_column=Column(JSON))
    breakfast: bool
    morning: int
    lunch: bool
    afternoon: int
    dinner: bool
    travel_route_places: list[TravelRoutePlace] = Relationship(back_populates="travelrouteplaces")

