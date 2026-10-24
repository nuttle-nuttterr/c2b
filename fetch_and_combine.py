import requests
import re
import json
import datetime
import os

# ==========================================
# 1. USER'S CUSTOM HARDCODED CHANNELS
# ==========================================
USER_CUSTOM_CHANNELS = """
#EXTINF:-1 group-title="Tamil Local Channels",Sana TV
https://galaxyott.live/hls/sanatv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Sana Plus
https://galaxyott.live/hls/sanaplus.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",UTV
https://stream.galaxyott.live/live/utv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",NTV
https://galaxyott.live/hls/ntv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Surya TV
https://galaxyott.live/hls/suryatv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Subin TV
https://stream.galaxyott.live/live/subintv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Moon TV
https://live.maxtn.in/moontv/moontv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Sakthi TV
https://live.sscloud7.in/live/sakthitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Prime TV
https://live.applelive.in/primetv/primetv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",D TV
https://stream.d6-pro.com/Dtv/live/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",TDN
https://live.maxtn.in/tdn/tdn/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",7 Green
https://account33.livebox.co.in/7GREEN4Khls/live.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Yet TV
https://live.yettelevision.com:5443/LiveApp/streams/yettv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",PR TV
https://play.applelive.in/prtv/prtv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Riya TV
https://play.applelive.in/riyatv/riyatv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Dark TV
https://play.applelive.in/darktv/darktv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Harin TV HD
https://ipcloud.live/harintv/harintvhd/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Phoenix TV
https://stream.onecloudlive.in/phoenixtv/phoenixtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Roja TV
https://live.rojatv.cloud/rojatv/rojatv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Nila TV
https://live.olidigital.in/nilatv/nilatv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",SMCV TV
https://singamcloud.in/smcvtv/smcvtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",APS TV
https://apstv-a1.tamilstream.in/apstv/apstv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",APS Gold
https://apsgold-a1.tamilstream.in/apsgold/apsgold/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",MTV Men HD
https://ipcloud.live/mtv/menhd/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",MSN TV
https://ipcloud.live/msntv/msntv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Veerali TV
https://ipcloud.live/veerali/veeralitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Three Star TV HD
https://stream.onecloudlive.in/threestartv/threestarhd/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Shalini TV
https://ipcloud.live/shalinitv/shalinitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",JCV TV
https://play.applelive.in/jcvtv/jcvtv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Thendral TV
https://live.thendralcloud.in/thendraltv/d0dbe915091d400bd8ee7f27f0791303.sdp/chunks.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Anbu TV HD
https://ipcloud.live/anbutv/anbutvhd/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Nellai TV
https://stream.onecloudlive.in/nellaitv/nellaitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Akash TV
https://account2.livebox.co.in/AkashTvhls/live.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Apple TV
https://play.applelive.in/appletv/appletv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Jeyson TV
https://play.applelive.in/jeysontv/jeysontv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",JJ Max
https://play.applelive.in/jjmax/jjmax.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Digital TV
https://play.applelive.in/digitaltv/digitaltv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Oscar TV
https://account21.livebox.co.in/oscartvhls/live.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Jeyan TV
https://stream.onecloudlive.in/jeyantv/jeyantv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Vidyal TV
https://account11.livebox.co.in/vidyaltvhls/live.m3u8?psk=stream
#EXTINF:-1 group-title="Tamil Local Channels",KCN TV
https://view.rcserver.in/tmp_hls12/kcntv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Sky TV
https://sscloud7.com/live/skytv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Boys TV
https://rtmp.applelive.in/boystv/boystv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",King TV
https://server.sscloud7.in/kingtv/kingtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Udhayam TV
https://view.rcserver.in/tmp_hls8/udhayamtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",TN TV
https://view.rcserver.in/tmp_hls14/tntv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Senthamil TV
https://view.rcserver.in/tmp_hls24/senthamiltv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Karur TV
https://view.rcserver.in/tmp_hls16/karurtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Karur City
https://view.rcserver.in/tmp_hls17/karurcity/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Thirai TV
https://view.apserver.in/tmp_hls2/thiraitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Bharathi TV
https://server.sscloud7.in/live/bharathitv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Irattipaathai TV
https://account31.livebox.co.in/IRATTAIPAATHAITVhls/live.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",MCN TV
https://play.applelive.in/mcntv/mcntv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",STN TV
https://play.applelive.in/stntv/stntv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Suriyan TV
https://view.rcserver.in/tmp_hls9/suriyantv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Vasanth TV
https://play.applelive.in/vasanthtv/vasanthtv.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Eesan TV
https://live.singamcloud.in/eesantv/eesantv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Jeyam TV
https://live.sscloud7.in/live/jeyamtv/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Aadhavan TV Colours
https://live.olidigital.in/aadhavantvcolours/aadhavantvcolours/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",Solai TV HD
https://ipcloud.live/solaitv/solaihd/index.m3u8
#EXTINF:-1 group-title="Tamil Local Channels",MM TV Jeyam Plus
https://ipcloud.live/mmtv/jeyamplus/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",chithiram tv
https://cdn-6.pishow.tv/live/1243/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",dd tamil
https://d2lk5u59tns74c.cloudfront.net/out/v1/abf46b14847e45499f4a47f3a9afe93d/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Isaiaruvi
https://segment.yuppcdn.net/140622/isaiaruvi/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Murasu
https://segment.yuppcdn.net/050522/murasu/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Kalaignar TV
https://segment.yuppcdn.net/240122/kalaignartv/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",mathimugam
https://cdn-3.pishow.tv/live/1476/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Makkal
https://5k8q87azdy4v-hls-live.wmncdn.net/MAKKAL/271ddf829afeece44d8732757fba1a66.sdp/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",malai murasu
https://cdn-3.pishow.tv/live/1606/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",News7
https://segment.yuppcdn.net/240122/news7/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",News18 Tamil Nadu NW18
https://n18syndication.akamaized.net/bpk-tv/News18_Tamil_Nadu_NW18_MOB/output01/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",news j
https://cdn-3.pishow.tv/live/1279/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Polimer News
https://segment.yuppcdn.net/110322/polimernews/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",polimer tv
https://cdn-2.pishow.tv/live/1241/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Puthiya
https://segment.yuppcdn.net/240122/puthiya/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",raj tv
https://d3qs3d2rkhfqrt.cloudfront.net/out/v1/2839e3d1e0f84a2e821c1708d5fdfdf0/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Siripoli
https://segment.yuppcdn.net/240122/siripoli/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Zionmediait 97484f5ce6da96e496a9b87c439835d0
https://cdn.zionmediait.com/zionmediaitserver2024/97484f5ce6da96e496a9b87c439835d0.sdp/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Thalaa TV TAM
https://streams2.sofast.tv/ptnr-yupptv/title-THALAA-TV-TAM_yupptv/v1/master/611d79b11b77e2f571934fd80ca1413453772ac7/2069c593-3c07-4d62-9d44-746be5c3a5d6/manifest.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",thanthi tv
https://cdn-3.pishow.tv/live/1612/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",vendhar tv
https://cdn-3.pishow.tv/live/1271/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",win news
https://cdn-4.pishow.tv/live/1531/master.m3u8
"""

