#!/usr/bin/env python3
"""Merge scraped NIE + manufacturer (halodoc_details.json) into products.json.

Only fills a product's `nie` / `manufacturer` when it's currently empty, so any
manually-entered values are never overwritten. Writes a short report.
"""
import json

PRODUCTS = "src/data/products.json"
DETAILS = "halodoc_details.json"
REPORT = "NIE_MERGE_REPORT.md"

products = json.load(open(PRODUCTS, encoding="utf-8"))
details = json.load(open(DETAILS, encoding="utf-8"))

nie_set = mfr_set = 0
for p in products:
    rec = details.get(p["id"])
    if not rec:
        continue
    if rec.get("nie") and not p.get("nie"):
        p["nie"] = rec["nie"]
        nie_set += 1
    if rec.get("manufacturer") and not p.get("manufacturer"):
        p["manufacturer"] = rec["manufacturer"]
        mfr_set += 1

json.dump(products, open(PRODUCTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

total = len(products)
with_nie = sum(1 for p in products if p.get("nie"))
open(REPORT, "w", encoding="utf-8").write(
    f"# NIE Merge Report\n\n"
    f"- Products: {total}\n"
    f"- NIE numbers set this run: {nie_set}\n"
    f"- Manufacturers set this run: {mfr_set}\n"
    f"- **Total products with an NIE now: {with_nie} ({100*with_nie//total}%)**\n"
    f"- Products still without NIE: {total - with_nie} "
    f"(no confident Halodoc match, or Halodoc had no BPOM number)\n"
)
print(f"Set {nie_set} NIEs, {mfr_set} manufacturers. Total with NIE: {with_nie}/{total}.")
print(f"Report -> {REPORT}")
