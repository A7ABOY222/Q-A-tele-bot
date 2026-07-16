"""
Leaderboard Cog — paginated leaderboard embeds for XP, coins, voice, weekly, monthly.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import format_number, format_voice_time, prestige_badge
from utils.xp_math import calculate_level

logger = logging.getLogger("bot.leaderboard")

LB_TYPES = ["xp", "messages", "voice", "coins", "weekly", "monthly"]
LB_LABELS = {
    "xp": "🏆 XP Leaderboard",
    "messages": "💬 Messages Leaderboard",
    "voice": "🎙 Voice Time Leaderboard",
    "coins": "💰 Coins Leaderboard",
    "weekly": "📅 Weekly XP Leaderboard",
    "monthly": "🗓 Monthly XP Leaderboard",
}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


async def _build_leaderboard_embed(
    bot: commands.Bot,
    guild: discord.Guild,
    lb_type: str,
    page: int = 1,
) -> discord.Embed:
    """Fetch and render a leaderboard embed for the given type and page."""
    page_size = 10
    offset = (page - 1) * page_size
    entries = await bot.db.get_leaderboard(str(guild.id), lb_type, limit=page_size, offset=offset)
    total = await bot.db.get_total_users(str(guild.id))
    total_pages = max(1, (total + page_size - 1) // page_size)

    embed = discord.Embed(
        title=LB_LABELS.get(lb_type, "Leaderboard"),
        color=bot.config.COLOR_XP,
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    if not entries:
        embed.description = "No data yet! Start chatting to appear here."
        return embed

    lines = []
    for entry in entries:
        rank = entry.get("rank", offset + entries.index(entry) + 1)
        medal = MEDALS.get(rank, f"`#{rank}`")
        user = guild.get_member(int(entry["user_id"]))
        name = user.display_name if user else f"User {entry['user_id']}"

        if lb_type in ("xp", "weekly", "monthly"):
            level, _, _ = calculate_level(entry.get("total_xp", 0))
            value_str = f"Lv.{level} • {format_number(entry.get('total_xp', 0))} XP"
        elif lb_type == "messages":
            value_str = f"{entry.get('messages', 0):,} messages"
        elif lb_type == "voice":
            value_str = format_voice_time(entry.get("voice_minutes", 0))
        elif lb_type == "coins":
            value_str = f"{entry.get('coins', 0):,} 💰"
        else:
            value_str = ""

        prestige = entry.get("prestige", 0)
        badge = prestige_badge(prestige) if prestige > 0 else ""
        lines.append(f"{medal} **{name}** {badge}\n　{value_str}")

    embed.description = "\n\n".join(lines)
    embed.set_footer(text=f"Page {page}/{total_pages} • {total} members ranked")
    return embed


class LeaderboardView(discord.ui.View):
    """Paginated leaderboard view with type selector."""

    def __init__(self, bot: commands.Bot, guild: discord.Guild, lb_type: str) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.lb_type = lb_type
        self.page = 1

    @discord.ui.select(
        placeholder="Change leaderboard type…",
        options=[
            discord.SelectOption(label="XP", value="xp", emoji="🏆"),
            discord.SelectOption(label="Messages", value="messages", emoji="💬"),
            discord.SelectOption(label="Voice Time", value="voice", emoji="🎙"),
            discord.SelectOption(label="Coins", value="coins", emoji="💰"),
            discord.SelectOption(label="Weekly XP", value="weekly", emoji="📅"),
            discord.SelectOption(label="Monthly XP", value="monthly", emoji="🗓"),
        ],
    )
    async def type_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.lb_type = select.values[0]
        self.page = 1
        embed = await _build_leaderboard_embed(self.bot, self.guild, self.lb_type, self.page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.page > 1:
            self.page -= 1
        embed = await _build_leaderboard_embed(self.bot, self.guild, self.lb_type, self.page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page += 1
        embed = await _build_leaderboard_embed(self.bot, self.guild, self.lb_type, self.page)
        await interaction.response.edit_message(embed=embed, view=self)


class LeaderboardCog(commands.Cog, name="Leaderboard"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View server leaderboards")
    @app_commands.describe(type="Type of leaderboard to display")
    @app_commands.choices(type=[
        app_commands.Choice(name="XP", value="xp"),
        app_commands.Choice(name="Messages", value="messages"),
        app_commands.Choice(name="Voice Time", value="voice"),
        app_commands.Choice(name="Coins", value="coins"),
        app_commands.Choice(name="Weekly XP", value="weekly"),
        app_commands.Choice(name="Monthly XP", value="monthly"),
    ])
    async def leaderboard(
        self, interaction: discord.Interaction, type: str = "xp"
    ) -> None:
        await interaction.response.defer()
        embed = await _build_leaderboard_embed(self.bot, interaction.guild, type)
        view = LeaderboardView(self.bot, interaction.guild, type)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
