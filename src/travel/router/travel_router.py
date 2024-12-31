from typing import Annotated

from fastapi import APIRouter, Body

from src.config.database.connection_async import get_async_session
from src.travel.dtos.travel_route import (
    GenerateTravelRouteRequest,
    GenerateTravelRouteResponse,
    GetTravelRouteListRequest,
    GetTravelRouteListResponse,
    GetTravelRouteOneRequest,
    GetTravelRouteOneResponse,
    ReGenerateTravelRouteRequest,
    ReGenerateTravelRouteResponse,
    SaveTravelRouteRequest,
    SaveTravelRouteResponse,
)
from src.travel.models.place import Place

router = APIRouter(prefix="/travelroute", tags=["Travel"])


@router.post("/", response_model=GenerateTravelRouteResponse)
async def generator_travel_route(request_data: GenerateTravelRouteRequest) -> GenerateTravelRouteResponse:
    return GenerateTravelRouteResponse()


@router.patch("/", response_model=ReGenerateTravelRouteResponse)
async def re_generator_travel_route(request_data: ReGenerateTravelRouteRequest) -> ReGenerateTravelRouteResponse:
    pass


@router.get("/save", response_model=SaveTravelRouteResponse)
async def save_travel_route(request_data: SaveTravelRouteRequest) -> SaveTravelRouteResponse:
    pass


@router.get("/", response_model=GetTravelRouteListResponse)
async def get_travel_routes(request_data: GetTravelRouteListRequest) -> GetTravelRouteListResponse:
    pass


@router.get("/{id}", response_model=GetTravelRouteOneResponse)
async def get_one_travel_route(request_data: GetTravelRouteOneRequest) -> GetTravelRouteOneResponse:
    pass


@router.delete("/{id}", status_code=204)
async def delete_one_travel_route() -> None:
    pass
