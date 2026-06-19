#!/usr/bin/env python3
"""
Internal Link Crawler
---------------------
Reads a list of URLs from a text file, crawls each website recursively,
extracts only internal links (same domain), and saves results to individual
.txt files, then compresses them all into internal_links.zip
"""

import os
import re
import time
import zipfile
import argparse
import urllib.parse
from collections import deque

import requests
from bs4 import BeautifulSoup

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_FILE  = "URLS.txt"
OUTPUT_DIR  = "internal_links"
OUTPUT_ZIP  = "internal_links.zip"
DELAY       = 1.0
MAX_PAGES   = 200
TIMEOUT     = 15
MAX_DEPTH   = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

SKIP_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "linkedin.com", "youtube.com", "pinterest.com", "tiktok.com",
    "reddit.com", "snapchat.com", "whatsapp.com", "telegram.org",
    "t.me", "wa.me",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def normalise_url(url):
    p = urllib.parse.urlparse(url)
    clean = urllib.parse.urlunparse((
        p.scheme.lower(), p.netloc.lower(),
        p.path, p.params, p.query, ""
    ))
    return clean.rstrip("/") or "/"


def get_domain(url):
    return urllib.parse.urlparse(url).netloc.lower()


def is_internal(link, base_netloc):
    return urllib.parse.urlparse(link).netloc.lower() == base_netloc


def is_skippable(href):
    lower = href.lower().strip()
    if lower.startswith(("mailto:", "tel:", "javascript:", "data:", "#", "void")):
        return True
    for sd in SKIP_DOMAINS:
        if sd in lower:
            return True
    return False


def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if is_skippable(href):
            continue
        absolute = urllib.parse.urljoin(base_url, href)
        if not absolute.startswith(("http://", "https://")):
            continue
        links.append(normalise_url(absolute))
    return links


def crawl_site(start_url, session, max_pages, delay):
    start_url = normalise_url(start_url)
    base_netloc = get_domain(start_url)

    visited = set()
    queue = deque()
    queue.append((start_url, 0))
    found = set()
    found.add(start_url)

    print("\n  -> Crawling {}  (domain: {})".format(start_url, base_netloc))

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=TIMEOUT, headers=HEADERS,
                               allow_redirects=True)
            ct = resp.headers.get("Content-Type", "")
            if "html" not in ct:
                continue
            if resp.status_code not in (200, 301, 302):
                continue

            links = extract_links(resp.text, resp.url)
            for link in links:
                if is_internal(link, base_netloc) and link not in found:
                    found.add(link)
                    if depth + 1 <= MAX_DEPTH:
                        queue.append((link, depth + 1))

            print("     [{:>3}/{}] depth={}  found={}  {}".format(
                len(visited), max_pages, depth, len(found), url[:80]))

        except Exception as exc:
            print("     [SKIP] {}  ({})".format(url[:70], exc))

        time.sleep(delay)

    return sorted(found)


def safe_filename(url):
    netloc = get_domain(url)
    name = re.sub(r"[^\w\-.]", "_", netloc)
    return name + ".txt"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Recursive internal-link crawler")
    parser.add_argument("--input",     default=INPUT_FILE)
    parser.add_argument("--outdir",    default=OUTPUT_DIR)
    parser.add_argument("--zip",       default=OUTPUT_ZIP)
    parser.add_argument("--delay",     type=float, default=DELAY)
    parser.add_argument("--max-pages", type=int,   default=MAX_PAGES)
    args = parser.parse_args()

    delay     = args.delay
    max_pages = args.max_pages

    os.makedirs(args.outdir, exist_ok=True)

    with open(args.input, encoding="utf-8") as f:
        raw_urls = [line.strip() for line in f if line.strip().startswith("http")]

    print("Loaded {} URLs from '{}'".format(len(raw_urls), args.input))

    seen_domains = {}
    unique_urls = []
    for u in raw_urls:
        d = get_domain(u)
        if d not in seen_domains:
            seen_domains[d] = u
            unique_urls.append(u)
        else:
            print("  [DUP domain] {}  (already have {})".format(u, seen_domains[d]))

    print("Unique domains: {}\n".format(len(unique_urls)))

    session = requests.Session()
    session.headers.update(HEADERS)

    txt_files = []

    for idx, url in enumerate(unique_urls, 1):
        print("[{}/{}] Starting: {}".format(idx, len(unique_urls), url))
        links = crawl_site(url, session, max_pages, delay)

        fname = safe_filename(url)
        fpath = os.path.join(args.outdir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(links) + "\n")

        txt_files.append(fpath)
        print("  Saved {} links -> {}".format(len(links), fpath))

    with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in txt_files:
            zf.write(fpath, arcname=os.path.basename(fpath))

    print("\nDone! ZIP saved as: {}".format(args.zip))
    print("Contains {} TXT files.".format(len(txt_files)))


if __name__ == "__main__":
    main()
