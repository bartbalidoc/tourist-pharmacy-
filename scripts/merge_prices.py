#!/usr/bin/env python3
"""Merge scraped Halodoc prices into products.json + write a merge report.

Applies a Halodoc price range to a product only when the match score is confident
(>= THRESHOLD). Sets halodoc_price_min_idr / halodoc_price_max_idr (retail ×1.5 and live
USD are computed downstream). Lower-confidence matches are left as 'Price coming soon' and
listed in the report for manual review. Controlled substances (per Halodoc) are flagged.
"""
import json, csv

THRESHOLD = 0.7
PRODUCTS = "src/data/products.json"
PRICES = "halodoc_prices.json"
REPORT = "PRICE_MERGE_REPORT.md"
REVIEW_CSV = "price_review.csv"

products = json.load(open(PRODUCTS, encoding="utf-8"))
prices = json.load(open(PRICES, encoding="utf-8"))

applied = 0
ranged = 0
review = []      # 0 < score < THRESHOLD
nomatch = []     # no result / score 0
controlled = []  # Halodoc flags as controlled substance

for p in products:
    rec = prices.get(p["id"])
    # reset, then set from confident matches
    p["halodoc_price_min_idr"] = 0
    p["halodoc_price_max_idr"] = 0
    if not rec:
        nomatch.append(p)
        continue
    score = rec.get("score", 0)
    mn, mx = rec.get("min", 0) or 0, rec.get("max", 0) or 0
    ctrl = (rec.get("ctrl") or "")
    if ctrl and ctrl != "not_controlled_substance":
        controlled.append((p, rec))
    if score >= THRESHOLD and mn > 0:
        p["halodoc_price_min_idr"] = mn
        p["halodoc_price_max_idr"] = max(mx, mn)
        applied += 1
        if mx > mn:
            ranged += 1
    elif score > 0 and mn > 0:
        review.append((p, rec))
    else:
        nomatch.append(p)

json.dump(products, open(PRODUCTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# review CSV (low-confidence matches to eyeball)
with open(REVIEW_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["our_slug", "our_name", "halodoc_name", "score", "min_idr", "max_idr", "halo_slug"])
    for p, rec in sorted(review, key=lambda x: -x[1].get("score", 0)):
        w.writerow([p["id"], p["name"], rec.get("halo_name", ""), rec.get("score"),
                    rec.get("min"), rec.get("max"), rec.get("halo_slug", "")])

total = len(products)
def pct(n): return f"{100*n/total:.0f}%"
L = []
L.append("# Halodoc Price Merge Report\n")
L.append(f"- **Products:** {total}")
L.append(f"- **Prices applied (score ≥ {THRESHOLD}):** {applied} ({pct(applied)}) — of which {ranged} are ranges")
L.append(f"- **Low-confidence, needs review (left blank):** {len(review)} → see `{REVIEW_CSV}`")
L.append(f"- **No confident match (left blank):** {len(nomatch)}")
L.append(f"- **Flagged controlled substance by Halodoc:** {len(controlled)}\n")
if controlled:
    L.append("## ⚠️ Controlled substances flagged by Halodoc (pharmacist review — brief excludes these)\n")
    for p, rec in controlled[:200]:
        L.append(f"- {p['name']}  →  {rec.get('halo_name','')}  ({rec.get('ctrl')})")
    L.append("")
open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")

print(f"Applied {applied} prices ({ranged} ranges). Review: {len(review)}. No match: {len(nomatch)}. Controlled: {len(controlled)}.")
print(f"Reports -> {REPORT}, {REVIEW_CSV}")
