import type { APIRoute } from 'astro';
import { productIndex } from '../lib/products';

// Static JSON index for the client-side catalog (search / filter / paginate).
// Built once to /search-index.json so the catalog page stays light and the full
// 3,500+ product list is fetched a single time, then cached by the browser.
export const GET: APIRoute = () =>
  new Response(JSON.stringify(productIndex), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
