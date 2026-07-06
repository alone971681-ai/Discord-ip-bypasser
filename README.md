# Discord Account Keeper — IP-Safe Edition

Routes all Discord traffic through a residential proxy so new accounts survive
on Replit without getting banned by Discord's IP detection.

## Architecture

| File | Purpose |
|---|---|
| `main.py` | Discord bot — proxy routing, telemetry, presence rotation, commands |
| `app.py`  | Flask status dashboard on port 5000 (keeps Replit alive) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for all environment variables |

## How to run

1. Open **Secrets** (🔒 in sidebar) and add:
   - `TOKEN` — your Discord account token
   - `OWNER_ID` — your Discord user ID
   - `PROXY_URL` — a residential/ISP proxy URL (**required** to avoid IP bans)
2. Hit **Run**

## Why a proxy is required

Replit runs on Google Cloud (a datacenter). Discord's ML system hard-flags new
accounts that connect from datacenter IPs. A residential or ISP proxy gives the
account a home-user IP that Discord trusts.

**Proxy providers (residential only):**
- [IPRoyal](https://iproyal.com) — ISP sticky ~$2.40/IP/month ✅ cheapest
- [Brightdata](https://brightdata.com) — ~$8.40/GB residential
- [Oxylabs](https://oxylabs.io) — enterprise

**Phone verification (real SIM numbers, not VoIP):**
- [sms-activate.org](https://sms-activate.org) — ~$0.20-0.50 per US number

## Bot commands

| Command | Description |
|---|---|
| `-ping` | Latency check |
| `-ip` | Show the IP Discord actually sees |
| `-status` | Full anti-ban protection report |
| `-warmup [hours]` | Simulate human activity on a fresh account (run this first!) |

## Anti-ban features built in

- **Proxy routing** — gateway + all HTTP through `PROXY_URL`
- **Dynamic X-Super-Properties** — Chrome 136, randomised build number per request
- **Telemetry heartbeat** — sends Discord science events every 5-10 min
- **Presence rotation** — status + activity changes every 20-60 min
- **Human-like warmup** — `-warmup` command for fresh accounts

## User preferences

- Keep the codebase minimal and focused on the proxy/anti-ban use case.
- No unnecessary dependencies.
