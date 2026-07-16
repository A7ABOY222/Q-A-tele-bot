"""
Admin Cog — XP management, coins management, user reset, server configuration.
All commands require Administrator or Manage Guild permission.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils.xp_math import calculate_level, xp_for_level

logger = logging.getLogger("bot.admin")

ADMIN_PERM = app_commands.default_permissions(manage_guild=True)


class AdminCog(commands.Cog, name="Admin"):
    """Administrator commands for managing the leveling system."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── XP management ─────────────────────────────────────────────────

    @app_commands.command(name="addxp", description="[Admin] Add XP to a member")
    @ADMIN_PERM
    @app_commands.describe(member="Target member", amount="XP to add")
    async def addxp(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        from datetime import date
        today = date.today()
        week = f"{today.year}-W{today.isocalendar()[1]:02d}"
        month = f"{today.year}-{today.month:02d}"
        user = await self.bot.db.add_xp(str(member.id), str(interaction.guild_id), amount, week, month)
        new_level, _, _ = calculate_level(user["total_xp"])
        await self.bot.db.update_user(str(member.id), str(interaction.guild_id), level=new_level)
        self.bot.cache.invalidate_user(str(member.id), str(interaction.guild_id))
        embed = discord.Embed(
            title="✅ XP Added",
            description=f"Added **{amount:,} XP** to {member.mention}\nNew total: **{user['total_xp']:,} XP** (Level {new_level})",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removexp", description="[Admin] Remove XP from a member")
    @ADMIN_PERM
    @app_commands.describe(member="Target member", amount="XP to remove")
    async def removexp(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        user = await self.bot.db.get_user(str(member.id), str(interaction.guild_id))
        new_total = max(0, user["total_xp"] - amount)
        new_xp = max(0, user["xp"] - amount)
        new_level, _, _ = calculate_level(new_total)
        await self.bot.db.update_user(
            str(member.id), str(interaction.guild_id),
            total_xp=new_total, xp=new_xp, level=new_level,
        )
        self.bot.cache.invalidate_user(str(member.id), str(interaction.guild_id))
        embed = discord.Embed(
            title="✅ XP Removed",
            description=f"Removed **{amount:,} XP** from {member.mention}\nNew total: **{new_total:,} XP** (Level {new_level})",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setlevel", description="[Admin] Set a member's level directly")
    @ADMIN_PERM
    @app_commands.describe(member="Target member", level="Level to set (1-100)")
    async def setlevel(self, interaction: discord.Interaction, member: discord.Member, level: int) -> None:
        max_level = self.bot.config.MAX_LEVEL
        if not 0 <= level <= max_level:
            await interaction.response.send_message(f"❌ Level must be 0–{max_level}.", ephemeral=True)
            return
        total_xp = xp_for_level(level)
        await self.bot.db.update_user(
            str(member.id), str(interaction.guild_id),
            level=level, xp=0, total_xp=total_xp,
        )
        self.bot.cache.invalidate_user(str(member.id), str(interaction.guild_id))
        embed = discord.Embed(
            title="✅ Level Set",
            description=f"Set {member.mention}'s level to **{level}**",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    # ── Coins management ──────────────────────────────────────────────

    @app_commands.command(name="addcoins", description="[Admin] Give coins to a member")
    @ADMIN_PERM
    @app_commands.describe(member="Target member", amount="Coins to give")
    async def addcoins(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        new_bal = await self.bot.db.add_coins(str(member.id), str(interaction.guild_id), amount, "Admin grant")
        embed = discord.Embed(
            title="✅ Coins Added",
            description=f"Gave **{amount:,}** 💰 to {member.mention}\nNew balance: **{new_bal:,}** 💰",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removecoins", description="[Admin] Remove coins from a member")
    @ADMIN_PERM
    @app_commands.describe(member="Target member", amount="Coins to remove")
    async def removecoins(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        new_bal = await self.bot.db.add_coins(str(member.id), str(interaction.guild_id), -amount, "Admin deduction")
        embed = discord.Embed(
            title="✅ Coins Removed",
            description=f"Removed **{amount:,}** 💰 from {member.mention}\nNew balance: **{new_bal:,}** 💰",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    # ── User reset ────────────────────────────────────────────────────

    @app_commands.command(name="resetuser", description="[Admin] Fully reset a member's data")
    @ADMIN_PERM
    @app_commands.describe(member="Member to reset")
    async def resetuser(self, interaction: discord.Interaction, member: discord.Member) -> None:
        embed = discord.Embed(
            title="⚠️ Confirm Reset",
            description=f"This will permanently delete all XP, coins, achievements, and stats for {member.mention}. This cannot be undone.",
            color=self.bot.config.COLOR_ERROR,
        )
        view = _ConfirmView(self.bot, member, str(interaction.guild_id))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ── Server configuration ──────────────────────────────────────────

    @app_commands.command(name="config", description="[Admin] View current bot configuration")
    @ADMIN_PERM
    async def config(self, interaction: discord.Interaction) -> None:
        settings = await self.bot.db.get_guild_settings(str(interaction.guild_id))
        embed = discord.Embed(title="⚙️ Server Configuration", color=self.bot.config.COLOR_INFO)
        embed.add_field(name="XP per Message", value=f"{settings['xp_per_message']}", inline=True)
        embed.add_field(name="XP Cooldown", value=f"{settings['xp_cooldown']}s", inline=True)
        embed.add_field(name="XP Multiplier", value=f"×{settings['xp_multiplier']}", inline=True)
        embed.add_field(name="Max Level", value=str(settings['max_level']), inline=True)
        embed.add_field(name="Daily XP Cap", value=f"{settings['daily_xp_cap']:,}", inline=True)
        embed.add_field(name="Voice XP", value="✅ On" if settings['voice_xp_enabled'] else "❌ Off", inline=True)
        embed.add_field(name="Economy", value="✅ On" if settings['coins_enabled'] else "❌ Off", inline=True)
        embed.add_field(name="Prestige", value="✅ On" if settings['prestige_enabled'] else "❌ Off", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="multiplier", description="[Admin] Set the server XP multiplier")
    @ADMIN_PERM
    @app_commands.describe(value="Multiplier value (e.g. 1.5 = 50% more XP)")
    async def multiplier(self, interaction: discord.Interaction, value: float) -> None:
        if not 0.1 <= value <= 10.0:
            await interaction.response.send_message("❌ Multiplier must be between 0.1 and 10.0.", ephemeral=True)
            return
        await self.bot.db.update_guild_settings(str(interaction.guild_id), xp_multiplier=value)
        self.bot.cache.invalidate_guild(str(interaction.guild_id))
        embed = discord.Embed(
            title="✅ Multiplier Updated",
            description=f"XP multiplier set to **×{value}**",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ignorechannel", description="[Admin] Toggle XP ignore for a channel")
    @ADMIN_PERM
    @app_commands.describe(channel="Channel to toggle")
    async def ignorechannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        settings = await self.bot.db.get_guild_settings(str(interaction.guild_id))
        ignored = settings["ignored_channels"]
        cid = str(channel.id)
        if cid in ignored:
            ignored.remove(cid)
            action = "un-ignored"
        else:
            ignored.append(cid)
            action = "ignored"
        await self.bot.db.update_guild_settings(str(interaction.guild_id), ignored_channels=ignored)
        self.bot.cache.invalidate_guild(str(interaction.guild_id))
        embed = discord.Embed(
            title="✅ Channel Updated",
            description=f"{channel.mention} is now **{action}** for XP.",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="levelrole", description="[Admin] Assign a role to a level")
    @ADMIN_PERM
    @app_commands.describe(level="Level required", role="Role to assign")
    async def levelrole(self, interaction: discord.Interaction, level: int, role: discord.Role) -> None:
        if not 1 <= level <= self.bot.config.MAX_LEVEL:
            await interaction.response.send_message(f"❌ Level must be 1–{self.bot.config.MAX_LEVEL}.", ephemeral=True)
            return
        await self.bot.db.set_level_role(str(interaction.guild_id), level, str(role.id))
        embed = discord.Embed(
            title="✅ Level Role Set",
            description=f"Members will receive {role.mention} at **Level {level}**.",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)


class _ConfirmView(discord.ui.View):
    def __init__(self, bot: commands.Bot, member: discord.Member, guild_id: str) -> None:
        super().__init__(timeout=30)
        self.bot = bot
        self.member = member
        self.guild_id = guild_id

    @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.bot.db.reset_user(str(self.member.id), self.guild_id)
        self.bot.cache.invalidate_user(str(self.member.id), self.guild_id)
        embed = discord.Embed(
            title="✅ User Reset",
            description=f"{self.member.mention}'s data has been fully reset.",
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="Reset cancelled.", embed=None, view=None)
        self.stop()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
