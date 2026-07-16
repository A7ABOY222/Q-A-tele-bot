# Server Levels+ Discord Bot

A feature-rich Discord leveling bot with XP, economy, achievements, prestige, and a web dashboard.

## Run & Operate

- `cd bot && python3 main.py` — run the Discord bot (also installs deps via pip)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080)
- `pnpm --filter @workspace/dashboard run dev` — run the web dashboard (Vite)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

## Required Secrets

- `DISCORD_TOKEN` — bot token from Discord Developer Portal
- `APPLICATION_ID` — bot's Application ID from Discord Developer Portal

## Optional Secrets (Dashboard OAuth)

- `DISCORD_CLIENT_ID` — OAuth Client ID (for dashboard login)
- `DISCORD_CLIENT_SECRET` — OAuth Client Secret
- `DISCORD_REDIRECT_URI` — OAuth redirect URI (e.g. `https://<your-domain>/auth/callback`)
- `API_SECRET` — shared secret between bot and dashboard API
- `GUILD_ID` — guild ID for instant slash-command sync (dev only)
- `TOPGG_TOKEN` — Top.gg API token for vote tracking

## Stack

- pnpm workspaces, Node.js 24, Python 3.11, TypeScript 5.9
- Bot: discord.py, aiosqlite (SQLite default), FastAPI dashboard API on port 8000
- API: Express 5, esbuild (CJS bundle)
- DB: PostgreSQL + Drizzle ORM (Node side); SQLite (bot side, default)
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Frontend: React, Vite, Tailwind CSS, Shadcn UI

## Where things live

- `bot/` — Python Discord bot (entry: `bot/main.py`)
- `bot/cogs/` — bot feature modules (xp, economy, leaderboard, admin, etc.)
- `bot/cogs/api_server.py` — FastAPI server for dashboard data (port 8000)
- `artifacts/api-server/` — Node.js/Express API server
- `artifacts/dashboard/` — React/Vite web dashboard
- `lib/db/src/schema/` — Drizzle ORM schema (source of truth for Node DB)

## Architecture decisions

- Bot uses SQLite by default; set `DATABASE_URL` to switch to PostgreSQL
- Bot also starts a FastAPI HTTP server (port 8000) for the dashboard to query
- Node API server builds with esbuild to `dist/` before starting

## Product

Discord bot that tracks XP, levels, and economy for server members. Members earn XP for messages and voice activity, can prestige, earn achievements, and use an economy system. Admins configure the bot per-server via slash commands or the web dashboard.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Install Python deps with `pip` (not `pip3`) — that's what the Replit environment exposes
- Python binary is `python3` in this environment
- `pnpm install` must be run before Node.js workflows will start (run at workspace root)

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See `bot/README.md` for full Discord bot documentation and deployment options
