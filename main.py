
from collections import Counter
from itertools import count
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Event Platform API")

EventType = Literal["click", "page_view", "purchase"]

class EventCreate(BaseModel):
    source: str = Field(min_length=2)
    event_type: EventType
    value: float = Field(ge=0)

class Event(EventCreate):
    id: int

events: dict[int, Event] = {}
next_id = count(1)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/events", response_model=Event, status_code=201)
def create_event(payload: EventCreate):
    event = Event(
        id=next(next_id),
        **payload.model_dump()
    )
    events[event.id] = event
    return event

@app.get("/events", response_model=list[Event])
def list_events(event_type: EventType | None = None):
    return [
        event for event in events.values()
        if event_type is None
        or event.event_type == event_type
    ]

@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int):
    event = events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.get("/metrics")
def get_metrics():
    counts = Counter(
        event.event_type for event in events.values()
    )
    return {
        "total_events": len(events),
        "by_type": dict(counts)
    }
