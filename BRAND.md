# Tourist Pharmacy — Brand Identity

The single source of truth for how the brand looks and why. Pairs with the design tokens in
[`src/styles/tokens.css`](src/styles/tokens.css) (every value below is a CSS variable there).

---

## Logo

Recreated as clean, scalable **SVG** (vector = infinitely high-res). All in [`public/`](public/):

| File | What it is | Used for |
|---|---|---|
| `logo.svg` | Full badge — ring + arched "TOURIST / PHARMACY" + globe + gold cross | Master logo, large displays |
| `logo-mark.svg` | Icon only — globe + gold cross (no text/ring) | **Site header & footer**, app icon, social avatar |
| `logo-lockup.svg` | Horizontal — mark + "Tourist Pharmacy" wordmark | Email signatures, wide headers, docs |
| `logo-reversed.svg` | White version (white ring/text, white globe, gold cross) | **Dark backgrounds** |
| `logo-mono.svg` | One-colour navy (no gold) | Stamps, fax, single-colour print |
| `favicon.svg` | = the icon mark | Browser tab |
| `og-default.svg` | Social share card (mark + wordmark + tagline) | Open Graph / link previews |

Wired into the site via [`src/components/Nav.astro`](src/components/Nav.astro) and
[`src/components/Footer.astro`](src/components/Footer.astro) (both `<img src="/logo-mark.svg">`),
and the favicon in [`src/layouts/BaseLayout.astro`](src/layouts/BaseLayout.astro).

> **Note:** these are a faithful **vector re-creation** of the operator's original PNG (the original
> pixels weren't available on disk). To make it pixel-exact, drop the original PNG into `public/` and
> ask Claude to trace it. The globe was intentionally **simplified** vs the original (see critique).

### Confirmed logo decisions (operator-approved)
- **Header lockup = icon mark (`logo-mark.svg`) + "Tourist Pharmacy" wordmark** — pristine and the
  letters stay legible at ~40px. (Full arched-text badge is reserved for large displays / OG.)
- **Globe = clean grid** (crisp longitude/latitude lines, no continents) — razor-sharp at every size
  including favicon. Gold cross centred on top. The original's detailed/textured continents were
  dropped on purpose for small-size clarity.

### Logo critique (why it's good + what was changed)
- **Strong concept** — globe + medical cross instantly says "pharmacy for travellers." Trustworthy
  emblem/badge format. Navy + gold = a premium, high-trust palette.
- **Changes made for scalability:** flattened the grunge texture, simplified the globe (detail turns
  to mud below ~32px), and built a proper **logo system** (badge / icon / lockup / reversed / mono)
  instead of one lockup. Small-size legibility and dark-background versions were the main gaps.

---

## Colour system  — *why these colours (conversion-led)*

Brand is **logo-led**: navy + gold. Choices are backed by colour/trust/conversion research, because
the site's whole job is to convert anxious visitors into a booking/upload.

| Role | Colour | Hex | Token | Why |
|---|---|---|---|---|
| **Brand / trust** | Navy | `#16365c` | `--c-terracotta`, `--c-jungle` | Blue is the #1 trust colour for healthcare/finance. Foundation: headers, text, links, icon chips. |
| **Primary CTA** | Gold | `#e3a52e` | `--c-cta` (text `--c-cta-ink` = navy) | Warm, max-saliency "pop" (only warm colour on the page). Amazon's gold buy-button is the most-proven e-com CTA. Navy text = AA contrast (~5:1). |
| **Success / in-stock** | Green | `#15803d` | `--c-in-stock`, `--c-sage` | "Go"/safe/health. Functional states only. |
| **Prescription / alert** | Red | `#dc2626` | `--c-red-label` | Rx-required warnings. |
| **WhatsApp** | Green | `#25d366` | `--c-whatsapp` | Brand-correct WhatsApp. |
| Ink / text | Dark slate-navy | `#16243a` / `#4b596f` | `--c-ink` / `--c-ink-soft` | Readable body text. |
| Surfaces | White / cool tint | `#ffffff` / `#f4f7fb` | `--c-surface` / `--c-paper-2` | Clean, lots of whitespace. |
| Hairlines | Cool grey | `#e3e9f1` | `--c-cream-line` | Subtle borders. |

**Usage rules**
- **Gold = conversion only.** Primary CTAs (`.btn--primary`): gold bg + navy text. Don't use gold for
  body text or thin icons on white (fails contrast).
- **Navy = everything structural** — brand, headings, links, secondary buttons (`.btn--navy`), icon tiles.
- **Green = state, not decoration** (in-stock, verified, success).
- Keep to these 3 + neutrals. ≤3 colours = looks legitimate, not templated.

> Variable names are legacy (`--c-terracotta` etc. from earlier warm/teal versions) but the **values**
> are navy/gold. Changing the whole palette = edit `tokens.css` only.

---

## Typography
- **UI / web:** `Plus Jakarta Sans` (Google Fonts) — clean, friendly-professional. Loaded in
  `BaseLayout.astro`. Tokens `--font-display` / `--font-body`.
- **Logo wordmark:** a serif (Georgia family) — gives the badge its classic, established feel.

## Voice & tone
Warm, clear, English-speaking. Like *a knowledgeable friend who knows every pharmacy in Bali* — calm
and reassuring for someone unwell and far from home. Plain English, no clinical jargon, no hard sell.
