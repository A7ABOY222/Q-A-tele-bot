"""
Profile Cog — /help command and bio/settings commands.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("bot.profile")


class ProfileCog(commands.Cog, name="Profile"):
    """User profile customization."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setbio", description="Set your profile bio")
    @app_commands.describe(bio="Your bio text (max 200 characters)")
    async def setbio(self, interaction: discord.Interaction, bio: str) -> None:
        if len(bio) > 200:
            await interaction.response.send_message("❌ Bio must be 200 characters or less.", ephemeral=True)
            return
        await self.bot.db.update_user(str(interaction.user.id), str(interaction.guild_id), bio=bio)
        embed = discord.Embed(
            title="✅ Bio Updated",
            description=f"Your bio has been set to:\n> {bio}",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="View all Server Levels+ commands")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🚀 Server Levels+ Commands",
            description="A powerful leveling and economy bot for your Discord server!",
            color=self.bot.config.COLOR_PRIMARY,
        )
        embed.add_field(
            name="📊 Leveling",
            value=(
                "`/rank` — View your rank card\n"
                "`/profile` — View your full profile\n"
                "`/leaderboard` — Server leaderboards\n"
                "`/prestige` — Prestige for exclusive rewards"
            ),
            inline=False,
        )
        embed.add_field(
            name="💰 Economy",
            value=(
                "`/coins` — Check coin balance\n"
                "`/daily` — Daily coin reward\n"
                "`/weekly` — Weekly coin reward\n"
                "`/monthly` — Monthly coin reward\n"
                "`/shop` — Browse the item shop\n"
                "`/buy <item>` — Purchase an item\n"
                "`/inventory` — View your items"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎖 Profile",
            value=(
                "`/achievements` — View achievements\n"
                "`/badges` — View your badges\n"
                "`/setbio` — Set your profile bio"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ Admin",
            value=(
                "`/addxp` `/removexp` `/setlevel`\n"
                "`/addcoins` `/removecoins`\n"
                "`/resetuser` `/config`\n"
                "`/multiplier` `/ignorechannel`\n"
                "`/levelrole`"
            ),
            inline=False,
        )
        embed.set_footer(text="Server Levels+ | Dashboard: " + self.bot.config.DASHBOARD_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
