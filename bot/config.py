"""
Bot configuration — all values can be overridden via environment variables or .env.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BotConfig:
    """Central configuration for Server Levels+."""

    # ------------------------------------------------------------------ #
    # Discord                                                              #
    # ------------------------------------------------------------------ #
    DISCORD_TOKEN: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    APPLICATION_ID: str = field(default_factory=lambda: os.getenv("APPLICATION_ID", ""))
    # Set GUILD_ID to a specific guild for faster slash-command sync in dev.
    # Leave empty to sync globally (takes up to an hour).
    GUILD_ID: Optional[str] = field(default_factory=lambda: os.getenv("GUILD_ID"))

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    # SQLite is the default. Set DATABASE_URL to a PostgreSQL URI to use PG.
    DATABASE_PATH: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/bot.db"))
    DATABASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("DATABASE_URL"))

    # ------------------------------------------------------------------ #
    # XP System                                                            #
    # ------------------------------------------------------------------ #
    XP_PER_MESSAGE_MIN: int = field(default_factory=lambda: int(os.getenv("XP_PER_MESSAGE_MIN", "15")))
    XP_PER_MESSAGE_MAX: int = field(default_factory=lambda: int(os.getenv("XP_PER_MESSAGE_MAX", "25")))
    XP_COOLDOWN_SECONDS: int = field(default_factory=lambda: int(os.getenv("XP_COOLDOWN_SECONDS", "60")))
    XP_PER_VOICE_MINUTE: int = field(default_factory=lambda: int(os.getenv("XP_PER_VOICE_MINUTE", "10")))
    DAILY_XP_CAP: int = field(default_factory=lambda: int(os.getenv("DAILY_XP_CAP", "5000")))
    MAX_LEVEL: int = field(default_factory=lambda: int(os.getenv("MAX_LEVEL", "100")))
    BASE_XP: int = field(default_factory=lambda: int(os.getenv("BASE_XP", "100")))

    # ------------------------------------------------------------------ #
    # Economy                                                              #
    # ------------------------------------------------------------------ #
    COINS_PER_MESSAGE: int = field(default_factory=lambda: int(os.getenv("COINS_PER_MESSAGE", "5")))
    COINS_PER_LEVEL_UP: int = field(default_factory=lambda: int(os.getenv("COINS_PER_LEVEL_UP", "100")))
    DAILY_COINS_MIN: int = field(default_factory=lambda: int(os.getenv("DAILY_COINS_MIN", "100")))
    DAILY_COINS_MAX: int = field(default_factory=lambda: int(os.getenv("DAILY_COINS_MAX", "500")))
    WEEKLY_COINS: int = field(default_factory=lambda: int(os.getenv("WEEKLY_COINS", "2500")))
    MONTHLY_COINS: int = field(default_factory=lambda: int(os.getenv("MONTHLY_COINS", "10000")))

    # ------------------------------------------------------------------ #
    # Colors (hex)                                                         #
    # ------------------------------------------------------------------ #
    COLOR_PRIMARY: int = 0x5865F2      # Discord Blurple
    COLOR_SUCCESS: int = 0x57F287      # Green
    COLOR_WARNING: int = 0xFEE75C      # Yellow
    COLOR_ERROR: int = 0xED4245        # Red
    COLOR_INFO: int = 0x5865F2         # Info blue
    COLOR_XP: int = 0x9B59B6           # Purple
    COLOR_COINS: int = 0xF1C40F        # Gold

    # ------------------------------------------------------------------ #
    # Dashboard API                                                        #
    # ------------------------------------------------------------------ #
    DASHBOARD_API_PORT: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_API_PORT", "8000")))
    DASHBOARD_URL: str = field(default_factory=lambda: os.getenv("DASHBOARD_URL", "http://localhost:3000"))
    API_SECRET: str = field(default_factory=lambda: os.getenv("API_SECRET", "change-me-in-production"))

    # ------------------------------------------------------------------ #
    # Prestige                                                             #
    # ------------------------------------------------------------------ #
    PRESTIGE_LEVEL_REQUIRED: int = 100  # Must reach this level to prestige
    MAX_PRESTIGE: int = 10

    # ------------------------------------------------------------------ #
    # Rank card                                                            #
    # ------------------------------------------------------------------ #
    RANK_CARD_WIDTH: int = 900
    RANK_CARD_HEIGHT: int = 280
    FONT_PATH: str = field(default_factory=lambda: os.getenv("FONT_PATH", "fonts/Montserrat-Bold.ttf"))
    FONT_REGULAR_PATH: str = field(
        default_factory=lambda: os.getenv("FONT_REGULAR_PATH", "fonts/Montserrat-Regular.ttf")
    )

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_CHANNEL_ID: Optional[str] = field(default_factory=lambda: os.getenv("LOG_CHANNEL_ID"))

    # ------------------------------------------------------------------ #
    # Top.gg                                                               #
    # ------------------------------------------------------------------ #
    TOPGG_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("TOPGG_TOKEN"))
    TOPGG_WEBHOOK_AUTH: str = field(default_factory=lambda: os.getenv("TOPGG_WEBHOOK_AUTH", ""))
    TOPGG_WEBHOOK_PORT: int = field(default_factory=lambda: int(os.getenv("TOPGG_WEBHOOK_PORT", "8001")))
