"""
Database Manager — aiosqlite-backed async database layer.
All SQL is parameterized to prevent injection.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger("bot.database")


class DatabaseManager:
    """Async SQLite database manager for Server Levels+."""

    def __init__(self, db_path: str = "data/bot.db") -> None:
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    # ------------------------------------------------------------------ #
    # Connection lifecycle                                                  #
    # ------------------------------------------------------------------ #

    async def initialize(self) -> None:
        """Open the database connection and create all tables."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")  # Better concurrent reads
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()
        await self._db.commit()
        logger.info("Database ready at %s", self.db_path)

    async def close(self) -> None:
        """Close the database connection gracefully."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    # ------------------------------------------------------------------ #
    # Schema creation                                                       #
    # ------------------------------------------------------------------ #

    async def _create_tables(self) -> None:
        """Create all tables if they don't already exist."""
        queries = [
            # Guild settings (one row per Discord server)
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id        TEXT PRIMARY KEY,
                xp_per_message  INTEGER NOT NULL DEFAULT 20,
                xp_cooldown     INTEGER NOT NULL DEFAULT 60,
                xp_multiplier   REAL    NOT NULL DEFAULT 1.0,
                max_level       INTEGER NOT NULL DEFAULT 100,
                daily_xp_cap    INTEGER NOT NULL DEFAULT 5000,
                announce_channel TEXT,
                announce_message TEXT NOT NULL DEFAULT '🎉 {user} leveled up to **Level {level}**!',
                stack_roles     INTEGER NOT NULL DEFAULT 0,
                ignored_channels TEXT NOT NULL DEFAULT '[]',
                ignored_roles   TEXT NOT NULL DEFAULT '[]',
                voice_xp_enabled INTEGER NOT NULL DEFAULT 1,
                coins_enabled   INTEGER NOT NULL DEFAULT 1,
                prestige_enabled INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,

            # Per-user, per-guild stats
            """
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id         TEXT NOT NULL,
                guild_id        TEXT NOT NULL,
                xp              INTEGER NOT NULL DEFAULT 0,
                level           INTEGER NOT NULL DEFAULT 0,
                total_xp        INTEGER NOT NULL DEFAULT 0,
                messages        INTEGER NOT NULL DEFAULT 0,
                voice_minutes   INTEGER NOT NULL DEFAULT 0,
                coins           INTEGER NOT NULL DEFAULT 0,
                prestige        INTEGER NOT NULL DEFAULT 0,
                daily_xp        INTEGER NOT NULL DEFAULT 0,
                last_xp_time    TEXT,
                last_daily      TEXT,
                last_weekly     TEXT,
                last_monthly    TEXT,
                login_streak    INTEGER NOT NULL DEFAULT 0,
                join_date       TEXT NOT NULL DEFAULT (datetime('now')),
                bio             TEXT,
                bg_image        TEXT,
                avatar_frame    TEXT,
                username_color  TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
            """,

            # Weekly XP tracking (reset each week)
            """
            CREATE TABLE IF NOT EXISTS weekly_xp (
                user_id     TEXT NOT NULL,
                guild_id    TEXT NOT NULL,
                week        TEXT NOT NULL,
                xp          INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, guild_id, week)
            )
            """,

            # Monthly XP tracking (reset each month)
            """
            CREATE TABLE IF NOT EXISTS monthly_xp (
                user_id     TEXT NOT NULL,
                guild_id    TEXT NOT NULL,
                month       TEXT NOT NULL,
                xp          INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, guild_id, month)
            )
            """,

            # Achievements unlocked by a user
            """
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id         TEXT NOT NULL,
                guild_id        TEXT NOT NULL,
                achievement_id  TEXT NOT NULL,
                unlocked_at     TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, guild_id, achievement_id)
            )
            """,

            # Inventory items (shop purchases)
            """
            CREATE TABLE IF NOT EXISTS user_inventory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                guild_id    TEXT NOT NULL,
                item_id     TEXT NOT NULL,
                equipped    INTEGER NOT NULL DEFAULT 0,
                purchased_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,

            # Transaction log (economy)
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                guild_id    TEXT NOT NULL,
                type        TEXT NOT NULL,
                amount      INTEGER NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,

            # Level → role mappings per guild
            """
            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id    TEXT NOT NULL,
                level       INTEGER NOT NULL,
                role_id     TEXT NOT NULL,
                PRIMARY KEY (guild_id, level)
            )
            """,

            # Activity log (level-ups, achievements, etc.)
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    TEXT NOT NULL,
                user_id     TEXT NOT NULL,
                username    TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                event_data  TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,

            # Dashboard OAuth sessions
            """
            CREATE TABLE IF NOT EXISTS dashboard_sessions (
                session_id  TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                username    TEXT NOT NULL,
                discriminator TEXT NOT NULL DEFAULT '0',
                avatar      TEXT,
                access_token TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,

            # Top.gg votes
            """
            CREATE TABLE IF NOT EXISTS votes (
                user_id     TEXT NOT NULL,
                voted_at    TEXT NOT NULL DEFAULT (datetime('now')),
                type        TEXT NOT NULL DEFAULT 'upvote',
                PRIMARY KEY (user_id, voted_at)
            )
            """,
        ]

        # Indexes for performance on large servers
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_levels_guild ON user_levels(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_levels_xp ON user_levels(guild_id, total_xp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_xp_week ON weekly_xp(guild_id, week)",
            "CREATE INDEX IF NOT EXISTS idx_monthly_xp_month ON monthly_xp(guild_id, month)",
            "CREATE INDEX IF NOT EXISTS idx_activity_log_guild ON activity_log(guild_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id, guild_id)",
        ]

        for query in queries:
            await self.db.execute(query)
        for index in indexes:
            await self.db.execute(index)

    # ------------------------------------------------------------------ #
    # Guild helpers                                                         #
    # ------------------------------------------------------------------ #

    async def init_guild(self, guild_id: str) -> None:
        """Insert default settings for a new guild."""
        await self.db.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (guild_id,),
        )
        await self.db.commit()

    async def get_guild_settings(self, guild_id: str) -> dict:
        """Return guild settings as a dict, initializing defaults if needed."""
        await self.init_guild(guild_id)
        async with self.db.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ) as cur:
            row = await cur.fetchone()
        result = dict(row)
        result["ignored_channels"] = json.loads(result["ignored_channels"])
        result["ignored_roles"] = json.loads(result["ignored_roles"])
        return result

    async def update_guild_settings(self, guild_id: str, **kwargs: Any) -> None:
        """Update one or more guild settings columns."""
        if not kwargs:
            return
        for key in ("ignored_channels", "ignored_roles"):
            if key in kwargs and isinstance(kwargs[key], list):
                kwargs[key] = json.dumps(kwargs[key])
        cols = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [guild_id]
        await self.db.execute(
            f"UPDATE guild_settings SET {cols}, updated_at = datetime('now') WHERE guild_id = ?",
            vals,
        )
        await self.db.commit()

    # ------------------------------------------------------------------ #
    # User helpers                                                          #
    # ------------------------------------------------------------------ #

    async def get_user(self, user_id: str, guild_id: str) -> dict:
        """Return user stats, inserting a new row if this is their first message."""
        await self.db.execute(
            "INSERT OR IGNORE INTO user_levels (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id),
        )
        await self.db.commit()
        async with self.db.execute(
            "SELECT * FROM user_levels WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ) as cur:
            row = await cur.fetchone()
        return dict(row)

    async def update_user(self, user_id: str, guild_id: str, **kwargs: Any) -> None:
        """Update one or more columns for a user."""
        if not kwargs:
            return
        cols = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [user_id, guild_id]
        await self.db.execute(
            f"UPDATE user_levels SET {cols} WHERE user_id = ? AND guild_id = ?",
            vals,
        )
        await self.db.commit()

    async def add_xp(
        self, user_id: str, guild_id: str, amount: int, week: str, month: str
    ) -> dict:
        """
        Atomically add XP to a user and update weekly/monthly trackers.
        Returns the updated user row.
        """
        user = await self.get_user(user_id, guild_id)
        new_xp = user["xp"] + amount
        new_total = user["total_xp"] + amount
        new_daily = user["daily_xp"] + amount

        await self.db.execute(
            """UPDATE user_levels
               SET xp = ?, total_xp = ?, daily_xp = ?, messages = messages + 1,
                   last_xp_time = datetime('now')
               WHERE user_id = ? AND guild_id = ?""",
            (new_xp, new_total, new_daily, user_id, guild_id),
        )
        # Weekly XP
        await self.db.execute(
            """INSERT INTO weekly_xp (user_id, guild_id, week, xp) VALUES (?, ?, ?, ?)
               ON CONFLICT (user_id, guild_id, week) DO UPDATE SET xp = xp + ?""",
            (user_id, guild_id, week, amount, amount),
        )
        # Monthly XP
        await self.db.execute(
            """INSERT INTO monthly_xp (user_id, guild_id, month, xp) VALUES (?, ?, ?, ?)
               ON CONFLICT (user_id, guild_id, month) DO UPDATE SET xp = xp + ?""",
            (user_id, guild_id, month, amount, amount),
        )
        await self.db.commit()

        return await self.get_user(user_id, guild_id)

    async def set_level(self, user_id: str, guild_id: str, level: int, xp: int = 0) -> None:
        """Directly set a user's level and XP."""
        await self.update_user(user_id, guild_id, level=level, xp=xp)

    # ------------------------------------------------------------------ #
    # Leaderboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_leaderboard(
        self,
        guild_id: str,
        lb_type: str = "xp",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch leaderboard rows for a given type."""
        order_map = {
            "xp": "total_xp DESC, level DESC",
            "messages": "messages DESC",
            "voice": "voice_minutes DESC",
            "coins": "coins DESC",
        }
        if lb_type in order_map:
            order = order_map[lb_type]
            async with self.db.execute(
                f"""SELECT *, ROW_NUMBER() OVER (ORDER BY {order}) AS rank
                    FROM user_levels WHERE guild_id = ?
                    ORDER BY {order} LIMIT ? OFFSET ?""",
                (guild_id, limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        elif lb_type == "weekly":
            week = _current_week()
            async with self.db.execute(
                """SELECT ul.*, wx.xp AS week_xp,
                          ROW_NUMBER() OVER (ORDER BY wx.xp DESC) AS rank
                   FROM weekly_xp wx
                   JOIN user_levels ul USING (user_id, guild_id)
                   WHERE wx.guild_id = ? AND wx.week = ?
                   ORDER BY wx.xp DESC LIMIT ? OFFSET ?""",
                (guild_id, week, limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        elif lb_type == "monthly":
            month = _current_month()
            async with self.db.execute(
                """SELECT ul.*, mx.xp AS month_xp,
                          ROW_NUMBER() OVER (ORDER BY mx.xp DESC) AS rank
                   FROM monthly_xp mx
                   JOIN user_levels ul USING (user_id, guild_id)
                   WHERE mx.guild_id = ? AND mx.month = ?
                   ORDER BY mx.xp DESC LIMIT ? OFFSET ?""",
                (guild_id, month, limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        else:
            return []

        return [dict(r) for r in rows]

    async def get_user_rank(self, user_id: str, guild_id: str) -> int:
        """Return a user's XP rank in a guild (1-indexed)."""
        async with self.db.execute(
            """SELECT COUNT(*) FROM user_levels
               WHERE guild_id = ? AND total_xp > (
                   SELECT total_xp FROM user_levels WHERE user_id = ? AND guild_id = ?
               )""",
            (guild_id, user_id, guild_id),
        ) as cur:
            row = await cur.fetchone()
        return (row[0] or 0) + 1

    async def get_total_users(self, guild_id: str) -> int:
        """Count total tracked users in a guild."""
        async with self.db.execute(
            "SELECT COUNT(*) FROM user_levels WHERE guild_id = ?", (guild_id,)
        ) as cur:
            row = await cur.fetchone()
        return row[0] or 0

    # ------------------------------------------------------------------ #
    # Achievements                                                          #
    # ------------------------------------------------------------------ #

    async def get_user_achievements(self, user_id: str, guild_id: str) -> list[str]:
        """Return list of achievement IDs the user has unlocked."""
        async with self.db.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ) as cur:
            rows = await cur.fetchall()
        return [r["achievement_id"] for r in rows]

    async def unlock_achievement(
        self, user_id: str, guild_id: str, achievement_id: str
    ) -> bool:
        """Unlock an achievement. Returns True if it was newly unlocked."""
        try:
            await self.db.execute(
                """INSERT OR IGNORE INTO user_achievements (user_id, guild_id, achievement_id)
                   VALUES (?, ?, ?)""",
                (user_id, guild_id, achievement_id),
            )
            await self.db.commit()
            return self.db.total_changes > 0
        except Exception as exc:
            logger.error("Failed to unlock achievement: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # Level roles                                                           #
    # ------------------------------------------------------------------ #

    async def get_level_roles(self, guild_id: str) -> list[dict]:
        """Return all level-role mappings for a guild."""
        async with self.db.execute(
            "SELECT * FROM level_roles WHERE guild_id = ? ORDER BY level",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def set_level_role(self, guild_id: str, level: int, role_id: str) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO level_roles (guild_id, level, role_id) VALUES (?, ?, ?)",
            (guild_id, level, role_id),
        )
        await self.db.commit()

    async def delete_level_role(self, guild_id: str, level: int) -> None:
        await self.db.execute(
            "DELETE FROM level_roles WHERE guild_id = ? AND level = ?",
            (guild_id, level),
        )
        await self.db.commit()

    # ------------------------------------------------------------------ #
    # Economy                                                               #
    # ------------------------------------------------------------------ #

    async def add_coins(
        self,
        user_id: str,
        guild_id: str,
        amount: int,
        description: str = "",
    ) -> int:
        """Add coins and log the transaction. Returns new balance."""
        user = await self.get_user(user_id, guild_id)
        new_balance = max(0, user["coins"] + amount)
        await self.update_user(user_id, guild_id, coins=new_balance)
        await self.db.execute(
            "INSERT INTO transactions (user_id, guild_id, type, amount, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, guild_id, "credit" if amount > 0 else "debit", abs(amount), description),
        )
        await self.db.commit()
        return new_balance

    async def purchase_item(
        self, user_id: str, guild_id: str, item_id: str, cost: int
    ) -> bool:
        """Deduct coins and record an inventory item. Returns False if insufficient funds."""
        user = await self.get_user(user_id, guild_id)
        if user["coins"] < cost:
            return False
        await self.add_coins(user_id, guild_id, -cost, f"Purchased {item_id}")
        await self.db.execute(
            "INSERT INTO user_inventory (user_id, guild_id, item_id) VALUES (?, ?, ?)",
            (user_id, guild_id, item_id),
        )
        await self.db.commit()
        return True

    async def get_inventory(self, user_id: str, guild_id: str) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM user_inventory WHERE user_id = ? AND guild_id = ? ORDER BY purchased_at DESC",
            (user_id, guild_id),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Activity log                                                          #
    # ------------------------------------------------------------------ #

    async def log_activity(
        self,
        guild_id: str,
        user_id: str,
        username: str,
        event_type: str,
        event_data: dict | None = None,
    ) -> None:
        await self.db.execute(
            """INSERT INTO activity_log (guild_id, user_id, username, event_type, event_data)
               VALUES (?, ?, ?, ?, ?)""",
            (guild_id, user_id, username, event_type, json.dumps(event_data or {})),
        )
        await self.db.commit()

    async def get_activity(self, guild_id: str, limit: int = 20) -> list[dict]:
        async with self.db.execute(
            """SELECT * FROM activity_log WHERE guild_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (guild_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["event_data"] = json.loads(d["event_data"])
            result.append(d)
        return result

    # ------------------------------------------------------------------ #
    # Dashboard sessions                                                    #
    # ------------------------------------------------------------------ #

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        username: str,
        discriminator: str,
        avatar: str | None,
        access_token: str,
        expires_at: str,
    ) -> None:
        await self.db.execute(
            """INSERT OR REPLACE INTO dashboard_sessions
               (session_id, user_id, username, discriminator, avatar, access_token, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, username, discriminator, avatar, access_token, expires_at),
        )
        await self.db.commit()

    async def get_session(self, session_id: str) -> dict | None:
        async with self.db.execute(
            "SELECT * FROM dashboard_sessions WHERE session_id = ? AND expires_at > datetime('now')",
            (session_id,),
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_session(self, session_id: str) -> None:
        await self.db.execute(
            "DELETE FROM dashboard_sessions WHERE session_id = ?", (session_id,)
        )
        await self.db.commit()

    # ------------------------------------------------------------------ #
    # Reset                                                                 #
    # ------------------------------------------------------------------ #

    async def reset_user(self, user_id: str, guild_id: str) -> None:
        """Fully reset a user's stats in a guild."""
        await self.db.execute(
            "DELETE FROM user_levels WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await self.db.execute(
            "DELETE FROM user_achievements WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await self.db.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await self.db.execute(
            "DELETE FROM weekly_xp WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await self.db.execute(
            "DELETE FROM monthly_xp WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await self.db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_week() -> str:
    """Return the ISO week string, e.g. '2024-W03'."""
    from datetime import date
    d = date.today()
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


def _current_month() -> str:
    from datetime import date
    d = date.today()
    return f"{d.year}-{d.month:02d}"
