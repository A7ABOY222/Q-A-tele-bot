/**
 * Guild routes — /api/guilds/*
 * Proxies authenticated requests to the bot's internal FastAPI server.
 */

import { Router } from "express";
import type { Request, Response, NextFunction } from "express";
import { logger } from "../lib/logger";
import { getSession } from "./auth";

const router = Router();

const BOT_API_URL = process.env.BOT_API_URL ?? "http://localhost:8000";
const BOT_API_SECRET = process.env.API_SECRET ?? "";

// ── Auth middleware ───────────────────────────────────────────────────────

function requireAuth(req: Request, res: Response, next: NextFunction): void {
  const session = getSession(req);
  if (!session) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }
  (req as any).session = session;
  next();
}

/**
 * Guild membership guard — place after requireAuth on every guild-scoped route.
 * Verifies the authenticated user is a member of the target guild by calling
 * Discord's /users/@me/guilds with the session's access token, preventing IDOR.
 *
 * Must run after requireAuth so req.session is populated.
 */
async function requireGuildMember(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const session = (req as any).session;

  // Defensive: if session is missing (called out of order), reject with 401
  if (!session) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }

  const { guildId } = req.params;
  if (!guildId) {
    next();
    return;
  }

  try {
    const guildsRes = await fetch("https://discord.com/api/v10/users/@me/guilds", {
      headers: { Authorization: `Bearer ${session.accessToken}` },
    });

    if (!guildsRes.ok) {
      logger.warn(
        { userId: session.userId, status: guildsRes.status },
        "Failed to fetch user guilds from Discord"
      );
      res.status(502).json({ error: "Could not verify guild membership" });
      return;
    }

    const userGuilds = (await guildsRes.json()) as Array<{ id: string }>;
    const isMember = userGuilds.some((g) => g.id === guildId);

    if (!isMember) {
      res.status(403).json({ error: "You are not a member of this guild" });
      return;
    }

    next();
  } catch (err) {
    logger.error({ err, guildId }, "Guild membership check failed");
    res.status(502).json({ error: "Could not verify guild membership" });
  }
}

// ── Bot API proxy helper ──────────────────────────────────────────────────

async function botFetch(
  path: string,
  options: RequestInit = {}
): Promise<globalThis.Response> {
  const url = `${BOT_API_URL}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "x-api-secret": BOT_API_SECRET,
    ...((options.headers as Record<string, string>) ?? {}),
  };
  return fetch(url, { ...options, headers });
}

async function proxyGet(
  req: Request,
  res: Response,
  botPath: string
): Promise<void> {
  try {
    const botRes = await botFetch(botPath);
    const data = await botRes.json();
    if (!botRes.ok) {
      res.status(botRes.status).json(data);
      return;
    }
    res.json(data);
  } catch (err) {
    logger.error({ err, botPath }, "Bot API proxy error");
    res.status(503).json({ error: "Bot API unavailable. Is the bot running?" });
  }
}

// ── GET /api/guilds — list user's guilds ─────────────────────────────────

router.get("/", requireAuth, async (req: Request, res: Response) => {
  const session = (req as any).session;
  try {
    const botRes = await botFetch(`/guilds?user_id=${session.userId}`);
    const guilds = await botRes.json();
    res.json(guilds);
  } catch (_err) {
    // Bot offline — return empty list
    res.json([]);
  }
});

// ── GET /api/guilds/:id ──────────────────────────────────────────────────

router.get("/:guildId", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}`);
});

// ── GET /api/guilds/:id/stats ────────────────────────────────────────────

router.get("/:guildId/stats", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}/stats`);
});

// ── GET /api/guilds/:id/settings ─────────────────────────────────────────

router.get("/:guildId/settings", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}/settings`);
});

// ── PUT /api/guilds/:id/settings ─────────────────────────────────────────

