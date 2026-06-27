#!/usr/bin/env python3
"""Scrape NIE (BPOM marketing-authorization number) + manufacturer from Halodoc.

For every confident price match (score >= 0.7) we already know the Halodoc slug. This
hits Halodoc's product detail API and pulls `bpom_number` (the NIE) and `manufacturer_name`.
Writes halodoc_details.json (resumable). Run with an int arg for a sample dry-run, e.g.
`halodoc_nie.py 8`.
"""
import json, re, sys, os, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DETAIL = "https://customers.api.halodoc.com/magneto-api/v1/buy-medicine/products/detail/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PRICES = "halodoc_prices.json"
OUT = "halodoc_details.json"
WORKERS = 16            # concurrent requests — Halodoc's API is fast (~0.3s) and tolerant
SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 0

def clean_nie(s):
    if not s:
        return ""
    s = re.sub(r'(?i)^\s*bpom\s*[:\-]?\s*', '', s).strip()
    return s

def fetch(slug):
    url = DETAIL + urllib.parse.quote(slug, safe='') + "?location_id="
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

def extract(d):
    """Find bpom_number + manufacturer_name anywhere in the detail payload."""
    nie = man = ""
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                kl = k.lower()
                if kl == 'bpom_number' and isinstance(v, str) and not nie:
                    nie = clean_nie(v)
                elif kl == 'manufacturer_name' and isinstance(v, str) and not man:
                    man = v.strip()
                elif isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(o, list):
            stack.extend(o)
    return nie, man

def main():
    prices = json.load(open(PRICES, encoding="utf-8"))
    # only confident matches that carry a halodoc slug
    targets = [(our, rec["halo_slug"]) for our, rec in prices.items()
               if rec.get("score", 0) >= 0.7 and rec.get("halo_slug")]

    done = {}
    if not SAMPLE and os.path.exists(OUT):
        try:
            done = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            done = {}

    todo = [(o, s) for (o, s) in targets if o not in done]
    if SAMPLE:
        todo = todo[::max(1, len(todo)//SAMPLE)][:SAMPLE]
    print(f"{len(targets)} matched products, {len(done)} done, {len(todo)} to fetch"
          + (" (SAMPLE)" if SAMPLE else "") + f" | {WORKERS} workers", flush=True)

    def work(item):
        our, slug = item
        for attempt in range(3):                  # quick retries for transient errors
            try:
                nie, man = extract(fetch(slug))
                return our, {"nie": nie, "manufacturer": man, "halo_slug": slug}
            except Exception as e:
                if attempt == 2:
                    return our, {"nie": "", "manufacturer": "", "halo_slug": slug, "error": str(e)[:80]}
        return our, {"nie": "", "manufacturer": "", "halo_slug": slug}

    n = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(work, it) for it in todo]
        for fut in as_completed(futures):
            our, rec = fut.result()
            done[our] = rec
            n += 1
            if SAMPLE:
                print(f"  {our[:40]:40} NIE={rec.get('nie') or '(none)':20} mfr={rec.get('manufacturer','')}", flush=True)
            elif n % 100 == 0:
                json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
                got = sum(1 for v in done.values() if v.get("nie"))
                print(f"  {len(done)} processed | {got} NIEs found", flush=True)

    if not SAMPLE:
        json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        got = sum(1 for v in done.values() if v.get("nie"))
        print(f"DONE. {len(done)} processed, {got} NIEs -> {OUT}", flush=True)

if __name__ == "__main__":
    main()
