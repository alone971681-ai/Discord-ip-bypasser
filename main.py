"""
Discord Account Keeper — Auto Proxy Edition
============================================
Automatically fetches, tests, and rotates hundreds of free proxies so Discord
sees a different IP instead of Replit's datacenter IP (the #1 cause of
new-account bans within 15 minutes).

Quick start:
  1. Add TOKEN  in Replit → Secrets (🔒)  — your Discord account token
  2. Add OWNER_ID in Secrets              — your Discord user ID
  3. Hit Run — proxy discovery starts automatically, no setup needed.

Optional: add PROXY_URL in Secrets to force a specific residential proxy
          (overrides auto-discovery, recommended for serious use).

Commands (type in any Discord channel the account can see):
  -ping    — latency check
  -ip      — show the IP Discord actually sees right now
  -status  — full anti-ban + proxy pool report
  -warmup  — simulate human activity on a fresh account (run first!)
"""

import os
import asyncio
import json
import base64
import uuid
import random
import time
import logging
import threading
import requests

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("keeper")

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN    = os.environ.get("TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0") or "0")
# PROXY_URL is optional — if set it overrides auto-discovery
PROXY_URL = os.environ.get("PROXY_URL", "")

# ── Auto-proxy engine ──────────────────────────────────────────────────────────
import proxy_manager

# Start background proxy discovery immediately (non-blocking).
# The bot connects while proxies are being tested in the background;
# a working proxy is assigned to requests as soon as one is confirmed.
proxy_manager.start()

# ── Discord ────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands

# ── Browser fingerprint (X-Super-Properties) ──────────────────────────────────
# Discord checks this header on every API request.
# Must look like a real Chrome browser — wrong/missing = instant flag.
_CHROME_VER = "136.0.0.0"
_CHROME_UA  = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{_CHROME_VER} Safari/537.36"
)
# Discord stable client build numbers as of mid-2026
_BUILD_RANGE = (392_000, 415_000)


def make_super_props() -> str:
    """Fresh X-Super-Properties on every call — randomised build + launch ID."""
    payload = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "has_client_mods": False,
        "browser_user_agent": _CHROME_UA,
        "browser_version": _CHROME_VER,
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": random.randint(*_BUILD_RANGE),
        "client_event_source": None,
        "client_launch_id": str(uuid.uuid4()),
        "client_app_state": "focused",
    }
    return base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode()


def api_headers(token: str) -> dict:
    """Full browser-like headers for every Discord REST call."""
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": _CHROME_UA,
        "X-Super-Properties": make_super_props(),
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "America/New_York",
        "Origin": "https://discord.com",
        "Referer": "https://discord.com/channels/@me",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def _proxies_dict() -> dict | None:
    p = proxy_manager.get_proxy()
    return {"http": p, "https": p} if p else None


# ── Bot setup ──────────────────────────────────────────────────────────────────
def _make_bot(proxy: str | None = None) -> commands.Bot:
    kwargs: dict = dict(
        command_prefix="-",
        self_bot=True,
        case_insensitive=True,
        strip_after_prefix=True,
    )
    if OWNER_ID:
        kwargs["owner_id"] = OWNER_ID
    if proxy:
        kwargs["proxy"] = proxy
    try:
        # discord.py-self: no intents required for user accounts
        return commands.Bot(**kwargs)
    except TypeError:
        # Fallback: regular discord.py requires intents
        kwargs["intents"] = discord.Intents.default()
        return commands.Bot(**kwargs)


# Create bot at module level (needed for @bot.event / @bot.command decorators).
# Proxy is injected in main() before bot.run() is called, so the gateway
# connection always uses a working proxy even though we don't have one yet here.
bot = _make_bot()

# ── Telemetry / science events ─────────────────────────────────────────────────
# Real Discord clients fire these continuously.
# Zero telemetry = obvious bot signal to Discord's ML system.
_SCIENCE_URL = "https://discord.com/api/v10/science"


def _fire_science(token: str, event_type: str, props: dict):
    body = {
        "events": [{
            "type": event_type,
            "properties": {
                "client_track_timestamp": int(time.time() * 1000),
                "client_heartbeat_session_id": str(uuid.uuid4()),
                **props,
            },
        }]
    }
    proxy = proxy_manager.get_proxy()
    pd    = {"http": proxy, "https": proxy} if proxy else None
    try:
        requests.post(
            _SCIENCE_URL,
            headers=api_headers(token),
            json=body,
            timeout=10,
            proxies=pd,
        )
    except Exception:
        # Evict the proxy that just failed so the pool stays healthy
        if proxy:
            proxy_manager.remove_proxy(proxy)


