import os, json, requests
from pathlib import Path

PINATA_JWT = os.environ.get("PINATA_JWT","").strip()
if not PINATA_JWT:
    print("WARN: PINATA_JWT not set. Skipping upload."); raise SystemExit(0)

root = Path(__file__).resolve().parents[1]
data_dir = root / "data"
media_dir = root / "media" / "originals"

def pin_file(p: Path):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {PINATA_JWT}"}
    with p.open("rb") as f:
        files = {"file": (p.name, f)}
        r = requests.post(url, headers=headers, files=files, timeout=120)
    r.raise_for_status()
    return r.json()["IpfsHash"]

changed = 0
for jf in sorted(data_dir.glob("*.json")):
    o = json.loads(jf.read_text(encoding="utf-8"))
    rights = o.get("rights", {})
    fname = (o.get("local_media") or "").strip()

    # อัปเฉพาะที่ mark upload_to_ipfs=true และมีชื่อไฟล์ต้นฉบับ
    if not rights.get("upload_to_ipfs") or not fname:
        continue

    media = o.setdefault("media", {})
    if media.get("ipfs_cid"):
        continue  # อัปไปแล้ว

    p = media_dir / fname
    if not p.exists():
        print(f"[skip] media missing for {jf.name}: {fname}")
        continue

    try:
        cid = pin_file(p)
    except Exception as e:
        print(f"[err] upload failed for {fname}: {e}")
        continue

    media["ipfs_cid"] = cid
    media["ipfs_gateway"] = f"https://gateway.pinata.cloud/ipfs/{cid}"
    jf.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    changed += 1
    print(f"[ok] {fname} → {cid}")

print(f"updated JSON files: {changed}")
