"""Shop View — paginated Discord UI for browsing and purchasing items."""

from __future__ import annotations

import discord
from discord.ext import commands


CATEGORY_LABELS = {
    "background": "🖼 Backgrounds",
    "frame": "🪟 Frames",
    "color": "🎨 Colors",
    "boost": "⚡ XP Boosts",
    "decoration": "✨ Decorations",
}


class ShopView(discord.ui.View):
    def __init__(self, bot: commands.Bot, items: dict, guild_id: str) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.items = items
        self.guild_id = guild_id
        self.category = "background"

    @discord.ui.select(
        placeholder="Choose a category…",
        options=[
            discord.SelectOption(label="Backgrounds", value="background", emoji="🖼"),
            discord.SelectOption(label="Frames", value="frame", emoji="🪟"),
            discord.SelectOption(label="Colors", value="color", emoji="🎨"),
            discord.SelectOption(label="XP Boosts", value="boost", emoji="⚡"),
            discord.SelectOption(label="Decorations", value="decoration", emoji="✨"),
        ],
    )
    async def category_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ) -> None:
        self.category = select.values[0]
        embed = self._build_embed(self.category)
        await interaction.response.edit_message(embed=embed, view=self)

    def _build_embed(self, category: str) -> discord.Embed:
        label = CATEGORY_LABELS.get(category, category.title())
        embed = discord.Embed(title=f"🛒 Shop — {label}", color=0xF1C40F)
        cat_items = [(iid, item) for iid, item in self.items.items() if item["category"] == category]
        if not cat_items:
            embed.description = "No items in this category yet."
            return embed
        for item_id, item in cat_items:
            embed.add_field(
                name=f"{item.get('icon', '🎁')} {item['name']} — {item['price']:,} 💰",
                value=f"{item['description']}\n`/buy {item_id}`",
                inline=False,
            )
        return embed
