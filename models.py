
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(String(100))

    event_type: Mapped[str] = mapped_column(
        String(20), index=True
    )

    value: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
