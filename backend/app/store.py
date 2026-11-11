from __future__ import annotations

import json
import threading
import time
from collections import defaultdict

from .config import get_settings

try:
    import redis
except ImportError:  # pragma: no cover - requirements include redis
    redis = None


class RateLimiter:
    def __init__(self, limit: int, window: int = 60) -> None:
        self.limit = limit
        self.window = window
        self._lock = threading.Lock()
        self._events: dict[str, list[float]] = defaultdict(list)
        self._redis = None
        settings = get_settings()
        if redis and settings.redis_url:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def allow(self, key: str) -> bool:
        if self._redis is not None:
            try:
                redis_key = f"sealquery:rate:{key}"
                count = self._redis.incr(redis_key)
                if count == 1:
                    self._redis.expire(redis_key, self.window)
                return int(count) <= self.limit
            except Exception:
                pass

        now = time.time()
        with self._lock:
            events = [event for event in self._events[key] if now - event < self.window]
            if len(events) >= self.limit:
                self._events[key] = events
                return False
            events.append(now)
            self._events[key] = events
            return True


class IdempotencyStore:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self._lock = threading.Lock()
        self._memory: dict[str, tuple[float, dict]] = {}
        self._redis = None
        settings = get_settings()
        if redis and settings.redis_url:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def get(self, key: str) -> dict | None:
        if self._redis is not None:
            try:
                value = self._redis.get(f"sealquery:idem:{key}")
                return json.loads(value) if value else None
            except Exception:
                pass
        now = time.time()
        with self._lock:
            cached = self._memory.get(key)
            if cached and now - cached[0] < self.ttl:
                return cached[1]
            self._memory.pop(key, None)
            return None

    def claim(self, key: str) -> bool:
        if self._redis is not None:
            try:
                return bool(
                    self._redis.set(
                        f"sealquery:idem-lock:{key}",
                        "1",
                        nx=True,
                        ex=30,
                    )
                )
            except Exception:
                pass
        with self._lock:
            cached = self._memory.get(key)
            if cached and time.time() - cached[0] < self.ttl:
                return False
            self._memory[key] = (time.time(), {"_pending": True})
            return True

    def release(self, key: str) -> None:
        if self._redis is not None:
            try:
                self._redis.delete(f"sealquery:idem-lock:{key}")
            except Exception:
                pass
        with self._lock:
            cached = self._memory.get(key)
            if cached and cached[1].get("_pending"):
                self._memory.pop(key, None)

    def set(self, key: str, value: dict) -> None:
        if self._redis is not None:
            try:
                self._redis.setex(
                    f"sealquery:idem:{key}",
                    self.ttl,
                    json.dumps(value),
                )
                return
            except Exception:
                pass
        with self._lock:
            self._memory[key] = (time.time(), value)
