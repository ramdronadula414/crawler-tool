# Internal Link Crawler

Recursively crawls every website in your URL list and extracts only
internal links (same domain). Saves one `.txt` per site and bundles
all of them into `internal_links.zip`.

---

## Setup (one time)

```bash
pip install -r requirements.txt
```

---

## Usage

1. Place your URL list file (e.g. `URLS.txt`) in the same folder as the script.
2. Run:

```bash
python crawl_internal_links.py
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | `URLS.txt` | Path to input URL list |
| `--outdir` | `internal_links` | Folder for per-site TXT files |
| `--zip` | `internal_links.zip` | Output ZIP archive name |
| `--delay` | `1.0` | Seconds between requests (be polite!) |
| `--max-pages` | `200` | Max pages crawled per domain |

**Example – faster crawl with 0.5 s delay, 100 page cap:**
```bash
python crawl_internal_links.py --delay 0.5 --max-pages 100
```

---

## Output

```
internal_links/
  bakingo_com.txt
  theobroma_in.txt
  ksbakers_com.txt
  ...
internal_links.zip   ← all TXT files zipped
```

Each TXT file contains one internal URL per line:
```
https://example.com
https://example.com/about
https://example.com/contact
...
```

---

## What it filters out

- External domains
- Social media links (Facebook, Twitter/X, Instagram, LinkedIn, YouTube, etc.)
- `mailto:` links
- `tel:` links
- `javascript:` links
- Duplicate URLs
- Non-HTML resources (images, PDFs, etc.)

---

## Notes

- Domains appearing more than once in the input list are crawled only once.
- The crawler respects `--delay` between each HTTP request to avoid overloading servers.
- Redirects are followed automatically.
