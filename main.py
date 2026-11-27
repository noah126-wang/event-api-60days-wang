
from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_db
from models import EventRecord

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from fastapi import BackgroundTasks
from tasks import record_recent_event

from cache import (
    get_cached_metrics,
    set_cached_metrics,
    invalidate_metrics_cache,
)

EventType = Literal["click", "page_view", "purchase"]


class EventCreate(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    event_type: EventType
    value: float = Field(ge=0)


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


app = FastAPI(title="Event Platform API")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health", responses={503: {"description": "Database unavailable"}})
def db_health(session: Session = Depends(get_db)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    return {"database": "connected"}


@app.post(
    "/events",
    response_model=EventRead,
    status_code=201,
)
def create_event(
    payload: EventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    event = EventRecord(**payload.model_dump())

    db.add(event)
    db.commit()
    db.refresh(event)

    invalidate_metrics_cache()

    background_tasks.add_task(
        record_recent_event,
        event.id,
        event.event_type,
        event.source,
    )

    return event


@app.get("/events", response_model=list[EventRead])
def list_events(
    session: Session = Depends(get_db),
    event_type: EventType | None = None
):
    stmt = select(EventRecord).order_by(EventRecord.id)

    if event_type is not None:
        stmt = stmt.where(
            EventRecord.event_type == event_type
        )

    return session.scalars(stmt).all()


@app.get("/events/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_db)
):
    record = session.get(EventRecord, event_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return record

@app.delete("/events/{event_id}", status_code=204, response_class=Response)
def delete_event(
    event_id: int,
    session: Session = Depends(get_db),
) -> Response:
    record = session.get(EventRecord, event_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Event not found")

    session.delete(record)
    session.commit()

    return Response(status_code=204)


@app.get("/metrics")
def get_metrics(
    response: Response,
    db: Session = Depends(get_db),
):
    cached, cache_state = get_cached_metrics()

    response.headers["X-Cache"] = cache_state

    if cached is not None:
        return cached

    rows = db.execute(
        select(
            EventRecord.event_type,
            func.count(EventRecord.id),
        ).group_by(EventRecord.event_type)
    ).all()

    counts = {
        event_type: count
        for event_type, count in rows
    }

    result = {
        "total": sum(counts.values()),
        "by_type": counts,
    }

    set_cached_metrics(result)

    return result

