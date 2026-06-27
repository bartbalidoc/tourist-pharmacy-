// Live IDR -> USD rate, fetched once and cached for performance + rate-limit safety.
// Runs in the browser (loaded via a tiny island). All failures degrade gracefully:
// callers fall back to showing IDR only.
//
// exchangerate-api.com free tier. Base = IDR, so conversion_rates.USD is "USD per 1 IDR".
import { CURRENCY_ENDPOINT, CURRENCY_API_KEY } from './site';

const CACHE_KEY = 'tp_usd_per_idr';
const TTL_MS = 60 * 60 * 1000; // 1 hour

type Cache = { rate: number; ts: number };

function readCache(): number | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Cache;
    if (typeof parsed.rate !== 'number' || !parsed.ts) return null;
    if (Date.now() - parsed.ts > TTL_MS) return null; // expired
    return parsed.rate;
  } catch {
    return null;
  }
}

function writeCache(rate: number): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ rate, ts: Date.now() } satisfies Cache));
  } catch {
    /* localStorage unavailable (private mode) — non-fatal */
  }
}

/**
 * Returns USD per 1 IDR, or null if the rate cannot be determined.
 * Uses a fresh in-TTL cache when available to avoid a network round-trip on
 * slow Bali connections.
 */
export async function getUsdPerIdr(): Promise<number | null> {
  // Don't even attempt a fetch while the API key is still the placeholder.
  if (CURRENCY_API_KEY === 'FREE_KEY_PLACEHOLDER') {
    return readCache(); // null unless something was cached previously
  }

  const cached = readCache();
  if (cached !== null) return cached;

  try {
    const res = await fetch(CURRENCY_ENDPOINT, { cache: 'no-store' });
    if (!res.ok) return null;
    const data = await res.json();
    const rate = data?.conversion_rates?.USD;
    if (data?.result !== 'success' || typeof rate !== 'number') return null;
    writeCache(rate);
    return rate;
  } catch {
    return null; // network failure / offline — caller shows IDR only
  }
}
