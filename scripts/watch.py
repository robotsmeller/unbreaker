"""Poll Steam Workshop comment threads and GitHub issue activity, toast on anything new.

Run by Task Scheduler every 20 minutes. Stdlib only.

    python scripts/watch.py               poll every source once
    python scripts/watch.py --test        send a test message to the phone and exit
    python scripts/watch.py --reset       forget all seen ids (next run re-baselines)
    python scripts/watch.py --dump        print what each source returns, change nothing
    python scripts/watch.py --dry-run     detect and print, send nothing, save nothing
    python scripts/watch.py --simulate 2  pretend the 2 newest per source are new (implies dry-run)

Verify with --simulate, never by hand-editing the state file. Editing state sends
a real message containing an old comment, and leaves the id armed to send again.

Delivery is Telegram, reusing the bot the Claude channel already set up, with a
local Windows toast as fallback. Three guarantees are deliberate:

  at-least-once  news is only marked seen after Telegram confirms delivery, so a
                 failed send retries on the next poll instead of vanishing
  heartbeat      after HEARTBEAT_HOURS of quiet it says so, so silence from this
                 tool means "nothing happened" and not "it died months ago"
  no secrets     the bot token is read at runtime and scrubbed from every log line

First run for a source records everything as already seen and stays silent, so
adding a source never dumps its whole backlog into your notifications.
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Config. Add a source here; nothing else needs to change.
# --------------------------------------------------------------------------

STEAM_OWNER_ID = "76561198032541351"  # robotsmeller

# Rob's own accounts. His replies and the issues this repo's tooling files under
# his token are not news to him. Still logged, just never pushed to the phone.
SELF_AUTHORS = {"robotsmeller", "rob-kingsbury"}

SOURCES: list[dict[str, str]] = [
    {"kind": "steam", "key": "steam:unbreaker", "label": "Unbreaker (Workshop)",
     "file_id": "3721648770"},
    {"kind": "steam", "key": "steam:hfth", "label": "Head for the Hills (Workshop)",
     "file_id": "3777845024"},
    {"kind": "gh_issues", "key": "gh:unbreaker:issues", "label": "Unbreaker (GitHub issue)",
     "repo": "robotsmeller/unbreaker"},
    {"kind": "gh_comments", "key": "gh:unbreaker:comments", "label": "Unbreaker (GitHub reply)",
     "repo": "robotsmeller/unbreaker"},
]

STATE_DIR = Path.home() / "AppData" / "Local" / "pz-watch"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = STATE_DIR / "watch.log"
NOTIFY_PS1 = Path(__file__).resolve().parent / "notify.ps1"

SEEN_CAP = 400        # ids retained per source
HTTP_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) pz-watch/1.0"

# Telegram. Reuses the bot the Claude channel already registered. Note this is
# the SEND path only: a plain HTTPS POST, no bot process, no long polling, so it
# does not care whether the Claude channel's receiver is running.
TELEGRAM_DIR = Path.home() / ".claude" / "channels" / "telegram"
SEND_RETRIES = (0, 3, 10)   # seconds to wait before attempts 1, 2, 3

# Silence is ambiguous: no comments and a dead watcher look identical from a
# phone. A heartbeat makes absence meaningful.
HEARTBEAT_HOURS = 24

# Anything that lands in this list is scrubbed out of every log line. The token
# appears inside the request URL, so urllib exception text leaks it otherwise.
_SECRETS: list[str] = []

# Windows: keep subprocesses from flashing a console window every 20 minutes.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# --------------------------------------------------------------------------
# Plumbing
# --------------------------------------------------------------------------

def scrub(value: object) -> str:
    """Strip known secrets from anything on its way to the log."""
    text = f"{type(value).__name__}: {value}" if isinstance(value, BaseException) else str(value)
    for secret in _SECRETS:
        if secret:
            text = text.replace(secret, "<token>")
    return text


def log(message: object) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    line = f"{stamp}  {scrub(message)}"
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log(f"! state file unreadable ({exc}), starting fresh")
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def toast(title: str, body: str) -> None:
    """Fire a Windows toast. Never raises: a failed toast still leaves a log line."""
    if not NOTIFY_PS1.exists():
        log(f"! notify.ps1 missing at {NOTIFY_PS1}")
        return
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(NOTIFY_PS1), "-Title", title[:120], "-Body", body[:250]],
            capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
        if result.returncode != 0:
            log(f"! toast failed: {(result.stdout + result.stderr).strip()[:200]}")
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"! toast failed: {exc}")


def telegram_config() -> tuple[str, str]:
    """Read the bot token and target chat. The token is never logged or printed."""
    token = ""
    for line in (TELEGRAM_DIR / ".env").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("TELEGRAM_BOT_TOKEN="):
            token = stripped.split("=", 1)[1].strip().strip('"').strip("'")
    if token:
        _SECRETS.append(token)

    access = json.loads((TELEGRAM_DIR / "access.json").read_text(encoding="utf-8"))
    allowed = access.get("allowFrom") or []

    if not token:
        raise RuntimeError(f"no TELEGRAM_BOT_TOKEN in {TELEGRAM_DIR / '.env'}")
    if not allowed:
        raise RuntimeError(f"allowFrom is empty in {TELEGRAM_DIR / 'access.json'}")
    return token, str(allowed[0])


def telegram_send(text: str) -> bool:
    """Push to the phone. Returns False rather than raising, so a poll never dies here."""
    try:
        token, chat_id = telegram_config()
    except (OSError, ValueError, RuntimeError) as exc:
        log(f"! telegram not usable: {exc}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text[:3900],
        "disable_web_page_preview": True,
    }).encode("utf-8")

    for attempt, pause in enumerate(SEND_RETRIES, start=1):
        if pause:
            time.sleep(pause)
        try:
            request = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                if json.loads(response.read().decode("utf-8")).get("ok"):
                    return True
                log(f"! telegram attempt {attempt}: api returned ok=false")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            log(f"! telegram attempt {attempt}: {exc}")
    return False


def notify(text: str) -> bool:
    """Telegram first. A local toast is the consolation prize if the phone push fails."""
    if telegram_send(text):
        log("  telegram sent")
        return True
    log("! telegram failed after retries, falling back to local toast")
    toast("pz-watch (Telegram failed)", text)
    return False


def clean(raw: str) -> str:
    """HTML fragment to a single line of readable text."""
    text = re.sub(r"<br\s*/?>", " ", raw)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# Sources. Each returns newest-first items: id, who, what, url.
# --------------------------------------------------------------------------

def fetch_steam(source: dict[str, str]) -> list[dict[str, str]]:
    url = (f"https://steamcommunity.com/comment/PublishedFile_Public/render/"
           f"{STEAM_OWNER_ID}/{source['file_id']}/?start=0&count=30")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not payload.get("success"):
        raise RuntimeError("steam returned success=false")

    blob = payload.get("comments_html", "")
    # Slice the blob at each comment id so fields can never pair across comments.
    marks = list(re.finditer(r'id="comment_(\d+)"', blob))
    items: list[dict[str, str]] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(blob)
        chunk = blob[mark.start():end]

        author = re.search(r"<bdi>([^<]*)</bdi>", chunk)
        stamp = re.search(r'data-timestamp="(\d+)"', chunk)
        body = re.search(r'class="commentthread_comment_text"[^>]*>(.*?)</div>', chunk, re.S)

        items.append({
            "id": mark.group(1),
            "who": author.group(1).strip() if author else "?",
            "when": stamp.group(1) if stamp else "",
            "what": clean(body.group(1)) if body else "",
            "url": (f"https://steamcommunity.com/sharedfiles/filedetails/"
                    f"?id={source['file_id']}"),
        })

    # Steam comment ids are not monotonic, so order by timestamp, newest first.
    items.sort(key=lambda item: int(item["when"] or 0), reverse=True)
    return items


def run_gh(args: list[str]) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True,
                            timeout=60, creationflags=NO_WINDOW)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[:200])
    return result.stdout


def fetch_gh_issues(source: dict[str, str]) -> list[dict[str, str]]:
    raw = run_gh(["issue", "list", "--repo", source["repo"], "--state", "all",
                  "--limit", "30", "--json", "number,title,author,createdAt,url"])
    return [{
        "id": f"issue:{issue['number']}",
        "who": (issue.get("author") or {}).get("login", "?"),
        "when": issue.get("createdAt", ""),
        "what": f"#{issue['number']} {issue.get('title', '')}",
        "url": issue.get("url", ""),
    } for issue in json.loads(raw)]


def fetch_gh_comments(source: dict[str, str]) -> list[dict[str, str]]:
    raw = run_gh(["api", f"repos/{source['repo']}/issues/comments"
                         "?per_page=30&sort=created&direction=desc"])
    return [{
        "id": f"comment:{comment['id']}",
        "who": (comment.get("user") or {}).get("login", "?"),
        "when": comment.get("created_at", ""),
        "what": clean(comment.get("body", "")),
        "url": comment.get("html_url", ""),
    } for comment in json.loads(raw)]


FETCHERS = {
    "steam": fetch_steam,
    "gh_issues": fetch_gh_issues,
    "gh_comments": fetch_gh_comments,
}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def poll(dump_only: bool = False, dry_run: bool = False, simulate: int = 0) -> int:
    state = load_state()
    fresh: list[tuple[dict[str, str], dict[str, str]]] = []
    # Held back until delivery is confirmed, so a failed send does not mark
    # unread news as seen.
    pending: dict[str, list[str]] = {}
    sources_with_news: set[str] = set()

    for source in SOURCES:
        try:
            items = FETCHERS[source["kind"]](source)
        except (urllib.error.URLError, OSError, ValueError, RuntimeError,
                subprocess.SubprocessError) as exc:
            # One dead source must not stop the others.
            log(f"! {source['key']}: {type(exc).__name__}: {exc}")
            continue

        if dump_only:
            log(f"  {source['key']}: {len(items)} items")
            for item in items[:5]:
                log(f"      {item['id']} {item['who']}: {item['what'][:70]}")
            continue

        seen = state.get(source["key"])
        ids = [item["id"] for item in items]

        if seen is None:
            state[source["key"]] = ids[:SEEN_CAP]
            log(f"  {source['key']}: baseline set, {len(ids)} items, silent")
            continue

        known = set(seen)
        if simulate:
            # Pretend the newest few were never seen. In memory only: the state
            # file is not touched, so this cannot arm a real send later.
            known -= set(ids[:simulate])
        new_items = [item for item in items if item["id"] not in known]
        for item in new_items:
            own = item["who"].lower() in SELF_AUTHORS
            tag = "OWN" if own else "NEW"
            log(f"{tag} {source['key']} {item['who']}: {item['what'][:100]}  {item['url']}")
            if own:
                continue
            fresh.append((source, item))
            sources_with_news.add(source["key"])

        # dict.fromkeys dedupes while keeping order. Without it every poll
        # re-appends the whole page and the cap fills with repeats.
        pending[source["key"]] = list(dict.fromkeys(ids + seen))[:SEEN_CAP]

    if dump_only:
        return 0

    meta = state.get("_meta", {})
    now = datetime.now(timezone.utc)

    if fresh:
        message = build_message(fresh)
        if dry_run:
            log(f"  DRY RUN: would send {len(fresh)} item(s). Nothing sent, state untouched.")
            for line in message.splitlines():
                log(f"    | {line}")
            return 0
        delivered = notify(message)
        if delivered:
            meta["last_send"] = now.isoformat()
            state.update(pending)
        else:
            # Commit only the quiet sources. Undelivered news stays unseen so the
            # next run tries again: at-least-once beats losing a comment silently.
            for key, ids in pending.items():
                if key not in sources_with_news:
                    state[key] = ids
            log("! not delivered, those items stay unseen and retry next run")
        log(f"  {len(fresh)} new")
    elif dry_run:
        due = " Heartbeat would fire." if heartbeat_due(meta, now) else ""
        log(f"  DRY RUN: nothing new.{due} State untouched.")
        return 0
    else:
        state.update(pending)
        log("  nothing new")
        if heartbeat_due(meta, now):
            if notify(f"pz-watch heartbeat: alive, {len(SOURCES)} sources, nothing new.\n"
                      f"You get this only when {HEARTBEAT_HOURS}h pass with no other message, "
                      f"so silence after this means something is broken."):
                meta["last_send"] = now.isoformat()

    state["_meta"] = meta
    save_state(state)
    return 0


def build_message(fresh: list[tuple[dict[str, str], dict[str, str]]]) -> str:
    header = "1 new message" if len(fresh) == 1 else f"{len(fresh)} new messages"
    blocks = [f"{source['label']}\n{item['who']}: {item['what'][:300]}\n{item['url']}"
              for source, item in fresh]
    return header + "\n\n" + "\n\n".join(blocks)


def heartbeat_due(meta: dict[str, str], now: datetime) -> bool:
    last = meta.get("last_send")
    if not last:
        return True
    try:
        return now - datetime.fromisoformat(last) >= timedelta(hours=HEARTBEAT_HOURS)
    except ValueError:
        return True


def main() -> int:
    # Comment text is full of smart quotes; the Windows console is cp1252.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="fire a test toast and exit")
    parser.add_argument("--reset", action="store_true", help="forget all seen ids")
    parser.add_argument("--dump", action="store_true", help="show each source, change nothing")
    parser.add_argument("--dry-run", action="store_true",
                        help="run detection and print the message, send nothing, save nothing")
    parser.add_argument("--simulate", type=int, metavar="N", default=0,
                        help="treat the N newest items per source as unseen; implies --dry-run")
    args = parser.parse_args()

    if args.test:
        ok = notify("pz-watch test. If this reached your phone, delivery works. "
                    "This is what a new Workshop comment will look like.")
        return 0 if ok else 1

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        log("  state cleared, next run re-baselines")
        return 0

    return poll(dump_only=args.dump,
                dry_run=args.dry_run or args.simulate > 0,
                simulate=args.simulate)


if __name__ == "__main__":
    sys.exit(main())
