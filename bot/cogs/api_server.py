"""
API Server Cog — runs an embedded FastAPI server for the dashboard.
Exposes read/write endpoints secured by the API_SECRET header.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import discord
import uvicorn
from discord.ext import commands, tasks
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.xp_math import calculate_level, xp_to_next_level

logger = logging.getLogger("bot.api_server")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class XpModifyRequest(BaseModel):
    amount: int
    action: str  # add | remove | set


class SettingsUpdateRequest(BaseModel):
    xp_per_message: int | None = None
    xp_cooldown: int | None = None
    xp_multiplier: float | None = None
    max_level: int | None = None
    daily_xp_cap: int | None = None
    announce_channel: str | None = None
    announce_message: str | None = None
    stack_roles: bool | None = None
    ignored_channels: list[str] | None = None
    ignored_roles: list[str] | None = None
    voice_xp_enabled: bool | None = None
    coins_enabled: bool | None = None
    prestige_enabled: bool | None = None


class LevelRoleRequest(BaseModel):
    level: int
    role_id: str


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class APIServerCog(commands.Cog, name="API Server"):
    """Embedded FastAPI server for the web dashboard."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api_secret = bot.config.API_SECRET
        self.port = bot.config.DASHBOARD_API_PORT
        self._server: uvicorn.Server | None = None
        self.app = self._build_app()

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="Server Levels+ Bot API", version="1.0.0")

        dashboard_url = self.bot.config.DASHBOARD_URL
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[dashboard_url, "http://localhost:3000", "http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        bot_ref = self.bot

        # ── Auth dependency ────────────────────────────────────────────

        async def require_auth(x_api_secret: str = Header(default="")):
            if x_api_secret != bot_ref.config.API_SECRET:
                raise HTTPException(status_code=401, detail="Unauthorized")

        # ── Health ────────────────────────────────────────────────────

        @app.get("/health")
        async def health():
            return {"status": "online", "guilds": len(bot_ref.guilds)}

        # ── Bot stats ─────────────────────────────────────────────────

        @app.get("/stats")
        async def bot_stats(auth=Depends(require_auth)):
            return {
                "guilds": len(bot_ref.guilds),
                "users": sum(g.member_count or 0 for g in bot_ref.guilds),
                "latency": round(bot_ref.latency * 1000, 1),
            }

        # ── Guild list ────────────────────────────────────────────────

        @app.get("/guilds")
        async def list_guilds(user_id: str, auth=Depends(require_auth)):
            """Return guilds where both the user and bot are present."""
            guilds = []
            for guild in bot_ref.guilds:
                member = guild.get_member(int(user_id))
                if member is None:
                    continue
                is_admin = member.guild_permissions.manage_guild
                guilds.append({
                    "id": str(guild.id),
                    "name": guild.name,
                    "icon": str(guild.icon) if guild.icon else None,
                    "iconUrl": str(guild.icon.url) if guild.icon else None,
                    "memberCount": guild.member_count or 0,
                    "botPresent": True,
                    "isAdmin": is_admin,
                })
            return guilds

        # ── Guild details ─────────────────────────────────────────────

        @app.get("/guilds/{guild_id}")
        async def get_guild(guild_id: str, auth=Depends(require_auth)):
            guild = bot_ref.get_guild(int(guild_id))
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            return {
                "id": str(guild.id),
                "name": guild.name,
                "icon": str(guild.icon) if guild.icon else None,
                "iconUrl": str(guild.icon.url) if guild.icon else None,
                "memberCount": guild.member_count or 0,
                "botPresent": True,
                "isAdmin": False,
            }

        # ── Guild stats ───────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/stats")
        async def guild_stats(guild_id: str, auth=Depends(require_auth)):
            guild = bot_ref.get_guild(int(guild_id))
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            total = await bot_ref.db.get_total_users(guild_id)
            lb = await bot_ref.db.get_leaderboard(guild_id, "xp", limit=1)
            top_level = lb[0]["level"] if lb else 0
            return {
                "totalMembers": total,
                "activeToday": 0,       # Extend with real tracking
                "messagesThisWeek": 0,
                "voiceMinutesThisWeek": 0,
                "totalXpAwarded": sum(e.get("total_xp", 0) for e in lb),
                "levelUpsThisWeek": 0,
                "topLevel": top_level,
                "avgLevel": top_level / 2 if top_level else 0,
            }

        # ── Settings ──────────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/settings")
        async def get_settings(guild_id: str, auth=Depends(require_auth)):
            settings = await bot_ref.db.get_guild_settings(guild_id)
            settings["guildId"] = settings.pop("guild_id")
            settings["xpPerMessage"] = settings.pop("xp_per_message")
            settings["xpCooldown"] = settings.pop("xp_cooldown")
            settings["xpMultiplier"] = settings.pop("xp_multiplier")
            settings["maxLevel"] = settings.pop("max_level")
            settings["dailyXpCap"] = settings.pop("daily_xp_cap")
            settings["announceChannel"] = settings.pop("announce_channel")
            settings["announceMessage"] = settings.pop("announce_message")
            settings["stackRoles"] = bool(settings.pop("stack_roles"))
            settings["ignoredChannels"] = settings.pop("ignored_channels")
            settings["ignoredRoles"] = settings.pop("ignored_roles")
            settings["voiceXpEnabled"] = bool(settings.pop("voice_xp_enabled"))
            settings["coinsEnabled"] = bool(settings.pop("coins_enabled"))
            settings["prestigeEnabled"] = bool(settings.pop("prestige_enabled"))
            return settings

        @app.put("/guilds/{guild_id}/settings")
        async def update_settings(
            guild_id: str, body: SettingsUpdateRequest, auth=Depends(require_auth)
        ):
            updates = {k: v for k, v in body.dict().items() if v is not None}
            # Map camelCase to snake_case
            mapping = {
                "xp_per_message": "xp_per_message",
                "xp_cooldown": "xp_cooldown",
                "xp_multiplier": "xp_multiplier",
                "max_level": "max_level",
                "daily_xp_cap": "daily_xp_cap",
                "announce_channel": "announce_channel",
                "announce_message": "announce_message",
                "stack_roles": "stack_roles",
                "ignored_channels": "ignored_channels",
                "ignored_roles": "ignored_roles",
                "voice_xp_enabled": "voice_xp_enabled",
                "coins_enabled": "coins_enabled",
                "prestige_enabled": "prestige_enabled",
            }
            db_updates = {mapping[k]: v for k, v in updates.items() if k in mapping}
            if db_updates:
                await bot_ref.db.update_guild_settings(guild_id, **db_updates)
                bot_ref.cache.invalidate_guild(guild_id)
            return await get_settings(guild_id, auth)

        # ── Leaderboard ───────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/leaderboard")
        async def leaderboard(
            guild_id: str,
            type: str = "xp",
            page: int = 1,
            limit: int = 20,
            auth=Depends(require_auth),
        ):
            guild = bot_ref.get_guild(int(guild_id))
            offset = (page - 1) * limit
            entries = await bot_ref.db.get_leaderboard(guild_id, type, limit=limit, offset=offset)
            total = await bot_ref.db.get_total_users(guild_id)
            total_pages = max(1, (total + limit - 1) // limit)

            result = []
            for i, e in enumerate(entries):
                member = guild.get_member(int(e["user_id"])) if guild else None
                level, curr_xp, xp_needed = calculate_level(e.get("total_xp", 0))
                result.append({
                    "rank": e.get("rank", offset + i + 1),
                    "userId": e["user_id"],
                    "username": member.display_name if member else f"User {e['user_id']}",
                    "discriminator": getattr(member, "discriminator", "0") if member else "0",
                    "avatarUrl": str(member.display_avatar.url) if member else None,
                    "level": level,
                    "xp": curr_xp,
                    "totalXp": e.get("total_xp", 0),
                    "messages": e.get("messages", 0),
                    "voiceMinutes": e.get("voice_minutes", 0),
                    "coins": e.get("coins", 0),
                    "prestige": e.get("prestige", 0),
                })
            return {"entries": result, "total": total, "page": page, "totalPages": total_pages}

        # ── Members ───────────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/members/{user_id}")
        async def get_member(guild_id: str, user_id: str, auth=Depends(require_auth)):
            guild = bot_ref.get_guild(int(guild_id))
            user = await bot_ref.db.get_user(user_id, guild_id)
            rank = await bot_ref.db.get_user_rank(user_id, guild_id)
            achievements = await bot_ref.db.get_user_achievements(user_id, guild_id)
            level, curr_xp, xp_needed = calculate_level(user["total_xp"])
            member = guild.get_member(int(user_id)) if guild else None

            from data.achievements_data import ACHIEVEMENTS
            ach_list = [
                {
                    "id": a,
                    "name": ACHIEVEMENTS.get(a, {}).get("name", a),
                    "description": ACHIEVEMENTS.get(a, {}).get("description", ""),
                    "icon": ACHIEVEMENTS.get(a, {}).get("icon", "🏆"),
                    "unlockedAt": None,
                }
                for a in achievements
            ]

            return {
                "userId": user_id,
                "guildId": guild_id,
                "username": member.display_name if member else f"User {user_id}",
                "discriminator": getattr(member, "discriminator", "0") if member else "0",
                "avatarUrl": str(member.display_avatar.url) if member else None,
                "level": level,
                "xp": curr_xp,
                "totalXp": user["total_xp"],
                "xpNeeded": xp_needed,
                "rank": rank,
                "messages": user["messages"],
                "voiceMinutes": user["voice_minutes"],
                "coins": user["coins"],
                "prestige": user["prestige"],
                "joinedAt": user["join_date"],
                "bio": user["bio"],
                "achievements": ach_list,
                "badges": [ACHIEVEMENTS.get(a, {}).get("icon", "🏆") for a in achievements[:10]],
            }

        @app.post("/guilds/{guild_id}/members/{user_id}/xp")
        async def modify_xp(
            guild_id: str, user_id: str, body: XpModifyRequest, auth=Depends(require_auth)
        ):
            from datetime import date
            today = date.today()
            week = f"{today.year}-W{today.isocalendar()[1]:02d}"
            month = f"{today.year}-{today.month:02d}"

            if body.action == "add":
                await bot_ref.db.add_xp(user_id, guild_id, body.amount, week, month)
            elif body.action == "remove":
                user = await bot_ref.db.get_user(user_id, guild_id)
                new_total = max(0, user["total_xp"] - body.amount)
                level, _, _ = calculate_level(new_total)
                await bot_ref.db.update_user(user_id, guild_id, total_xp=new_total, level=level)
            elif body.action == "set":
                level, _, _ = calculate_level(body.amount)
                await bot_ref.db.update_user(user_id, guild_id, total_xp=body.amount, level=level)

            bot_ref.cache.invalidate_user(user_id, guild_id)
            return {"success": True, "message": "XP modified"}

        @app.post("/guilds/{guild_id}/members/{user_id}/reset")
        async def reset_member(guild_id: str, user_id: str, auth=Depends(require_auth)):
            await bot_ref.db.reset_user(user_id, guild_id)
            bot_ref.cache.invalidate_user(user_id, guild_id)
            return {"success": True, "message": "User reset"}

        # ── Level roles ───────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/level-roles")
        async def get_level_roles(guild_id: str, auth=Depends(require_auth)):
            guild = bot_ref.get_guild(int(guild_id))
            roles = await bot_ref.db.get_level_roles(guild_id)
            result = []
            for lr in roles:
                role = guild.get_role(int(lr["role_id"])) if guild else None
                result.append({
                    "guildId": guild_id,
                    "level": lr["level"],
                    "roleId": lr["role_id"],
                    "roleName": role.name if role else lr["role_id"],
                })
            return result

        @app.post("/guilds/{guild_id}/level-roles")
        async def create_level_role(
            guild_id: str, body: LevelRoleRequest, auth=Depends(require_auth)
        ):
            await bot_ref.db.set_level_role(guild_id, body.level, body.role_id)
            guild = bot_ref.get_guild(int(guild_id))
            role = guild.get_role(int(body.role_id)) if guild else None
            return {
                "guildId": guild_id,
                "level": body.level,
                "roleId": body.role_id,
                "roleName": role.name if role else body.role_id,
            }

        @app.delete("/guilds/{guild_id}/level-roles/{level}")
        async def delete_level_role(guild_id: str, level: int, auth=Depends(require_auth)):
            await bot_ref.db.delete_level_role(guild_id, level)
            return {"success": True, "message": "Level role deleted"}

        # ── Activity ──────────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/activity")
        async def get_activity(guild_id: str, limit: int = 20, auth=Depends(require_auth)):
            events = await bot_ref.db.get_activity(guild_id, limit=limit)
            result = []
            guild = bot_ref.get_guild(int(guild_id))
            for ev in events:
                member = guild.get_member(int(ev["user_id"])) if guild else None
                data = ev["event_data"]
                result.append({
                    "id": str(ev["id"]),
                    "type": ev["event_type"],
                    "userId": ev["user_id"],
                    "username": member.display_name if member else ev["username"],
                    "avatarUrl": str(member.display_avatar.url) if member else None,
                    "level": data.get("level"),
                    "achievement": data.get("name"),
                    "timestamp": ev["created_at"],
                })
            return result

        # ── Shop ─────────────────────────────────────────────────────

        @app.get("/guilds/{guild_id}/shop")
        async def get_shop(guild_id: str, auth=Depends(require_auth)):
            from pathlib import Path
            items_raw = {}
            p = Path("data/shop_items.json")
            if p.exists():
                items_raw = json.loads(p.read_text())
            return [
                {
                    "id": item_id,
                    "name": item["name"],
                    "description": item["description"],
                    "category": item["category"],
                    "price": item["price"],
                    "icon": item.get("icon", "🎁"),
                }
                for item_id, item in items_raw.items()
            ]

        return app

    # ------------------------------------------------------------------ #
    # Lifecycle                                                             #
    # ------------------------------------------------------------------ #

    async def cog_load(self) -> None:
        """Start the uvicorn server when the cog loads."""
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        import asyncio
        asyncio.create_task(self._server.serve())
        logger.info("Bot API server started on port %d", self.port)

    async def cog_unload(self) -> None:
        if self._server:
            self._server.should_exit = True


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(APIServerCog(bot))
