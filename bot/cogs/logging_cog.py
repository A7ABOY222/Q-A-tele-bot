"""
Logging Cog — records member joins/leaves, XP events, and errors to a log channel.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from utils.helpers import get_avatar_url

logger = logging.getLogger("bot.logging")


class LoggingCog(commands.Cog, name="Logging"):
    """Event logging to a designated server log channel."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _get_log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Return the configured log channel for a guild, or None."""
        settings = await self.bot.db.get_guild_settings(str(guild.id))
        ch_id = settings.get("announce_channel")  # Reuse the announce channel as log target for simplicity
        log_ch_id = self.bot.config.LOG_CHANNEL_ID
        target_id = log_ch_id or ch_id
        if not target_id:
            return None
        ch = guild.get_channel(int(target_id))
        return ch if isinstance(ch, discord.TextChannel) else None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        ch = await self._get_log_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} joined the server.",
            color=self.bot.config.COLOR_SUCCESS,
        )
        embed.set_thumbnail(url=get_avatar_url(member))
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        try:
            await ch.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        ch = await self._get_log_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"**{member}** left the server.",
            color=self.bot.config.COLOR_ERROR,
        )
        embed.set_footer(text=f"ID: {member.id}")
        try:
            await ch.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: discord.app_commands.Command
    ) -> None:
        logger.info(
            "Command /%s used by %s in guild %s",
            command.name,
            interaction.user,
            interaction.guild_id,
        )

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ) -> None:
        logger.error("App command error: %s", error, exc_info=True)
        msg = "❌ An error occurred. Please try again later."
        if isinstance(error, discord.app_commands.MissingPermissions):
            msg = "❌ You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            msg = f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f}s."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LoggingCog(bot))
