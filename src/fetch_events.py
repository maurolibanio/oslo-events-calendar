#!/usr/bin/env python3
"""
fetch_events.py — Fetch Oslo events from Visit Oslo via jina.ai scraping.

The Visit Oslo site migrated from a REST JSON API to Craft CMS + Sprig (HTMX).
No public JSON API remains. This script uses jina.ai (r.jina.ai) to render the
server-side HTML pages into structured markdown and parses the events from it.

Output: events.json (compatible with generate_ics.py)
"""

import json
import re
import os
import sys
import time
from datetime import date, datetime, timedelta

import requests

# ── Configuration ──────────────────────────────────────────────────────────

JINA_BASE = "https://r.jina.ai/https://www.visitoslo.com/whats-on/events"
JINA_HEADERS = {
    "Accept": "text/markdown",
    "X-Return-Format": "markdown",
}

OUTPUT_FILE = "events.json"

# Scrape up to 200 pages (each = ~12 events = ~2400 total)
MAX_PAGES = 200

# Delay between jina.ai calls to be gentle (jina.ai free tier rate limit)
PAGE_DELAY_SECS = 2.0

# Retry backoff delays (seconds) for 429 / transient errors
RETRY_DELAYS = [5, 15, 30]

# Stop if this many consecutive pages return zero events
EMPTY_PAGE_LIMIT = 5

# jina.ai timeout (they can be slow on large pages)
JINA_TIMEOUT = 120

# ── Parsing helpers ────────────────────────────────────────────────────────

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

# Norwegian & English 3-letter months (from "24.aug" / "24.okt" format)
# The site uses Norwegian abbreviations: mai, okt, des
MONTH_SHORT = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "mai": 5,  # English / Norwegian
    "jun": 6, "jul": 7, "aug": 8,
    "sep": 9,
    "oct": 10, "okt": 10,  # English / Norwegian
    "nov": 11,
    "dec": 12, "des": 12  # English / Norwegian
}


def parse_day_header(text):
    """Parse 'Monday 24. August 2026' → date(2026, 8, 24)."""
    m = re.match(r'\w+\s+(\d+)\.\s+(\w+)\s+(\d{4})', text.strip())
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2).lower()
    year = int(m.group(3))
    month = MONTH_MAP.get(month_name)
    if not month:
        return None
    return date(year, month, day)


def parse_short_date(text, reference_year):
    """Parse '24.aug' → (day, month) given a reference year."""
    text = text.strip().lower().rstrip('.')
    parts = text.split('.')
    if len(parts) != 2:
        return None
    try:
        day = int(parts[0])
    except ValueError:
        return None
    month = MONTH_SHORT.get(parts[1])
    if not month:
        return None
    return date(reference_year, month, day)


def extract_time_from_bullet(text):
    """Extract time like '10:15' from bullet point text."""
    m = re.search(r'(\d{1,2}):(\d{2})', text)
    if m:
        return m.group(0)
    return None


def normalize_url(url):
    """Make sure event URL is absolute."""
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://www.visitoslo.com' + url
    return url


