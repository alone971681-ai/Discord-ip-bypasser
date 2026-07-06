"""
Flask status dashboard — serves on port 5000.
Shows real-time bot and proxy pool health.
"""

import os
import time
import json
import proxy_manager
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret")

START_TIME = time.time()

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Account Keeper</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0f1117; color: #e2e8f0;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh; padding: 2rem;
    }
    .card {
      background: #1a1d27; border: 1px solid #2d3148; border-radius: 16px;
      padding: 2.5rem; max-width: 540px; width: 100%;
      box-shadow: 0 8px 32px rgba(0,0,0,.4);
    }
    h1 { font-size: 1.6rem; margin-bottom: .25rem; color: #a78bfa; }
    .sub { color: #64748b; font-size: .85rem; margin-bottom: 2rem; }
    .row {
      display: flex; justify-content: space-between; align-items: center;
      padding: .75rem 0; border-bottom: 1px solid #2d3148; font-size: .9rem;
    }
    .row:last-child { border-bottom: none; }
    .label { color: #94a3b8; }
    .badge { padding: .25rem .75rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }
    .ok   { background: #052e16; color: #4ade80; }
    .warn { background: #2d1600; color: #fb923c; }
    .bad  { background: #2d0000; color: #f87171; }
    .pool-list {
      margin-top: 1.25rem; background: #12151e; border: 1px solid #2d3148;
      border-radius: 10px; padding: 1rem; font-size: .78rem;
    }
    .pool-list h3 { color: #7c3aed; margin-bottom: .5rem; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; }
    .pool-list code { display: block; color: #a3e635; padding: .15rem 0; }
    .warn-box {
      margin-top: 1.5rem; padding: 1rem; background: #1c0a00;
      border: 1px solid #92400e; border-radius: 8px;
      font-size: .85rem; color: #fbbf24; line-height: 1.6;
    }
    .uptime { margin-top: 1.5rem; text-align: center; color: #475569; font-size: .8rem; }
    #status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
                  background: #4ade80; margin-right: 6px; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  </style>
</head>
<body>
<div class="card" id="card">
  <h1>🛡️ Account Keeper</h1>
  <p class="sub"><span id="status-dot"></span>Live status — updates every 10s</p>

  <div class="row">
    <span class="label">Bot process</span>
    <span class="badge ok">✅ Running</span>
  </div>
  <div class="row">
    <span class="label">Discord token</span>
    <span id="token-badge" class="badge">…</span>
  </div>
  <div class="row">
    <span class="label">Proxy</span>
    <span id="proxy-badge" class="badge">…</span>
  </div>
  <div class="row">
    <span class="label">Pool size</span>
    <span id="pool-size" class="badge ok">…</span>
  </div>
  <div class="row">
    <span class="label">SOCKS5 / HTTP</span>
    <span id="pool-types" class="badge ok">…</span>
  </div>
  <div class="row">
    <span class="label">Avg latency</span>
    <span id="pool-latency" class="badge ok">…</span>
  </div>
  <div class="row">
    <span class="label">Pool refreshing</span>
    <span id="pool-refresh" class="badge">…</span>
  </div>
  <div class="row">
    <span class="label">Telemetry heartbeat</span>
    <span class="badge ok">✅ Active (every 5–10 min)</span>
  </div>
  <div class="row">
    <span class="label">Presence rotation</span>
    <span class="badge ok">✅ Active (every 20–60 min)</span>
  </div>
  <div class="row">
    <span class="label">X-Super-Properties</span>
    <span class="badge ok">✅ Dynamic Chrome 136</span>
  </div>

  <div id="pool-box" class="pool-list" style="display:none">
    <h3>Working proxies in pool</h3>
    <div id="pool-entries"></div>
  </div>

  <div id="warn-box" class="warn-box" style="display:none">
    ⚠️ <strong>No proxy set</strong><br>
    New Discord accounts on Replit's datacenter IP get banned in ~15 min.
    Add <code>PROXY_URL</code> in <strong>Replit → Secrets (🔒)</strong>, e.g.:<br>
    <code style="color:#a3e635">http://user:pass@proxy-host:port</code>
  </div>

  <p class="uptime" id="uptime-line">Uptime: …</p>
</div>

<script>
function fmt(s) {
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  return h ? h+'h '+m+'m '+sec+'s' : m ? m+'m '+sec+'s' : sec+'s';
}
async function refresh() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();

    // token
    const tb = document.getElementById('token-badge');
    tb.textContent = d.token ? '✅ Configured' : '❌ Missing — bot will not start';
    tb.className = 'badge ' + (d.token ? 'ok' : 'bad');

    // proxy
    const pb = document.getElementById('proxy-badge');
    if (d.manual_proxy) {
      pb.textContent = '✅ Manual: ' + d.proxy_display;
      pb.className = 'badge ok';
    } else if (d.pool_size > 0) {
      pb.textContent = '✅ Auto pool active';
      pb.className = 'badge ok';
    } else if (d.refreshing) {
      pb.textContent = '🔄 Discovering proxies…';
      pb.className = 'badge warn';
    } else {
      pb.textContent = '❌ None found yet';
      pb.className = 'badge bad';
    }

    // pool size
    const ps = document.getElementById('pool-size');
    ps.textContent = d.pool_size + ' working';
    ps.className = 'badge ' + (d.pool_size >= 3 ? 'ok' : d.pool_size > 0 ? 'warn' : 'bad');

    // socks5 / http breakdown
    const pt = document.getElementById('pool-types');
    pt.textContent = d.socks5_count + ' SOCKS5  /  ' + d.http_count + ' HTTP';
    pt.className = 'badge ' + (d.socks5_count > 0 ? 'ok' : 'warn');

    // avg latency
    const pl = document.getElementById('pool-latency');
    pl.textContent = d.pool_size ? d.avg_latency + ' ms avg' : '—';
    pl.className = 'badge ' + (d.avg_latency < 500 ? 'ok' : d.avg_latency < 1500 ? 'warn' : 'bad');

    // refreshing
    const pr = document.getElementById('pool-refresh');
    pr.textContent = d.refreshing ? '🔄 Yes' : 'No (auto every 1h)';
    pr.className = 'badge ' + (d.refreshing ? 'warn' : 'ok');

    // pool list
    const box = document.getElementById('pool-box');
    const entries = document.getElementById('pool-entries');
    if (d.pool_sample && d.pool_sample.length) {
      box.style.display = 'block';
      entries.innerHTML = d.pool_sample.map(p => '<code>' + p + '</code>').join('');
      if (d.pool_size > d.pool_sample.length)
        entries.innerHTML += '<code style="color:#64748b">… and ' + (d.pool_size - d.pool_sample.length) + ' more</code>';
    } else {
      box.style.display = 'none';
    }

    // warn box
    document.getElementById('warn-box').style.display =
      (!d.manual_proxy && d.pool_size === 0 && !d.refreshing) ? 'block' : 'none';

    // uptime
    document.getElementById('uptime-line').textContent = 'Uptime: ' + fmt(Math.floor(d.uptime));
  } catch(e) { /* server restarting */ }
}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


def _fmt_uptime(s: float) -> str:
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h: return f"{h}h {m}m {sec}s"
    if m: return f"{m}m {sec}s"
    return f"{sec}s"


@app.route("/")
def index():
    return render_template_string(_HTML)


@app.route("/api/status")
def api_status():
    ps = proxy_manager.pool_status()
    proxy_raw = os.environ.get("PROXY_URL", "")
    proxy_display = proxy_raw.split("@")[-1] if "@" in proxy_raw else proxy_raw

    return jsonify({
        "token":         bool(os.environ.get("TOKEN")),
        "manual_proxy":  ps["manual"],
        "proxy_display": proxy_display or None,
        "pool_size":     ps["pool_size"],
        "socks5_count":  ps["socks5_count"],
        "http_count":    ps["http_count"],
        "avg_latency":   ps["avg_latency"],
        "refreshing":    ps["refreshing"],
        "pool_sample":   ps["sample"],
        "uptime":        time.time() - START_TIME,
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "uptime": time.time() - START_TIME})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
