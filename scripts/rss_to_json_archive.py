import os, json, hashlib
from pathlib import Path
from datetime import datetime
import feedparser
from dateutil import parser as dateparser

USERNAME = os.environ.get("TIKTOK_USERNAME","").strip().lstrip("@")
RSS_BASE = os.environ.get("RSS_BASE","https://rsshub.app").rstrip("/")
if not USERNAME:
    raise SystemExit("ERROR: set TIKTOK_USERNAME")

root = Path(__file__).resolve().parents[1]
data = root / "data"
state = root / ".state" / "seen.json"
data.mkdir(parents=True, exist_ok=True)
state.parent.mkdir(parents=True, exist_ok=True)

# โหลดรายการที่ทำไปแล้วกันซ้ำ
seen = {}
if state.exists():
    try:
        seen = json.loads(state.read_text(encoding="utf-8"))
        if not isinstance(seen, dict):
            seen = {}
    except Exception:
        seen = {}

rss = f"{RSS_BASE}/tiktok/user/@{USERNAME}"
feed = feedparser.parse(rss)

def norm_id(e):
    if getattr(e, "id", None):
        return e.id
    if getattr(e, "link", None):
        return hashlib.sha1(e.link.encode("utf-8")).hexdigest()[:16]
    title = getattr(e, "title", "")
    return hashlib.sha1(title.encode("utf-8")).hexdigest()[:16]

new = 0
for e in feed.entries or []:
    eid = norm_id(e)
    if eid in seen:
        continue

    title = getattr(e, "title","").strip()
    link = getattr(e, "link","").strip()
    summary = getattr(e, "summary","").strip()
    published_raw = getattr(e, "published","") or getattr(e,"updated","")
    try:
        published_dt = dateparser.parse(published_raw) if published_raw else datetime.utcnow()
    except Exception:
        published_dt = datetime.utcnow()

    rec = {
        "id": f"tiktok:{eid}",
        "title": title,
        "tiktok_url": link,
        "posted_at": published_dt.isoformat(),
        "caption": summary,
        "local_media": "",                      # ถ้าจะอัป IPFS ใส่ชื่อไฟล์ต้นฉบับทีหลัง
        "media": {},                            # จะถูกเติม ipfs_cid หลังอัป
        "rights": {
            "audio_source": "unknown",          # "MaMeeFarm Original" / "TikTok Music Library" / ...
            "upload_to_ipfs": False             # ค่าเริ่มต้น: ไม่อัป IPFS → ปลอดลิขสิทธิ์
        },
        "proof": {"fetched_at": datetime.utcnow().isoformat(), "updated_at": ""}
    }

    out = data / f"day-{published_dt.strftime('%Y%m%d')}-{eid}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    seen[eid] = True
    new += 1

state.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"new entries: {new}")