def make_slug(title):
    """Create a URL-safe slug from a title."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:80]


# ── Main scraping logic ────────────────────────────────────────────────────

def fetch_page(page_num, attempt=1):
    """Fetch one page of events via jina.ai with optional retry.

    Returns raw markdown text, or None after exhausting retries.
    """
    if page_num == 1:
        url = JINA_BASE
    else:
        url = f"{JINA_BASE}?page={page_num}"

    print(f"  Fetching page {page_num}...", flush=True)

    try:
        resp = requests.get(url, headers=JINA_HEADERS, timeout=JINA_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status == 429:
            if attempt <= len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt - 1]
                print(f"  ⚠️  429 on page {page_num} (attempt {attempt}) — retrying in {delay}s...", flush=True)
                time.sleep(delay)
                return fetch_page(page_num, attempt=attempt + 1)
            else:
                print(f"  ❌ 429 on page {page_num} — exhausted retries, skipping.", flush=True)
                return None
        else:
            print(f"  ⚠️  HTTP {status} on page {page_num}: {e}", flush=True)
            if attempt <= len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt - 1]
                print(f"     Retrying in {delay}s...", flush=True)
                time.sleep(delay)
                return fetch_page(page_num, attempt=attempt + 1)
            return None
    except requests.RequestException as e:
        print(f"  ⚠️  Connection error on page {page_num}: {e}", flush=True)
        if attempt <= len(RETRY_DELAYS):
            delay = RETRY_DELAYS[attempt - 1]
            print(f"     Retrying in {delay}s...", flush=True)
            time.sleep(delay)
            return fetch_page(page_num, attempt=attempt + 1)
        return None


def parse_page(markdown_text, current_year, seen_urls):
    """
    Parse event data from a jina.ai markdown page.

    Returns list of event dicts compatible with generate_ics.py.
    """
    events = []

    if not markdown_text:
        return events

    # Strip everything before the first day header (## Monday DD. Month YYYY)
    # This removes cookie consent, nav, ads etc.
    day_header_re = re.compile(
        r'^##\s+\w+\s+\d+\.\s+\w+\s+\d{4}\s*$',
        re.MULTILINE
    )
    first_day = day_header_re.search(markdown_text)
    if not first_day:
        return events

    content = markdown_text[first_day.start():]

    # Split by day headers to get sections
    # Pattern: ## Day Date (e.g., "## Monday 24. August 2026")
    sections = re.split(
        r'^(##\s+\w+\s+\d+\.\s+\w+\s+\d{4}\s*)$',
        content,
        flags=re.MULTILINE
    )
    # sections is [text_before, header1, content1, header2, content2, ...]

    current_day = None
    current_date = None

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Is this a day header?
        day_m = re.match(
            r'^##\s+(\w+\s+\d+\.\s+\w+\s+\d{4})\s*$',
            section
        )
        if day_m:
            current_day = day_m.group(1)
            current_date = parse_day_header(current_day)
            continue

        if current_date is None:
            continue

        # Parse events in this section
        # Each event block starts with [![Image N: title](img_url)](event_url)
        # and typically goes: date_line, category, ### title, bullets
        event_blocks = re.split(
            r'\[!\[Image\s+\d+:[^\]]*\]\([^)]*\)\]\(([^)]+)\)',
            section
        )
        # event_blocks = [before_first_event, url1, block1_text, url2, block2_text, ...]

        # Reconstruct: pair URLs with their following text
        for i in range(1, len(event_blocks) - 1, 2):
            event_url = normalize_url(event_blocks[i].strip())
            block_text = event_blocks[i + 1]

            event = parse_event_block(
                block_text, event_url, current_date, current_year, seen_urls
            )
            if event:
                events.append(event)

    return events


def parse_event_block(block_text, event_url, current_date, year, seen_urls):
    """Parse a single event block from the markdown."""

    lines = block_text.split('\n')
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l]

    if not lines:
        return None

    # First non-empty line should be the short date (e.g., "24.aug")
    # But sometimes it's already consumed... let's look for date pattern
    short_date_str = None
    for line in lines[:3]:
        if re.match(r'^\d{1,2}\.\s*\w{3}\.?\s*$', line.strip().rstrip('.')):
            short_date_str = line.strip()
            break

    if not short_date_str:
        return None

    short_date = parse_short_date(short_date_str, year)
    if not short_date:
        return None

    # The actual event date (use the short date's day+month, but the day header's
    # year. If short_date month doesn't match the section date (e.g., overnight),
    # trust the short date.
    # Actually: use the exact date from short_date if day/month match section,
    # otherwise trust short_date (it handles year boundaries)
    event_date = date(year, short_date.month, short_date.day)

    # Extract category: the line after the short date, before ###
    category_lines = []
    found_short_date = False
    found_hashes = False
    cat_end = 0

    for idx, line in enumerate(lines):
        if re.match(r'^\d{1,2}\.\s*\w{3}\.?\s*$', line.strip()):
            found_short_date = True
            continue
        if found_short_date and line.startswith('###'):
            found_hashes = True
            cat_end = idx
            break
        if found_short_date and not found_hashes:
            category_lines.append(line)

    # Extract title from ### [Title](url)
    title = None
    title_match = re.search(r'^\s*###\s+\[([^\]]+)\]\([^)]+\)\s*$', block_text, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()

    if not title:
        return None

    # Skip duplicates (same event URL already seen)
    if event_url in seen_urls and event_date not in seen_urls.get(event_url, []):
        pass  # same event, different date - keep it
    elif event_url in seen_urls:
        return None

    if event_url not in seen_urls:
        seen_urls[event_url] = []
    seen_urls[event_url].append(event_date)

    # Extract time, location, price from bullet points after the ### heading
    time_str = None
    location = ""
    price = ""

    # Find bullets - they're after ### line
    bullets_start = False
    bullet_lines = []
    for line in lines:
        if line.startswith('### '):
            bullets_start = True
            continue
        if bullets_start and (line.startswith('*') or line.startswith('-') or line.startswith('[')):
            bullet_lines.append(line)
        elif bullets_start and not line.startswith('*') and not line.startswith('-') and not line.startswith('['):
            # Non-bullet line after bullets started
            if bullet_lines:
                break

    # Also search more broadly for bullets
    if not bullet_lines:
        for line in lines:
            if line.startswith('*') or line.startswith('-'):
                bullet_lines.append(line)

    for bline in bullet_lines:
        # Check for "Book now" links - not data bullets
        if bline.startswith('[Book now]') or bline == '':
            continue

        # Try to extract time
        t = extract_time_from_bullet(bline)
        if t:
            time_str = t
            continue

        # Check for location SVG icon or text
        # The location bullets don't have special text markers, but we can
        # identify them by exclusion: not time, not price
        price_match = re.search(r'(\d+)\s*kr', bline)
        if price_match:
            price = price_match.group(0)
            continue
        if 'Free' in bline or 'free' in bline.lower():
            price = 'Free'
            continue

        # If it's not time, not price, and has text -> location
        # Extract text after the icon
        icon_clean = re.sub(r'!\[.*?\]\(.*?\)\s*', '', bline).strip()
        icon_clean = re.sub(r'^[\*\-\s]+', '', icon_clean).strip()
        if icon_clean and not icon_clean.startswith('http'):
            location = icon_clean

    # Build fromDate / toDate
    if time_str:
        try:
            hour, minute = time_str.split(':')
            from_dt = datetime(event_date.year, event_date.month, event_date.day,
                                int(hour), int(minute))
            to_dt = from_dt + timedelta(hours=2)
        except (ValueError, IndexError):
            from_dt = datetime(event_date.year, event_date.month, event_date.day)
            to_dt = from_dt + timedelta(hours=3)
    else:
        # All-day event
        from_dt = datetime(event_date.year, event_date.month, event_date.day)
        to_dt = from_dt + timedelta(hours=12)

    slug = make_slug(title)
    unique_id = f"{slug}-{event_date.isoformat()}"

    # Build description
    description_parts = []
    if category_lines:
        cat_text = ", ".join(cl for cl in category_lines if cl and not cl.startswith('[!['))
        if cat_text:
            description_parts.append(f"Category: {cat_text}")
    if price:
        description_parts.append(f"Price: {price}")
    if description_parts:
        description = " | ".join(description_parts)
    else:
        description = ""

    return {
        "id": unique_id,
        "title": title,
        "url": event_url,
        "place": location,
        "intro": location,
        "fromDate": from_dt.isoformat(),
        "toDate": to_dt.isoformat(),
        "description": {
            "shortPlainText": description
        }
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    today = date.today()
    current_year = today.year
    seen_urls = {}
    all_events = []

    print(f"Oslo Events Calendar — Fetch via jina.ai")
    print(f"Date: {today.isoformat()}")
    print(f"Pages: up to {MAX_PAGES}")
    print()

    consecutive_empty = 0

    for page in range(1, MAX_PAGES + 1):
        markdown = fetch_page(page)

        events = parse_page(markdown, current_year, seen_urls)

        if not events:
            consecutive_empty += 1
            print(f"  No events on page {page} ({consecutive_empty}/{EMPTY_PAGE_LIMIT} consecutive empty)", flush=True)
            if consecutive_empty >= EMPTY_PAGE_LIMIT:
                print(f"  {EMPTY_PAGE_LIMIT} consecutive empty pages — assuming end of results. Done.", flush=True)
                break
        else:
            consecutive_empty = 0
            all_events.extend(events)
            print(f"  → {len(events)} events (total: {len(all_events)})", flush=True)

        # Gentle delay
        if page < MAX_PAGES:
            time.sleep(PAGE_DELAY_SECS)

    print(f"\nTotal events collected: {len(all_events)}")

    # Build output
    output = {
        "generatedAt": today.isoformat(),
        "totalResults": len(all_events),
        "events": all_events
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved to {OUTPUT_FILE}")

    # Stats
    with_times = sum(1 for e in all_events if 'T' in e.get('fromDate', ''))
    all_day = len(all_events) - with_times
    print(f"  {with_times} with specific times, {all_day} all-day")


if __name__ == "__main__":
    main()