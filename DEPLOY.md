# Deploying Tourist Pharmacy

The site is a **static build** — `npm run build` produces a `dist/` folder of plain files you can
host anywhere. Pick one option below.

> Before deploying, make sure `CURRENCY_API_KEY` is set (it is) and review the remaining
> placeholders in [README.md](README.md) (Calendly URL, pharmacist schedule, office address).

---

## Option A — Netlify (recommended, easiest)

A `netlify.toml` is already included (build command + publish dir + caching).

**Drag-and-drop (fastest):**
1. Run `npm run build` locally.
2. Go to https://app.netlify.com/drop and drag the `dist/` folder in. Live in seconds.

**Connected to Git (auto-deploys on push):**
1. Push this repo to GitHub/GitLab.
2. Netlify → “Add new site” → “Import an existing project” → pick the repo.
3. It reads `netlify.toml` automatically (build `npm run build`, publish `dist`). Deploy.

**CLI:**
```bash
npm i -g netlify-cli
npm run build
netlify deploy --prod --dir=dist
```

---

## Option B — Vercel

```bash
npm i -g vercel
vercel --prod
```
Vercel auto-detects Astro (build `npm run build`, output `dist`). No extra config needed.

---

## Option C — Cloudflare Pages

1. Cloudflare dashboard → Workers & Pages → Create → Pages → connect your Git repo.
2. Build command: `npm run build` · Build output directory: `dist`.
3. Deploy.

---

## Point the domain (touristpharmacy.com)

1. In your host (Netlify/Vercel/Cloudflare), add the custom domain `touristpharmacy.com`.
2. Update the domain’s DNS as the host instructs (usually a CNAME, or A/ALIAS for the apex).
3. Enable HTTPS (automatic on all three).
4. Confirm `https://touristpharmacy.com/sitemap.xml` loads, then submit it in Google Search Console
   so the ~3,500 product pages get indexed (important when replacing the old site).

## Post-deploy checklist
- [ ] Currency: product pages show USD + IDR (live rate working).
- [ ] WhatsApp button works on every page.
- [ ] Map loads on the About page.
- [ ] `robots.txt` and `sitemap.xml` reachable.
- [ ] Submit sitemap to Google Search Console.
- [ ] Set up redirects from old site URLs if their paths differ (optional, preserves SEO).
