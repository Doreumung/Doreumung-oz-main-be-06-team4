from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from sqlmodel import Field, SQLModel

from src.travel.models.base import BaseDatetime


class TravelRoutePlace(BaseDatetime, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    travel_route_id: int = Field(..., foreign_key="travelroute.id")
    place_id: int = Field(..., foreign_key="place.id")
    priority: int
    route_time: datetime
    distance: float

