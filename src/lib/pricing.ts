// Pricing helpers — shared by build-time (product list) and client-side (live USD).

/** Retail IDR price = Halodoc reference price × 1.5. Returns 0 for unset placeholders. */
export function computeRetailIdr(halodocPriceIdr: number): number {
  if (!halodocPriceIdr || halodocPriceIdr <= 0) return 0;
  return Math.round(halodocPriceIdr * 1.5);
}

/** Format an IDR amount with Indonesian thousand separators, e.g. 199500 -> "Rp 199.500". */
export function formatIdr(amount: number): string {
  return 'Rp ' + Math.round(amount).toLocaleString('id-ID');
}

/** Convert an IDR amount to a USD string given a rate (USD per 1 IDR), e.g. "USD 12.50". */
export function formatUsd(amountIdr: number, usdPerIdr: number): string {
  const usd = amountIdr * usdPerIdr;
  return 'USD ' + usd.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
