import requests
import re
import concurrent.futures
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION (Tweak these if needed)
# ==========================================
# Set to False to keep ALL channels (Recommended). 
# Set to True if you want to spend ~10 mins scanning and removing dead links.
CHECK_DEAD_LINKS = False 

# --- LOCAL SOURCES (Will NOT be filtered, forced into "Local TV" group) ---
LOCAL_SOURCES = [
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels-nortmp.m3u"
]

# --- MAIN SOURCES (Will be filtered for Tamil, forced into "Main TV" group) ---
MAIN_SOURCES = [
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/dishd2h.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ektv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/fastvjp.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/jayamott.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/joshuaott.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/jtv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/maduraiiptv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/nellaiiptv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/pishow.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/yupptvfast.m3u"
]

# Keywords to block ONLY from the MAIN_SOURCES
BLOCK_KEYWORDS = ["hindi", "telugu", "malayalam", "kannada", "bengali", "marathi", "punjabi", "english movie", "english news", "bhojpuri", "gujarati", "odiya", "urdu", "sinhala"]


# ==========================================
# 🧠 CORE FUNCTIONS
# ==========================================

def fetch_source(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        # Ensure we got actual text, not a GitHub 404 HTML page
        if response.status_code == 200 and 'html' not in response.headers.get('Content-Type', '').lower():
            return response.text
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
    return ""

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            # Safely split attributes and name even if name has commas
            last_comma_idx = line.rfind(',')
            if last_comma_idx != -1:
                attributes = line[:last_comma_idx]
                name = line[last_comma_idx+1:].strip()
            else:
                attributes = line
                name = "Unknown"
            
            # Find the stream URL (skip any #EXTVLCOPT or #KODIPROP lines)
            url = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('#'):
                    url = next_line
                    break
                j += 1
            
            if url and not url.startswith('#'):
                channels.append({
                    'attributes': attributes,
                    'name': name,
                    'url': url,
                    'original_name': name
                })
            i = j + 1
        else:
            i += 1
    return channels

def set_group_title(attributes, new_group):
    """Forces the channel into a specific category in your IPTV player"""
    # Remove existing group-title
    attributes = re.sub(r'group-title="[^"]*"', '', attributes)
    attributes = re.sub(r'\s+', ' ', attributes).strip()
    # Add new group-title
    if not attributes.endswith(' '):
        attributes += ' '
    attributes += f'group-title="{new_group}"'
    return attributes

def is_tamil_allowed(channel):
    """Checks if a Main TV channel contains blocked languages"""
    text_to_check = (channel['attributes'] + " " + channel['name']).lower()
    for kw in BLOCK_KEYWORDS:
        if kw in text_to_check:
            return False
    return True

def check_link_status(channel):
    """Robust stream checker. Uses VLC headers to bypass basic IPTV blocks."""
    url = channel['url']
    headers = {'User-Agent': 'VLC/3.0.16 LibVLC/3.0.16'}
    try:
        with requests.get(url, stream=True, timeout=10, headers=headers) as r:
            if r.status_code == 200:
                # Read a tiny bit to ensure it's a valid stream
                chunk = next(r.iter_content(256), None)
                if chunk is not None:
                    return True
    except:
        pass
    return False

def process_dead_links(channels):
    if not CHECK_DEAD_LINKS:
        return channels
        
    print(f"🔍 Checking {len(channels)} links for dead streams...")
    alive_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_channel = {executor.submit(check_link_status, ch): ch for ch in channels}
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            done_count += 1
            if future.result():
                alive_channels.append(ch)
            if done_count % 500 == 0:
                print(f"   Progress: {done_count}/{len(channels)} checked...")
    print(f"✅ Dead link check complete. Kept {len(alive_channels)} alive channels.")
    return alive_channels

def deduplicate_and_rename(channels):
    print("🔄 Deduplicating and renaming (+1, +2)...")
    seen_urls = set()
    name_counts = {}
    final_channels = []
    
    for ch in channels:
        url = ch['url']
        name = ch['original_name']
        
        # RULE 1: Skip exact duplicate URLs
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # RULE 2: Handle duplicate names (e.g. Sun TV, Sun TV +1, Sun TV +2)
        norm_name = name.lower().strip()
        if norm_name in name_counts:
            name_counts[norm_name] += 1
            new_name = f"{name} +{name_counts[norm_name] - 1}"
            ch['name'] = new_name
        else:
            name_counts[norm_name] = 1
            
        final_channels.append(ch)
        
    return final_channels

def sort_channels(channels):
    # Sort by Group Title, then Alphabetical
    def sort_key(ch):
        group_match = re.search(r'group-title="([^"]*)"', ch['attributes'])
        group = group_match.group(1) if group_match else "ZZZ_Uncategorized"
        return (group.lower(), ch['name'].lower())
    return sorted(channels, key=sort_key)

def main():
    print("🚀 Starting IPTV Playlist Aggregator...")
    all_channels = []
    
    # 1. Fetch LOCAL sources (No language filter applied)
    for url in LOCAL_SOURCES:
        print(f"📡 Fetching Local: {url}")
        content = fetch_source(url)
        if content:
            parsed = parse_m3u(content)
            print(f"   Found {len(parsed)} channels")
            for ch in parsed:
                ch['attributes'] = set_group_title(ch['attributes'], "Local TV")
            all_channels.extend(parsed)
            
    # 2. Fetch MAIN sources (Language filter APPLIED)
    for url in MAIN_SOURCES:
        print(f"📡 Fetching Main: {url}")
        content = fetch_source(url)
        if content:
            parsed = parse_m3u(content)
            print(f"   Found {len(parsed)} raw channels")
            for ch in parsed:
                ch['attributes'] = set_group_title(ch['attributes'], "Main TV")
                if is_tamil_allowed(ch):
                    all_channels.append(ch)
                    
    print(f"\n📊 Total valid channels fetched: {len(all_channels)}")
    
    # 3. Remove Dead Links (Only if CHECK_DEAD_LINKS = True)
    alive_channels = process_dead_links(all_channels)
    
    # 4. Deduplicate & Rename
    clean_channels = deduplicate_and_rename(alive_channels)
    
    # 5. Sort
    sorted_channels = sort_channels(clean_channels)
    
    # 6. Write Output
    with open('master_playlist.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for ch in sorted_channels:
            f.write(f"{ch['attributes']},{ch['name']}\n{ch['url']}\n")
            
    print(f"✅ Successfully wrote {len(sorted_channels)} clean channels to master_playlist.m3u")
    
    # 7. Write Summary
    with open("update_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Playlist Update Summary\n======================\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Total Clean Channels: {len(sorted_channels)}\n")
        
    print("🎉 Playlist update complete!")

if __name__ == "__main__":
    main()
