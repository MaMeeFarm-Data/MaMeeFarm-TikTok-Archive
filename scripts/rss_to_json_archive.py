# scripts/rss_to_json_archive.py
# MaMeeFarm – TikTok RSS → JSON (metadata only)
# เก็บเฉพาะข้อมูลเมตา เพื่อหลักฐานการทำงาน (Proof-of-Work)
# ไม่ดาวน์โหลดวิดีโอ/เพลง ปลอดลิขสิทธิ์

import os, json, hashlib, time, sys, re
from pathlib import Path
from datetime import datetime, timezone
import requests
import feedparser
from dateutil import parser as dateparser

# -------- Settings --------
USERNAME = os.environ.get("TIKTOK_USERNAME", "").strip().lstrip("@")
RSS_BASE = os.environ.get("RSS_BASE", "https://rsshub.hellogithub.workers.dev").strip()

MIRRORS = [
    RSS_BASE.rstrip("/"),
    "https://rsshub.app",
    "https://rsshub.moeyy.cn",
    "https://r.jina.ai/http://rsshub.app",  # last-resort proxy (html→text)
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) MaMeeFarmBot/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "close",
}

# -------- Paths --------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
STATE_FILE = ROOT / ".state" / "seen.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def short_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def fetch_feed():
    if not USERNAME:
        print("WARN: TIKTOK_USERNAME not set")
        return None
    last_err = None
    for base in MIRRORS:
        url = f"{base.rstrip('/')}/tiktok/user/@{USERNAME}"
        try:
            print(f"[fetch] {url}")
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200 or not r.text.strip():
                last_err = f"HTTP {r.status_code} from {base}"
                print(f"[skip] {last_err}")
                time.sleep(1.0)
                continue
            feed = feedparser.parse(r.text)
            if getattr(feed, "entries", None):
                print(f"[ok] entries={len(feed.entries)} from {base}")
                return feed
            last_err = f"no entries from {base}"
            print(f"[skip] {last_err}")
        except Exception as e:
            last_err = f"{type(e).__name__}: {e} from {base}"
            print(f"[err] {last_err}")
        time.sleep(1.0)
    print(f"[fatal] RSS fetch failed: {last_err}")
    return None

def load_seen():
    if STATE_FILE.exists():
        try:
            obj = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}
    return {}

def save_seen(seen: dict):
    STATE_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_tiktok_id(link: str) -> str:
    # ตัวอย่างลิงก์: https://www.tiktok.com/@mameefarm/video/73333333333
    m = re.search(r"/video/(\d+)", link or "")
    return m.group(1) if m else short_hash(link or "")

def entry_id(e) -> str:
    if getattr(e, "id", None):
        return str(e.id)
    if getattr(e, "link", None):
        return f"lnk:{short_hash(e.link)}"
    t = getattr(e, "title", "") or ""
    return f"ttl:{short_hash(t)}"

def to_record(e):
    link = getattr(e, "link", "").strip()
    cap  = (getattr(e, "summary", "") or getattr(e, "description", "") or "").strip()
    title = (getattr(e, "title", "") or "").strip()

    raw_time = getattr(e, "published", "") or getattr(e, "updated", "") or ""
    try:
        posted_at = dateparser.parse(raw_time).astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        posted_at = now_iso()

    thumb = None
    # RSSHub ใส่ media_thumbnail / media_content บางเคส
    if "media_thumbnail" in e and e.media_thumbnail:
        try:
            thumb = e.media_thumbnail[0]["url"]
        except Exception:
            pass
    if not thumb and "image" in e:
        thumb = getattr(e, "image", None)

    tid = parse_tiktok_id(link)

    rec = {
        "id": f"tiktok:{tid}",
        "title": title,
        "caption": cap,
        "tiktok_url": link,
        "thumbnail": thumb,
        "posted_at": posted_at,
        "author": USERNAME,
        "media": {},                 # ไม่เก็บไฟล์สื่อจริง
        "rights": {
            "audio_source": "unknown",
            "upload_to_ipfs": False  # ให้มี้เปิดเองทีหลังเฉพาะที่สิทธิ์ชัดเจน
        },
        "proof": {
            "fetched_at": now_iso(),
            "source": "rsshub"
        }
    }
    return rec

def main():
    seen = load_seen()
    feed = fetch_feed()
    if not feed:
        # อย่าให้ job fail — ให้ผ่านเพื่อรันรอบหน้า
        print("No feed. Exit without error.")
        return

    new_count = 0
    for e in feed.entries:
        eid = entry_id(e)
        if eid in seen:
            continue
        rec = to_record(e)

        # ตั้งชื่อไฟล์: day-YYYYMMDD-<short>.json
        ts = rec["posted_at"][:10].replace("-", "")  # YYYYMMDD
        short = short_hash(rec["id"])
        out = DATA_DIR / f"day-{ts}-{short}.json"

        out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        seen[eid] = True
        new_count += 1
        print(f"[write] {out.name}")

    save_seen(seen)
    print(f"[done] new_entries={new_count} total_seen={len(seen)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # ป้องกันไม่ให้ workflow fail เพราะบั๊กเล็ก ๆ — log ไว้พอ
        print(f"[unexpected] {type(e).__name__}: {e}")
        sys.exit(0)
