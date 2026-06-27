#!/usr/bin/env python3
"""Map the BaliPharma Shopify export -> products.json + a data-quality report.

Decisions baked in (per operator):
- Import ALL sellable products (exclude Type == 'Drug Information', which are not sold).
- Keep the halodoc x1.5 pricing model: halodoc_price_idr stays 0 (TODO). The export's
  Variant Price (USD) is preserved as ref_price_usd so it isn't lost.
- NIE absent in export -> left empty; product page shows an 'available on request' fallback.
- dosage_form derived from keywords; strength parsed from the title. Both best-effort.
"""
import csv, re, json, html, sys

csv.field_size_limit(10**8)
SRC = "products_export_1.csv"
OUT = "src/data/products.json"
REPORT = "DATA_QUALITY_REPORT.md"

FORM_VOCAB = [
    ("suppositor", "Suppository"), ("inhaler", "Inhaler"), ("injection", "Injection"),
    ("suspension", "Suspension"), ("ointment", "Ointment"), ("solution", "Solution"),
    ("lozenge", "Lozenge"), ("capsule", "Capsule"), ("caplet", "Caplet"),
    ("tablet", "Tablet"), ("syrup", "Syrup"), ("cream", "Cream"), ("drops", "Drops"),
    ("spray", "Spray"), ("powder", "Powder"), ("patch", "Patch"), ("gel", "Gel"),
    ("pen", "Injection Pen"), ("vial", "Injection"),
]
# strength: number (+optional decimal) + unit, optionally a ratio like 10mg/5ml or 0.1%
STRENGTH_RE = re.compile(
    r'(\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|g|ml|iu|%)(?:\s*/\s*\d*(?:[.,]\d+)?\s*(?:ml|mg|g|dose|tab|cap|hour|h))?)',
    re.I,
)

def field(body, key):
    m = re.search(r'<p>\s*' + re.escape(key) + r'\s*:(.*?)</p>', body, re.I | re.S)
    if not m:
        return ""
    txt = re.sub(r'<[^>]+>', ' ', m.group(1))
    txt = html.unescape(txt)
    return re.sub(r'\s+', ' ', txt).strip()

def derive_form(title, packaging, body):
    hay = f"{title} {packaging} {body}".lower()
    for needle, label in FORM_VOCAB:
        if needle in hay:
            return label
    return ""

def derive_strength(title):
    m = STRENGTH_RE.search(title or "")
    if not m:
        return ""
    s = m.group(1)
    s = re.sub(r'\s+', '', s).replace(',', '.')
    # normalise: put a space before the unit cluster -> "500 mg"
    s = re.sub(r'(?i)^(\d+(?:\.\d+)?)(mg|mcg|µg|g|ml|iu|%)', r'\1 \2', s)
    return s

products = []
seen = set()
missing = {k: 0 for k in ["nie", "dosage_form", "strength", "composition", "packaging", "image_url", "price"]}
total = 0
skipped_info = 0