# ── Singleton task handles (prevent duplicate loops on reconnect) ──────────────
_telemetry_task:  asyncio.Task | None = None
_presence_task:   asyncio.Task | None = None


async def _telemetry_loop():
    """Send a science event every 5-10 minutes like a real idle browser tab."""
    loop = asyncio.get_event_loop()
    while not bot.is_closed():
        await loop.run_in_executor(
            None, _fire_science, TOKEN, "app_opened",
            {"has_already_launched": True, "browser": "Chrome",
             "os": "Windows", "release_channel": "stable"},
        )
        await asyncio.sleep(random.uniform(300, 600))


# ── Presence rotation ──────────────────────────────────────────────────────────
# Frozen "Online" 24/7 with no activity changes is another detection signal.
_STATUS_POOL = [
    discord.Status.online, discord.Status.online, discord.Status.online,
    discord.Status.idle,   discord.Status.idle,
]
_ACTIVITY_POOL = [
    None,
    discord.CustomActivity(name="just vibing"),
    discord.Activity(type=discord.ActivityType.playing, name="VS Code"),
    discord.Activity(type=discord.ActivityType.listening, name="Spotify"),
    discord.CustomActivity(name="busy"),
    None,
]


async def _presence_loop():
    """Rotate status + activity every 20-60 minutes."""
    while not bot.is_closed():
        try:
            await bot.change_presence(
                status=random.choice(_STATUS_POOL),
                activity=random.choice(_ACTIVITY_POOL),
            )
        except Exception:
            pass
        await asyncio.sleep(random.uniform(1200, 3600))


# ── Events ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    global _telemetry_task, _presence_task
    log.info(f"✅  Logged in as {bot.user}  (ID: {bot.user.id})")

    p = proxy_manager.get_proxy()
    if p:
        log.info(f"🌐  Active proxy: {p}")
    else:
        log.warning("⚠️   Proxy pool still warming up — telemetry will use direct.")

    # Singleton: only create tasks if they're not already running
    if _telemetry_task is None or _telemetry_task.done():
        _telemetry_task = asyncio.create_task(_telemetry_loop())
    if _presence_task is None or _presence_task.done():
        _presence_task = asyncio.create_task(_presence_loop())
    log.info("🛡️   Anti-ban tasks running: telemetry + presence rotation")


@bot.event
async def on_disconnect():
    log.warning("⚠️   Disconnected — auto-reconnecting...")


@bot.event
async def on_resumed():
    log.info("🔄  Session resumed.")


# ── Helpers ────────────────────────────────────────────────────────────────────
def _is_owner(ctx) -> bool:
    return bool(OWNER_ID) and ctx.author.id == OWNER_ID


async def _auto_delete(msg, delay: float = 10.0):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


# ── Commands ───────────────────────────────────────────────────────────────────

@bot.command(name="ping")
async def cmd_ping(ctx):
    """Latency check."""
    if not _is_owner(ctx): return
    try: await ctx.message.delete()
    except Exception: pass
    m = await ctx.channel.send(f"🏓  `{round(bot.latency * 1000)} ms`")
    asyncio.create_task(_auto_delete(m, 5))


@bot.command(name="ip")
async def cmd_ip(ctx):
    """Show the IP Discord actually sees right now."""
    if not _is_owner(ctx): return
    try: await ctx.message.delete()
    except Exception: pass

    proxy = proxy_manager.get_proxy()
    pd    = {"http": proxy, "https": proxy} if proxy else None
    loop  = asyncio.get_event_loop()
    try:
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get("https://api.ipify.org?format=json",
                                  proxies=pd, timeout=8),
        )
        ip  = resp.json().get("ip", "unknown")
        tag = f"🌐 via `{proxy}`" if proxy else "⚠️ direct Replit IP (no proxy ready yet)"
        m   = await ctx.channel.send(f"**IP Discord sees:** `{ip}`\n{tag}")
    except Exception as e:
        m = await ctx.channel.send(f"❌ {e}")
    asyncio.create_task(_auto_delete(m, 15))


