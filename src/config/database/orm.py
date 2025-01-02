from sqlmodel import SQLModel

from src.travel.models.travel_route_place import *
from src.user.models.models import *


class Base(SQLModel):
    pass
