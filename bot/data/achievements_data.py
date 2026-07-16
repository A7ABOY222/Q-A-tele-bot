"""
Achievement definitions for Server Levels+.
Each entry: id → { name, description, icon, category }
"""

ACHIEVEMENTS: dict[str, dict] = {
    # ── Messaging ─────────────────────────────────────────────────────
    "first_message": {
        "name": "First Words",
        "description": "Send your very first message",
        "icon": "💬",
        "category": "💬 Messaging",
    },
    "messages_100": {
        "name": "Chatty",
        "description": "Send 100 messages",
        "icon": "📢",
        "category": "💬 Messaging",
    },
    "messages_1000": {
        "name": "Talkative",
        "description": "Send 1,000 messages",
        "icon": "📣",
        "category": "💬 Messaging",
    },
    "messages_10000": {
        "name": "Megaphone",
        "description": "Send 10,000 messages",
        "icon": "📡",
        "category": "💬 Messaging",
    },

    # ── Leveling ──────────────────────────────────────────────────────
    "level_5": {
        "name": "Getting Started",
        "description": "Reach Level 5",
        "icon": "⭐",
        "category": "📊 Leveling",
    },
    "level_10": {
        "name": "Rising Star",
        "description": "Reach Level 10",
        "icon": "🌟",
        "category": "📊 Leveling",
    },
    "level_25": {
        "name": "Dedicated",
        "description": "Reach Level 25",
        "icon": "💫",
        "category": "📊 Leveling",
    },
    "level_50": {
        "name": "Veteran",
        "description": "Reach Level 50",
        "icon": "🏆",
        "category": "📊 Leveling",
    },
    "level_75": {
        "name": "Elite",
        "description": "Reach Level 75",
        "icon": "👑",
        "category": "📊 Leveling",
    },
    "level_100": {
        "name": "Legendary",
        "description": "Reach the maximum Level 100",
        "icon": "🌈",
        "category": "📊 Leveling",
    },

    # ── Prestige ──────────────────────────────────────────────────────
    "prestige_1": {
        "name": "Reborn",
        "description": "Achieve Prestige 1",
        "icon": "🥉",
        "category": "🏅 Prestige",
    },
    "prestige_3": {
        "name": "Devoted",
        "description": "Achieve Prestige 3",
        "icon": "🥇",
        "category": "🏅 Prestige",
    },
    "prestige_5": {
        "name": "Ascended",
        "description": "Achieve Prestige 5",
        "icon": "💎",
        "category": "🏅 Prestige",
    },
    "prestige_10": {
        "name": "Transcendent",
        "description": "Reach Maximum Prestige 10",
        "icon": "🌈",
        "category": "🏅 Prestige",
    },

    # ── Economy ───────────────────────────────────────────────────────
    "coins_1000": {
        "name": "Penny Pincher",
        "description": "Accumulate 1,000 coins",
        "icon": "🪙",
        "category": "💰 Economy",
    },
    "coins_10000": {
        "name": "Rich Player",
        "description": "Accumulate 10,000 coins",
        "icon": "💰",
        "category": "💰 Economy",
    },
    "coins_100000": {
        "name": "Millionaire",
        "description": "Accumulate 100,000 coins",
        "icon": "💎",
        "category": "💰 Economy",
    },

    # ── Voice ─────────────────────────────────────────────────────────
    "voice_1h": {
        "name": "Voice Visitor",
        "description": "Spend 1 hour in voice channels",
        "icon": "🎙",
        "category": "🎙 Voice",
    },
    "voice_10h": {
        "name": "Voice Master",
        "description": "Spend 10 hours in voice channels",
        "icon": "🎤",
        "category": "🎙 Voice",
    },
    "voice_100h": {
        "name": "Voice Legend",
        "description": "Spend 100 hours in voice channels",
        "icon": "🎵",
        "category": "🎙 Voice",
    },

    # ── Streaks ───────────────────────────────────────────────────────
    "streak_7": {
        "name": "Weekly Warrior",
        "description": "Maintain a 7-day daily streak",
        "icon": "🔥",
        "category": "🔥 Streaks",
    },
    "streak_30": {
        "name": "Monthly Master",
        "description": "Maintain a 30-day daily streak",
        "icon": "⚡",
        "category": "🔥 Streaks",
    },
    "streak_100": {
        "name": "Unstoppable",
        "description": "Maintain a 100-day daily streak",
        "icon": "🌟",
        "category": "🔥 Streaks",
    },
}
