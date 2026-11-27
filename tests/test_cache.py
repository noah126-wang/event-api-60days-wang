
import cache
from redis.exceptions import ConnectionError


class FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)


def test_metrics_cache_lifecycle(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(
        cache, "redis_client", fake
    )

    value, state = cache.get_cached_metrics()
    assert value is None
    assert state == "MISS"

    expected = {"counts": {"purchase": 3}}
    cache.set_cached_metrics(expected)

    value, state = cache.get_cached_metrics()
    assert value == expected
    assert state == "HIT"

    cache.invalidate_metrics_cache()

    value, state = cache.get_cached_metrics()
    assert value is None
    assert state == "MISS"


def test_redis_failure_bypasses_cache(monkeypatch):
    class UnavailableRedis:
        def get(self, key):
            raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(
        cache, "redis_client", UnavailableRedis()
    )

    value, state = cache.get_cached_metrics()

    assert value is None
    assert state == "BYPASS"
