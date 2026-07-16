"""
Rewards Cog — daily, weekly, monthly coin rewards and streak bonuses.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("bot.rewards")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _next_reset(period: str) -> datetime:
    """Return the next reset time for 'daily', 'weekly', or 'monthly'."""
    now = _utc_now()
    if period == "daily":
        reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif period == "weekly":
        days_until_monday = (7 - now.weekday()) % 7 or 7
        reset = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # monthly
        if now.month == 12:
            reset = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            reset = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return reset


def _can_claim(last_claim_str: str | None, period: str) -> bool:
    """Return True if the user can claim their reward for the given period."""
    if not last_claim_str:
        return True
    try:
        last_claim = datetime.fromisoformat(last_claim_str).replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    now = _utc_now()
    if period == "daily":
        return (now - last_claim).total_seconds() >= 86_400
    if period == "weekly":
        return (now - last_claim).total_seconds() >= 7 * 86_400
    # monthly
    return now.month != last_claim.month or now.year != last_claim.year


class RewardsCog(commands.Cog, name="Rewards"):
    """Daily, weekly, monthly rewards and streaks."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="daily", description="Claim your daily coin reward")
    async def daily(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        user = await self.bot.db.get_user(user_id, guild_id)

        if not _can_claim(user["last_daily"], "daily"):
            next_reset = _next_reset("daily")
            ts = int(next_reset.timestamp())
            embed = discord.Embed(
                title="⏰ Daily Reward",
                description=f"You already claimed today's reward!\nCome back <t:{ts}:R>.",
                color=self.bot.config.COLOR_WARNING,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calculate streak bonus
        streak = user["login_streak"]
        if user["last_daily"]:
            try:
                last = datetime.fromisoformat(user["last_daily"]).replace(tzinfo=timezone.utc)
                hours_ago = (_utc_now() - last).total_seconds() / 3600
                streak = (streak + 1) if hours_ago <= 48 else 1
            except ValueError:
                streak = 1
        else:
            streak = 1

        base_min = self.bot.config.DAILY_COINS_MIN
        base_max = self.bot.config.DAILY_COINS_MAX
        streak_bonus = min(streak * 10, 200)  # cap at +200
        coins = random.randint(base_min, base_max) + streak_bonus

        await self.bot.db.add_coins(user_id, guild_id, coins, "Daily reward")
        await self.bot.db.update_user(
            user_id, guild_id,
            last_daily=_utc_now().isoformat(),
            login_streak=streak,
        )

        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            color=self.bot.config.COLOR_SUCCESS,
        )
        embed.add_field(name="💰 Coins", value=f"+**{coins:,}**", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak}** day{'s' if streak != 1 else ''}", inline=True)
        if streak_bonus > 0:
            embed.add_field(name="✨ Streak Bonus", value=f"+{streak_bonus}", inline=True)
        embed.set_footer(text="Come back tomorrow to keep your streak!")
        await interaction.response.send_message(embed=embed)

        # Check achievements
        ach_cog = self.bot.get_cog("Achievements")
        if ach_cog:
            await ach_cog.check_streak_achievements(interaction.user, guild_id, streak)

    @app_commands.command(name="weekly", description="Claim your weekly coin reward")
    async def weekly(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        user = await self.bot.db.get_user(user_id, guild_id)

        if not _can_claim(user["last_weekly"], "weekly"):
            next_reset = _next_reset("weekly")
            ts = int(next_reset.timestamp())
            embed = discord.Embed(
                title="⏰ Weekly Reward",
                description=f"You already claimed this week's reward!\nCome back <t:{ts}:R>.",
                color=self.bot.config.COLOR_WARNING,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        coins = self.bot.config.WEEKLY_COINS
        await self.bot.db.add_coins(user_id, guild_id, coins, "Weekly reward")
        await self.bot.db.update_user(user_id, guild_id, last_weekly=_utc_now().isoformat())

        embed = discord.Embed(
            title="🎉 Weekly Reward Claimed!",
            description=f"You received **{coins:,}** 💰 coins!\nSee you next week!",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="monthly", description="Claim your monthly coin reward")
    async def monthly(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        user = await self.bot.db.get_user(user_id, guild_id)

        if not _can_claim(user["last_monthly"], "monthly"):
            next_reset = _next_reset("monthly")
            ts = int(next_reset.timestamp())
            embed = discord.Embed(
                title="⏰ Monthly Reward",
                description=f"You already claimed this month's reward!\nCome back <t:{ts}:R>.",
                color=self.bot.config.COLOR_WARNING,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        coins = self.bot.config.MONTHLY_COINS
        await self.bot.db.add_coins(user_id, guild_id, coins, "Monthly reward")
        await self.bot.db.update_user(user_id, guild_id, last_monthly=_utc_now().isoformat())

        embed = discord.Embed(
            title="🎊 Monthly Reward Claimed!",
            description=f"You received **{coins:,}** 💰 coins! See you next month!",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RewardsCog(bot))
