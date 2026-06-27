#!/usr/bin/env python3
"""UNIFIED Halodoc scraper — prices + NIE + manufacturer in ONE pass.

Preferred script for future re-imports (after import_products.py rebuilds products.json
from a new export). Per product: search to find the best match, then ONE detail call that
returns price range, NIE (bpom_number) and manufacturer together.

Writes BOTH output files so the existing merge steps work unchanged:
  halodoc_prices.json   -> merge_prices.py
  halodoc_details.json  -> merge_nie.py
Resumable. Optional int arg = sample dry-run, e.g. `halodoc_full.py 8`.

Note: this does the same ~2 requests/product as the two-script flow (search to locate +
detail to read) — there is no single endpoint that returns NIE without a slug. The win is
one clean pass instead of two, with no second iteration over the catalog.
"""
import json, re, sys, time, os, urllib.parse, urllib.request, difflib

SEARCH = "https://customers.api.halodoc.com/magneto-api/v1/buy-medicine/products/search/"
DETAIL = "https://customers.api.halodoc.com/magneto-api/v1/buy-medicine/products/detail/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PRODUCTS = "src/data/products.json"
OUT_PRICES = "halodoc_prices.json"
OUT_DETAILS = "halodoc_details.json"
DELAY = 1.0
SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 0

NOISE = re.compile(r'\b(box|strip|strips|tablet|tablets|caplet|caplets|capsule|capsules|btl|botol|'
                   r'tube|sachet|hemat|borongan|per|pcs|fc|salut|selaput|film|soft)\b', re.I)

def clean_query(name):
    s = re.sub(r'\(.*?\)', ' ', name); s = re.sub(r'@.*$', ' ', s)
    s = NOISE.sub(' ', s); s = re.sub(r'\s+', ' ', s).strip()
    return ' '.join(s.split()[:5]) or name

def norm(s): return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

def search(q):
    return get(SEARCH + urllib.parse.quote(q, safe='') + "?page=1&per_page=10").get("result") or []

def detail(slug):
    return get(DETAIL + urllib.parse.quote(slug, safe='') + "?location_id=")

def best(name, results):
    nn = norm(name); scored = []
    for o in results:
        cn = norm(o.get('name', ''))
        if not cn: continue
        r = difflib.SequenceMatcher(None, nn, cn).ratio()
        if nn.split()[:1] == cn.split()[:1]: r += 0.15
        scored.append((r, o))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else (0, None)

def clean_nie(s):
    return re.sub(r'(?i)^\s*bpom\s*[:\-]?\s*', '', s).strip() if s else ""

def find_field(d, key):
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                if k.lower() == key and not isinstance(v, (dict, list)): return v
                if isinstance(v, (dict, list)): stack.append(v)
        elif isinstance(o, list): stack.extend(o)
    return None

def main():
    products = json.load(open(PRODUCTS, encoding="utf-8"))
    prices = json.load(open(OUT_PRICES, encoding="utf-8")) if os.path.exists(OUT_PRICES) and not SAMPLE else {}
    details = json.load(open(OUT_DETAILS, encoding="utf-8")) if os.path.exists(OUT_DETAILS) and not SAMPLE else {}

    todo = [p for p in products if p["id"] not in prices]
    if SAMPLE: todo = todo[::max(1, len(todo)//SAMPLE)][:SAMPLE]
    print(f"{len(products)} products, {len(prices)} done, {len(todo)} to fetch"
          + (" (SAMPLE)" if SAMPLE else ""), flush=True)

    errors = 0
    for n, p in enumerate(todo, 1):
        slug, name = p["id"], p["name"]
        try:
            score, m = best(name, search(clean_query(name)))
            if not m:
                prices[slug] = {"min": 0, "max": 0, "score": 0, "halo_name": ""}
            else:
                hslug = m.get("slug", "")
                rec = {"min": m.get("min_price", 0), "max": m.get("base_price", m.get("min_price", 0)),
                       "halo_name": m.get("name", ""), "halo_slug": hslug, "score": round(score, 3),
                       "ctrl": m.get("controlled_substance_type", ""), "rx": bool(m.get("prescription_required", False))}
                prices[slug] = rec
                if score >= 0.7 and hslug:           # only open confident matches
                    dd = detail(hslug)
                    details[slug] = {"nie": clean_nie(find_field(dd, "bpom_number")),
                                     "manufacturer": (find_field(dd, "manufacturer_name") or "").strip(),
                                     "halo_slug": hslug}
                    if SAMPLE:
                        print(f"  {name[:34]:34} Rp{rec['min']}-{rec['max']} NIE={details[slug]['nie'] or '-'}", flush=True)
                    time.sleep(DELAY)
            errors = 0
        except Exception as e:
            errors += 1; prices[slug] = {"min": 0, "max": 0, "score": 0, "error": str(e)[:80]}
            if errors >= 5: print("  backing off 30s", flush=True); time.sleep(30); errors = 0
        if not SAMPLE and n % 25 == 0:
            json.dump(prices, open(OUT_PRICES, "w", encoding="utf-8"), ensure_ascii=False)
            json.dump(details, open(OUT_DETAILS, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {len(prices)} processed | {sum(1 for v in details.values() if v.get('nie'))} NIEs", flush=True)
        time.sleep(DELAY)

    if not SAMPLE:
        json.dump(prices, open(OUT_PRICES, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(details, open(OUT_DETAILS, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"DONE. {len(prices)} products, {sum(1 for v in details.values() if v.get('nie'))} NIEs.", flush=True)

if __name__ == "__main__":
    main()
