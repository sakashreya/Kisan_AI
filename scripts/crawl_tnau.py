"""Crawl TNAU Agritech 'Crop Protection' pages (English) into one .txt file per crop.
Put this file in  scripts/  and run from the project root:
    python -m pip install beautifulsoup4
    python scripts/crawl_tnau.py
Output: data/pdfs/<crop>__tnau_crop_protection.txt  (then run scripts/ingest.py)
"""
import os, re, time, collections
from urllib.parse import urljoin, urldefrag, quote, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup

START = "https://agritech.tnau.ac.in/crop_protection/crop_prot.html"
PREFIX = "https://agritech.tnau.ac.in/crop_protection/"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pdfs")
MAX_PAGES = 1500
DELAY = 0.3
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
RENAME = {"paddy": "rice", "soya": "soybean", "soyabean": "soybean", "red_gram": "tur",
          "pigeonpea": "tur", "bengal_gram": "chickpea", "gram": "chickpea", "corn": "maize"}
JUNK = ("About Us", "All Rights Reserved", "Success Stories", "Farmers Association", "Disclaimer")


def norm(url):
    url = urldefrag(url)[0].replace("http://", "https://")
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), quote(p.path, safe="/%"), p.query, ""))


def crop_of(url):
    rest = url[len(PREFIX):]
    parts = rest.split("/")
    if len(parts) < 2:
        return "multi"
    c = re.sub(r"[^a-z0-9_]", "", parts[0].lower())
    return RENAME.get(c, c) or "multi"


def page_text(soup):
    for t in soup(["script", "style", "nav", "header", "footer"]):
        t.decompose()
    lines = [l.strip() for l in soup.get_text("\n").splitlines()]
    return "\n".join(l for l in lines if l and not any(j in l for j in JUNK))


seen, queue = set(), collections.deque([norm(START)])
by_crop = collections.defaultdict(list)
fail = 0
while queue and len(seen) < MAX_PAGES:
    url = queue.popleft()
    if url in seen:
        continue
    seen.add(url)
    try:
        r = requests.get(url, headers=H, timeout=30)
    except Exception as e:
        fail += 1
        print("error", type(e).__name__, url)
        continue
    if not r.ok or "html" not in r.headers.get("content-type", ""):
        continue
    soup = BeautifulSoup(r.content, "html.parser")
    for a in soup.find_all("a", href=True):
        nxt = norm(urljoin(url, a["href"]))
        if (nxt.startswith(PREFIX) and nxt.lower().endswith((".html", ".htm"))
                and "/ta/" not in nxt and nxt not in seen):
            queue.append(nxt)
    text = page_text(soup)
    if len(text) > 200:
        title = soup.title.get_text(strip=True) if soup.title else url
        by_crop[crop_of(url)].append(f"### {title}\nSource: {url}\n{text}\n")
    if len(seen) % 25 == 0:
        print(f"crawled {len(seen)} pages, queue {len(queue)}")
    time.sleep(DELAY)

os.makedirs(OUT, exist_ok=True)
print(f"\nCrawled {len(seen)} pages ({fail} errors). Files written:")
for crop, pages in sorted(by_crop.items()):
    path = os.path.join(OUT, f"{crop}__tnau_crop_protection.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(pages))
    print(f"  {crop:15s} {len(pages):4d} pages -> {os.path.basename(path)}")
print("\nCheck the crop names above. Rename files whose prefix is not a real crop, then run ingest.py")
