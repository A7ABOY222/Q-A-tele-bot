"""
Achievements Cog — automatic achievement unlocking and display.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from data.achievements_data import ACHIEVEMENTS

logger = logging.getLogger("bot.achievements")


class AchievementsCog(commands.Cog, name="Achievements"):
    """Track and award achievements automatically."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Auto-check helpers (called from other cogs)                           #
    # ------------------------------------------------------------------ #

    async def check_level_achievements(
        self, member: discord.Member, guild_id: str, level: int
    ) -> None:
        level_milestones = {
            5: "level_5",
            10: "level_10",
            25: "level_25",
            50: "level_50",
            75: "level_75",
            100: "level_100",
        }
        for milestone, ach_id in level_milestones.items():
            if level >= milestone:
                await self._try_unlock(member, guild_id, ach_id)

    async def check_message_achievements(
        self, member: discord.Member, guild_id: str, messages: int
    ) -> None:
        msg_milestones = {
            1: "first_message",
            100: "messages_100",
            1000: "messages_1000",
            10000: "messages_10000",
        }
        for milestone, ach_id in msg_milestones.items():
            if messages >= milestone:
                await self._try_unlock(member, guild_id, ach_id)

    async def check_streak_achievements(
        self, member: discord.Member, guild_id: str, streak: int
    ) -> None:
        streak_milestones = {7: "streak_7", 30: "streak_30", 100: "streak_100"}
        for milestone, ach_id in streak_milestones.items():
            if streak >= milestone:
                await self._try_unlock(member, guild_id, ach_id)

    async def check_coins_achievements(
        self, member: discord.Member, guild_id: str, coins: int
    ) -> None:
        coin_milestones = {
            1000: "coins_1000",
            10000: "coins_10000",
            100000: "coins_100000",
        }
        for milestone, ach_id in coin_milestones.items():
            if coins >= milestone:
                await self._try_unlock(member, guild_id, ach_id)

    async def check_voice_achievements(
        self, member: discord.Member, guild_id: str, voice_minutes: int
    ) -> None:
        voice_milestones = {
            60: "voice_1h",
            600: "voice_10h",
            6000: "voice_100h",
        }
        for milestone, ach_id in voice_milestones.items():
            if voice_minutes >= milestone:
                await self._try_unlock(member, guild_id, ach_id)

    async def _try_unlock(
        self, member: discord.Member, guild_id: str, achievement_id: str
    ) -> None:
        """Attempt to unlock an achievement; notify if newly unlocked."""
        if achievement_id not in ACHIEVEMENTS:
            return
        unlocked = await self.bot.db.unlock_achievement(str(member.id), guild_id, achievement_id)
        if unlocked:
            ach = ACHIEVEMENTS[achievement_id]
            await self._notify(member, guild_id, ach)
            await self.bot.db.log_activity(
                guild_id, str(member.id), str(member),
                "achievement", {"achievement_id": achievement_id, "name": ach["name"]},
            )
            logger.info("Achievement unlocked: %s for %s in %s", achievement_id, member, guild_id)

    async def _notify(
        self, member: discord.Member, guild_id: str, ach: dict
    ) -> None:
        """Send a brief achievement DM or channel notification."""
        try:
            embed = discord.Embed(
                title=f"{ach['icon']} Achievement Unlocked!",
                description=f"**{ach['name']}**\n{ach['description']}",
                color=self.bot.config.COLOR_SUCCESS,
            )
            embed.set_footer(text=f"Server: {member.guild.name}")
            await member.send(embed=embed)
        except discord.Forbidden:
            pass  # User has DMs disabled — silently skip

    # ------------------------------------------------------------------ #
    # Slash commands                                                        #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="achievements", description="View your achievements")
    @app_commands.describe(member="Member to check (leave empty for yourself)")
    async def achievements(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ) -> None:
        target = member or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)

        unlocked_ids = await self.bot.db.get_user_achievements(user_id, guild_id)
        unlocked_set = set(unlocked_ids)
        total = len(ACHIEVEMENTS)
        earned = len(unlocked_ids)

        embed = discord.Embed(
            title=f"🎖 {target.display_name}'s Achievements ({earned}/{total})",
            color=self.bot.config.COLOR_XP,
        )

        # Group by category
        categories: dict[str, list] = {}
        for ach_id, ach in ACHIEVEMENTS.items():
            cat = ach.get("category", "General")
            categories.setdefault(cat, []).append((ach_id, ach))

        for cat, items in categories.items():
            lines = []
            for ach_id, ach in items:
                if ach_id in unlocked_set:
                    lines.append(f"{ach['icon']} ~~**{ach['name']}**~~ ✅")
                else:
                    lines.append(f"🔒 **{ach['name']}** — {ach['description']}")
            embed.add_field(name=cat, value="\n".join(lines), inline=False)

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="badges", description="View your badge collection")
    async def badges(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        unlocked_ids = await self.bot.db.get_user_achievements(user_id, guild_id)

        badge_icons = [ACHIEVEMENTS[a]["icon"] for a in unlocked_ids if a in ACHIEVEMENTS]
        embed = discord.Embed(
            title="🏅 Your Badges",
            description=" ".join(badge_icons) if badge_icons else "No badges yet! Complete achievements to earn badges.",
            color=self.bot.config.COLOR_XP,
        )
        embed.set_footer(text=f"{len(badge_icons)} badges earned")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AchievementsCog(bot))
