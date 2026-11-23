
from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_db
from models import EventRecord

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


@app.post("/events", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    session: Session = Depends(get_db)
):
    record = EventRecord(**payload.model_dump())

    session.add(record)
    session.commit()
    session.refresh(record)

    return record


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
def get_metrics(session: Session = Depends(get_db)):
    rows = session.execute(
        select(
            EventRecord.event_type,
            func.count(EventRecord.id)
        ).group_by(EventRecord.event_type)
    ).all()

    return {
        "total_events": sum(count for _, count in rows),
        "by_type": {
            event_type: count
            for event_type, count in rows
        }
    }
