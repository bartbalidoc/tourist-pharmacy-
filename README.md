# Tourist Pharmacy

> 📚 **Key docs:** [DOCS.md](DOCS.md) — how everything works, where it's stored & **why** (incl. a
> decision log) · [BRAND.md](BRAND.md) — logo system + colour/identity & rationale ·
> [DEPLOY.md](DEPLOY.md) — go live (public, static) · [DEPLOY_REVIEW.md](DEPLOY_REVIEW.md) — the
> login-gated review build on the droplet · **[UPDATING.md](UPDATING.md) — how to push changes &
> redeploy (start here for everyday updates)** · [SERVICES.md](SERVICES.md) — every API/key & where it
> goes (reusable for other projects; real values stay in gitignored `SECRETS.local.md`).
> *(All kept up to date as decisions are made.)*

> **Launch status: technically ready to go live.** 3,555 products; **99% priced** (Halodoc ×1.5,
> live USD+IDR ranges) and **99% with NIE + manufacturer**. SEO (sitemap, robots, JSON-LD), pinned
> map, custom 404, legal drafts, and deploy configs all in place. See [DEPLOY.md](DEPLOY.md) to ship.
>
> **Before launch, the operator still needs to:** add the Calendly URL, pharmacist schedule, and full
> Jakarta office address; have the Privacy/Terms **drafts** reviewed by legal counsel; sign off on the
> 37 Halodoc-flagged controlled meds (`PRICE_MERGE_REPORT.md`); optionally swap the text logo for an
> SVG and confirm the exact pharmacy GPS coordinate (currently geocoded/approximate).



A static, BPOM-compliant **catalog + booking funnel** for English-speaking tourists and expats in
Bali. Built with **Astro** (static output, zero-JS by default) so it loads fast on slow Bali
connections and deploys as a plain folder of files. Operated by PT Sehat Investasi Digital.

> This is **not** a cart/checkout. The journey is: browse product → read full detail →
> "Get Prescription & Order" → booking page → BaliDoc consultation → prescription → pharmacy dispenses.

---

## Run it

```bash
npm install      # one time
npm run dev      # local dev server at http://localhost:4321
npm run build    # static site -> dist/
npm run preview  # preview the production build
```

Deploy the `dist/` folder to any static host (Netlify, Vercel, Cloudflare Pages, etc.).

---

## Project structure

```
src/
├─ data/products.json     ← THE product library (edit this to add products)
├─ lib/
│  ├─ site.ts             ← brand, WhatsApp, compliance data, API key, Calendly  ← MOST PLACEHOLDERS HERE
│  ├─ products.ts         ← loads + validates products.json, derives prices
│  ├─ pricing.ts          ← price math + IDR/USD formatting
│  └─ currency.ts         ← live IDR→USD rate (cached 1h, fails gracefully)
├─ components/            ← Nav, Footer, ProductCard, PriceDisplay, RedLabelNotice, StickyWhatsApp
├─ layouts/               ← BaseLayout (SEO/OG), LegalLayout
├─ pages/                 ← index, products/, about, booking, privacy, terms
└─ styles/tokens.css      ← all colors/fonts/spacing (the design system)
public/images/products/   ← product photos (replace placeholder.svg)
```

---

## ✅ TODO — replace these placeholders before launch

All are marked in code with `TODO: replace`. Search the repo for `TODO: replace` to find every one.

### 1. Product pricing — DONE (scraped from Halodoc)
Prices were scraped from Halodoc and merged in: **~95% of products are priced** (`halodoc_price_min_idr`
/ `halodoc_price_max_idr`). Retail = Halodoc price **× 1.5**, shown as a **USD range (live) + IDR range**.
Products without a confident match show "Price coming soon".

Pipeline (all in `scripts/`):
- **`halodoc_full.py`** → ⭐ preferred for re-imports: ONE pass that gets price + NIE + manufacturer
  (search to locate each product, then one detail call for everything). Writes both
  `halodoc_prices.json` and `halodoc_details.json`. Optional int arg = sample dry-run.
- `halodoc_prices.py` → prices only (search API). *(Used for the first pass of the current data.)*
- `halodoc_nie.py` → NIE + manufacturer only (detail API), for products already price-matched.
  *(Used as the second pass for the current data, since NIE was discovered after prices.)*
- `merge_prices.py` → applies confident price matches (score ≥ 0.7); writes **`PRICE_MERGE_REPORT.md`**
  + **`price_review.csv`**.
- `merge_nie.py` → fills empty `nie`/`manufacturer` from `halodoc_details.json`; writes `NIE_MERGE_REPORT.md`.
- `progress_dashboard.py` → live progress UI at http://localhost:8765 (tracks both phases).
- `import_products.py` → rebuild `products.json` from a new `products_export_*.csv`.

