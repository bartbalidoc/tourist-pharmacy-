# Tourist Pharmacy — Project Reference & Decision Log

How everything works, where it's stored, and **why** it was built this way. Companion docs:
[`README.md`](README.md) (setup + TODOs), [`BRAND.md`](BRAND.md) (identity), [`DEPLOY.md`](DEPLOY.md).

---

## 1. What this is
A **static** (Astro) website for **Tourist Pharmacy** — an English-speaking online pharmacy for
tourists/expats in Bali. It is a **catalog + prescription funnel**, NOT a cart/checkout. Operated by
PT Sehat Investasi Digital; dispensed by partner pharmacy PharmaCare Sidakarya. Designed to **replicate
to other countries** later (all market-specifics live in config).

**Core model = a clean, Western-friendly clone of Halodoc's structure:** search → condition tiles →
product page → **prescription gate** → fulfilment. Because we're prescription-only with no cart, the
gate offers **two funnels**, both ending in dispense + Bali delivery:
1. **Book a consult** (`/booking`) — no prescription yet → licensed doctor issues one.
2. **Upload a prescription** (`/prescription`) — already have one → pharmacist reviews it.

---

## 2. Where things are stored (file map)
```
src/
├─ styles/tokens.css      ← ALL colours/spacing/type (brand = navy+gold). Edit here to re-skin.
├─ styles/global.css      ← base styles, buttons (.btn--primary = gold CTA)
├─ lib/
│  ├─ site.ts             ← ★ CONFIG: brand, WhatsApp, compliance data, MARKET block,
│  │                         CATEGORY_GROUPS, TRUST_BADGES, TESTIMONIALS, currency key, Calendly
│  ├─ products.ts         ← loads products.json, derives price, builds search index (+ ingredient kw)
│  ├─ pricing.ts          ← price math + IDR/USD formatting
│  └─ currency.ts         ← live IDR→USD (cached 1h, graceful fail)
├─ data/products.json     ← THE catalog (3,555 products) — generated from the BaliPharma export
├─ components/            ← Icon, SearchBar, CategoryTiles, Rail, ProductCard, PriceDisplay,
│                            ProductInfoTabs, Steps, TrustBadges, Testimonials, Stars, PathChooser,
│                            PrescriptionUpload, Nav, Footer, StickyWhatsApp, RedLabelNotice
├─ layouts/               ← BaseLayout (SEO/OG/fonts/favicon), LegalLayout
└─ pages/
   ├─ index.astro             Home (search-hero, path chooser, tiles, trust, rail, reviews)
   ├─ products/index.astro    Catalog (sidebar filters + sort + deep links; client search index)
   ├─ products/[slug].astro   Product page (tabbed info, dual Rx gate, sticky mobile CTA)
   ├─ booking.astro           Consult funnel
   ├─ prescription.astro      Upload funnel (NEW)
   ├─ about.astro             Story + compliance + map + pharmacist portrait
   ├─ search-index.json.ts    Generates /search-index.json (client search/catalog)
   ├─ sitemap.xml.ts          Generates /sitemap.xml (all 3,500+ URLs)
   ├─ privacy / terms / 404
public/                    ← logos, images (AI), robots.txt, favicon, og
scripts/                   ← data + ops tooling (see §5)
```

## 3. How key things work
- **Search (instant autocomplete)** — `SearchBar.astro`. Fetches `/search-index.json` once (cached),
  shows a live dropdown with thumbnails. Matches by name → **active-ingredient** (so "amlodipine"
  finds brand "A-B Vask") → fuzzy typo ("amoxicilin" → "Amoxicillin"). Ingredient keywords (`kw`) are
  extracted from each product's composition in `products.ts`.
- **Catalog** — `products/index.astro`. Server-renders first 48 for SEO; a client controller filters
  the full index (condition group + in-stock + sort) with `?cat=`/`?q=` deep links; mobile = bottom-sheet filters.
- **Category tiles** — 28 raw product `Type`s are curated into ~12 plain-English **groups** in
  `CATEGORY_GROUPS` (`site.ts`); tiles deep-link to the filtered catalog.
- **Pricing** — `price = halodoc_price_idr × 1.5`, shown as a **USD (live) + IDR** range. USD is
  computed client-side from the cached exchange rate; IDR renders even with no JS.
