"""
In-memory cache for frequently accessed data to reduce SQLite I/O.
Uses a simple TTL-based eviction strategy.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional


class TTLCache:
    """Thread-safe TTL cache backed by a plain dict."""

    def __init__(self, ttl: float = 60.0, max_size: int = 10_000) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.monotonic() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if len(self._store) >= self._max_size:
            self._evict()
        self._store[key] = (value, time.monotonic() + (ttl or self._ttl))

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all keys starting with `prefix`."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]

    def _evict(self) -> None:
        """Remove expired entries; if still full, drop oldest half."""
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        if len(self._store) >= self._max_size:
            # Drop the oldest half by insertion order
            half = list(self._store.keys())[: self._max_size // 2]
            for k in half:
                del self._store[k]


class BotCache:
    """
    Domain-specific cache façade for the bot.

    Namespaces:
      - users       : per-user guild data  (TTL 30s)
      - guild       : guild settings       (TTL 120s)
      - cooldowns   : XP cooldown trackers (TTL = cooldown duration)
      - leaderboard : cached leaderboards  (TTL 60s)
    """

    def __init__(self) -> None:
        self.users = TTLCache(ttl=30)
        self.guild = TTLCache(ttl=120)
        self.cooldowns = TTLCache(ttl=300)
        self.leaderboard = TTLCache(ttl=60)

    # ------------------------------------------------------------------ #
    # User helpers                                                          #
    # ------------------------------------------------------------------ #

    def get_user(self, user_id: str, guild_id: str) -> Optional[dict]:
        return self.users.get(f"{guild_id}:{user_id}")

    def set_user(self, user_id: str, guild_id: str, data: dict) -> None:
        self.users.set(f"{guild_id}:{user_id}", data)

    def invalidate_user(self, user_id: str, guild_id: str) -> None:
        self.users.delete(f"{guild_id}:{user_id}")

    def invalidate_guild_users(self, guild_id: str) -> None:
        self.users.invalidate_prefix(f"{guild_id}:")

    # ------------------------------------------------------------------ #
    # XP cooldowns                                                          #
    # ------------------------------------------------------------------ #

    def is_on_cooldown(self, user_id: str, guild_id: str) -> bool:
        return self.cooldowns.get(f"xp:{guild_id}:{user_id}") is not None

    def set_cooldown(self, user_id: str, guild_id: str, seconds: int) -> None:
        self.cooldowns.set(f"xp:{guild_id}:{user_id}", True, ttl=float(seconds))

    # ------------------------------------------------------------------ #
    # Guild settings                                                        #
    # ------------------------------------------------------------------ #

    def get_guild(self, guild_id: str) -> Optional[dict]:
        return self.guild.get(guild_id)

    def set_guild(self, guild_id: str, data: dict) -> None:
        self.guild.set(guild_id, data)

    def invalidate_guild(self, guild_id: str) -> None:
        self.guild.delete(guild_id)

    # ------------------------------------------------------------------ #
    # Leaderboard                                                           #
    # ------------------------------------------------------------------ #

    def get_leaderboard(self, guild_id: str, lb_type: str) -> Optional[list]:
        return self.leaderboard.get(f"{guild_id}:{lb_type}")

    def set_leaderboard(self, guild_id: str, lb_type: str, data: list) -> None:
        self.leaderboard.set(f"{guild_id}:{lb_type}", data)

    def invalidate_leaderboard(self, guild_id: str) -> None:
        self.leaderboard.invalidate_prefix(f"{guild_id}:")