with open(SRC, newline='', encoding='utf-8', errors='replace') as f:
    r = csv.DictReader(f)
    for row in r:
        title = (row.get('Title') or '').strip()
        handle = (row.get('Handle') or '').strip()
        if not title or not handle:
            continue
        if handle in seen:            # one row per product (skip extra image/variant rows)
            continue
        seen.add(handle)
        ptype = (row.get('Type') or '').strip()
        if ptype == 'Drug Information':
            skipped_info += 1
            continue

        body = row.get('Body (HTML)') or ''
        composition = field(body, 'composition')
        packaging = field(body, 'packaging')
        description = field(body, 'description')
        name = field(body, 'name') or title

        dosage_form = derive_form(title, packaging, body)
        strength = derive_strength(title) or derive_strength(name)

        img = (row.get('Image Src') or '').strip()

        try:
            ref_usd = round(float(row.get('Variant Price') or 0), 2)
        except ValueError:
            ref_usd = 0.0

        qty = (row.get('Variant Inventory Qty') or '').strip()
        status = (row.get('Status') or '').strip().lower()
        in_stock = status == 'active' and qty not in ('', '0', '-')

        category = ptype or 'Other Medications'

        total += 1
        if not composition: missing['composition'] += 1
        if not packaging:   missing['packaging'] += 1
        if not dosage_form: missing['dosage_form'] += 1
        if not strength:    missing['strength'] += 1
        if not img:         missing['image_url'] += 1
        missing['nie'] += 1            # NIE never present in this export
        if ref_usd <= 0:    missing['price'] += 1

        entry = {
            "id": handle,
            "name": name[:160],
            "nie": "",                 # TODO: not in export — page shows 'available on request'
            "category": category,
            "dosage_form": dosage_form,
            "packaging": packaging,
            "strength": strength,
            "composition": composition,
            "description": description[:600],
            "image_url": img or "/images/products/placeholder.svg",
            "halodoc_price_idr": 0,    # halodoc x1.5 model — operator to populate
            "ref_price_usd": ref_usd,  # preserved export price (USD), not displayed yet
            "in_stock": in_stock,
            "stock_note": "",
        }
        products.append(entry)

products.sort(key=lambda p: p["name"].lower())

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=1)

# ---- data-quality report ----
def pct(n): return f"{100*n/total:.0f}%" if total else "0%"
cats = {}
for p in products:
    cats[p['category']] = cats.get(p['category'], 0) + 1

lines = []
lines.append("# BaliPharma Import — Data Quality Report\n")
lines.append(f"Generated from `{SRC}`.\n")
lines.append(f"- **Products imported:** {total}")
lines.append(f"- Info-only pages skipped (Type = 'Drug Information'): {skipped_info}\n")
lines.append("## Missing / unavailable fields\n")
lines.append("| Field | Missing | % of catalog | Notes |")
lines.append("|---|---:|---:|---|")
lines.append(f"| NIE (marketing auth. no.) | {missing['nie']} | {pct(missing['nie'])} | **Not in export.** Page shows 'available on request' until supplied. BPOM-required. |")
lines.append(f"| Strength | {missing['strength']} | {pct(missing['strength'])} | Parsed from product title; blank where no number/unit found. |")
lines.append(f"| Dosage form | {missing['dosage_form']} | {pct(missing['dosage_form'])} | Derived from keywords; blank where none matched. |")
lines.append(f"| Composition | {missing['composition']} | {pct(missing['composition'])} | From export body. |")
lines.append(f"| Packaging | {missing['packaging']} | {pct(missing['packaging'])} | From export body. |")
lines.append(f"| Image | {missing['image_url']} | {pct(missing['image_url'])} | Falls back to placeholder.svg. |")
lines.append(f"| Price (export ref USD) | {missing['price']} | {pct(missing['price'])} | Active price is halodoc×1.5 (currently 0 → 'Price coming soon'). |")
lines.append("\n## Categories (from Shopify 'Type')\n")
lines.append("| Category | Products |")
lines.append("|---|---:|")
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    lines.append(f"| {c} | {n} |")
lines.append("\n## ⚠️ Pharmacist review needed")
lines.append("- **NIE numbers** must be added for full BPOM compliance (every product page).")
lines.append("- **Controlled substances / narcotics**: the brief excludes these. This import trusts")
lines.append("  the pharmacy's own published catalog — the responsible pharmacist should confirm no")
lines.append("  narcotics/psychotropics are listed before launch.")
lines.append("- **Pricing**: all products currently show 'Price coming soon' (halodoc×1.5 model with")
lines.append("  halodoc_price_idr=0). Export USD prices are preserved in `ref_price_usd` if you choose")
lines.append("  to switch to displaying them.")

with open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines) + "\n")

print(f"Imported {total} products -> {OUT}")
print(f"Skipped {skipped_info} info-only pages")
print("Missing:", {k: v for k, v in missing.items()})
print(f"Report -> {REPORT}")