- **Prescription gate** — every product page shows both funnels; the primary (gold) CTA sticks to the
  bottom on mobile (CRO).
- **Upload submit** — `PrescriptionUpload.astro` posts to `MARKET.uploadEndpoint` if set, else opens
  **WhatsApp** prefilled (default; static site has no backend).

## 4. Data pipeline (how the catalog was built)
`products_export_1.csv` (BaliPharma Shopify export, **sensitive, gitignored**) →
`scripts/import_products.py` → `products.json`. Prices + NIE scraped from **Halodoc**:
`scripts/halodoc_prices.py` (search API) + `scripts/halodoc_nie.py` (detail API → NIE + manufacturer),
merged by `merge_prices.py` / `merge_nie.py`. Recovery pass `recover_prices.py`. **Result: ~99% priced
+ NIE.** Re-import flow: `import_products.py` → `halodoc_full.py` (one-pass) → merges → `npm run build`.

## 5. Scripts (`scripts/`)
| Script | Purpose |
|---|---|
| `import_products.py` | BaliPharma CSV → products.json (+ data-quality report) |
| `halodoc_prices.py` / `halodoc_nie.py` / `halodoc_full.py` | Scrape prices / NIE (concurrent) |
| `merge_prices.py` / `merge_nie.py` / `recover_prices.py` | Merge scraped data, recover misses |
| `gen_images.py` | AI imagery via Google Imagen/Gemini (key in gitignored `.gemini_key`); ffmpeg optimises |
| `build_dashboard.py` + `build_status.json` + `status_update.py` | Live build-progress UI at :8765 |

## 6. Open items (operator/legal — all marked TODO in code)
Calendly URL · prescription `uploadEndpoint` · real delivery ETA (`MARKET.deliveryEtaHours`) · real
testimonials (`TESTIMONIALS`, currently samples) · pharmacist schedule · Jakarta office address ·
pharmacist sign-off on ~37 controlled meds · real logo PNG (optional, to trace exact original).

---

## 7. Decision log (what changed & why)
- **Stack = Astro static.** 3,500+ pages from JSON at build, zero-JS default, fast on laggy Bali
  connections, deploys anywhere. → `astro.config.mjs`.
- **Catalog from real data, not manual.** Scraped BaliPharma + Halodoc (prices/NIE) for speed &
  completeness; Halodoc×1.5 pricing is a **placeholder** to replace with own pricing per market.
- **Visual direction (evolved):** warm "apothecary" → "clean white" → **navy + gold (current)**.
  Final driver = the **operator's logo** (navy + gold) + conversion research (navy=trust foundation,
  gold=Amazon-proven CTA pop, green=success). Logo leads the brand.
- **Halodoc-modeled, Western-clean.** Adopt Halodoc's proven commerce structure but strip its clutter;
  the operator found Halodoc "weird" — goal is intuitive for Westerners.
- **Two funnels (consult + upload)** because we're prescription-only (no cart). Mirrors Halodoc flows
  B + C minus OTC.
- **Conversion-first (CRO research baked in):** sticky mobile CTA, trust+social-proof near CTAs,
  above-the-fold action, progress bars, minimal-fields-first, privacy reassurance, mobile-first.
- **Replication-ready:** market-specifics isolated in `site.ts` `MARKET` + `CATEGORY_GROUPS` so a 2nd
  country is a config swap, not a rebuild.
- **Instant search with ingredient + typo matching** so tourists find meds by generic name or despite
  misspelling (conversion win).

### UX test fixes (external tester report)
- **CRITICAL — product CTA was blocked by the floating WhatsApp button** (mobile): the sticky bottom
  "Get prescription" bar was covered by `.sticky-wa`. Fix: `BaseLayout` `stickyCta` prop → `body.has-sticky-cta`
  → CSS lifts the WhatsApp button above the bar on mobile (`global.css`). Product pages pass `stickyCta`.
- **Booking handoff:** the medication now flows into the WhatsApp message (script on `[data-wa-book]`
  reads the field), field given a `name`; removed the "[X] hours" token (conditional on
  `MARKET.deliveryEtaHours`) and the "scheduler will appear here" placeholder (reframed to a clean
  WhatsApp booking card until `CALENDLY_URL` is set).
