# BaliPharma Import — Data Quality Report

Generated from `products_export_1.csv`.

- **Products imported:** 3555
- Info-only pages skipped (Type = 'Drug Information'): 20

## Missing / unavailable fields

| Field | Missing | % of catalog | Notes |
|---|---:|---:|---|
| NIE (marketing auth. no.) | 3555 | 100% | **Not in export.** Page shows 'available on request' until supplied. BPOM-required. |
| Strength | 258 | 7% | Parsed from product title; blank where no number/unit found. |
| Dosage form | 45 | 1% | Derived from keywords; blank where none matched. |
| Composition | 1 | 0% | From export body. |
| Packaging | 1 | 0% | From export body. |
| Image | 0 | 0% | Falls back to placeholder.svg. |
| Price (export ref USD) | 5 | 0% | Active price is halodoc×1.5 (currently 0 → 'Price coming soon'). |

## Categories (from Shopify 'Type')

| Category | Products |
|---|---:|
| Drug | 925 |
| Infection | 741 |
| Other Medications | 348 |
| Fever & Pain | 280 |
| Digestive Problems | 279 |
| Skin Conditions | 276 |
| Eye Problems | 143 |
| Allergy | 126 |
| Bone & Joint Pain | 93 |
| Cancer Medicine | 83 |
| Female Hormones | 32 |
| Inhalers | 26 |
| Oral Contraception | 25 |
| Erectile Dysfunction | 24 |
| Insulin | 23 |
| Fertility & More | 22 |
| Asthma | 22 |
| Immunosuppressant Drugs | 20 |
| Health & Immune | 16 |
| ENT problems | 14 |
| Mature | 8 |
| Diabetes | 6 |
| Special Supplements | 6 |
| Woman | 6 |
| Medicines & Supplements | 5 |
| For Everyday | 4 |
| Self Care | 1 |
| Bones & Joints | 1 |

## ⚠️ Pharmacist review needed
- **NIE numbers** must be added for full BPOM compliance (every product page).
- **Controlled substances / narcotics**: the brief excludes these. This import trusts
  the pharmacy's own published catalog — the responsible pharmacist should confirm no
  narcotics/psychotropics are listed before launch.
- **Pricing**: all products currently show 'Price coming soon' (halodoc×1.5 model with
  halodoc_price_idr=0). Export USD prices are preserved in `ref_price_usd` if you choose
  to switch to displaying them.