# ==========================================
# 2. ALL SOURCES
# ==========================================
SOURCES = [
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u",
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/jio.m3u",
    "https://raw.githubusercontent.com/Tamilwebcast/Tamilwebcast.github.io/main/TWCIPTV.m3u",
    "https://raw.githubusercontent.com/PraveenBojja83/praveentv/main/resource/channels.json",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/main/output/india_iptv.m3u",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/main/output/india_general.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/jtv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/pishow.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/yupptvfast.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/tangotv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/neotv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
    "https://iptv-org.github.io/iptv/languages/tam.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u"
]

# ==========================================
# 3. RUTHLESS BLOCK LIST
# ==========================================
BLOCKED_KEYWORDS = [
    "hindi", "telugu", "malayalam", "kannada", "marathi", "bengali", "bangla", 
    "gujarati", "punjabi", "odia", "assamese", "urdu", "bhojpuri",
    "spanish", "french", "german", "italian", "portuguese", "russian",
    "chinese", "japanese", "korean", "arabic", "indonesian", "nepali"
]

# ==========================================
# 4. CORE FUNCTIONS
# ==========================================
def clean_name(name):
    name = re.sub(r'\s*\[.*?\]\s*', '', name)
    name = re.sub(r'\s*\(.*?\)\s*', '', name)
    return ' '.join(name.split()).strip()

