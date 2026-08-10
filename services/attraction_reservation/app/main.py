from __future__ import annotations

import os
from datetime import date
from enum import StrEnum
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from services.attraction_reservation.app.repository import ReservationRepository

router = APIRouter()


def create_app(database_url: str | None = None) -> FastAPI:
    application = FastAPI(
        title="Attraction Recommendation and Reservation Service",
        version="0.1.0",
    )
    repository = ReservationRepository(
        database_url or os.getenv("ATTRACTION_DATABASE_URL")
    )
    repository.initialize()
    application.state.repository = repository
    application.include_router(router)
    return application


def get_repository(request: Request) -> ReservationRepository:
    return request.app.state.repository


app: FastAPI


class ReservationStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class Attraction(BaseModel):
    attraction_id: str
    name: str
    category: str
    district: str
    indoor: bool
    tags: list[str]
    rating: float = Field(ge=0, le=5)
    capacity_per_day: int = Field(gt=0)
    open_days: list[str]
    description: str


class ReservationCreate(BaseModel):
    attraction_id: str
    citizen_id: str = Field(min_length=3, max_length=40)
    visit_date: date
    visitor_count: int = Field(gt=0, le=10)
    contact_phone: str | None = Field(default=None, max_length=30)


class Reservation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reservation_id: str
    attraction_id: str
    citizen_id: str
    visit_date: date
    visitor_count: int
    status: ReservationStatus
    contact_phone: str | None = None


class ReservationStatusUpdate(BaseModel):
    status: ReservationStatus


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] | None = None


ATTRACTIONS: dict[str, Attraction] = {
    "ATTR-1001": Attraction(
        attraction_id="ATTR-1001",
        name="Riverside Museum",
        category="museum",
        district="central",
        indoor=True,
        tags=["history", "family", "rainy-day"],
        rating=4.7,
        capacity_per_day=80,
        open_days=["tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        description="City history exhibitions with guided family sessions.",
    ),
    "ATTR-1002": Attraction(
        attraction_id="ATTR-1002",
        name="Harbour Botanic Garden",
        category="park",
        district="harbour",
        indoor=False,
        tags=["nature", "walking", "accessible"],
        rating=4.5,
        capacity_per_day=120,
        open_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
        description="Waterfront gardens, shaded paths, and accessible picnic areas.",
    ),
    "ATTR-1003": Attraction(
        attraction_id="ATTR-1003",
        name="Skyline Culture Tower",
        category="landmark",
        district="central",
        indoor=True,
        tags=["view", "evening", "popular"],
        rating=4.8,
        capacity_per_day=60,
        open_days=["wednesday", "thursday", "friday", "saturday", "sunday"],
        description="Observation deck and rotating local culture exhibition.",
    ),
    "ATTR-1004": Attraction(
        attraction_id="ATTR-1004",
        name="North Creek Heritage Trail",
        category="heritage",
        district="north",
        indoor=False,
        tags=["history", "walking", "quiet"],
        rating=4.2,
        capacity_per_day=90,
        open_days=["monday", "tuesday", "thursday", "friday", "saturday", "sunday"],
        description="Self-guided trail linking restored civic buildings.",
    ),
}

STATUS_TRANSITIONS = {
    ReservationStatus.pending: {
        ReservationStatus.confirmed,
        ReservationStatus.cancelled,
    },
    ReservationStatus.confirmed: {
        ReservationStatus.completed,
        ReservationStatus.cancelled,
    },
    ReservationStatus.completed: set(),
    ReservationStatus.cancelled: set(),
}


def error(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorDetail(code=code, message=message, details=details).model_dump(),
    )


def remaining_capacity(
    repository: ReservationRepository, attraction_id: str, visit_date: date
) -> int:
    attraction = ATTRACTIONS[attraction_id]
    reserved = repository.reserved_visitors(attraction_id, visit_date)
    return attraction.capacity_per_day - reserved


def ensure_available(
    repository: ReservationRepository,
    attraction: Attraction,
    visit_date: date,
    visitor_count: int,
) -> None:
    day_name = visit_date.strftime("%A").lower()
    if day_name not in attraction.open_days:
        raise error(
            status.HTTP_400_BAD_REQUEST,
            "ATTRACTION_CLOSED",
            "The attraction is closed on the requested date.",
            {"open_days": attraction.open_days},
        )

    remaining = remaining_capacity(repository, attraction.attraction_id, visit_date)
    if visitor_count > remaining:
        raise error(
            status.HTTP_409_CONFLICT,
            "CAPACITY_CONFLICT",
            "The requested visitor count exceeds remaining capacity.",
            {"remaining_capacity": remaining},
        )


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "attraction-reservation",
        "version": "0.1.0",
    }


