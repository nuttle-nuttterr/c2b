import requests
import re
import os
import concurrent.futures
from datetime import datetime

# --- 1. YOUR SOURCES ---
SOURCES = [
    # Local Tamil Channels (No language filter, just dedup)
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels-nortmp.m3u",
    
    # Other Repos (Filtered for Tamil)
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

# Block non-Tamil languages that might slip into the "other repos"
BLOCK_KEYWORDS = ["hindi", "telugu", "malayalam", "kannada", "bengali", "marathi", "punjabi", "english movie"]

# --- 2. HELPER FUNCTIONS ---

def fetch_source(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
    return ""

def parse_m3u(content):
    channels = []
    lines = content.strip().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            extinf = line
            # Find the URL (skip extra #EXTVLCOPT or #KODIPROP lines)
            url = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('#'):
                    url = next_line
                    break
                j += 1
            
            if url:
                # Extract name (everything after the last comma)
                match = re.search(r',(.+)$', extinf)
                name = match.group(1).strip() if match else "Unknown"
                
                channels.append({
                    'extinf': extinf,
                    'url': url,
                    'name': name,
                    'original_name': name
                })
            i = j + 1
        else:
            i += 1
    return channels

def check_link_status(channel):
    """Checks if a link is alive. Returns True if alive, False if dead."""
    url = channel['url']
    try:
        # Try HEAD first (faster)
        response = requests.head(url, timeout=5, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code < 400:
            return True
    except: pass
    
    try:
        # Fallback to GET (some IPTV servers block HEAD requests)
        response = requests.get(url, timeout=5, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code < 400:
            response.close()
            return True
    except: pass
        
    return False

def process_dead_links(channels):
    print(f"🔍 Checking {len(channels)} links for dead streams (this takes ~2-5 mins)...")
    alive_channels = []
    
    # Use 50 threads to check links concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_channel = {executor.submit(check_link_status, ch): ch for ch in channels}
        
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            done_count += 1
            try:
                if future.result():
                    alive_channels.append(ch)
            except: pass
            
            if done_count % 100 == 0:
                print(f"   Progress: {done_count}/{len(channels)} checked...")
                
    print(f"✅ Dead link check complete. {len(alive_channels)} alive, {len(channels) - len(alive_channels)} dead removed.")
    return alive_channels

def deduplicate_and_rename(channels):
    print("🔄 Deduplicating and renaming (+1, +2)...")
    seen_urls = set()
    name_counts = {}
    final_channels = []
    
    for ch in channels:
        url = ch['url']
        name = ch['original_name']
        
        # RULE 1: If exact same URL -> Skip (Deduplicate)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Filter out non-Tamil languages just in case
        extinf_lower = ch['extinf'].lower()
        if any(kw in extinf_lower for kw in BLOCK_KEYWORDS):
            continue
            
        # RULE 2: If same Name but different URL -> Rename with +1, +2
        if name in name_counts:
            name_counts[name] += 1
            new_name = f"{name} +{name_counts[name] - 1}" # e.g. Sun TV +1
            ch['extinf'] = re.sub(r',.+$', f",{new_name}", ch['extinf'])
            ch['name'] = new_name
        else:
            name_counts[name] = 1
            
        final_channels.append(ch)
        
    return final_channels

def sort_channels(channels):
    # Sort by Group Title first, then Alphabetical by Name
    def sort_key(ch):
        group_match = re.search(r'group-title="([^"]*)"', ch['extinf'])
        group = group_match.group(1) if group_match else "ZZZ_Uncategorized"
        return (group.lower(), ch['name'].lower())
        
    return sorted(channels, key=sort_key)

def write_m3u(channels, filename="master_playlist.m3u"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f"{ch['extinf']}\n{ch['url']}\n")
    print(f"✅ Successfully wrote {len(channels)} clean channels to {filename}")

def main():
    print("🚀 Starting IPTV Playlist Aggregator...")
    
    all_channels = []
    for url in SOURCES:
        print(f"📡 Fetching: {url}")
        content = fetch_source(url)
        if content:
            parsed = parse_m3u(content)
            print(f"   Found {len(parsed)} channels")
            all_channels.extend(parsed)
            
    print(f"\n📊 Total raw channels fetched: {len(all_channels)}")
    
    # Step 1: Remove Dead Links (Concurrent)
    alive_channels = process_dead_links(all_channels)
    
    # Step 2: Deduplicate & Rename
    clean_channels = deduplicate_and_rename(alive_channels)
    
    # Step 3: Sort
    sorted_channels = sort_channels(clean_channels)
    
    # Step 4: Write output
    write_m3u(sorted_channels, "master_playlist.m3u")
    
    # Step 5: Save Summary
    with open("update_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Playlist Update Summary\n======================\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Total Clean Channels: {len(sorted_channels)}\n")
        f.write(f"Dead Links Removed: {len(all_channels) - len(alive_channels)}\n")
        f.write(f"Duplicates Removed/Renamed: {len(alive_channels) - len(sorted_channels)}\n")
        
    print("🎉 Playlist update complete!")

if __name__ == "__main__":
    main()
