/**
 * Discord OAuth routes — /api/auth/*
 * Handles login, callback, session info, and logout.
 */

import { Router } from "express";
import type { Request, Response } from "express";
import { logger } from "../lib/logger";

const router = Router();

const DISCORD_API = "https://discord.com/api/v10";
const CLIENT_ID = process.env.DISCORD_CLIENT_ID ?? "";
const CLIENT_SECRET = process.env.DISCORD_CLIENT_SECRET ?? "";
const REDIRECT_URI = process.env.DISCORD_REDIRECT_URI ?? "";
const DASHBOARD_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const SESSION_SECRET = process.env.SESSION_SECRET ?? "change-me";

// Simple session store (in-memory; use Redis in production for multi-instance)
interface SessionData {
  userId: string;
  username: string;
  discriminator: string;
  avatar: string | null;
  accessToken: string;
  expiresAt: number; // unix ms
}
const sessions = new Map<string, SessionData>();

function generateSessionId(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 48; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

function getSession(req: Request): SessionData | null {
  const sid = req.cookies?.["session_id"];
  if (!sid) return null;
  const data = sessions.get(sid);
  if (!data) return null;
  if (Date.now() > data.expiresAt) {
    sessions.delete(sid);
    return null;
  }
  return data;
}

// ── GET /api/auth/discord — redirect to Discord OAuth ────────────────────

router.get("/discord", (_req: Request, res: Response) => {
  if (!CLIENT_ID || !REDIRECT_URI) {
    res.status(500).json({ error: "Discord OAuth is not configured. Set DISCORD_CLIENT_ID and DISCORD_REDIRECT_URI." });
    return;
  }
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: "code",
    scope: "identify guilds",
  });
  res.redirect(`${DISCORD_API}/oauth2/authorize?${params}`);
});

// ── GET /api/auth/callback — handle OAuth callback ───────────────────────

router.get("/callback", async (req: Request, res: Response) => {
  const { code, error } = req.query as Record<string, string>;

  if (error || !code) {
    res.redirect(`${DASHBOARD_URL}/?error=oauth_denied`);
    return;
  }

  try {
    // Exchange code for token
    const tokenRes = await fetch(`${DISCORD_API}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
        grant_type: "authorization_code",
        code,
        redirect_uri: REDIRECT_URI,
      }),
    });

    if (!tokenRes.ok) {
      const err = await tokenRes.text();
      logger.error({ err }, "Discord token exchange failed");
      res.redirect(`${DASHBOARD_URL}/?error=token_failed`);
      return;
    }

    const tokenData = (await tokenRes.json()) as {
      access_token: string;
      token_type: string;
      expires_in: number;
    };

    // Fetch Discord user info
    const userRes = await fetch(`${DISCORD_API}/users/@me`, {
      headers: { Authorization: `Bearer ${tokenData.access_token}` },
    });

    if (!userRes.ok) {
      res.redirect(`${DASHBOARD_URL}/?error=user_fetch_failed`);
      return;
    }

    const user = (await userRes.json()) as {
      id: string;
      username: string;
      discriminator: string;
      avatar: string | null;
    };

    // Create session
    const sessionId = generateSessionId();
    const expiresAt = Date.now() + tokenData.expires_in * 1000;

    sessions.set(sessionId, {
      userId: user.id,
      username: user.username,
      discriminator: user.discriminator,
      avatar: user.avatar,
      accessToken: tokenData.access_token,
      expiresAt,
    });

    res.cookie("session_id", sessionId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: tokenData.expires_in * 1000,
    });

    logger.info({ userId: user.id, username: user.username }, "User logged in via Discord OAuth");
    res.redirect(`${DASHBOARD_URL}/dashboard`);
  } catch (err) {
    logger.error({ err }, "OAuth callback error");
    res.redirect(`${DASHBOARD_URL}/?error=internal_error`);
  }
});

// ── GET /api/auth/me — return current session user ───────────────────────

router.get("/me", (req: Request, res: Response) => {
  const session = getSession(req);
  if (!session) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }

  const avatarUrl = session.avatar
    ? `https://cdn.discordapp.com/avatars/${session.userId}/${session.avatar}.png`
    : `https://cdn.discordapp.com/embed/avatars/${Number(session.userId) % 5}.png`;

  res.json({
    id: session.userId,
    username: session.username,
    discriminator: session.discriminator,
    avatar: session.avatar,
    avatarUrl,
  });
});

// ── POST /api/auth/logout — clear session ────────────────────────────────

router.post("/logout", (req: Request, res: Response) => {
  const sid = req.cookies?.["session_id"];
  if (sid) {
    sessions.delete(sid);
  }
  res.clearCookie("session_id");
  res.json({ success: true, message: "Logged out" });
});

export { router as authRouter, getSession, sessions };
