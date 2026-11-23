
import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


db_url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER", "postgres"),
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "event_platform"),
)

engine = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
