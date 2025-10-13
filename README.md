# MaMeeFarm — TikTok Data Archive (Selective IPFS System)

**Purpose:**  
This repository is designed to **automatically archive every TikTok post** from the official [@mameefarm](https://www.tiktok.com/@mameefarm) channel as structured **JSON metadata**, without downloading or redistributing copyrighted media.  
It serves as a **Proof-of-Work (PoW) and Proof-of-Life data system** for MaMeeFarm — turning daily farm activities into verifiable digital records.

---

## 🔹 Key Objectives

- 🪶 **Archive TikTok data safely:**  
  Collect post titles, captions, timestamps, and video URLs via RSS, stored as verifiable JSON files in `/data`.

- 💾 **Preserve ownership rights:**  
  No copyrighted media is stored or distributed.  
  Only clips explicitly marked as “MaMeeFarm Original” (with clear rights) are uploaded to IPFS.

- 🌍 **Enable transparent data provenance:**  
  Each record acts as a traceable “life-data point” that can be linked to blockchain, ESG, or NFT systems later.

---

## ⚙️ How It Works

1. **TikTok → JSON Archive**  
   - The GitHub Action `tiktok_data_archive.yml` runs every 10 minutes.  
   - It fetches the latest TikTok RSS feed and generates new `.json` files for each post inside `/data/`.

2. **Selective IPFS Upload**  
   - Only original files with verified rights (`upload_to_ipfs=true`) are uploaded to [Pinata](https://pinata.cloud).  
   - The returned IPFS CID and gateway link are written back into the same JSON record automatically.

3. **Manual OpenSea Curation**  
   - MaMeeFarm manually selects and mints NFTs using verified IPFS URIs.  
   - OpenSea-related records or notes can be saved in `/data/opensea/`.

---

## 🧩 Folder Structure

.github/workflows/ → GitHub Actions automation files
scripts/ → Python automation scripts
data/ → JSON records for each TikTok post
data/opensea/ → Optional folder for manually curated NFT data
media/originals/ → Local media files (for IPFS upload only)
.state/ → Internal state tracking for processed entries

---

## 🪙 Example JSON Record

```json
{
  "id": "tiktok:a1b2c3d4e5",
  "title": "Morning Egg Collection",
  "tiktok_url": "https://www.tiktok.com/@mameefarm/video/1234567890",
  "posted_at": "2025-10-13T07:15:00+07:00",
  "caption": "Another rainy day at the farm 🦆",
  "local_media": "",
  "media": {},
  "rights": {
    "audio_source": "unknown",
    "upload_to_ipfs": false
  },
  "proof": {
    "fetched_at": "2025-10-13T12:05:32Z",
    "updated_at": ""
  }
}

