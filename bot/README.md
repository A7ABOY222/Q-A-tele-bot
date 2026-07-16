# 🚀 Server Levels+ Discord Bot

A professional, feature-rich Discord leveling bot with XP, economy, achievements, prestige, and a beautiful web dashboard.

---

## Features

| Feature | Details |
|---|---|
| **XP System** | Message XP, voice XP, cooldowns, multipliers, daily cap |
| **Rank Cards** | Beautiful image cards with avatar, progress bar, badges |
| **Leaderboards** | XP, messages, voice, coins, weekly, monthly |
| **Economy** | Coins, shop, inventory, daily/weekly/monthly rewards |
| **Achievements** | 25+ automatic achievements with notifications |
| **Prestige** | Reset at max level for exclusive badges & +5% XP/prestige |
| **Profiles** | Bio, badges, stats, achievement showcase |
| **Admin Tools** | Add/remove XP, set level, manage coins, configure server |
| **Dashboard** | Web dashboard for per-server configuration |
| **Top.gg** | Vote support and webhook integration |

---

## Quick Start

### 1. Install dependencies

```bash
cd bot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your DISCORD_TOKEN and other values
```

### 3. Run the bot

```bash
python main.py
```

The bot will:
- Create the SQLite database at `data/bot.db` automatically
- Load all cogs and register slash commands
- Start the dashboard API on port 8000

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Your bot token from Discord Developer Portal |
| `APPLICATION_ID` | ✅ | Your bot's Application ID |
| `GUILD_ID` | Optional | Guild ID for instant slash-command sync (dev only) |
| `DATABASE_PATH` | Optional | SQLite path (default: `data/bot.db`) |
| `DASHBOARD_URL` | Optional | Your dashboard URL (for OAuth redirects) |
| `API_SECRET` | Optional | Shared secret between bot and dashboard API |
| `DISCORD_CLIENT_ID` | Dashboard | OAuth Client ID |
| `DISCORD_CLIENT_SECRET` | Dashboard | OAuth Client Secret |
| `DISCORD_REDIRECT_URI` | Dashboard | OAuth redirect URI |
| `TOPGG_TOKEN` | Optional | Top.gg API token for vote tracking |
| `LOG_LEVEL` | Optional | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

---

## Slash Commands

### User Commands

| Command | Description |
|---|---|
| `/rank [member]` | View rank card |
| `/profile [member]` | View full profile |
| `/leaderboard [type]` | Server leaderboards (xp/messages/voice/coins/weekly/monthly) |
| `/coins [member]` | Check coin balance |
| `/daily` | Claim daily reward |
| `/weekly` | Claim weekly reward |
| `/monthly` | Claim monthly reward |
| `/shop` | Browse item shop |
| `/buy <item>` | Purchase an item |
| `/inventory` | View owned items |
| `/achievements [member]` | View achievements |
| `/badges` | View badge collection |
| `/prestige` | Prestige at max level |
| `/setbio <text>` | Set profile bio |
| `/help` | List all commands |

### Admin Commands

| Command | Description |
|---|---|
| `/addxp <member> <amount>` | Add XP to a member |
| `/removexp <member> <amount>` | Remove XP from a member |
| `/setlevel <member> <level>` | Set member level directly |
| `/addcoins <member> <amount>` | Give coins to a member |
| `/removecoins <member> <amount>` | Remove coins from a member |
| `/resetuser <member>` | Fully reset a member's data |
| `/config` | View server configuration |
| `/multiplier <value>` | Set XP multiplier (e.g. 1.5) |
| `/ignorechannel <channel>` | Toggle XP ignore for a channel |
| `/levelrole <level> <role>` | Assign role at a level |

---

## Web Dashboard

The dashboard requires Discord OAuth. After the bot is running:

1. Set `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, and `DISCORD_REDIRECT_URI` in your `.env`
2. In the Discord Developer Portal → OAuth2 → Redirects, add your redirect URI
3. Visit the dashboard and click "Login with Discord"
4. Select your server and configure settings

### Dashboard URL structure

- `/` — Landing page
- `/dashboard` — Server selector
- `/dashboard/:guildId` — Server overview and stats
- `/dashboard/:guildId/settings` — Bot configuration
- `/dashboard/:guildId/leaderboard` — Leaderboard viewer
- `/dashboard/:guildId/members` — Member management

---

## Deployment

### Replit (recommended for testing)

1. Add `DISCORD_TOKEN` and other secrets in Replit's Secrets panel
2. The bot workflow starts automatically
3. The dashboard is served at your Replit dev domain

### Railway

```bash
# railway.toml
[build]
  builder = "NIXPACKS"

[deploy]
  startCommand = "python bot/main.py"
  restartPolicyType = "ON_FAILURE"
```

Set environment variables in Railway's Variables panel.

### VPS / Self-hosted

```bash
# Using systemd
[Unit]
Description=Server Levels+ Bot

[Service]
WorkingDirectory=/opt/serverlevels/bot
ExecStart=/usr/bin/python3 main.py
Restart=always
EnvironmentFile=/opt/serverlevels/bot/.env

[Install]
WantedBy=multi-user.target
```

---

## Top.gg Listing

To list on [top.gg](https://top.gg):

1. Create your bot listing at top.gg
2. Set `TOPGG_TOKEN` in your `.env`
3. The bot will automatically post stats every 30 minutes
4. Set up vote webhooks by configuring your top.gg webhook URL and `TOPGG_WEBHOOK_AUTH`

---

## Database

By default, Server Levels+ uses **SQLite** (`data/bot.db`).

To switch to **PostgreSQL**, set `DATABASE_URL` to your PostgreSQL connection string. The bot will automatically use async PostgreSQL instead.

The database is created automatically on first run with all required tables and indexes.

---

## Adding Fonts

For the best rank card experience, download **Montserrat** from Google Fonts and place the files in the `fonts/` directory:

- `fonts/Montserrat-Bold.ttf`
- `fonts/Montserrat-Regular.ttf`

If fonts are not present, the bot will use a fallback system font.

---

## Architecture

```
bot/
├── main.py              — Bot entry point
├── config.py            — All configuration via env vars
├── cogs/
│   ├── xp.py            — XP, level-ups, rank cards
│   ├── economy.py       — Coins, shop, inventory
│   ├── rewards.py       — Daily/weekly/monthly rewards
│   ├── leaderboard.py   — Leaderboard commands
│   ├── admin.py         — Admin management commands
│   ├── achievements.py  — Achievement system
│   ├── prestige.py      — Prestige system
│   ├── profile.py       — Profile commands, /help
│   ├── logging_cog.py   — Event logging
│   └── api_server.py    — Dashboard API (FastAPI)
├── database/
│   └── db.py            — Async SQLite database manager
├── utils/
│   ├── xp_math.py       — XP/level calculations
│   ├── rank_card.py     — Rank card image generation (Pillow)
│   ├── cache.py         — TTL in-memory cache
│   └── helpers.py       — Misc utilities
├── views/
│   └── shop_view.py     — Discord UI shop view
└── data/
    ├── achievements_data.py — Achievement definitions
    └── shop_items.json      — Shop item catalog
```

---

## License

MIT — use freely, attribution appreciated.
