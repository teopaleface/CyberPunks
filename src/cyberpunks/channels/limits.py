"""Limite locale explicite, partajate de text și de uneltele vocale."""

import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from cyberpunks.channels.models import ChannelError


class Limits:
    def __init__(self, per_minute=12, concurrency=2, max_actors=1000):
        self.per_minute, self.concurrency, self.max_actors = per_minute, concurrency, max_actors
        self.calls = defaultdict(deque)
        self.active = set()
        self.lock = threading.Lock()

    @asynccontextmanager
    async def acquire(self, actor_key: tuple, *, voice=False):
        now = time.monotonic()
        key = (*actor_key, "voice" if voice else "turn")
        with self.lock:
            for expired in [k for k, v in self.calls.items() if not v or v[-1] < now - 60]:
                del self.calls[expired]
            if key not in self.calls and len(self.calls) >= self.max_actors:
                raise ChannelError("rate_limit", "The conversation service is busy. Try again later.", 429)
            q = self.calls[key]
            while q and q[0] < now - 60:
                q.popleft()
            limit = 3 if voice else self.per_minute
            if len(q) >= limit or key in self.active or len(self.active) >= self.concurrency:
                raise ChannelError("rate_limit", "Too many conversation requests. Wait before trying again.", 429)
            q.append(now)
            self.active.add(key)
        try:
            yield
        finally:
            with self.lock:
                self.active.discard(key)


limits = Limits()
