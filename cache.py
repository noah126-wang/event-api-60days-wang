
import json
import logging
import os

from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "60"))

METRICS_CACHE_KEY = "metrics:counts:v1"

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)


def get_cached_metrics():
    try:
        raw = redis_client.get(METRICS_CACHE_KEY)

        if raw is None:
            return None, "MISS"

        return json.loads(raw), "HIT"

    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Cache read failed: %s", exc)
        return None, "BYPASS"


def set_cached_metrics(data):
    try:
        redis_client.set(
            METRICS_CACHE_KEY,
            json.dumps(data),
            ex=CACHE_TTL,
        )
    except RedisError as exc:
        logger.warning("Cache write failed: %s", exc)


def invalidate_metrics_cache():
    try:
        redis_client.delete(METRICS_CACHE_KEY)
    except RedisError as exc:
        logger.warning("Cache invalidation failed: %s", exc)
