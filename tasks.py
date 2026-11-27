
import json
import logging
from datetime import datetime, timezone

from redis.exceptions import RedisError

from cache import redis_client

logger = logging.getLogger(__name__)

RECENT_EVENTS_KEY = "events:recent"


def record_recent_event(
    event_id: int,
    event_type: str,
    source: str,
):
    activity = {
        "event_id": event_id,
        "event_type": event_type,
        "source": source,
        "processed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    logger.info(
        "Background processing event id=%s",
        event_id,
    )

    try:
        with redis_client.pipeline() as pipe:
            pipe.lpush(
                RECENT_EVENTS_KEY,
                json.dumps(activity),
            )
            pipe.ltrim(RECENT_EVENTS_KEY, 0, 49)
            pipe.execute()

    except RedisError as exc:
        logger.warning(
            "Could not record event activity: %s",
            exc,
        )
