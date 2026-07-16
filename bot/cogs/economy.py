"""
Economy Cog — coins, shop, inventory management.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import format_number

logger = logging.getLogger("bot.economy")


def _load_shop_items() -> dict:
    path = Path("data/shop_items.json")
    if path.exists():
        return json.loads(path.read_text())
    return {}


class EconomyCog(commands.Cog, name="Economy"):
    """Coin economy: shop, inventory, coin management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.shop_items: dict = _load_shop_items()

    # ------------------------------------------------------------------ #
    # Slash commands                                                        #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="coins", description="Check your coin balance")
    @app_commands.describe(member="Member to check (leave empty for yourself)")
    async def coins(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ) -> None:
        target = member or interaction.user
        user = await self.bot.db.get_user(str(target.id), str(interaction.guild_id))
        embed = discord.Embed(
            title="💰 Coin Balance",
            description=f"{target.mention} has **{user['coins']:,}** coins",
            color=self.bot.config.COLOR_COINS,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="Browse the item shop")
    async def shop(self, interaction: discord.Interaction) -> None:
        from views.shop_view import ShopView
        view = ShopView(self.bot, self.shop_items, str(interaction.guild_id))
        embed = discord.Embed(
            title="🛒 Server Levels+ Shop",
            description="Spend your coins on exclusive cosmetics and boosts!",
            color=self.bot.config.COLOR_COINS,
        )
        categories = {}
        for item_id, item in self.shop_items.items():
            cat = item.get("category", "Other")
            categories.setdefault(cat, []).append((item_id, item))

        for cat, items in categories.items():
            lines = [f"**{i['name']}** — {i['price']:,} 💰 {i['description']}" for _, i in items[:5]]
            embed.add_field(name=cat, value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="inventory", description="View your owned items")
    async def inventory(self, interaction: discord.Interaction) -> None:
        inv = await self.bot.db.get_inventory(str(interaction.user.id), str(interaction.guild_id))
        if not inv:
            embed = discord.Embed(
                title="🎒 Inventory",
                description="You don't own any items yet. Visit the `/shop`!",
                color=self.bot.config.COLOR_INFO,
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="🎒 Your Inventory", color=self.bot.config.COLOR_INFO)
        for entry in inv:
            item_data = self.shop_items.get(entry["item_id"], {})
            name = item_data.get("name", entry["item_id"])
            equipped = "✅ Equipped" if entry["equipped"] else ""
            embed.add_field(name=name, value=equipped or "Not equipped", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase an item from the shop")
    @app_commands.describe(item_id="The item ID to purchase")
    async def buy(self, interaction: discord.Interaction, item_id: str) -> None:
        if item_id not in self.shop_items:
            await interaction.response.send_message("❌ Item not found.", ephemeral=True)
            return

        item = self.shop_items[item_id]
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        # Check if already owned
        inv = await self.bot.db.get_inventory(user_id, guild_id)
        if any(i["item_id"] == item_id for i in inv):
            await interaction.response.send_message("❌ You already own this item.", ephemeral=True)
            return

        success = await self.bot.db.purchase_item(user_id, guild_id, item_id, item["price"])
        if not success:
            await interaction.response.send_message(
                f"❌ Insufficient coins. You need **{item['price']:,}** 💰.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="✅ Purchase Successful",
            description=f"You bought **{item['name']}** for {item['price']:,} 💰!",
            color=self.bot.config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EconomyCog(bot))
