import { z } from 'astro/zod';
import raw from '../data/products.json';
import { computeRetailIdr } from './pricing';
import { groupForType, CATEGORY_GROUPS, HIDE_CONTROLLED } from './site';

// Schema for a product entry. Built from the real BaliPharma Shopify export, so fields
// that the export doesn't reliably carry (NIE, dosage_form, strength, composition) are
// optional with empty-string defaults — the product page shows a compliant fallback for
// each. Only id + name are truly required. (Missing fields are surfaced in the data-quality
// report generated at import time, not by failing the build.)
const ProductSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  nie: z.string().optional().default(''),
  category: z.string().optional().default('Other Medications'),
  dosage_form: z.string().optional().default(''),
  packaging: z.string().optional().default(''),
  strength: z.string().optional().default(''),
  composition: z.string().optional().default(''),
  description: z.string().optional().default(''),
  manufacturer: z.string().optional().default(''),
  image_url: z.string().optional().default('/images/products/placeholder.svg'),
  // Halodoc reference price range (IDR). Halodoc shows a low–high range; retail = ×1.5 each.
  // Single-price products have min == max. halodoc_price_idr (single) kept for back-compat.
  halodoc_price_idr: z.number().nonnegative().optional().default(0),
  halodoc_price_min_idr: z.number().nonnegative().optional().default(0),
  halodoc_price_max_idr: z.number().nonnegative().optional().default(0),
  /** Retail price from the BaliPharma export (USD). Preserved for reference. */
  ref_price_usd: z.number().nonnegative().optional().default(0),
  in_stock: z.boolean().optional().default(true),
  stock_note: z.string().optional().default(''),
  /** Controlled / psychiatric ("specialist consultation only"). Set by scripts/merge_controlled.py. */
  controlled: z.boolean().optional().default(false),
});

export type RawProduct = z.infer<typeof ProductSchema>;

export type Product = RawProduct & {
  /** Retail price range = Halodoc price × 1.5 (IDR). 0 while price is a TODO placeholder. */
  price_min_idr: number;
  price_max_idr: number;
  /** True when there is no Halodoc price yet. */
  priceMissing: boolean;
  /** True when min and max differ (show as a range). */
  priceIsRange: boolean;
  slug: string;
  href: string;
};

function load(): Product[] {
  const parsed = z.array(ProductSchema).parse(raw);
  return parsed.map((p) => {
    const hMin = p.halodoc_price_min_idr || p.halodoc_price_idr || 0;
    const hMax = p.halodoc_price_max_idr || p.halodoc_price_min_idr || p.halodoc_price_idr || 0;
    const minIdr = computeRetailIdr(hMin);
    const maxIdr = computeRetailIdr(hMax);
    return {
      ...p,
      image_url: p.image_url || '/images/products/placeholder.svg',
      category: p.category || 'Other Medications',
      price_min_idr: minIdr,
      price_max_idr: maxIdr,
      priceMissing: minIdr <= 0,
      priceIsRange: maxIdr > minIdr,
      slug: p.id,
      href: `/products/${p.id}`,
    };
  });
}

const allProducts: Product[] = load();

// Single visibility switch: when HIDE_CONTROLLED is true, controlled/specialist-only meds are
// dropped from the entire site (catalog, search index, related, generated pages, sitemap).
export const products: Product[] = HIDE_CONTROLLED
  ? allProducts.filter((p) => !p.controlled)
  : allProducts;

export const categories: string[] = Array.from(
  new Set(products.map((p) => p.category)),
).sort();

export function getProduct(slug: string): Product | undefined {
  return products.find((p) => p.slug === slug);
}

// Active-ingredient keywords from composition — powers "available under a different name"
// search (e.g. typing "amlodipine" finds brand "A-B Vask"). Filler/units stripped.
const KW_STOP = new Set([
  'each', 'tablet', 'tablets', 'capsule', 'capsules', 'caplet', 'caplets', 'contains',
  'contain', 'containing', 'equivalent', 'every', 'with', 'film', 'coated', 'syrup',
  'cream', 'injection', 'solution', 'suspension', 'drops', 'this', 'that', 'from',
  'dose', 'base', 'anhydrous', 'monohydrate', 'trihydrate', 'gram', 'grams', 'each.',
  'per', 'and', 'the', 'for', 'mg/ml', 'mg/5ml',
]);
function ingredientKeywords(composition: string): string {
  const words = (composition || '')
    .toLowerCase()
    .replace(/[^a-z\s]/g, ' ') // drop digits, units, punctuation
    .split(/\s+/)
    .filter((w) => w.length >= 4 && !KW_STOP.has(w));
  return Array.from(new Set(words)).slice(0, 8).join(' ');
}

/** Lightweight index for the client-side catalog + instant search. */
export type ProductIndexEntry = {
  s: string;  // slug
  n: string;  // name
  c: string;  // category (raw type)
  gr: string; // category-group slug
  f: string;  // dosage form
  g: string;  // strength
  k: 0 | 1;   // in stock
  i: string;  // image url
  kw: string; // active-ingredient keywords (alt-name search)
  x: 0 | 1;   // controlled / specialist-only
};

export const productIndex: ProductIndexEntry[] = products.map((p) => ({
  s: p.slug,
  n: p.name,
  c: p.category,
  gr: groupForType(p.category)?.slug ?? 'general',
  f: p.dosage_form,
  g: p.strength,
  k: p.in_stock ? 1 : 0,
  i: p.image_url,
  kw: ingredientKeywords(p.composition),
  x: p.controlled ? 1 : 0,
}));

/** Product count per category group — for the homepage condition tiles. */
export const groupCounts: Record<string, number> = Object.fromEntries(
  CATEGORY_GROUPS.map((grp) => [grp.slug, products.filter((p) => grp.types.includes(p.category)).length]),
);

/** Related products: same group, in stock, excluding self. */
export function relatedProducts(p: Product, n = 6): Product[] {
  const grp = groupForType(p.category)?.slug;
  return products
    .filter((x) => x.slug !== p.slug && x.in_stock && !x.controlled && (groupForType(x.category)?.slug === grp))
    .slice(0, n);
}