@router.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "attraction-reservation",
        "owner": "C",
        "implementation": "selected_microservice",
        "status": "ready",
    }


@router.get("/api/v1/attractions")
async def list_attractions(
    request: Request,
    category: str | None = None,
    district: str | None = None,
    indoor: bool | None = None,
    min_rating: float = Query(default=0, ge=0, le=5),
    visit_date: date | None = None,
    visitor_count: int = Query(default=1, gt=0, le=10),
    recommend: bool = False,
) -> list[dict[str, object]]:
    repository = get_repository(request)
    attractions = list(ATTRACTIONS.values())
    if category:
        attractions = [item for item in attractions if item.category == category]
    if district:
        attractions = [item for item in attractions if item.district == district]
    if indoor is not None:
        attractions = [item for item in attractions if item.indoor is indoor]
    attractions = [item for item in attractions if item.rating >= min_rating]

    enriched = []
    for attraction in attractions:
        available_capacity = (
            remaining_capacity(repository, attraction.attraction_id, visit_date)
            if visit_date
            else attraction.capacity_per_day
        )
        if visit_date and available_capacity < visitor_count:
            continue
        score = attraction.rating * 20 + min(available_capacity, 50) / 5
        if visit_date:
            day_name = visit_date.strftime("%A").lower()
            if day_name in attraction.open_days:
                score += 5
            else:
                continue
        enriched.append(
            {
                **attraction.model_dump(),
                "available_capacity": available_capacity,
                "recommendation_score": round(score, 1),
            }
        )

    if recommend:
        enriched.sort(
            key=lambda item: (
                item["recommendation_score"],
                item["rating"],
                item["available_capacity"],
            ),
            reverse=True,
        )
    else:
        enriched.sort(key=lambda item: str(item["name"]))
    return enriched


@router.post(
    "/api/v1/reservations",
    response_model=Reservation,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    request: Request, payload: ReservationCreate
) -> Reservation:
    repository = get_repository(request)
    attraction = ATTRACTIONS.get(payload.attraction_id)
    if attraction is None:
        raise error(
            status.HTTP_404_NOT_FOUND,
            "ATTRACTION_NOT_FOUND",
            "The requested attraction was not found.",
        )

    ensure_available(
        repository,
        attraction,
        payload.visit_date,
        payload.visitor_count,
    )
    reservation = Reservation(
        reservation_id=f"RSV-{uuid4().hex[:8].upper()}",
        attraction_id=payload.attraction_id,
        citizen_id=payload.citizen_id,
        visit_date=payload.visit_date,
        visitor_count=payload.visitor_count,
        contact_phone=payload.contact_phone,
        status=ReservationStatus.confirmed,
    )
    record = repository.create(reservation.model_dump())
    return Reservation.model_validate(record)


@router.get("/api/v1/reservations/{reservation_id}", response_model=Reservation)
async def get_reservation(request: Request, reservation_id: str) -> Reservation:
    reservation = get_repository(request).get(reservation_id)
    if reservation is None:
        raise error(
            status.HTTP_404_NOT_FOUND,
            "RESERVATION_NOT_FOUND",
            "The requested reservation was not found.",
        )
    return Reservation.model_validate(reservation)


@router.patch(
    "/api/v1/reservations/{reservation_id}/status", response_model=Reservation
)
async def update_reservation_status(
    request: Request,
    reservation_id: str,
    payload: ReservationStatusUpdate,
) -> Reservation:
    repository = get_repository(request)
    reservation_record = repository.get(reservation_id)
    reservation = (
        Reservation.model_validate(reservation_record)
        if reservation_record is not None
        else None
    )
    if reservation is None:
        raise error(
            status.HTTP_404_NOT_FOUND,
            "RESERVATION_NOT_FOUND",
            "The requested reservation was not found.",
        )

    allowed = STATUS_TRANSITIONS[reservation.status]
    if payload.status not in allowed:
        raise error(
            status.HTTP_409_CONFLICT,
            "INVALID_RESERVATION_STATUS",
            "The requested reservation status transition is not allowed.",
            {
                "current_status": reservation.status,
                "requested_status": payload.status,
            },
        )

    updated = repository.update_status(reservation_id, payload.status.value)
    assert updated is not None
    return Reservation.model_validate(updated)


app = create_app()
