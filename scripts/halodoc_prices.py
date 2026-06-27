#!/usr/bin/env python3
"""Look up Halodoc prices for every product and write them to halodoc_prices.json.

Uses Halodoc's product search API (query in the PATH). Fuzzy-matches each BaliPharma
product to the best Halodoc result by name and records min_price / base_price (the
natural low–high range Halodoc shows), plus match score and Halodoc's controlled-substance
flag. Resumable: re-run to continue where it left off.

Output (keyed by our slug):
  { "<slug>": {"min": 137000, "max": 173500, "halo_name": "...", "halo_slug": "...",
               "score": 1.13, "ctrl": "not_controlled_substance", "rx": true} }

This writes ONLY halodoc_prices.json — products.json is updated by a separate merge step,
so the scrape stays independent and reviewable.
"""
import json, re, sys, time, os, urllib.parse, urllib.request, difflib

API = "https://customers.api.halodoc.com/magneto-api/v1/buy-medicine/products/search/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PRODUCTS = "src/data/products.json"
OUT = "halodoc_prices.json"
DELAY = 1.0

NOISE = re.compile(r'\b(box|strip|strips|tablet|tablets|caplet|caplets|capsule|capsules|btl|botol|'
                   r'tube|sachet|hemat|borongan|per|pcs|fc|salut|selaput|film|soft)\b', re.I)

def clean_query(name):
    s = re.sub(r'\(.*?\)', ' ', name)
    s = re.sub(r'@.*$', ' ', s)
    s = NOISE.sub(' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return ' '.join(s.split()[:5]) or name

def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def fetch(q):
    # safe='' so '/' in names (e.g. "125 mg/5 ml") is encoded, not treated as a path separator.
    url = API + urllib.parse.quote(q, safe='') + "?page=1&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

def best(name, results):
    nn = norm(name)
    scored = []
    for o in results:
        cn = norm(o.get('name', ''))
        if not cn:
            continue
        ratio = difflib.SequenceMatcher(None, nn, cn).ratio()
        if nn.split()[:1] == cn.split()[:1]:
            ratio += 0.15
        scored.append((ratio, o))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else (0, None)

def main():
    products = json.load(open(PRODUCTS, encoding="utf-8"))
    done = {}
    if os.path.exists(OUT):
        try:
            done = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            done = {}

    todo = [p for p in products if p["id"] not in done]
    print(f"{len(products)} products, {len(done)} already done, {len(todo)} to fetch", flush=True)

    errors = 0
    for n, p in enumerate(todo, 1):
        slug, name = p["id"], p["name"]
        try:
            data = fetch(clean_query(name))
            results = data.get("result") if isinstance(data, dict) else []
            score, m = best(name, results or [])
            if m:
                done[slug] = {
                    "min": m.get("min_price", 0),
                    "max": m.get("base_price", m.get("min_price", 0)),
                    "halo_name": m.get("name", ""),
                    "halo_slug": m.get("slug", ""),
                    "score": round(score, 3),
                    "ctrl": m.get("controlled_substance_type", ""),
                    "rx": bool(m.get("prescription_required", False)),
                }
            else:
                done[slug] = {"min": 0, "max": 0, "score": 0, "halo_name": ""}
            errors = 0
        except Exception as e:
            errors += 1
            done[slug] = {"min": 0, "max": 0, "score": 0, "error": str(e)[:80]}
            if errors >= 5:
                print(f"  {errors} consecutive errors — backing off 30s", flush=True)
                time.sleep(30)
                errors = 0

        if n % 25 == 0:
            json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
            matched = sum(1 for v in done.values() if v.get("score", 0) >= 0.7)
            print(f"  {len(done)}/{len(products)} processed | {matched} confident matches", flush=True)
        time.sleep(DELAY)

    json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    matched = sum(1 for v in done.values() if v.get("score", 0) >= 0.7)
    print(f"DONE. {len(done)} processed, {matched} confident matches -> {OUT}", flush=True)

if __name__ == "__main__":
    main()