- **No fake reviews live:** `Testimonials.astro` renders nothing while `TESTIMONIALS_ARE_SAMPLES` is true.
- **Search dropdown:** name/dose now stack (were inline) — `SearchBar.astro` `.ac__txt` flex-column.
- **Hero:** added explicit "Browse all medicines" CTA (not search-only).

### About reposition · controlled meds · manual requests
- **About is operator-led:** leads with **PT Sehat Investasi Digital** (runs **BaliDoc** + Tourist
  Pharmacy) + an **"In association with BaliDoc"** strip. The partner pharmacy is demoted to a subtle
  **"Licensing & dispensing"** compliance panel (all legal data kept: Izin Apotek, SIPA/STR, NIB).
  Config: `BALIDOC` block in `site.ts` (add `logo` path when available).
- **Controlled / psychiatric meds:** `scripts/merge_controlled.py` sets `controlled:true` on **46**
  products (Halodoc `ctrl` flag + a curated psychotropic ingredient list) → `products.json`; report in
  `CONTROLLED_REPORT.md`. They show a red **"Controlled · specialist only"** badge (card + PDP), are
  kept out of the home popular rail + related, and their PDP gate routes to a **specialist consult**
  (`/booking?...&specialist=1` → booking copy + WhatsApp message adapt). **Single switch
  `HIDE_CONTROLLED` in `site.ts`** removes them site-wide (catalog, search index, sitemap, generated
  pages) — verified both states. Field added to schema/index (`controlled` / index `x`) in `products.ts`.
- **Manual "can't find it" request:** `src/components/MedicineRequest.astro` (intake → WhatsApp, model
  of PrescriptionUpload) + page `src/pages/request.astro`. Entry points: search-dropdown no-results,
  catalog empty state + a persistent "Can't find your medicine?" strip, and a footer link. Fields:
  medication, quantity, country you're in, already-have-Rx, name, WhatsApp, notes. `?q=` prefills.
- **Fixed:** `ProductCard.astro` styles made **global** (`<style is:global>`) so the catalog's
  client-rendered cards (built via innerHTML, which replace the server cards once the index loads) are
  actually styled — they previously relied on component-scoped CSS that didn't apply to them.

> Convention: keep this log updated when a notable decision is made, and keep `BRAND.md` current when
> identity changes.

---

## Private review deployment + feedback collection (2026-06-27)

To put the site in front of the team for feedback (not public yet), we added a **review server** and
an **in-page feedback tool**, deploying to the **DigitalOcean droplet** (a Node server, not a static
host, because AI processing needs a secret key and feedback must be written to files — neither is safe
in a static build).

- **`server.mjs`** (Express, `npm run serve`) — serves `dist/` behind a **login page** (one shared
  `SITE_PASSWORD`, HMAC cookie), exposes **`POST /api/feedback`** which (optionally) AI-structures each
  note via **OpenAI** into *title · type · severity · summary · suggested action*, then writes
  `feedback/<id>.md` (+ `feedback/screenshots/<id>.jpg`). Degrades gracefully: no `OPENAI_API_KEY` →
  saves verbatim; no `SITE_PASSWORD` → warns. Gated **`/feedback`** admin index for browsing notes.
  Reads a gitignored **`.env`** (tiny built-in loader, no dependency). `FEEDBACK_GIT=1` auto commits +
  pushes each note back to the repo.
- **`src/components/FeedbackWidget.astro`** — left-edge **"Feedback"** tab (non-obstructive) → modal
  with name, message, and **optional screenshot** (html2canvas). Posts to `FEEDBACK_ENDPOINT`. Only
  rendered when **`REVIEW_MODE`** (`site.ts`) is true; flip to `false` for public launch.
- **`DEPLOY_REVIEW.md`** — droplet runbook (Node, `npm run build`, pm2, nginx + certbot HTTPS, env
  vars, how feedback flows back via `FEEDBACK_GIT` or scp). The public static path stays in `DEPLOY.md`.
- **Why a login:** the build isn't ready for the world; reviewers get one password.
- **Open items:** OpenAI key (optional; from the simple Asana board — not stored in repo) and the
  GitHub push to `bartbalidoc/tourist-pharmacy-` (replaces the current live site, behind login) both
  need the operator's credentials/go-ahead.
