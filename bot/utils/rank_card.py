"""
Rank card image generator using Pillow.
Produces a 900×280 PNG with avatar, XP bar, stats, badges, and gradients.
"""

from __future__ import annotations

import io
import logging
import os
from typing import Optional

import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger("bot.rank_card")

# ---------------------------------------------------------------------------
# Font loading helpers
# ---------------------------------------------------------------------------

FONT_BOLD_PATH = os.getenv("FONT_PATH", "fonts/Montserrat-Bold.ttf")
FONT_REGULAR_PATH = os.getenv("FONT_REGULAR_PATH", "fonts/Montserrat-Regular.ttf")
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except (OSError, IOError):
            logger.warning("Font not found at %s, using default bitmap font.", path)
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------

def _circle_mask(size: int) -> Image.Image:
    """Create a circular mask image."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    return mask


def _rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


async def _fetch_avatar(url: str) -> Image.Image:
    """Download and return an avatar image as PIL Image."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")


# ---------------------------------------------------------------------------
# Main rank card generator
# ---------------------------------------------------------------------------

async def generate_rank_card(
    *,
    username: str,
    discriminator: str,
    avatar_url: str,
    level: int,
    current_xp: int,
    xp_needed: int,
    rank: int,
    total_users: int,
    coins: int,
    prestige: int,
    badges: list[str],
    bg_color: tuple[int, int, int] = (30, 31, 48),
    accent_color: tuple[int, int, int] = (88, 101, 242),
    join_date: Optional[str] = None,
) -> bytes:
    """
    Generate a rank card image and return it as PNG bytes.

    Parameters
    ----------
    username      : Display name
    discriminator : Discord discriminator (or '0' for new usernames)
    avatar_url    : URL of user's avatar
    level         : Current level
    current_xp    : XP progress within this level
    xp_needed     : XP required to reach the next level
    rank          : Server rank position
    total_users   : Total ranked users in the server
    coins         : Current coin balance
    prestige      : Prestige tier (0 = none)
    badges        : List of badge emoji strings
    bg_color      : Background RGB color
    accent_color  : Progress bar / accent RGB color
    join_date     : ISO join date string (optional)
    """
    W, H = 900, 280

    # ── Background ──────────────────────────────────────────────────────
    card = Image.new("RGBA", (W, H), (*bg_color, 255))
    draw = ImageDraw.Draw(card)

    # Subtle gradient overlay
    gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    for x in range(W):
        alpha = int(40 * (1 - x / W))
        grad_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    card = Image.alpha_composite(card, gradient)
    draw = ImageDraw.Draw(card)

    # ── Avatar ──────────────────────────────────────────────────────────
    AVATAR_SIZE = 180
    AVATAR_X, AVATAR_Y = 40, 50

    try:
        avatar = await _fetch_avatar(avatar_url)
        avatar = avatar.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
        # Circular mask
        mask = _circle_mask(AVATAR_SIZE)
        avatar.putalpha(mask)
        card.paste(avatar, (AVATAR_X, AVATAR_Y), avatar)

        # Accent ring around avatar
        ring = Image.new("RGBA", (AVATAR_SIZE + 8, AVATAR_SIZE + 8), (0, 0, 0, 0))
        ring_draw = ImageDraw.Draw(ring)
        ring_draw.ellipse((0, 0, AVATAR_SIZE + 8, AVATAR_SIZE + 8), outline=(*accent_color, 255), width=4)
        card.paste(ring, (AVATAR_X - 4, AVATAR_Y - 4), ring)
    except Exception as exc:
        logger.warning("Could not load avatar: %s", exc)

    # ── Fonts ────────────────────────────────────────────────────────────
    font_xl = _load_font(FONT_BOLD_PATH, 36)
    font_lg = _load_font(FONT_BOLD_PATH, 26)
    font_md = _load_font(FONT_BOLD_PATH, 20)
    font_sm = _load_font(FONT_REGULAR_PATH, 16)
    font_xs = _load_font(FONT_REGULAR_PATH, 14)

    TEXT_X = 260

    # ── Username ─────────────────────────────────────────────────────────
    disp_name = username if len(username) <= 20 else username[:20] + "…"
    draw.text((TEXT_X, 50), disp_name, font=font_xl, fill=(255, 255, 255, 255))

    # Prestige badge
    if prestige > 0:
        from utils.helpers import prestige_badge
        badge_text = prestige_badge(prestige) + f" Prestige {prestige}"
        draw.text((TEXT_X, 93), badge_text, font=font_sm, fill=(*accent_color, 220))

    # ── Level & Rank ─────────────────────────────────────────────────────
    level_text = f"LEVEL {level}"
    rank_text = f"RANK #{rank}"
    draw.text((TEXT_X, 120), level_text, font=font_lg, fill=(*accent_color, 255))
    draw.text((TEXT_X + 170, 120), rank_text, font=font_lg, fill=(160, 160, 180, 255))

    # ── XP Progress bar ──────────────────────────────────────────────────
    BAR_X, BAR_Y = TEXT_X, 158
    BAR_W, BAR_H = 580, 22
    BAR_RADIUS = 11

    # Background track
    _rounded_rectangle(draw, (BAR_X, BAR_Y, BAR_X + BAR_W, BAR_Y + BAR_H), BAR_RADIUS, (60, 60, 80, 255))

    # Fill
    if xp_needed > 0:
        fill_pct = min(1.0, current_xp / xp_needed)
        fill_w = int(BAR_W * fill_pct)
        if fill_w > 0:
            fill_w = max(fill_w, BAR_RADIUS * 2)
            _rounded_rectangle(
                draw,
                (BAR_X, BAR_Y, BAR_X + fill_w, BAR_Y + BAR_H),
                BAR_RADIUS,
                (*accent_color, 255),
            )

    # XP label
    xp_label = f"{current_xp:,} / {xp_needed:,} XP"
    draw.text((BAR_X, BAR_Y - 20), xp_label, font=font_sm, fill=(200, 200, 220, 200))

    # ── Stats row ────────────────────────────────────────────────────────
    stats_y = 200
    stats = [
        ("💰 Coins", f"{coins:,}"),
        ("💬 Messages", "—"),
        ("🕐 Joined", join_date[:10] if join_date else "—"),
    ]
    stat_x = TEXT_X
    for label, value in stats:
        draw.text((stat_x, stats_y), label, font=font_xs, fill=(150, 150, 170, 200))
        draw.text((stat_x, stats_y + 18), value, font=font_md, fill=(255, 255, 255, 230))
        stat_x += 195

    # ── Badges ───────────────────────────────────────────────────────────
    if badges:
        badge_text = "  ".join(badges[:6])
        draw.text((TEXT_X, 250), badge_text, font=font_md, fill=(255, 255, 255, 200))

    # ── Convert to PNG bytes ─────────────────────────────────────────────
    output = io.BytesIO()
    card.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output.getvalue()
