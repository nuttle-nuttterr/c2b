# Tamil & English IPTV Playlist Automation

Automatically fetches, filters, combines, and deduplicates Tamil local TV channel playlists from multiple GitHub sources every 6 hours.

## 🚀 How It Works
| Step | Description |
|---|---|
| 1. Fetch | Downloads M3U/JSON playlists from 15+ source repositories |
| 2. Filter | Keeps only wanted channels, ruthlessly blocks unwanted languages |
| 3. Deduplicate | Removes duplicate channels by URL to guarantee 1 link per channel |
| 4. Sort | Alphabetically sorts all channels within their categories |
| 5. Publish | Commits updated `master_playlist.m3u` to this repo |

## 📡 Source Repositories
This script aggregates from trusted community sources including:
- Vmfm/tamilvmtv
- Tamilwebcast/Tamilwebcast.github.io
- Indiblog/india-iptv
- amazeyourself/m3u
- iptv-org (Tamil & English)
- Plus 50+ hardcoded premium local channels.

## 📂 Output Files
| File | Description |
|---|---|
| `master_playlist.m3u` | Combined, filtered, deduplicated, and sorted playlist |
| `update_summary.txt` | Last update log with channel count and category breakdown |

## ⏰ Update Schedule
Runs automatically via GitHub Actions every 6 hours:
- 00:00 UTC
- 06:00 UTC
- 12:00 UTC
- 18:00 UTC

You can also trigger manually via **Actions** → **Update M3U Playlist** → **Run workflow**.

## 🛠 Local Usage
```bash
# Clone the repo
git clone https://github.com/nuttle-nuttterr/tv-playlist-automation.git
cd tv-playlist-automation

# Install dependency
pip install requests

# Run the script
python fetch_and_combine.py
```

## 📋 Included Channel Categories
- ✅ Tamil Local Channels
- ✅ News Channels (Polimer, Thanthi, News7, etc.)
- ✅ Entertainment (Zee Tamil, Kalaignar, Raj TV, etc.)
- ✅ Sports, Movies, Music, Kids, and Devotional channels

## ⚙️ Customization
Edit `fetch_and_combine.py` to:
- Add/remove source URLs (`SOURCES`)
- Add/remove custom hardcoded channels (`USER_CUSTOM_CHANNELS`)
- Update blocked languages (`BLOCKED_KEYWORDS`)

---
*This project is for personal/educational use. Channel streams belong to their respective owners.*# c2b
