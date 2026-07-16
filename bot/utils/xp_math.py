"""
XP & level calculation utilities.

Formula: XP required for level N = BASE_XP * (N ^ 1.8)
This creates a gentle curve — early levels are fast, late levels require effort.
"""

from __future__ import annotations

import math


BASE_XP = 100  # XP required for level 1 → 2


def xp_for_level(level: int) -> int:
    """
    Return the total XP required to *reach* a given level from level 0.
    xp_for_level(0) = 0
    xp_for_level(1) = 100
    xp_for_level(10) ≈ 6310
    xp_for_level(50) ≈ 148K
    xp_for_level(100) ≈ 630K
    """
    if level <= 0:
        return 0
    return int(BASE_XP * (level ** 1.8))


def xp_to_next_level(current_level: int) -> int:
    """Return XP needed to go from current_level to current_level + 1."""
    return xp_for_level(current_level + 1) - xp_for_level(current_level)


def calculate_level(total_xp: int) -> tuple[int, int, int]:
    """
    Given total accumulated XP, return (level, current_xp, xp_needed).

    current_xp  — XP within the current level (resets on level-up)
    xp_needed   — XP required to reach the next level
    """
    level = 0
    while xp_for_level(level + 1) <= total_xp:
        level += 1

    current_xp = total_xp - xp_for_level(level)
    xp_needed = xp_to_next_level(level)
    return level, current_xp, xp_needed


def progress_percent(total_xp: int) -> float:
    """Return 0–100 progress percentage toward the next level."""
    _, current, needed = calculate_level(total_xp)
    if needed == 0:
        return 100.0
    return min(100.0, current / needed * 100)


def xp_multiplier_bonus(prestige: int) -> float:
    """Prestige gives a +5% XP multiplier per prestige level."""
    return 1.0 + prestige * 0.05
