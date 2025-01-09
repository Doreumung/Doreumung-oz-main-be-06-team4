from datetime import datetime, time
from typing import Annotated, List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlmodel import Field, Relationship, SQLModel

from src.reviews.models.models import Review
from src.travel.models.base import BaseDatetime, kst
from src.travel.models.enums import RegionEnum, ThemeEnum
from src.user.models.models import User


class TravelRoute(BaseDatetime, table=True):
    __tablename__ = "travelroute"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    user_id: str = Field(..., foreign_key="users.id")
    regions: list[RegionEnum] = Field(sa_type=JSON)
    themes: list[ThemeEnum] = Field(sa_type=JSON)
    breakfast: bool
    morning: int
    lunch: bool
    afternoon: int
    dinner: bool
    travel_route_places: list["TravelRoutePlace"] = Relationship(
        back_populates="travel_route", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    user: "User" = Relationship(back_populates="travel_routes")
    reviews: List["Review"] = Relationship(back_populates="travel_route")


class TravelRoutePlace(BaseDatetime, table=True):
    __tablename__ = "travelrouteplace"
    id: Optional[int] = Field(default=None, primary_key=True)
    travel_route_id: int = Field(..., foreign_key="travelroute.id")
    place_id: int = Field(..., foreign_key="place.id")
    priority: int
    travel_route: "TravelRoute" = Relationship(back_populates="travel_route_places")
    place: "Place" = Relationship(back_populates="travel_route_places")  # type: ignore
