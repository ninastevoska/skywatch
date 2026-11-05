from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.clients.spacecatalog import (
    SpaceCatalogClient,
    SpaceCatalogError,
)
from app.models.event import AstronomicalEvent


router = APIRouter(
    prefix="/api/events",
    tags=["Astronomical Events"],
)


class EventsResponse(BaseModel):
    """Response containing astronomical events and their date range."""

    from_date: date
    to_date: date
    count: int = Field(ge=0)
    events: list[AstronomicalEvent]


@router.get("", response_model=EventsResponse)
def get_events(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> EventsResponse:
    """Retrieve astronomical events for the selected date range."""

    start = from_date or date.today()
    end = to_date or (start + timedelta(days=30))

    if start > end:
        raise HTTPException(
            status_code=400,
            detail="The start date must not be after the end date.",
        )

    if (end - start).days > 365:
        raise HTTPException(
            status_code=400,
            detail="The selected date range cannot exceed 365 days.",
        )

    try:
        client = SpaceCatalogClient()
        events = client.get_events(
            from_date=start,
            to_date=end,
        )

    except SpaceCatalogError as exc:
        raise HTTPException(
            status_code=502,
            detail="Astronomical event data is currently unavailable.",
        ) from exc

    return EventsResponse(
        from_date=start,
        to_date=end,
        count=len(events),
        events=events,
    )