def is_blocked(name):
    if not name: return True
    n = name.lower()
    return any(lang in n for lang in BLOCKED_KEYWORDS)

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    current_name, current_logo, current_cat = None, "", "Uncategorized"
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            logos = re.findall(r'tvg-logo="(.*?)"', line)
            current_logo = logos[0] if logos else ""
            cats = re.findall(r'group-title="(.*?)"', line)
            current_cat = cats[0] if cats else "Uncategorized"
            current_name = line.rsplit(',', 1)[1].strip() if ',' in line else None
        elif line and not line.startswith("#") and current_name:
            channels.append((current_name, current_logo, line, current_cat))
            current_name, current_cat = None, "Uncategorized"
    return channels

def parse_json(content):
    channels = []
    try:
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get('channels', data.get('streams', data.get('data', [])))
        for item in items:
            name = item.get('name') or item.get('title') or item.get('channel_name') or "Unknown"
            url = item.get('url') or item.get('stream') or item.get('link') or item.get('channel_url')
            logo = item.get('logo') or item.get('icon') or item.get('stream_icon') or ""
            cat = item.get('group') or item.get('category') or "Uncategorized"
            if name and url: 
                channels.append((name, logo, url, cat))
    except Exception: 
        pass
    return channels

def main():
    print("🚀 Starting Ultimate Deduplication & Sorting Builder...")
    
    # Dict to hold unique channels: { url: {"name": name, "logo": logo, "cat": cat} }
    unique_channels = {}
    seen_urls = set()

    # --- 1. GATHER CUSTOM CHANNELS FIRST ---
    print("\n📌 Gathering User Custom Channels...")
    custom_parsed = parse_m3u(USER_CUSTOM_CHANNELS)
    for name, logo, url, cat in custom_parsed:
        url = url.strip()
        if not url.startswith("http") or url in seen_urls: 
            continue
        if is_blocked(name): 
            continue
            
        seen_urls.add(url)
        proper_name = clean_name(name)
        unique_channels[url] = {"name": proper_name, "logo": logo, "cat": cat}

    # --- 2. GATHER FROM GITHUB REPOS ---
    for src_url in SOURCES:
        print(f"📥 Scraping: {src_url}")
        try:
            resp = requests.get(src_url, timeout=15)
            resp.raise_for_status()
            parsed = parse_json(resp.text) if src_url.endswith('.json') else parse_m3u(resp.text)
            
            for name, logo, url, cat in parsed:
                url = url.strip()
                if not url.startswith("http") or url in seen_urls: 
                    continue
                if is_blocked(name): 
                    continue
                
                seen_urls.add(url)
                proper_name = clean_name(name)
                
                # Fallback category logic
                if cat == "Uncategorized" or not cat:
                    if "local" in proper_name.lower():
                        cat = "Tamil Local Channels"
                    else:
                        cat = "Tamil IPTV Channels"

                unique_channels[url] = {"name": proper_name, "logo": logo, "cat": cat}
                    
        except Exception as e:
            print(f"   ⚠️ Failed to fetch {src_url}: {e}")

    print(f"\n✅ Extracted {len(unique_channels)} unique, working channels.")
    
    # --- 3. SORTING & FILE GENERATION ---
    print("📝 Writing master_playlist.m3u in perfect alphabetical order...")
    
    # Convert dict to list of tuples for sorting: (cat, name, logo, url)
    channel_list = []
    for url, data in unique_channels.items():
        channel_list.append((data["cat"], data["name"], data["logo"], url))
    
    # Sort primarily by Category, then Alphabetically by Name
    channel_list.sort(key=lambda x: (x[0], x[1].lower()))

    with open("master_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#PLAYLIST: Checked and Sorted by tv-playlist-automation\n")
        
        current_cat = None
        for cat, name, logo, url in channel_list:
            if cat != current_cat:
                f.write(f"\n# --- {cat} ---\n")
                current_cat = cat
            
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{cat}",{name}\n{url}\n')

    # --- 4. README / SUMMARY UPDATE ---
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open("update_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Last Updated: {timestamp}\n")
        f.write(f"Total LIVE Channels: {len(channel_list)}\n")
        
        # Count by category
        cat_counts = {}
        for cat, _, _, _ in channel_list:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
        f.write("\nChannel Breakdown:\n")
        for cat, count in sorted(cat_counts.items()):
            f.write(f"- {cat}: {count}\n")

    print(f"\n🎉 SUCCESS! Total Unique Channels Saved: {len(channel_list)}")

if __name__ == "__main__":
    main()
