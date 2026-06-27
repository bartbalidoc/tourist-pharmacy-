#!/usr/bin/env python3
"""Flag controlled / psychiatric ("specialist-only") medicines in products.json.

Two sources, OR'd:
  1. Halodoc's `ctrl == "purchasable_controlled_substance"` (from halodoc_prices.json).
  2. A curated psychotropic active-ingredient list matched against each product's composition
     (catches any the scrape missed or mismatched).

Sets `"controlled": true/false` on every product and writes a short report. These are then
shown with a "specialist consultation required" label, kept out of the popular rail, and can be
hidden site-wide via HIDE_CONTROLLED in src/lib/site.ts.
"""
import json, re, os

PRODUCTS = "src/data/products.json"
PRICES = "halodoc_prices.json"
REPORT = "CONTROLLED_REPORT.md"

# Active ingredients of antidepressants, antipsychotics, mood stabilisers, benzodiazepines/
# hypnotics, and other commonly-controlled psychotropics. Lowercase, matched as whole words.
PSYCHOTROPIC = {
    # antidepressants
    "sertraline", "fluoxetine", "paroxetine", "escitalopram", "citalopram", "fluvoxamine",
    "venlafaxine", "duloxetine", "amitriptyline", "clomipramine", "mirtazapine", "trazodone",
    "vortioxetine", "tianeptine", "maprotiline", "imipramine", "agomelatine",
    # antipsychotics
    "olanzapine", "risperidone", "quetiapine", "aripiprazole", "clozapine", "clozapin",
    "haloperidol", "chlorpromazine", "sulpiride", "paliperidone", "zotepine", "trifluoperazine",
    "fluphenazine", "amisulpride", "lurasidone",
    # mood stabilisers / psych-used anticonvulsants
    "lithium", "valproate", "valproic", "divalproex", "lamotrigine", "carbamazepine",
    # benzodiazepines / anxiolytics / hypnotics
    "diazepam", "lorazepam", "alprazolam", "clonazepam", "bromazepam", "clobazam", "midazolam",
    "estazolam", "nitrazepam", "zolpidem", "buspirone", "chlordiazepoxide",
    # pain/neuro psychotropics commonly controlled
    "pregabalin", "gabapentin",
    # adhd
    "methylphenidate", "atomoxetine",
}

products = json.load(open(PRODUCTS, encoding="utf-8"))
prices = json.load(open(PRICES, encoding="utf-8")) if os.path.exists(PRICES) else {}

halo_controlled = {s for s, v in prices.items()
                   if (v.get("ctrl") or "") == "purchasable_controlled_substance"}

def ingredient_hit(comp: str):
    words = set(re.findall(r"[a-z]+", (comp or "").lower()))
    return PSYCHOTROPIC & words

by_halo, by_ingredient, both = [], [], []
for p in products:
    halo = p["id"] in halo_controlled
    hits = ingredient_hit(p.get("composition", ""))
    p["controlled"] = bool(halo or hits)
    if p["controlled"]:
        if halo and hits: both.append(p["name"])
        elif halo: by_halo.append(p["name"])
        else: by_ingredient.append((p["name"], sorted(hits)))

json.dump(products, open(PRODUCTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

total = len(products)
flagged = sum(1 for p in products if p.get("controlled"))
L = [
    "# Controlled / Specialist-only Medicines\n",
    f"- Products: {total}",
    f"- **Flagged controlled: {flagged}** ({100*flagged//total}%)",
    f"  - via Halodoc controlled flag only: {len(by_halo)}",
    f"  - via psychotropic ingredient only: {len(by_ingredient)}",
    f"  - both: {len(both)}\n",
    "These show a 'Controlled · specialist consultation required' label, are kept out of the home",
    "popular rail, and are hidden everywhere when HIDE_CONTROLLED=true in src/lib/site.ts.\n",
    "## Flagged by ingredient (review — caught beyond Halodoc's list)",
]
for name, ings in sorted(by_ingredient)[:200]:
    L.append(f"- {name}  ({', '.join(ings)})")
open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"Flagged {flagged}/{total} controlled (halo:{len(by_halo)} ingredient:{len(by_ingredient)} both:{len(both)}). Report -> {REPORT}")
