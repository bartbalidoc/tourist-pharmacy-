#!/usr/bin/env python3
"""Recovery pass for products that got no confident Halodoc match the first time.

Tries several looser query variants (brand+strength, fewer words, active ingredient from
composition). Accepts the first variant that yields a confident match (score >= 0.7) and
updates halodoc_prices.json in place. Concurrent.
"""
import json, re, os, urllib.parse, urllib.request, difflib
from concurrent.futures import ThreadPoolExecutor, as_completed

SEARCH = "https://customers.api.halodoc.com/magneto-api/v1/buy-medicine/products/search/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PRICES = "halodoc_prices.json"
PRODUCTS = "src/data/products.json"
WORKERS = 16
THRESH = 0.7

NOISE = re.compile(r'\b(box|boxes|strip|strips|tablet|tablets|chewable|caplet|caplets|capsule|capsules|'
                   r'btl|botol|tube|sachet|hemat|borongan|wholesale|savings|whole|routine|per|pcs|fc|'
                   r'salut|selaput|film|soft|injection|inj|pills|pill|kb|fe)\b', re.I)

def norm(s): return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def variants(name, composition):
    base = re.sub(r'\(.*?\)', ' ', name)
    base = re.sub(r'-\s*\w.*$', ' ', base)          # drop "- Wholesale ..." tails
    base = NOISE.sub(' ', base); base = re.sub(r'\s+', ' ', base).strip()
    words = base.split()
    vs = []
    if words: vs.append(' '.join(words[:3]))
    if words: vs.append(' '.join(words[:2]))
    # active ingredient (first chemical-ish token of composition)
    if composition:
        c = re.sub(r'(?i)each.*?contains|:|;', ' ', composition)
        c = re.sub(r'\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|%)', ' ', c)
        ct = [w for w in re.split(r'[\s,]+', c) if len(w) > 4][:2]
        # pair active ingredient with strength if present
        m = re.search(r'\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|%)', name)
        if ct:
            vs.append((ct[0] + (' ' + m.group(0) if m else '')).strip())
    seen, out = set(), []
    for v in vs:
        v = v.strip()
        if v and v.lower() not in seen:
            seen.add(v.lower()); out.append(v)
    return out

def search(q):
    url = SEARCH + urllib.parse.quote(q, safe='') + "?page=1&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8', 'replace')).get("result") or []

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

def main():
    prices = json.load(open(PRICES, encoding="utf-8"))
    prods = {p['id']: p for p in json.load(open(PRODUCTS, encoding="utf-8"))}
    miss = [s for s, v in prices.items() if v.get('score', 0) < THRESH or not (v.get('min', 0) or 0)]
    print(f"{len(miss)} products to retry", flush=True)

    def work(slug):
        p = prods.get(slug)
        if not p: return slug, None
        for q in variants(p['name'], p.get('composition', '')):
            try:
                score, m = best(p['name'], search(q))
                if m and score >= THRESH:
                    return slug, {"min": m.get("min_price", 0),
                                  "max": m.get("base_price", m.get("min_price", 0)),
                                  "halo_name": m.get("name", ""), "halo_slug": m.get("slug", ""),
                                  "score": round(score, 3), "ctrl": m.get("controlled_substance_type", ""),
                                  "rx": bool(m.get("prescription_required", False))}
            except Exception:
                continue
        return slug, None

    recovered = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for fut in as_completed([ex.submit(work, s) for s in miss]):
            slug, rec = fut.result()
            if rec:
                prices[slug] = rec; recovered += 1
    json.dump(prices, open(PRICES, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Recovered {recovered} of {len(miss)} previously-unmatched products.", flush=True)

if __name__ == "__main__":
    main()
