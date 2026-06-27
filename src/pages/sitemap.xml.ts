import type { APIRoute } from 'astro';
import { products } from '../lib/products';
import { SITE } from '../lib/site';

// Custom sitemap covering every static page + all product pages. Built once to
// /sitemap.xml so the new domain gets fully indexed when it replaces the old site.
const STATIC_PATHS = ['/', '/products', '/about', '/booking', '/privacy', '/terms'];

export const GET: APIRoute = () => {
  const urls = [
    ...STATIC_PATHS.map((p) => ({ loc: p, priority: p === '/' ? '1.0' : '0.8' })),
    ...products.map((p) => ({ loc: p.href, priority: '0.6' })),
  ];

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls
      .map(
        (u) =>
          `  <url><loc>${new URL(u.loc, SITE.url).href}</loc>` +
          `<changefreq>weekly</changefreq><priority>${u.priority}</priority></url>`,
      )
      .join('\n') +
    `\n</urlset>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
