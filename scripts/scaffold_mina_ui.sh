#!/usr/bin/env bash
set -euo pipefail

# =========================================
# Mina UI Scaffolder
# - Creates routes/pages.py + templates + css
# - Default: empty TODO stubs
# - --full  : write full premium templates
# - --force : overwrite if files exist
# =========================================

ROOT_DIR="$(pwd)"
FULL=0
FORCE=0

usage() {
  cat <<'USAGE'
Usage:
  scripts/scaffold_mina_ui.sh [--full] [--force]

Options:
  --full   Write full example content (premium templates/CSS) into files.
  --force  Overwrite files if they already exist.
Notes:
  - Default creates TODO stubs so you can paste your own content.
  - Nothing here touches your transcription pipeline.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $arg"; usage; exit 1 ;;
  esac
done

ensure_dir() { mkdir -p "$1"; }

write_file() {
  local path="$1"; shift
  local content="$*"
  if [[ -e "$path" && $FORCE -eq 0 ]]; then
    echo "SKIP: $path exists (use --force to overwrite)"
    return 0
  fi
  printf "%s" "$content" > "$path"
  echo "WROTE: $path"
}

append_hint_if_missing() {
  # Gently remind user to register pages_bp if needed
  local app_file="$1"
  if [[ -f "$app_file" ]]; then
    if ! grep -q "from routes.pages import pages_bp" "$app_file"; then
      echo "HINT: Add the following to $app_file near other blueprints:"
      echo "      from routes.pages import pages_bp"
      echo "      app.register_blueprint(pages_bp)"
    fi
  fi
}

# -----------------------------------------
# 1) Directories
# -----------------------------------------
ensure_dir "$ROOT_DIR/routes"
ensure_dir "$ROOT_DIR/templates"
ensure_dir "$ROOT_DIR/static/css"
ensure_dir "$ROOT_DIR/scripts"

# -----------------------------------------
# 2) pages.py
# -----------------------------------------
if [[ $FULL -eq 1 ]]; then
read -r -d '' PAGES <<'PY'
from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)

@pages_bp.get("/")
def home():
    return redirect(url_for("pages.dashboard"))

@pages_bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@pages_bp.get("/live")
def live():
    return render_template("live.html")

@pages_bp.get("/meetings")
def meetings():
    try:
        return render_template("meetings.html")
    except Exception:
        return render_template("meetings_fallback.html")

@pages_bp.get("/tasks")
def tasks():
    try:
        return render_template("tasks.html")
    except Exception:
        return render_template("tasks_fallback.html")

@pages_bp.get("/calendar")
def calendar():
    return render_template("calendar.html")

@pages_bp.get("/settings")
def settings():
    try:
        return render_template("settings.html")
    except Exception:
        return render_template("settings_fallback.html")
PY
else
read -r -d '' PAGES <<'PY'
# routes/pages.py
from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)

@pages_bp.get("/")
def home():
    return redirect(url_for("pages.dashboard"))

@pages_bp.get("/dashboard")
def dashboard():
    # TODO: create templates/dashboard.html
    return render_template("dashboard.html")

@pages_bp.get("/live")
def live():
    # NOTE: this uses your existing working live.html
    return render_template("live.html")

@pages_bp.get("/meetings")
def meetings():
    try:
        return render_template("meetings.html")
    except Exception:
        return render_template("meetings_fallback.html")

@pages_bp.get("/tasks")
def tasks():
    try:
        return render_template("tasks.html")
    except Exception:
        return render_template("tasks_fallback.html")

@pages_bp.get("/calendar")
def calendar():
    # TODO: create templates/calendar.html
    return render_template("calendar.html")

@pages_bp.get("/settings")
def settings():
    try:
        return render_template("settings.html")
    except Exception:
        return render_template("settings_fallback.html")
PY
fi
write_file "$ROOT_DIR/routes/pages.py" "$PAGES"

