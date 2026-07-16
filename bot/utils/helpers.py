"""General-purpose helper utilities."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

import discord


def format_number(n: int | float) -> str:
    """Format large numbers with k/M suffixes: 1500 → '1.5k'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(int(n))


def format_time(seconds: int) -> str:
    """Format seconds into a human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h {m}m"


def format_voice_time(minutes: int) -> str:
    """Format voice minutes into hours and minutes."""
    if minutes < 60:
        return f"{minutes}m"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m"


def time_until(target: datetime) -> str:
    """Return a human-readable countdown to a future datetime."""
    now = datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    diff = int((target - now).total_seconds())
    if diff <= 0:
        return "now"
    return format_time(diff)


def get_avatar_url(member: discord.Member | discord.User) -> str:
    """Return the member's avatar URL, falling back to the default Discord avatar."""
    if member.avatar:
        return member.avatar.url
    return member.default_avatar.url


def prestige_color(prestige: int) -> int:
    """Return a color int based on prestige tier."""
    colors = [
        0x7F8C8D,  # 0 — grey
        0xC0392B,  # 1 — red
        0xF39C12,  # 2 — orange
        0xF1C40F,  # 3 — yellow
        0x2ECC71,  # 4 — green
        0x1ABC9C,  # 5 — teal
        0x3498DB,  # 6 — blue
        0x9B59B6,  # 7 — purple
        0xE91E63,  # 8 — pink
        0xFF6B6B,  # 9 — coral
        0xFFD700,  # 10 — gold
    ]
    return colors[min(prestige, len(colors) - 1)]


def prestige_badge(prestige: int) -> str:
    """Return an emoji badge for the given prestige level."""
    badges = ["", "🥉", "🥈", "🥇", "💎", "🔥", "⚡", "🌟", "👑", "🦋", "🌈"]
    return badges[min(prestige, len(badges) - 1)]


def truncate(text: str, max_len: int = 100) -> str:
    """Truncate text to max_len characters, adding '…' if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def is_valid_color(value: str) -> bool:
    """Check if a string is a valid hex color (#RRGGBB or #RGB)."""
    return bool(re.match(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$", value))


def parse_color(value: str) -> Optional[int]:
    """Parse a hex color string to an int."""
    if not is_valid_color(value):
        return None
    return int(value.lstrip("#"), 16)


def discord_timestamp(dt: datetime, style: str = "R") -> str:
    """Return a Discord timestamp markdown string."""
    ts = int(dt.replace(tzinfo=timezone.utc).timestamp() if dt.tzinfo is None else dt.timestamp())
    return f"<t:{ts}:{style}>"