**Re-import flow:** `import_products.py` → `halodoc_full.py` → `merge_prices.py` → `merge_nie.py` → `npm run build`.

> Original BaliPharma export USD price is also kept per product as `ref_price_usd` (reference only).
> See **`DATA_QUALITY_REPORT.md`** for per-field import coverage.

**Open price items:** ~133 products had no confident Halodoc match and 13 are low-confidence
(`price_review.csv`) — both show "Price coming soon" until reviewed. **37–38 products are flagged by
Halodoc as controlled substances** (kept per your decision; listed in `PRICE_MERGE_REPORT.md` for
pharmacist sign-off).

### 2. Currency API key (`src/lib/site.ts` → `CURRENCY_API_KEY`)
Sign up free at **exchangerate-api.com** (no credit card) and paste your key in place of
`FREE_KEY_PLACEHOLDER`. Until then, products show IDR only with "USD price temporarily unavailable."

> **Getting the key via BEX** (the Claude browser extension). Paste this prompt into BEX and let it
> do the signup + key generation in your browser:
>
> ```
> Go to https://www.exchangerate-api.com and sign up for the FREE plan
> (no credit card) using my email info.balidoctor@gmail.com. Complete any
> email verification. On the dashboard, copy my API key and report it back
> to me, plus confirm this endpoint returns "result":"success":
> https://v6.exchangerate-api.com/v6/<MY_KEY>/latest/IDR
> ```
>
> Then paste the key BEX gives you into `CURRENCY_API_KEY` in [src/lib/site.ts](src/lib/site.ts)
> (replace `FREE_KEY_PLACEHOLDER`) and run `npm run build`. USD prices go live.

### 3. Compliance data (`src/lib/site.ts`)
- `PHARMACIST.sipa` → **DONE** (`570/SIPA/0025/III/DPMPTSP/2025`, read from the SIPA certificate)
- `PHARMACY.gpsCoordinates` → `[GPS_COORDINATES]` (also drives the About-page map pin) — still needed
- `PHARMACIST.schedule` → `[PHARMACIST_SCHEDULE]` (e.g. `Mon–Sat, 08:00–20:00 WITA`) — still needed
- `OPERATOR.office` → full Jakarta office address — still needed

### 3b. NIE (marketing authorization numbers) — BPOM-required, currently missing
The BaliPharma export contained **no NIE numbers**, so every product page shows
*"Available on request — shown on original product packaging"* for the NIE field. This is a
**BPOM compliance gap**: NIE must be displayed per product. Add the NIE to each product's `"nie"`
field in `products.json` (sourced via cekbpom.pom.go.id or pharmacy records). The
responsible pharmacist should also confirm no controlled substances/narcotics are in the catalog.

### 4. Booking (`src/lib/site.ts` + `src/pages/booking.astro`)
- `CALENDLY_URL` → your BaliDoc Calendly link (the placeholder shows a "Book via WhatsApp" fallback).
  When set, also uncomment the Calendly widget `<script>` at the bottom of `booking.astro`.
- `[X] hours` in Step 3 → real dispensing turnaround time.

### 5. Legal copy (`src/pages/privacy.astro`, `src/pages/terms.astro`)
Layouts are built; paste final copy and set the `[DATE]`.

### 6. Branding
- Replace the text logo in `Nav.astro` with an SVG when ready.
- Replace `public/images/products/placeholder.svg` with real product photos; set each product's
  `image_url` in `products.json`.

---

## Adding / editing products

Edit `src/data/products.json`. Each entry is validated at build time (the build fails loudly if a
required field is missing). Required fields:

```jsonc
{
  "id": "unique-slug",            // becomes the URL: /products/unique-slug
  "name": "Amoxicillin 500mg",
  "nie": "GKL...",                // marketing authorization number
  "category": "Antibiotics",
  "dosage_form": "Capsule",
  "packaging": "Box of 10 strips @ 10 capsules",
  "strength": "500 mg",
  "composition": "Each capsule contains ...",
  "image_url": "/images/products/amoxicillin.jpg",
  "halodoc_price_idr": 0,         // set the real Halodoc price; retail = ×1.5, USD live
  "in_stock": true,
  "stock_note": ""                // optional, e.g. "Available on request"
}
```

Add 1 object per product. The catalog grid, filters, product page, and SEO are all generated
automatically — no other files to touch.

---

## Design notes

The aesthetic is a deliberate **warm "tropical apothecary"** (terracotta + jungle green + cream),
chosen over the default clinical white-and-blue because the visitor is often anxious and far from
home — warmth reads as *care* and *trust*, not bureaucracy. The full rationale is at the top of
`src/styles/tokens.css`. Change any color, font, or spacing value there to restyle the whole site.

Performance is treated as a hard constraint (Bali connections can lag): static HTML, near-zero JS,
lazy-loaded map, 1-hour-cached currency rate, and graceful fallbacks everywhere.