# -----------------------------------------
# 3) CSS
# -----------------------------------------
if [[ $FULL -eq 1 ]]; then
read -r -d '' CSS <<'CSS'
:root{
  --bg:#0d0f12; --elev1:#12151b; --elev2:#0f1116; --stroke:#20242d;
  --muted:#9aa4b2; --brand:#6aa3ff; --brand-2:#6ef3d6;
  --ok:#27d980; --warn:#ffb454; --bad:#ff6b6b;
  --shadow:0 8px 30px rgba(0,0,0,.45); --radius:14px;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:#e7edf7;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{text-decoration:none;color:inherit}
.app{display:grid;grid-template-columns:260px 1fr;grid-template-rows:auto 1fr;grid-template-areas:"sidebar header" "sidebar main";height:100%}
.sidebar{grid-area:sidebar;background:linear-gradient(180deg,#0f131a,#0c0f14);border-right:1px solid var(--stroke);padding:14px 12px;position:relative}
.header{grid-area:header;display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--stroke);backdrop-filter:saturate(120%) blur(6px);background:#0e1116e6;position:sticky;top:0;z-index:5}
.main{grid-area:main;padding:26px 28px 40px;overflow:auto}
.brand{display:flex;align-items:center;gap:10px;padding:6px 10px;margin-bottom:10px}
.logo{width:28px;height:28px;border-radius:8px;background:radial-gradient(120% 120% at 20% 10%, #7db3ff 0%, #2a6fff 45%, #1834ff 90%);box-shadow:inset 0 0 0 2px #1a2a55}
.brand h1{font-size:18px;margin:0;letter-spacing:.3px}
.search-mini{position:relative;margin:8px 10px 14px}
.search-mini input{width:100%;background:#0b0e13;border:1px solid var(--stroke);color:#cfe1ff;border-radius:10px;padding:10px 34px 10px 12px;outline:none}
.search-mini kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:10px;color:#6b7685;background:#10141a;border:1px solid #1f2430;padding:2px 6px;border-radius:6px}
.nav{display:flex;flex-direction:column;gap:6px;padding:4px}
.nav a{display:flex;align-items:center;gap:10px;padding:10px;border-radius:10px;color:#cdd8e6;border:1px solid transparent}
.nav a:hover{background:#121726;border-color:#1f2a3d}
.nav a.active{background:linear-gradient(180deg,#11182b,#0f1422);border-color:#2b3750;box-shadow:0 6px 20px rgba(19,33,66,.25)}
.nav .badge{margin-left:auto;font-size:10px;color:#7fbef7;background:#0e223d;border:1px solid #224d7d;padding:2px 6px;border-radius:999px}
.footer{position:absolute;left:0;right:0;bottom:10px;padding:0 12px}
.user{display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--stroke);background:#10141b;border-radius:12px}
.user img{width:28px;height:28px;border-radius:10px}
.user .name{font-weight:600;font-size:12px}
.user .role{color:#9aa4b2;font-size:11px}
.search{position:relative;flex:1}
.search input{width:100%;background:#0c1016;border:1px solid var(--stroke);color:#cfe1ff;border-radius:12px;padding:12px 44px 12px 14px;outline:none}
.search .hint{position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:11px;color:#74819b;background:#10141a;border:1px solid #1f2430;padding:2px 8px;border-radius:6px}
.head-actions{display:flex;align-items:center;gap:8px}
.btn{display:inline-flex;align-items:center;justify-content:center;background:#121722;border:1px solid #24314a;color:#d9e6ff;border-radius:10px;padding:10px 12px;cursor:pointer}
.btn:hover{background:#162136}
.btn.cta{background:linear-gradient(90deg,#6aa3ff,#58e7ca);border:none;color:#06111a;font-weight:700}
.h1{font-size:28px;margin:6px 0 18px;letter-spacing:.2px}
.sub{color:#9aa4b2;font-size:12px}
.grid{display:grid;gap:16px}
.grid.cols-2{grid-template-columns:1.4fr .8fr}
.grid.cols-3{grid-template-columns:repeat(3,1fr)}
.card{background:var(--elev1);border:1px solid var(--stroke);border-radius:var(--radius);box-shadow:var(--shadow)}
.card .hd{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--stroke)}
.card .bd{padding:14px 16px}
.timeline{display:flex;gap:12px;flex-wrap:wrap}
.pill{background:#0f1522;border:1px solid #22304c;color:#bcd3ff;border-radius:12px;padding:10px;min-width:220px}
.pill .t{font-weight:600}
.pill .m{color:#9aa4b2;font-size:12px}
.meeting{border:1px solid #1f2733;background:#121721;border-radius:12px;padding:12px 14px;margin:10px 0}
.meeting .row{display:flex;gap:8px;justify-content:space-between;align-items:center}
.meeting .title{font-weight:700}
.tags{display:flex;gap:6px}
.tag{font-size:11px;padding:4px 8px;border-radius:999px;border:1px solid #2b3c58;background:#0f1a2a;color:#9ec4ff}
.kpi{display:flex;gap:16px}
.kpi .unit{flex:1;border:1px solid #1f2733;background:#121721;border-radius:12px;padding:12px}
.kpi .num{font-size:22px;font-weight:800}
.spark{height:36px;background:linear-gradient(180deg,#132033,#0f1724);border:1px solid #1d2a3b;border-radius:8px;margin-top:8px}
.kanban{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.col{border:1px solid #1f2733;background:#121721;border-radius:12px;min-height:120px}
.col .title{padding:10px 12px;border-bottom:1px solid #1f2733;font-weight:700}
.task{margin:10px;border:1px solid #223046;border-radius:10px;padding:10px;background:#0f1522}
.task .meta{display:flex;gap:8px;margin-top:6px}
.chip{font-size:10px;border:1px solid #2a3e5f;padding:2px 6px;border-radius:999px}
.calendar{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}
.day{border:1px solid var(--stroke);border-radius:10px;min-height:84px;background:#12131a;padding:8px}
CSS
else
read -r -d '' CSS <<'CSS'
/* static/css/mina_ui.css — TODO scaffold */
:root{ --bg:#0d0f12 }
body{ margin:0; background:var(--bg); color:#e7edf7; font-family:Inter,system-ui,sans-serif }
.app{ display:grid; grid-template-columns:260px 1fr; grid-template-rows:auto 1fr; height:100% }
.sidebar{ background:#0f131a; border-right:1px solid #20242d; padding:14px 12px }
.header{ display:flex; align-items:center; gap:12px; padding:14px 18px; border-bottom:1px solid #20242d; position:sticky; top:0 }
.main{ padding:26px 28px 40px }
.nav a{ display:block; padding:10px; color:#cdd8e6; border-radius:8px }
.nav a.active{ background:#11182b }
.card{ background:#12151b; border:1px solid #20242d; border-radius:12px; padding:14px; margin-bottom:12px }
.h1{ font-size:28px; margin:6px 0 18px }
CSS
fi
write_file "$ROOT_DIR/static/css/mina_ui.css" "$CSS"

# -----------------------------------------
# 4) Templates
# -----------------------------------------

if [[ $FULL -eq 1 ]]; then
# Full dashboard.html
read -r -d '' DASHBOARD <<'HTML'
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Mina — Dashboard</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand"><div class="logo"></div><h1>Mina</h1></div>
    <div class="search-mini"><input placeholder="Quick search…"/><kbd>⌘K</kbd></div>
    <nav class="nav">
      <a class="active" href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
      <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription <span class="badge">Live</span></a>
      <a href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
      <a href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
      <a href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
      <a href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
    </nav>
    <div class="footer">
      <div class="user"><img src="https://i.pravatar.cc/50?img=12" alt="">
        <div><div class="name">Alex Morgan</div><div class="role">Pro • Team</div></div>
      </div>
    </div>
  </aside>
  <header class="header">
    <div class="search"><input placeholder="Search meetings, people, actions…"/><span class="hint">⌘K</span></div>
    <div class="head-actions"><a class="btn" href="{{ url_for('pages.meetings') }}">+ New</a><a class="btn cta" href="{{ url_for('pages.live') }}">Start recording</a></div>
  </header>
  <main class="main">
    <div class="h1">Dashboard <span class="sub">capture → insight → action</span></div>
    <div class="grid cols-2">
      <section class="grid" style="gap:16px">
        <div class="card">
          <div class="hd"><strong>Recent timeline</strong><span class="sub">This week</span></div>
          <div class="bd timeline">
            <div class="pill"><div class="t">Design Review</div><div class="m">55m • 3 tasks • 1 decision</div></div>
            <div class="pill"><div class="t">Acme Call</div><div class="m">31m • shared</div></div>
            <div class="pill"><div class="t">Growth Sync</div><div class="m">42m • OKRs aligned</div></div>
          </div>
        </div>
        <div class="card">
          <div class="hd"><strong>Recent meetings</strong><span class="sub">Last 7 days</span></div>
          <div class="bd">
            <div class="meeting">
              <div class="row"><div class="title">Design Review — Recorder</div>
                <div class="tags"><span class="tag">completed</span><a class="tag" href="{{ url_for('pages.live') }}">Transcript</a><span class="tag">Share</span></div>
              </div>
              <div class="sub" style="margin-top:6px">AI: Waveform UI; hotkeys + resume-on-mic.</div>
            </div>
            <div class="meeting">
              <div class="row"><div class="title">Customer Call — Acme</div>
                <div class="tags"><span class="tag">shared</span><a class="tag" href="{{ url_for('pages.live') }}">Transcript</a></div>
              </div>
              <div class="sub" style="margin-top:6px">AI: Accuracy + Slack export; risk on delivery date.</div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="hd"><strong>Insights</strong><span class="sub">Week to date</span></div>
          <div class="bd kpi">
            <div class="unit"><div class="sub">Meetings</div><div class="num">5</div><div class="spark"></div></div>
            <div class="unit"><div class="sub">Recorded</div><div class="num">3h 20m</div><div class="spark"></div></div>
            <div class="unit"><div class="sub">Talk ratio</div><div class="num">65/35</div><div class="spark"></div></div>
            <div class="unit"><div class="sub">Sentiment</div><div class="num">🙂 ↑</div><div class="spark"></div></div>
          </div>
        </div>
      </section>
      <section class="grid" style="gap:16px">
        <div class="card">
          <div class="hd"><strong>Tasks</strong><span class="sub">Linked to conversations</span></div>
          <div class="bd kanban">
            <div class="col"><div class="title">To do</div>
              <div class="task">Prep Q3 report<div class="meta"><span class="chip" style="border-color:#4c3e1d;color:#ffcf6d">Due Fri</span></div></div>
              <div class="task">Collect pricing feedback<div class="meta"><span class="chip">Backlog</span></div></div>
            </div>
            <div class="col"><div class="title">Doing</div>
              <div class="task">Tune summarizer prompts<div class="meta"><span class="chip">In progress</span></div></div>
            </div>
            <div class="col"><div class="title">Done</div>
              <div class="task">Export page polish<div class="meta"><span class="chip" style="border-color:#2a5b46;color:#8ef2be">Done</span></div></div>
            </div>
          </div>
        </div>
        <div class="card"><div class="hd"><strong>Quick actions</strong></div>
          <div class="bd"><a class="btn cta" href="{{ url_for('pages.live') }}" style="width:100%">🎙 Start recording</a></div>
        </div>
      </section>
    </div>
  </main>
</div>
</body></html>
HTML
else
read -r -d '' DASHBOARD <<'HTML'
<!-- templates/dashboard.html (stub) -->
<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Mina — Dashboard</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar"><div class="brand"><div class="logo"></div><h1>Mina</h1></div>
      <nav class="nav">
        <a class="active" href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
        <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription</a>
        <a href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
        <a href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
        <a href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
        <a href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
      </nav>
    </aside>
    <header class="header"><div class="search"><input placeholder="Search…"></div></header>
    <main class="main">
      <div class="h1">Dashboard</div>
      <div class="card">TODO: paste the premium dashboard markup here.</div>
    </main>
  </div>
</body></html>
HTML
fi
write_file "$ROOT_DIR/templates/dashboard.html" "$DASHBOARD"

# calendar.html
if [[ $FULL -eq 1 ]]; then
read -r -d '' CAL <<'HTML'
<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Mina — Calendar</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><div class="logo"></div><h1>Mina</h1></div>
      <div class="search-mini"><input placeholder="Quick search…"/><kbd>⌘K</kbd></div>
      <nav class="nav">
        <a href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
        <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription</a>
        <a href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
        <a href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
        <a class="active" href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
        <a href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
      </nav>
    </aside>
    <header class="header">
      <div class="search"><input placeholder="Search meetings, people, actions…"/><span class="hint">⌘K</span></div>
      <div class="head-actions"><a class="btn" href="{{ url_for('pages.meetings') }}">+ New</a><a class="btn cta" href="{{ url_for('pages.live') }}">Start recording</a></div>
    </header>
    <main class="main">
      <div class="h1">Calendar <span class="sub">agenda • week • month</span></div>
      <div class="card" style="margin-bottom:14px">
        <div class="hd"><div><a class="btn" href="#">‹</a><a class="btn" href="#">›</a></div><span class="sub">September 2025</span><a class="btn cta" href="{{ url_for('pages.live') }}">🎙 Start from next event</a></div>
        <div class="bd"><div class="calendar">{% for i in range(1,31) %}<div class="day">{{ i }}</div>{% endfor %}</div></div>
      </div>
    </main>
  </div>
</body></html>
HTML
else
read -r -d '' CAL <<'HTML'
<!-- templates/calendar.html (stub) -->
<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Mina — Calendar</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar"><div class="brand"><div class="logo"></div><h1>Mina</h1></div></aside>
    <header class="header"><div class="search"><input placeholder="Search…"></div></header>
    <main class="main">
      <div class="h1">Calendar</div>
      <div class="card">TODO: paste the premium calendar markup here.</div>
    </main>
  </div>
</body></html>
HTML
fi
write_file "$ROOT_DIR/templates/calendar.html" "$CAL"

# meetings_fallback.html
read -r -d '' MEET <<'HTML'
<!doctype html>
<html><head>
  <meta charset="utf-8"><title>Mina — Meetings</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar"><div class="brand"><div class="logo"></div><h1>Mina</h1></div>
      <nav class="nav">
        <a href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
        <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription</a>
        <a class="active" href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
        <a href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
        <a href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
        <a href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
      </nav>
    </aside>
    <header class="header"><div class="search"><input placeholder="Search…"><span class="hint">⌘K</span></div></header>
    <main class="main">
      <div class="h1">Meeting library <span class="sub">Fallback view</span></div>
      <div class="grid cols-3">
        <div class="card"><div class="hd"><strong>Design Review</strong><span class="sub">55m • 3 speakers</span></div><div class="bd">Decisions on UI; 3 tasks</div></div>
        <div class="card"><div class="hd"><strong>Customer Call</strong><span class="sub">31m • 2 speakers</span></div><div class="bd">Accuracy + Slack export requested</div></div>
        <div class="card"><div class="hd"><strong>Weekly Sync</strong><span class="sub">42m • 5 speakers</span></div><div class="bd">Spend ramp and KPI targets</div></div>
      </div>
    </main>
  </div>
</body></html>
HTML
write_file "$ROOT_DIR/templates/meetings_fallback.html" "$MEET"

# tasks_fallback.html
read -r -d '' TASKS <<'HTML'
<!doctype html>
<html><head>
  <meta charset="utf-8"><title>Mina — Tasks</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar"><div class="brand"><div class="logo"></div><h1>Mina</h1></div>
      <nav class="nav">
        <a href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
        <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription</a>
        <a href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
        <a class="active" href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
        <a href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
        <a href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
      </nav>
    </aside>
    <header class="header"><div class="search"><input placeholder="Search…"><span class="hint">⌘K</span></div></header>
    <main class="main">
      <div class="h1">Tasks <span class="sub">Fallback view</span></div>
      <div class="kanban">
        <div class="col"><div class="title">To do</div><div class="task">Prep Q3 report</div></div>
        <div class="col"><div class="title">Doing</div><div class="task">Tune summarizer prompts</div></div>
        <div class="col"><div class="title">Done</div><div class="task">Export page polish</div></div>
      </div>
    </main>
  </div>
</body></html>
HTML
write_file "$ROOT_DIR/templates/tasks_fallback.html" "$TASKS"

# settings_fallback.html
read -r -d '' SETTINGS <<'HTML'
<!doctype html>
<html><head>
  <meta charset="utf-8"><title>Mina — Settings</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/mina_ui.css') }}">
</head><body>
  <div class="app">
    <aside class="sidebar"><div class="brand"><div class="logo"></div><h1>Mina</h1></div>
      <nav class="nav">
        <a href="{{ url_for('pages.dashboard') }}">🏠 Dashboard</a>
        <a href="{{ url_for('pages.live') }}">🎙️ Live Transcription</a>
        <a href="{{ url_for('pages.meetings') }}">📅 Meeting Library</a>
        <a href="{{ url_for('pages.tasks') }}">✅ Tasks</a>
        <a href="{{ url_for('pages.calendar') }}">📆 Calendar</a>
        <a class="active" href="{{ url_for('pages.settings') }}">⚙️ Settings</a>
      </nav>
    </aside>
    <header class="header"><div class="search"><input placeholder="Search…"><span class="hint">⌘K</span></div></header>
    <main class="main">
      <div class="h1">Settings <span class="sub">Fallback view</span></div>
      <div class="grid" style="grid-template-columns:1fr 1fr">
        <div class="card"><div class="hd"><strong>Preferences</strong></div><div class="bd"><p class="sub">Auto-summaries on meeting end</p><p class="sub">Auto-tasks from decisions</p><p class="sub">Theme: Dark</p></div></div>
        <div class="card"><div class="hd"><strong>Account & plan</strong></div><div class="bd"><p class="sub">Email: alex@mina.app</p><p class="sub">Plan: Pro</p></div></div>
      </div>
    </main>
  </div>
</body></html>
HTML
write_file "$ROOT_DIR/templates/settings_fallback.html" "$SETTINGS"

# -----------------------------------------
# 5) Hints
# -----------------------------------------
echo
echo "Scaffold complete."
append_hint_if_missing "$ROOT_DIR/app.py"
append_hint_if_missing "$ROOT_DIR/app_refactored.py"
echo
echo "Next:"
echo "  - If you ran WITHOUT --full: open each template & paste the premium code I provided."
echo "  - Restart your Replit server and visit:"
echo "      /dashboard   /live   /meetings   /tasks   /calendar   /settings"