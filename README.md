# Minecraft SMP — Railway Hosting

## What you need
- A [Railway](https://railway.app) account (Hobby plan, $5/month — required for TCP)
- A GitHub account (to push this folder)

---

## Deploy steps

### 1 — Push to GitHub
Create a new **private** GitHub repo, push this `railway-minecraft` folder to it.

### 2 — Create a Railway project
1. Go to [railway.app](https://railway.app) → **New Project**
2. Choose **Deploy from GitHub repo** → select your repo
3. Railway auto-detects the Dockerfile and builds it

### 3 — Add a Volume (persistent world)
In your Railway service:
1. Click **+ Add Volume**
2. Set mount path: `/minecraft/world`
3. Do the same for `/minecraft/plugins` (optional but recommended)

Without a volume your world resets every deploy!

### 4 — Enable TCP Proxy (so players can connect)
1. In your service → **Settings** → **Networking**
2. Click **Add TCP Proxy**
3. Set internal port: **25565**
4. Railway gives you an address like `trolley.proxy.rlwy.net:12345`
5. That's the address players use to connect ✅

### 5 — Set RAM (optional)
In **Variables**, add:
```
MEMORY=1536
```
Change to `2048` if you have more RAM available on your plan.

### 6 — Deploy & connect
- Hit **Deploy** — it takes ~2 minutes to build and start
- Open the Railway **Logs** tab to watch it boot
- Once you see `Done! For help, type "help"` it's live
- Connect in Minecraft → **Multiplayer → Direct Connection** → paste the TCP proxy address

---

## After connecting

Give yourself op in the Railway **console** (or click the terminal icon):
```
op YourMinecraftName
```

## Recommended plugins (drop into `/minecraft/plugins` volume)
| Plugin | Purpose |
|---|---|
| [EssentialsX](https://essentialsx.net) | /home, /spawn, /tpa, /kit |
| [LuckPerms](https://luckperms.net) | Ranks & permissions |
| [CoreProtect](https://www.spigotmc.org/resources/coreprotect.8631/) | Anti-grief & block logging |

Download `.jar` files and upload them to your Railway volume via the **Volume** tab.