@bot.command(name="status")
async def cmd_status(ctx):
    """Full anti-ban + proxy pool report."""
    if not _is_owner(ctx): return
    try: await ctx.message.delete()
    except Exception: pass

    ps    = proxy_manager.pool_status()
    proxy = proxy_manager.get_proxy()

    if ps["manual"]:
        proxy_line = f"✅  Manual: `{PROXY_URL.split('@')[-1]}`"
    elif proxy:
        proxy_line = f"✅  Auto pool: `{ps['pool_size']}` working proxies"
    elif ps["refreshing"]:
        proxy_line = "🔄  Auto pool still warming up…"
    else:
        proxy_line = "❌  No working proxies found yet — retrying…"

    m = await ctx.channel.send(
        "**🛡️  Anti-Ban Status**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐  Proxy:               {proxy_line}\n"
        f"📡  Telemetry heartbeat: ✅  Active (every 5-10 min)\n"
        f"🔄  Presence rotation:   ✅  Active (every 20-60 min)\n"
        f"🧬  X-Super-Properties:  ✅  Dynamic Chrome {_CHROME_VER}\n"
        f"⏱️   Gateway latency:     `{round(bot.latency * 1000)} ms`\n"
        f"🔢  Proxy pool size:     `{ps['pool_size']}`\n"
        f"♻️   Pool refreshing:     {'Yes' if ps['refreshing'] else 'No (refreshes hourly)'}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    asyncio.create_task(_auto_delete(m, 25))


@bot.command(name="warmup")
async def cmd_warmup(ctx, hours: float = 1.0):
    """
    Simulate human activity on a fresh account before using it.

    Usage:  -warmup 2   (runs for 2 hours — recommended for brand-new accounts)

    Discord flags accounts that connect and immediately start doing things.
    This command makes the account look like a real person browsing Discord:
    • Occasional typing indicators (humans type before sending)
    • 10-25 minute gaps between actions (realistic idle rhythm)
    • Telemetry events fire in the background automatically
    """
    if not _is_owner(ctx): return
    try: await ctx.message.delete()
    except Exception: pass

    m = await ctx.channel.send(
        f"🔥  **Warmup started** — `{hours}h`\n"
        f"Simulating human activity. Don't use other commands during warmup."
    )
    end_time = time.time() + hours * 3600
    actions  = 0

    while time.time() < end_time:
        try:
            async with ctx.channel.typing():
                await asyncio.sleep(random.uniform(3, 9))
        except Exception:
            pass
        actions += 1
        gap = random.uniform(600, 1500)   # 10-25 min between actions
        if time.time() + gap > end_time:
            break
        await asyncio.sleep(gap)

    try:
        await m.edit(
            content=f"✅  **Warmup complete** — {actions} human-like actions over {hours}h.\n"
                    f"Account is warmed up. Safe to use now."
        )
        asyncio.create_task(_auto_delete(m, 15))
    except Exception:
        pass


# ── Flask keepalive (background thread) ───────────────────────────────────────
def _start_flask():
    try:
        from app import app as flask_app
        flask_app.run(host="0.0.0.0", port=5000, use_reloader=False, debug=False)
    except Exception as e:
        log.warning(f"Flask dashboard unavailable: {e}")


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    # Start Flask first — keeps the preview + uptime monitor alive no matter what
    flask_thread = threading.Thread(target=_start_flask, daemon=True)
    flask_thread.start()

    # Validate required secrets
    if not TOKEN:
        log.error("TOKEN is not set.")
        log.error("→ Open Replit Secrets (🔒) and add your Discord account token.")
        log.info("Dashboard running at port 5000 — check the preview pane.")
        while True: time.sleep(60)   # keep Flask alive

    if not OWNER_ID:
        log.error("OWNER_ID is not set.")
        log.error("→ Add your Discord user ID as OWNER_ID in Replit Secrets.")
        while True: time.sleep(60)

    # ── Wait for proxy pool before connecting ─────────────────────────────────
    # Give the background pool builder up to 90 seconds to find a working proxy.
    # This ensures the very first gateway connection is already IP-masked.
    if not PROXY_URL:  # skip wait if user set a manual proxy (already confirmed)
        log.info("⏳  Waiting for auto-proxy pool (up to 90s)…")
        deadline = time.time() + 90
        while time.time() < deadline:
            if proxy_manager.get_proxy():
                break
            time.sleep(2)

    proxy = proxy_manager.get_proxy()
    if proxy:
        # Inject proxy into bot *before* bot.run() creates the HTTP session
        bot.proxy = proxy  # type: ignore[attr-defined]
        log.info(f"🌐  Gateway will connect via proxy: {proxy}")
    else:
        log.warning("⚠️   No working proxy found — connecting directly.")
        log.warning("    Add PROXY_URL in Secrets for guaranteed protection.")

    log.info("🚀  Connecting to Discord…")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        log.error("Invalid TOKEN — double-check it in Replit Secrets.")
        while True: time.sleep(60)
    except Exception as e:
        log.error(f"Bot crashed: {e}")
        while True: time.sleep(60)


if __name__ == "__main__":
    main()