router.put("/:guildId/settings", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  try {
    const botRes = await botFetch(`/guilds/${req.params.guildId}/settings`, {
      method: "PUT",
      body: JSON.stringify(req.body),
    });
    const data = await botRes.json();
    res.status(botRes.status).json(data);
  } catch (err) {
    logger.error({ err }, "Settings update proxy error");
    res.status(503).json({ error: "Bot API unavailable" });
  }
});

// ── GET /api/guilds/:id/leaderboard ──────────────────────────────────────

router.get("/:guildId/leaderboard", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  const { type = "xp", page = "1", limit = "20" } = req.query as Record<string, string>;
  await proxyGet(req, res, `/guilds/${req.params.guildId}/leaderboard?type=${type}&page=${page}&limit=${limit}`);
});

// ── GET /api/guilds/:id/members ──────────────────────────────────────────

router.get("/:guildId/members", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  const { page = "1" } = req.query as Record<string, string>;
  // Return leaderboard as member list (search isn't implemented in bot API yet)
  try {
    const botRes = await botFetch(
      `/guilds/${req.params.guildId}/leaderboard?page=${page}&limit=20`
    );
    const data = await botRes.json() as any;
    res.json({
      members: (data.entries ?? []).map((e: any) => ({
        ...e,
        userId: e.userId,
        guildId: req.params.guildId,
        xpNeeded: 0,
        joinedAt: new Date().toISOString(),
        achievements: [],
        badges: [],
      })),
      total: data.total ?? 0,
      page: data.page ?? 1,
      totalPages: data.totalPages ?? 1,
    });
  } catch (_err) {
    res.json({ members: [], total: 0, page: 1, totalPages: 1 });
  }
});

// ── GET /api/guilds/:id/members/:userId ──────────────────────────────────

router.get("/:guildId/members/:userId", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}/members/${req.params.userId}`);
});

// ── POST /api/guilds/:id/members/:userId/xp ──────────────────────────────

router.post("/:guildId/members/:userId/xp", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  try {
    const botRes = await botFetch(
      `/guilds/${req.params.guildId}/members/${req.params.userId}/xp`,
      { method: "POST", body: JSON.stringify(req.body) }
    );
    res.status(botRes.status).json(await botRes.json());
  } catch (err) {
    res.status(503).json({ error: "Bot API unavailable" });
  }
});

// ── POST /api/guilds/:id/members/:userId/reset ────────────────────────────

router.post("/:guildId/members/:userId/reset", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  try {
    const botRes = await botFetch(
      `/guilds/${req.params.guildId}/members/${req.params.userId}/reset`,
      { method: "POST" }
    );
    res.status(botRes.status).json(await botRes.json());
  } catch (err) {
    res.status(503).json({ error: "Bot API unavailable" });
  }
});

// ── Level roles ────────────────────────────────────────────────────────────

router.get("/:guildId/level-roles", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}/level-roles`);
});

router.post("/:guildId/level-roles", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  try {
    const botRes = await botFetch(`/guilds/${req.params.guildId}/level-roles`, {
      method: "POST",
      body: JSON.stringify(req.body),
    });
    res.status(botRes.status).json(await botRes.json());
  } catch (err) {
    res.status(503).json({ error: "Bot API unavailable" });
  }
});

router.delete("/:guildId/level-roles/:level", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  try {
    const botRes = await botFetch(
      `/guilds/${req.params.guildId}/level-roles/${req.params.level}`,
      { method: "DELETE" }
    );
    res.status(botRes.status).json(await botRes.json());
  } catch (err) {
    res.status(503).json({ error: "Bot API unavailable" });
  }
});

// ── Activity ──────────────────────────────────────────────────────────────

router.get("/:guildId/activity", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  const { limit = "20" } = req.query as Record<string, string>;
  await proxyGet(req, res, `/guilds/${req.params.guildId}/activity?limit=${limit}`);
});

// ── Shop ──────────────────────────────────────────────────────────────────

router.get("/:guildId/shop", requireAuth, requireGuildMember, async (req: Request, res: Response) => {
  await proxyGet(req, res, `/guilds/${req.params.guildId}/shop`);
});

export { router as guildsRouter };
