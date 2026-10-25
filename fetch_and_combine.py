#!/usr/bin/env python3
"""
fetch_and_combine.py — Self-updating IPTV playlist builder for the c2b repo.

Pipeline:
  1. Fetch 3 LOCAL sources  -> no Tamil filter, only dedupe
  2. Fetch 11 MAIN sources   -> Tamil-only filter, then dedupe
  3. Parallel deadlink check on Main TV only (Local TV is trusted as-is)
  4. Write master_playlist.m3u with two groups: "Local TV" and "Main TV"
  5. Write stats.json with per-source counts + dead count + run timestamp

Dedup rule (per group):
  - Same URL  -> drop duplicate
  - Same name + different URL -> rename +1, +2, +3 ...

Run locally:
    pip install requests urllib3
    python fetch_and_combine.py

Run in GitHub Actions every 6 hours (see .github/workflows/update-playlist.yml).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

LOCAL_SOURCES: List[tuple] = [
    # (label, raw-url) — Local TV: NO Tamil filter, only dedupe
    ("tamilvmtv",         "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u"),
    ("tamil-local",       "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/main/channels.m3u"),
    ("tamil-local-nortmp","https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/main/channels-nortmp.m3u"),
]

MAIN_SOURCES: List[tuple] = [
    # (label, raw-url) — Main TV: Tamil filter applied
    ("ashokadigital", "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u"),
    ("dishd2h",       "https://raw.githubusercontent.com/amazeyourself/m3u/main/dishd2h.m3u"),
    ("ektv",          "https://raw.githubusercontent.com/amazeyourself/m3u/main/ektv.m3u"),
    ("fastvjp",       "https://raw.githubusercontent.com/amazeyourself/m3u/main/fastvjp.m3u"),
    ("jayamott",      "https://raw.githubusercontent.com/amazeyourself/m3u/main/jayamott.m3u"),
    ("joshuaott",     "https://raw.githubusercontent.com/amazeyourself/m3u/main/joshuaott.m3u"),
    ("jtv",           "https://raw.githubusercontent.com/amazeyourself/m3u/main/jtv.m3u"),
    ("maduraiiptv",   "https://raw.githubusercontent.com/amazeyourself/m3u/main/maduraiiptv.m3u"),
    ("nellaiiptv",    "https://raw.githubusercontent.com/amazeyourself/m3u/main/nellaiiptv.m3u"),
    ("pishow",        "https://raw.githubusercontent.com/amazeyourself/m3u/main/pishow.m3u"),
    ("yupptvfast",    "https://raw.githubusercontent.com/amazeyourself/m3u/main/yupptvfast.m3u"),
]

# Tamil channel detection keywords (lowercased substrings).
# Multi-signal: any one match => Tamil channel.
TAMIL_KEYWORDS = [
    # Generic language tags
    "tamil", "tamizh", "thamizh", "tamilan", "tamizhan",
    # Sun Network
    "sun tv", "sun news", "sun life", "sun music", "sun action",
    "adithya", "chutti", "ktv", "k tv", "vasanth tv", "vasantham",
    "santhosh tv", "santhosh",
    # Star Vijay
    "vijay tv", "vijay tak", "star vijay", "vijay super", "vijay jolly",
    # Zee Tamil
    "zee tamil", "zee tamizh", "zeetamil",
    # Colors Tamil
    "colors tamil", "colours tamil",
    # Kalaignar
    "kalaignar",
    # Captain TV
    "captain tv", "captain news",
    # Mega TV
    "mega tv", "megatv",
    # Polimer
    "polimer",
    # Puthuyugam
    "puthuyugam", "puthu yugam",
    # Jaya TV
    "jaya tv", "jaya plus", "jaya max", "jaya movies", "jaya star",
    # MK TV / SVBC
    "mk tv", "mktv", "svbc",
    # Religious / spiritual
    "shalom tv", "god tv tamil", "arutperunjothi", "imayam tv",
    # News
    "news18 tamil", "news 18 tamil",
    # Misc known Tamil channels
    "tamizhan", "peppers tv", "akaram tv", "azhagu tv", "azhagu",
    "7g tv", "bravo tv", "win tv tamil", "sangamam tv",
    # Common group-title tags
    "tamil entertainment", "tamil news", "tamil movies", "tamil music",
    "tamil sports", "tamil kids",
]

# Tamil Unicode block: U+0B80 .. U+0BFF  (catches channels named in Tamil script)
TAMIL_SCRIPT_RE = re.compile(r"[\u0B80-\u0BFF]")

# Deadlink checking — Main TV only
DEADLINK_TIMEOUT = 8          # seconds per stream
DEADLINK_WORKERS = 100        # concurrent workers
DEADLINK_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 MPV-Compatible"
)

# Output paths (relative to repo root when running in Actions)
OUTPUT_PLAYLIST = "master_playlist.m3u"
OUTPUT_STATS = "stats.json"

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("c2b")


# ----------------------------------------------------------------------
# HTTP session
# ----------------------------------------------------------------------
def make_session(pool_size: int = 100) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": "c2b-playlist-builder/2.0 (+https://github.com/nuttle-nuttterr/c2b)",
        "Accept": "*/*",
    })
    return s


def fetch_source(session: requests.Session, name: str, url: str) -> str:
    log.info(f"  Fetching [{name}] {url}")
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        log.info(f"    [{name}] OK ({len(r.text)} bytes)")
        return r.text
    except Exception as e:
        log.warning(f"    [{name}] FAILED: {e}")
        return ""


# ----------------------------------------------------------------------
# M3U parsing
# ----------------------------------------------------------------------
EXTINF_RE = re.compile(r'^#EXTINF:(-?\d+(?:\.\d+)?)\s*(.*)$')
ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)="([^"]*)"')


def parse_m3u(text: str, source_name: str) -> List[Dict]:
    """
    Parse M3U text into list of dicts:
        {name, url, attrs (dict), source}
    Robust against:
        - missing commas in #EXTINF
        - quoted attribute values
        - blank lines / unknown directives
        - channels with no name (defaults to source label)
    """
    channels: List[Dict] = []
    if not text:
        return channels

    lines = text.splitlines()
    current_attrs: Dict[str, str] = {}
    current_name: str = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            m = EXTINF_RE.match(line)
            if not m:
                current_attrs = {}
                current_name = ""
                continue
            payload = m.group(2)

            # Split attribute string and trailing channel name at the LAST comma
            # that is OUTSIDE any quoted segment.
            in_quote = False
            split_at = -1
            for i, ch in enumerate(payload):
                if ch == '"':
                    in_quote = not in_quote
                elif ch == "," and not in_quote:
                    split_at = i

            if split_at == -1:
                # No comma -> entire payload is the channel name
                attrs_part = ""
                name = payload.strip()
            else:
                attrs_part = payload[:split_at].strip()
                name = payload[split_at + 1:].strip()

            attrs: Dict[str, str] = {}
            for kv in ATTR_RE.finditer(attrs_part):
                attrs[kv.group(1).lower()] = kv.group(2)

            current_attrs = attrs
            current_name = name
            continue

        if line.startswith("#EXTGRP:"):
            grp = line[len("#EXTGRP:"):].strip()
            if grp:
                current_attrs["group-title"] = grp
            continue

        if line.startswith("#"):
            # Other directives (#EXTVLCOPT, #EXTM3U header, comments) — skip
            continue

        # URL line
        url = line
        if url:
            name = current_name.strip() or f"Unknown-{source_name}"
            channels.append({
                "name": name,
                "url": url,
                "attrs": dict(current_attrs),
                "source": source_name,
            })
        # Reset for next entry
        current_attrs = {}
        current_name = ""

    return channels


# ----------------------------------------------------------------------
# Tamil detection
# ----------------------------------------------------------------------
def is_tamil_channel(name: str, group_title: str = "") -> bool:
    """
    Multi-signal Tamil detection:
      1. Substring match against TAMIL_KEYWORDS (case-insensitive)
      2. Tamil Unicode script character present in name or group-title
    """
    haystack = f"{name} {group_title}".lower()

    for kw in TAMIL_KEYWORDS:
        if kw in haystack:
            return True

    if TAMIL_SCRIPT_RE.search(name) or TAMIL_SCRIPT_RE.search(group_title):
        return True

    return False


# ----------------------------------------------------------------------
# Deduplication
# ----------------------------------------------------------------------
def dedupe(channels: List[Dict], group_label: str) -> List[Dict]:
    """
    Apply the user's dedup rule:
      - Same URL  -> drop duplicate (keep first occurrence)
      - Same name + different URL -> rename +1, +2, +3 ... (preserve alternates)
    """
    seen_urls: set = set()
    name_counter: Dict[str, int] = defaultdict(int)
    result: List[Dict] = []

    for ch in channels:
        url = ch["url"].strip()
        if not url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        base_name = ch["name"].strip() or f"Unknown-{group_label}"

        if name_counter[base_name] == 0:
            new_name = base_name
        else:
            new_name = f"{base_name} +{name_counter[base_name]}"
        name_counter[base_name] += 1

        new_ch = dict(ch)
        new_ch["name"] = new_name
        result.append(new_ch)

    return result


# ----------------------------------------------------------------------
# Deadlink checking (Main TV only)
# ----------------------------------------------------------------------
def is_stream_alive(session: requests.Session, url: str) -> bool:
    """
    Check if a stream URL is alive.
      - HLS (.m3u8): GET playlist, check for #EXTINF or #EXT-X-STREAM-INF in first 16KB
      - Other: HEAD (fallback to ranged GET)
    """
    headers = {"User-Agent": DEADLINK_USER_AGENT}

    try:
        lower = url.lower()
        if ".m3u8" in lower or "application/vnd.apple.mpegurl" in lower:
            # HLS playlist
            r = session.get(url, timeout=DEADLINK_TIMEOUT, headers=headers, stream=True, allow_redirects=True)
            if r.status_code >= 400:
                r.close()
                return False
            chunk = b""
            try:
                chunk = r.raw.read(16384, decode_content=True) or b""
            except Exception:
                pass
            r.close()
            if not chunk:
                return False
            text = chunk.decode("utf-8", errors="ignore")
            if "#EXT-X-ERROR" in text:
                return False
            # A valid HLS playlist has either segments or sub-playlists
            return ("#EXTINF" in text) or ("#EXT-X-STREAM-INF" in text)
        else:
            # Non-HLS stream: try HEAD first
            try:
                r = session.head(url, timeout=DEADLINK_TIMEOUT, headers=headers, allow_redirects=True)
                if 200 <= r.status_code < 400:
                    return True
                if r.status_code == 405:
                    # HEAD not allowed -> fall through to ranged GET
                    pass
                else:
                    return False
            except requests.RequestException:
                pass  # fall through to ranged GET

            r = session.get(
                url,
                timeout=DEADLINK_TIMEOUT,
                headers={**headers, "Range": "bytes=0-1023"},
                stream=True,
                allow_redirects=True,
            )
            ok = 200 <= r.status_code < 400
            r.close()
            return ok
    except Exception:
        return False


def check_deadlinks(channels: List[Dict], workers: int = DEADLINK_WORKERS) -> tuple:
    """
    Parallel deadlink check.
    Returns (alive_list, dead_count).
    """
    if not channels:
        return [], 0

    session = make_session(pool_size=workers + 10)
    alive: List[Dict] = []
    dead_count = 0
    total = len(channels)
    log.info(f"  Checking {total} streams with {workers} workers (timeout {DEADLINK_TIMEOUT}s each)")

    start = time.time()
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_ch = {ex.submit(is_stream_alive, session, ch["url"]): ch for ch in channels}
        for future in as_completed(future_to_ch):
            ch = future_to_ch[future]
            try:
                ok = future.result()
            except Exception:
                ok = False
            done += 1
            if ok:
                alive.append(ch)
            else:
                dead_count += 1
            if done % 200 == 0 or done == total:
                elapsed = time.time() - start
                rate = done / max(elapsed, 0.001)
                eta = (total - done) / max(rate, 0.001)
                log.info(f"    Progress: {done}/{total} | alive={len(alive)} dead={dead_count} | "
                         f"rate={rate:.1f}/s eta={eta:.0f}s")

    return alive, dead_count


# ----------------------------------------------------------------------
# M3U writing
# ----------------------------------------------------------------------
def write_m3u(path: str, local_channels: List[Dict], main_channels: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
        f.write(f"# Local TV: {len(local_channels)} channels | Main TV: {len(main_channels)} channels\n")
        f.write("# Generated by fetch_and_combine.py — runs every 6h via GitHub Actions\n")
        f.write("#\n")

        for ch in local_channels:
            _write_channel(f, ch, "Local TV")
        for ch in main_channels:
            _write_channel(f, ch, "Main TV")

    log.info(f"  Wrote {path}  (Local={len(local_channels)} + Main={len(main_channels)})")


def _write_channel(f, ch: Dict, group: str) -> None:
    attrs = dict(ch.get("attrs") or {})
    attrs["group-title"] = group
    if not attrs.get("tvg-name"):
        attrs["tvg-name"] = ch["name"]

    # Build attribute string, skipping empty values
    parts = []
    for k, v in attrs.items():
        if v is None:
            continue
        v = str(v).strip()
        if v:
            parts.append(f'{k}="{v}"')
    attr_str = " ".join(parts)

    f.write(f"#EXTINF:-1 {attr_str},{ch['name']}\n")
    f.write(f"{ch['url']}\n")


# ----------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------
def write_stats(path: str, stats: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    log.info(f"  Wrote {path}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    start = time.time()
    session = make_session()

    log.info("=" * 60)
    log.info("c2b playlist builder — starting run")
    log.info("=" * 60)

    stats: Dict = {
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": {},
    }

    # ---- 1. Fetch Local sources (no Tamil filter) ----
    log.info("--- Stage 1: Fetching LOCAL sources (no Tamil filter) ---")
    local_raw: List[Dict] = []
    for name, url in LOCAL_SOURCES:
        text = fetch_source(session, name, url)
        channels = parse_m3u(text, name)
        stats["sources"][f"local:{name}"] = {
            "url": url,
            "raw_channels": len(channels),
        }
        local_raw.extend(channels)
        log.info(f"    [{name}] parsed {len(channels)} channels")

    # ---- 2. Fetch Main sources (Tamil filter) ----
    log.info("--- Stage 2: Fetching MAIN sources (Tamil filter ON) ---")
    main_raw: List[Dict] = []
    for name, url in MAIN_SOURCES:
        text = fetch_source(session, name, url)
        channels = parse_m3u(text, name)
        tamil_only = [c for c in channels if is_tamil_channel(c["name"], c["attrs"].get("group-title", ""))]
        stats["sources"][f"main:{name}"] = {
            "url": url,
            "raw_channels": len(channels),
            "tamil_channels": len(tamil_only),
        }
        log.info(f"    [{name}] {len(channels)} raw -> {len(tamil_only)} Tamil")
        main_raw.extend(tamil_only)

    stats["totals"] = {
        "local_raw": len(local_raw),
        "main_raw_tamil": len(main_raw),
    }

    # ---- 3. Dedupe Local ----
    log.info("--- Stage 3: Deduping Local ---")
    local_deduped = dedupe(local_raw, "Local TV")
    log.info(f"  {len(local_raw)} -> {len(local_deduped)} after dedup")
    stats["totals"]["local_after_dedup"] = len(local_deduped)

    # ---- 4. Dedupe Main ----
    log.info("--- Stage 4: Deduping Main ---")
    main_deduped = dedupe(main_raw, "Main TV")
    log.info(f"  {len(main_raw)} -> {len(main_deduped)} after dedup")
    stats["totals"]["main_after_dedup"] = len(main_deduped)

    # ---- 5. Deadlink check on Main TV only ----
    log.info("--- Stage 5: Deadlink check (Main TV only) ---")
    alive, dead_count = check_deadlinks(main_deduped)
    log.info(f"  Main TV: {len(main_deduped)} -> {len(alive)} alive, {dead_count} dead")
    stats["totals"]["main_final"] = len(alive)
    stats["totals"]["main_dead"] = dead_count

    # ---- 6. Write outputs ----
    log.info("--- Stage 6: Writing outputs ---")
    write_m3u(OUTPUT_PLAYLIST, local_deduped, alive)
    stats["totals"]["elapsed_seconds"] = round(time.time() - start, 1)
    write_stats(OUTPUT_STATS, stats)

    log.info(f"DONE in {time.time() - start:.1f}s")
    log.info(f"  Local TV: {len(local_deduped)}")
    log.info(f"  Main TV:  {len(alive)} (dead: {dead_count})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
