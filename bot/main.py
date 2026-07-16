"""
Server Levels+ Discord Bot
--------------------------
Main entry point. Loads all cogs, configures intents, and starts the bot.
"""

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import BotConfig
from database.db import DatabaseManager
from utils.cache import BotCache

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Configure structured logging for the bot."""
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler for persistent logs
    os.makedirs("data/logs", exist_ok=True)
    file_handler = logging.FileHandler("data/logs/bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


# ---------------------------------------------------------------------------
# Bot class
# ---------------------------------------------------------------------------

class ServerLevelsBot(commands.Bot):
    """Main bot class with database and cache integration."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        intents.guilds = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

        self.config = BotConfig()
        self.db: DatabaseManager = None  # type: ignore  (set in setup_hook)
        self.cache: BotCache = BotCache()
        self.logger = logging.getLogger("bot")

    async def setup_hook(self) -> None:
        """Called once before login to perform async setup."""
        # Initialize database
        self.db = DatabaseManager(self.config.DATABASE_PATH)
        await self.db.initialize()
        self.logger.info("Database initialized at %s", self.config.DATABASE_PATH)

        # Load all cogs
        cogs = [
            "cogs.xp",
            "cogs.economy",
            "cogs.profile",
            "cogs.leaderboard",
            "cogs.admin",
            "cogs.rewards",
            "cogs.achievements",
            "cogs.prestige",
            "cogs.logging_cog",
            "cogs.api_server",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                self.logger.info("Loaded cog: %s", cog)
            except Exception as exc:
                self.logger.error("Failed to load cog %s: %s", cog, exc, exc_info=True)

        # Sync slash commands globally (or per guild in development)
        if self.config.GUILD_ID:
            guild = discord.Object(id=int(self.config.GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            self.logger.info("Slash commands synced to guild %s", self.config.GUILD_ID)
        else:
            await self.tree.sync()
            self.logger.info("Slash commands synced globally")

    async def on_ready(self) -> None:
        """Called when the bot is fully ready."""
        self.logger.info(
            "Server Levels+ is online! Logged in as %s (ID: %s)",
            self.user,
            self.user.id,
        )
        self.logger.info("Serving %d guilds", len(self.guilds))

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help",
            )
        )

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Initialize settings when the bot joins a new guild."""
        await self.db.init_guild(str(guild.id))
        self.logger.info("Joined new guild: %s (%s)", guild.name, guild.id)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Log when bot leaves a guild."""
        self.logger.info("Left guild: %s (%s)", guild.name, guild.id)

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Global error handler."""
        self.logger.error("Unhandled error in event %s", event, exc_info=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    setup_logging()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.critical("DISCORD_TOKEN is not set. Add it to your .env file.")
        sys.exit(1)

    bot = ServerLevelsBot()

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shut down by keyboard interrupt.")
