"""
XP Cog — handles message XP, voice XP, level-ups, and rank cards.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import date

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.xp_math import calculate_level, xp_to_next_level, xp_multiplier_bonus
from utils.rank_card import generate_rank_card
from utils.helpers import get_avatar_url, format_number, prestige_color

logger = logging.getLogger("bot.xp")


class XPCog(commands.Cog, name="XP"):
    """Core XP tracking and leveling system."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Track users currently in voice channels: {guild_id: {user_id: channel_id}}
        self._voice_members: dict[int, set[int]] = {}
        self.voice_xp_task.start()

    def cog_unload(self) -> None:
        self.voice_xp_task.cancel()

    # ------------------------------------------------------------------ #
    # Message XP                                                            #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Award XP for chat messages with cooldown and anti-spam protection."""
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        # Check cache first to avoid DB call for settings
        settings = self.bot.cache.get_guild(guild_id)
        if settings is None:
            settings = await self.bot.db.get_guild_settings(guild_id)
            self.bot.cache.set_guild(guild_id, settings)

        # Respect ignored channels / roles
        if str(message.channel.id) in settings["ignored_channels"]:
            return
        member_role_ids = [str(r.id) for r in message.author.roles]
        if any(r in settings["ignored_roles"] for r in member_role_ids):
            return

        # Cooldown check
        if self.bot.cache.is_on_cooldown(user_id, guild_id):
            return

        # Spam filter: minimum message length
        if len(message.content.strip()) < 3:
            return

        # Calculate XP amount with server multiplier + prestige bonus
        user = await self.bot.db.get_user(user_id, guild_id)
        daily_cap = settings["daily_xp_cap"]
        if user["daily_xp"] >= daily_cap:
            return

        base_xp = random.randint(
            self.bot.config.XP_PER_MESSAGE_MIN,
            self.bot.config.XP_PER_MESSAGE_MAX,
        )
        multiplier = settings["xp_multiplier"] * xp_multiplier_bonus(user["prestige"])
        xp_gain = max(1, int(base_xp * multiplier))

        # Respect daily cap
        remaining = daily_cap - user["daily_xp"]
        xp_gain = min(xp_gain, remaining)

        # Set cooldown before DB write to prevent race conditions
        self.bot.cache.set_cooldown(user_id, guild_id, settings["xp_cooldown"])

        # Compute week/month keys for period trackers
        today = date.today()
        week = f"{today.year}-W{today.isocalendar()[1]:02d}"
        month = f"{today.year}-{today.month:02d}"

        old_level = user["level"]
        updated = await self.bot.db.add_xp(user_id, guild_id, xp_gain, week, month)

        # Recalculate level from total XP
        new_level, _, _ = calculate_level(updated["total_xp"])

        if new_level > old_level:
            await self.bot.db.update_user(user_id, guild_id, level=new_level)
            await self._handle_level_up(message, user_id, guild_id, new_level, settings)

        # Invalidate user cache
        self.bot.cache.invalidate_user(user_id, guild_id)

        # Check message-count achievements
        achievements_cog = self.bot.get_cog("Achievements")
        if achievements_cog:
            refreshed = await self.bot.db.get_user(user_id, guild_id)
            await achievements_cog.check_message_achievements(
                message.author, guild_id, refreshed["messages"]
            )

    async def _handle_level_up(
        self,
        message: discord.Message,
        user_id: str,
        guild_id: str,
        new_level: int,
        settings: dict,
    ) -> None:
        """Announce level-up, assign roles, award coins, log activity."""
        member = message.guild.get_member(int(user_id))
        if member is None:
            return

        # Coins reward for leveling up
        if settings["coins_enabled"]:
            bonus = self.bot.config.COINS_PER_LEVEL_UP * new_level
            await self.bot.db.add_coins(user_id, guild_id, bonus, f"Level {new_level} reward")

        # Assign level role if configured
        await self._assign_level_roles(member, guild_id, new_level, settings["stack_roles"])

        # Announcement embed
        announce_ch_id = settings.get("announce_channel")
        channel = (
            message.guild.get_channel(int(announce_ch_id))
            if announce_ch_id
            else message.channel
        )
        if channel is None:
            channel = message.channel

        template = settings["announce_message"]
        text = template.format(user=member.mention, level=new_level, server=message.guild.name)

        embed = discord.Embed(
            description=text,
            color=prestige_color(0),
        )
        embed.set_thumbnail(url=get_avatar_url(member))
        embed.set_footer(text=f"Server Levels+ • {message.guild.name}")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning("Cannot send level-up message in guild %s", guild_id)

        # Log activity for dashboard feed
        await self.bot.db.log_activity(
            guild_id, user_id, str(member), "level_up", {"level": new_level}
        )

        # Check achievements related to levels
        achievements_cog = self.bot.get_cog("Achievements")
        if achievements_cog:
            await achievements_cog.check_level_achievements(member, guild_id, new_level)

    async def _assign_level_roles(
        self,
        member: discord.Member,
        guild_id: str,
        level: int,
        stack: bool,
    ) -> None:
        """Grant the appropriate level role, removing others if not stacking."""
        level_roles = await self.bot.db.get_level_roles(guild_id)
        if not level_roles:
            return

        roles_to_add: list[discord.Role] = []
        roles_to_remove: list[discord.Role] = []

        for lr in level_roles:
            role = member.guild.get_role(int(lr["role_id"]))
            if role is None:
                continue
            if lr["level"] <= level:
                if role not in member.roles:
                    roles_to_add.append(role)
            elif not stack and role in member.roles:
                roles_to_remove.append(role)

        try:
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Server Levels+ level-up")
            if roles_to_remove and not stack:
                await member.remove_roles(*roles_to_remove, reason="Server Levels+ role cleanup")
        except discord.Forbidden:
            logger.warning("Missing permissions to assign roles in guild %s", guild_id)

    # ------------------------------------------------------------------ #
    # Voice XP (periodic)                                                   #
    # ------------------------------------------------------------------ #

    @tasks.loop(minutes=1)
    async def voice_xp_task(self) -> None:
        """Award XP to users currently in voice channels every minute."""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            settings = self.bot.cache.get_guild(guild_id)
            if settings is None:
                settings = await self.bot.db.get_guild_settings(guild_id)
                self.bot.cache.set_guild(guild_id, settings)

            if not settings["voice_xp_enabled"]:
                continue

            xp_per_min = self.bot.config.XP_PER_VOICE_MINUTE
            multiplier = settings["xp_multiplier"]
            xp_gain = max(1, int(xp_per_min * multiplier))

            today = date.today()
            week = f"{today.year}-W{today.isocalendar()[1]:02d}"
            month = f"{today.year}-{today.month:02d}"

            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.bot:
                        continue
                    # Skip muted/deafened users (AFK)
                    if member.voice and (member.voice.afk or member.voice.self_deaf or member.voice.deaf):
                        continue

                    user_id = str(member.id)
                    user = await self.bot.db.get_user(user_id, guild_id)
                    if user["daily_xp"] >= settings["daily_xp_cap"]:
                        continue

                    old_level = user["level"]
                    updated = await self.bot.db.add_xp(user_id, guild_id, xp_gain, week, month)

                    # Add voice minutes
                    new_voice_minutes = user["voice_minutes"] + 1
                    await self.bot.db.update_user(
                        user_id, guild_id, voice_minutes=new_voice_minutes
                    )

                    # Check level-up
                    new_level, _, _ = calculate_level(updated["total_xp"])
                    if new_level > old_level:
                        await self.bot.db.update_user(user_id, guild_id, level=new_level)

                    # Check voice achievements
                    achievements_cog = self.bot.get_cog("Achievements")
                    if achievements_cog:
                        await achievements_cog.check_voice_achievements(
                            member, guild_id, new_voice_minutes
                        )

                    self.bot.cache.invalidate_user(user_id, guild_id)

    @voice_xp_task.before_loop
    async def before_voice_xp_task(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ #
    # Slash commands                                                        #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="rank", description="View your rank card or another member's")
    @app_commands.describe(member="The member to view (leave empty for yourself)")
    async def rank(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ) -> None:
        await interaction.response.defer()

        target = member or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)

        user = await self.bot.db.get_user(user_id, guild_id)
        rank = await self.bot.db.get_user_rank(user_id, guild_id)
        total = await self.bot.db.get_total_users(guild_id)
        achievements = await self.bot.db.get_user_achievements(user_id, guild_id)

        level, current_xp, xp_needed = calculate_level(user["total_xp"])

        # Load achievement data for badges
        from data.achievements_data import ACHIEVEMENTS
        badges = [
            ACHIEVEMENTS.get(a, {}).get("icon", "🏆")
            for a in achievements[:6]
        ]

        card_bytes = await generate_rank_card(
            username=str(target.display_name),
            discriminator=getattr(target, "discriminator", "0"),
            avatar_url=get_avatar_url(target),
            level=level,
            current_xp=current_xp,
            xp_needed=xp_needed,
            rank=rank,
            total_users=total,
            coins=user["coins"],
            prestige=user["prestige"],
            badges=badges,
            join_date=user["join_date"],
        )

        file = discord.File(
            fp=__import__("io").BytesIO(card_bytes),
            filename="rank_card.png",
        )
        await interaction.followup.send(file=file)

    @app_commands.command(name="profile", description="View your full profile")
    @app_commands.describe(member="The member to view (leave empty for yourself)")
    async def profile(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ) -> None:
        await interaction.response.defer()
        target = member or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)

        user = await self.bot.db.get_user(user_id, guild_id)
        rank = await self.bot.db.get_user_rank(user_id, guild_id)
        achievements = await self.bot.db.get_user_achievements(user_id, guild_id)
        level, current_xp, xp_needed = calculate_level(user["total_xp"])

        from utils.helpers import format_voice_time, prestige_badge
        from data.achievements_data import ACHIEVEMENTS

        embed = discord.Embed(
            title=f"{'⭐ ' if user['prestige'] > 0 else ''}{target.display_name}'s Profile",
            color=prestige_color(user["prestige"]),
        )
        embed.set_thumbnail(url=get_avatar_url(target))

        embed.add_field(name="📊 Level", value=f"**{level}** (Rank #{rank})", inline=True)
        embed.add_field(name="✨ XP", value=f"**{format_number(current_xp)}** / {format_number(xp_needed)}", inline=True)
        embed.add_field(name="🌟 Total XP", value=f"**{format_number(user['total_xp'])}**", inline=True)
        embed.add_field(name="💰 Coins", value=f"**{user['coins']:,}**", inline=True)
        embed.add_field(name="💬 Messages", value=f"**{user['messages']:,}**", inline=True)
        embed.add_field(name="🎙 Voice", value=f"**{format_voice_time(user['voice_minutes'])}**", inline=True)

        if user["prestige"] > 0:
            embed.add_field(
                name="🏆 Prestige",
                value=f"{prestige_badge(user['prestige'])} **{user['prestige']}**",
                inline=True,
            )

        if user["bio"]:
            embed.add_field(name="📝 Bio", value=user["bio"], inline=False)

        if achievements:
            badge_line = " ".join(
                ACHIEVEMENTS.get(a, {}).get("icon", "🏆") for a in achievements[:10]
            )
            embed.add_field(name=f"🎖 Achievements ({len(achievements)})", value=badge_line, inline=False)

        embed.set_footer(text=f"Joined: {user['join_date'][:10]}")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(XPCog(bot))
