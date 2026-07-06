# Perfect Selfbot

A powerful Discord selfbot built on `discord.py-self` with harassment tools, snipe system, quest automation, avatar lookup, server control, and a Flask web dashboard.

> ⚠️ **Disclaimer:** Selfbots violate Discord's Terms of Service. Use entirely at your own risk.

---

## Table of Contents

- [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Replit](#replit)
  - [VPS / Bare Linux Server](#vps--bare-linux-server)
  - [Docker](#docker)
  - [Railway / Render / Fly.io](#railway--render--flyio)
- [Commands](#commands)
- [Key Features](#key-features)

---

## Setup

### Environment Variables

These must be set before running. **Never put them in code or commit them to git.**

| Variable | Required | Description |
|---|---|---|
| `TOKEN` | ✅ Yes | Your Discord account token |
| `OWNER_ID` | ✅ Yes | Your Discord user ID (right-click yourself → Copy ID) |
| `DATABASE_URL` | ❌ No | PostgreSQL URL — falls back to SQLite if not set |
| `SESSION_SECRET` | ❌ No | Flask session secret — any random string |
| `APP_URL` | ❌ No | Your public URL (used in the 24/7 setup page) |

---

### Replit

1. Open **Secrets** (🔒 icon in the sidebar)
2. Add `TOKEN` and `OWNER_ID`
3. Hit **Run** — the bot and web dashboard start automatically

---

### VPS / Bare Linux Server

```bash
# 1. Clone the repo
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. Install Python 3.11+ and FFmpeg
sudo apt update && sudo apt install -y python3.11 python3-pip ffmpeg

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your environment variables
cp .env.example .env
nano .env          # fill in TOKEN and OWNER_ID

# 5. Start everything (bot + web dashboard)
chmod +x start.sh
./start.sh
```

Web dashboard will be available at `http://your-server-ip:5000`

To keep it running after logout use `screen` or `tmux`:

```bash
screen -S selfbot
./start.sh
# Press Ctrl+A then D to detach
```

---

### Docker

**Quickest way to deploy anywhere that supports Docker.**

```bash
# 1. Clone the repo
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. Fill in secrets
cp .env.example .env
nano .env          # fill in TOKEN and OWNER_ID

# 3. Build and start (bot + PostgreSQL auto-included)
docker compose up -d

# View logs
docker compose logs -f bot
```

To stop:
```bash
docker compose down
```

---

### Railway / Render / Fly.io

1. Connect your GitHub repo to the platform
2. Set these environment variables in the platform dashboard:

```
TOKEN          = your Discord token
OWNER_ID       = your Discord user ID
SESSION_SECRET = any random string
```

3. Deploy — `start.sh` runs automatically as the start command

> For **Railway**: set Start Command to `./start.sh`  
> For **Render**: set Start Command to `bash start.sh`  
> For **Fly.io**: the `Dockerfile` is picked up automatically

---

## Commands

### 🖼️ Avatar & Profile

| Command | Description |
|---|---|
| `-av` | Your own avatar + banner at max resolution |
| `-av @user` | Anyone's avatar + banner |
| `-av <user_id>` | Lookup by bare user ID |

---

### 😤 Harassment

| Command | Description |
|---|---|
| `-drown @user` | Auto-insult on every message (English + Hindi + Hinglish) |
| `-drownenglish @user` | English insults only |
| `-drownhindi @user` | Hindi insults only |
| `-drownhinglish @user` | Hinglish insults only |
| `-stop @user` | Stop drowning a user |
| `-debate @user` | Savage Hinglish comeback on every message |
| `-stopd @user` | Stop debating a user |
| `-spam <msg>` | Rapid message spam |
| `-stops` | Stop spam |
| `-troll @user` | Reply to every message with troll responses |
| `-stoptroll [@user]` | Stop trolling (no mention = stop all) |
| `-copycat @user` | Mirror everything a user types |
| `-stopcopycat [@user]` | Stop copycatting (no mention = stop all) |

> All harassment commands respect the **whitelist** — whitelisted users are immune.

---

### 🔊 Voice

| Command | Description |
|---|---|
| `-annoy @user` | Continuously drag user through voice channels + mute/deafen |
| `-stopannoy @user` | Stop annoying a user |

---

### 💬 Group Chat

| Command | Description |
|---|---|
| `-jija <msg>` | Ultra-fast group chat name spam (0.02s intervals + burst mode) |
| `-stopjija` | Stop jija |
| `-gcspam` | Create 3-person group chats with all saved targets |
| `-stopgcspam` | Stop gcspam |

---

### 🎯 Target System

| Command | Description |
|---|---|
| `-target @user` | Add a user to your target list |
| `-list` | View all saved targets |
| `-cleartargets` | Clear all targets |

---

### 🛡️ Whitelist

| Command | Description |
|---|---|
| `-wl @user add` | Protect a user from all harassment features |
| `-wl @user remove` | Remove whitelist protection |
| `-wl list` | View all whitelisted users |
| `-clearwhitelist` | Clear entire whitelist |

---

### 🕵️ Snipe

| Command | Description |
|---|---|
| `-snipe` | Show last deleted message in this channel |
| `-esnipe` | Show last edited message (before/after) |

---

### 🧹 Channel Tools

| Command | Description |
|---|---|
| `-purge [amount]` | Delete your own messages (up to 200) |
| `-nuke` | Clone channel then delete original |
| `-invite [uses] [hours]` | Generate a server invite link |
| `-type [seconds]` | Spam typing indicator (up to 300s) |
| `-stoptype` | Stop typing spam |

---

### 📨 Mass Actions

| Command | Description |
|---|---|
| `-massdm <msg>` | DM every non-bot member of the server |
| `-stopmassdm` | Stop an ongoing mass DM |

---

### 📊 Info & Lookup

| Command | Description |
|---|---|
| `-uinfo [@user]` | Full user profile — ID, creation date, badges, avatar |
| `-sinfo` | Full server stats — members, channels, roles, boosts |
| `-checktoken <token>` | Validate any Discord token and show account info |
| `-ping` | Latency check |

---

### 💤 AFK

| Command | Description |
|---|---|
| `-afk [message]` | Go AFK — auto-replies to all mentions and DMs |
| `-removeafk` | Come back from AFK, shows duration |

> AFK is removed automatically when you send any message.

---

### 😀 Auto React

| Command | Description |
|---|---|
| `-react @user <emoji>` | Auto-react to a user's every message |
| `-stopreact @user` | Stop auto-reacting |

---

### 🎮 Discord Quests

| Command | Description |
|---|---|
| `-quests` | List all active quests with live progress bars |
| `-autoquest` | Auto-enroll + complete all quests via heartbeat loop + claim rewards |
| `-stopquest` | Stop an ongoing auto quest run |

---

### 📡 Streaming Status

| Command | Description |
|---|---|
| `-stream <activity>` | Set a streaming status |
| `-streamall <msgs>` | Stream across multiple tokens |
| `-streamoff` | Remove streaming status |
| `-streamrotate <s1,s2,s3>` | Rotate streaming statuses on a schedule |
| `-streamrotateoff` | Stop rotation |
| `-streamstatus` | Show current stream status |

---

### 🏠 Server Templates

| Command | Description |
|---|---|
| `-copytemplate <name>` | Save current server layout as a named template |
| `-applytemplate <name>` | Wipe server and rebuild from saved template |
| `-listtemplates` | List all saved templates |
| `-deletetemplate <name>` | Delete a saved template |

---

### 🔐 Access Control

| Command | Description |
|---|---|
| `-access @user` | Grant limited bot access to another user |
| `-removeaccess @user` | Revoke access from a user |
| `-listaccess` | List all authorized users |
| `-removemyaccess` | Remove your own access |

---

### 🚪 Auto Onboarding

Fires **automatically** the moment the bot joins any server — no command needed. Completes:
1. **Member verification** — accepts rules/terms screening
2. **Onboarding prompts** — selects required roles/channels

| Command | Description |
|---|---|
| `-onboard [guild_id]` | Manually re-trigger onboarding on any server |

---

### 📋 Misc

| Command | Description |
|---|---|
| `-history [limit]` | View recent command usage log |
| `-help` | Paginated command menu (8 pages) |
| `-help <1-8>` | Jump to a specific help page |

---

## Key Features

- **Platform agnostic** — runs on Replit, VPS, Docker, Railway, Render, Fly.io, or any Linux host
- **Whitelist protection** — whitelisted users are immune to all harassment commands
- **Anti-detection** — human-like delays (0.1–0.5s), rate limiting, activity rotation, anti-ban loop
- **Owner-only access** — all destructive commands locked to `OWNER_ID` env var
- **Authorized users** — limited command access for trusted users via `-access`
- **Auto onboarding** — automatically completes Discord server verification on join
- **Quest heartbeat** — spoofs Discord desktop client headers to complete quests via API
- **Snipe cache** — persists last deleted/edited message per channel in memory
- **Persistent storage** — PostgreSQL (or SQLite fallback) via SQLAlchemy for logs, whitelist, targets
- **Web dashboard** — Flask app on port 5000 with real-time analytics and bot control

---

## Files to Upload to GitHub

```
main.py
app.py
models.py
wsgi.py
requirements.txt
Dockerfile
docker-compose.yml
.dockerignore
start.sh
.env.example
.gitignore
README.md
```

> **Do NOT upload:** `.env`, `authorized_users.txt`, `*.db`, `.replit`, `replit.nix`, `replit.md`, `pyproject.toml`
