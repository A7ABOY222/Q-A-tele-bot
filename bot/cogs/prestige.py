"""
Prestige Cog — prestige system allowing users to reset for exclusive rewards.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import prestige_badge, prestige_color
from utils.xp_math import xp_for_level

logger = logging.getLogger("bot.prestige")


class PrestigeCog(commands.Cog, name="Prestige"):
    """Prestige system — reset at max level for exclusive badges and multipliers."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="prestige", description="Prestige — reset your level for exclusive rewards")
    async def prestige(self, interaction: discord.Interaction) -> None:
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        settings = await self.bot.db.get_guild_settings(guild_id)
        if not settings["prestige_enabled"]:
            await interaction.response.send_message("❌ Prestige is disabled on this server.", ephemeral=True)
            return

        user = await self.bot.db.get_user(user_id, guild_id)
        required_level = self.bot.config.PRESTIGE_LEVEL_REQUIRED
        max_prestige = self.bot.config.MAX_PRESTIGE

        if user["level"] < required_level:
            await interaction.response.send_message(
                f"❌ You must reach **Level {required_level}** to prestige.\n"
                f"You are currently **Level {user['level']}**.",
                ephemeral=True,
            )
            return

        if user["prestige"] >= max_prestige:
            await interaction.response.send_message(
                f"✨ You've already reached **Maximum Prestige {max_prestige}**! You're a legend.",
                ephemeral=True,
            )
            return

        new_prestige = user["prestige"] + 1
        badge = prestige_badge(new_prestige)

        # Show confirmation
        embed = discord.Embed(
            title=f"{badge} Prestige {new_prestige}",
            description=(
                f"You're about to **prestige** to **{badge} Prestige {new_prestige}**!\n\n"
                f"**What you'll lose:**\n"
                f"• Your level will reset to **1**\n"
                f"• Your XP progress will be wiped\n\n"
                f"**What you'll keep:**\n"
                f"• All your **coins** 💰\n"
                f"• All your **achievements** 🎖\n"
                f"• Your **messages** count 💬\n"
                f"• Your **inventory** items 🎒\n\n"
                f"**What you'll gain:**\n"
                f"• {badge} Prestige {new_prestige} badge\n"
                f"• **+5%** permanent XP multiplier\n"
                f"• Exclusive prestige cosmetics"
            ),
            color=prestige_color(new_prestige),
        )
        view = _PrestigeConfirmView(self.bot, user_id, guild_id, new_prestige)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class _PrestigeConfirmView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: str, guild_id: str, new_prestige: int) -> None:
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.new_prestige = new_prestige

    @discord.ui.button(label="✨ Confirm Prestige", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your confirmation!", ephemeral=True)
            return

        # Reset level/xp but keep coins, achievements, inventory
        await self.bot.db.update_user(
            self.user_id, self.guild_id,
            level=0,
            xp=0,
            total_xp=0,
            prestige=self.new_prestige,
        )
        self.bot.cache.invalidate_user(self.user_id, self.guild_id)

        # Unlock prestige achievement
        ach_cog = self.bot.get_cog("Achievements")
        if ach_cog:
            member = interaction.guild.get_member(int(self.user_id))
            if member:
                ach_id = f"prestige_{self.new_prestige}"
                await ach_cog._try_unlock(member, self.guild_id, ach_id)

        badge = prestige_badge(self.new_prestige)
        embed = discord.Embed(
            title=f"🎊 Congratulations, {badge} Prestige {self.new_prestige}!",
            description=f"You've prestiged! Your level has been reset.\nEnjoy your +{self.new_prestige * 5}% XP multiplier!",
            color=prestige_color(self.new_prestige),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

        # Log activity
        await self.bot.db.log_activity(
            self.guild_id, self.user_id, str(interaction.user),
            "prestige", {"prestige": self.new_prestige},
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="Prestige cancelled.", embed=None, view=None)
        self.stop()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PrestigeCog(bot))
