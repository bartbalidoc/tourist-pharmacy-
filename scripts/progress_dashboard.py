#!/usr/bin/env python3
"""Live dashboard for the Halodoc price scrape. Open http://localhost:8765

Serves an auto-refreshing page that reads halodoc_prices.json (written by
scripts/halodoc_prices.py) and shows progress, confident-match rate, throughput,
ETA, and a feed of the latest matches. No external network — localhost only.
"""
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
PRODUCTS = "src/data/products.json"
PRICES = "halodoc_prices.json"
DETAILS = "halodoc_details.json"

try:
    TOTAL = len(json.load(open(PRODUCTS, encoding="utf-8")))
except Exception:
    TOTAL = 3555

_hist = []  # (ts, processed) samples for throughput/ETA

def status():
    data = {}
    if os.path.exists(PRICES):
        try:
            data = json.load(open(PRICES, encoding="utf-8"))
        except Exception:
            data = {}
    items = list(data.items())
    processed = len(items)
    confident = sum(1 for _, v in items if v.get("score", 0) >= 0.7)
    ranged = sum(1 for _, v in items if v.get("score", 0) >= 0.7 and (v.get("max", 0) or 0) > (v.get("min", 0) or 0))
    nomatch = sum(1 for _, v in items if (v.get("score", 0) or 0) <= 0 or not (v.get("min", 0) or 0))

    now = time.time()
    _hist.append((now, processed))
    while _hist and now - _hist[0][0] > 90:
        _hist.pop(0)
    rate = 0.0
    if len(_hist) >= 2:
        dt = _hist[-1][0] - _hist[0][0]
        dn = _hist[-1][1] - _hist[0][1]
        if dt > 0:
            rate = dn / dt  # products/sec
    remaining = max(0, TOTAL - processed)
    eta = int(remaining / rate) if rate > 0.01 else None

    recent = []
    for slug, v in items[-9:][::-1]:
        recent.append({
            "name": v.get("halo_name") or slug,
            "min": v.get("min", 0), "max": v.get("max", 0),
            "score": v.get("score", 0),
            "ctrl": v.get("ctrl", ""),
        })
    # NIE phase (runs after prices). Target = confident price matches that carry a halodoc slug.
    nie = None
    if os.path.exists(DETAILS):
        try:
            dd = json.load(open(DETAILS, encoding="utf-8"))
        except Exception:
            dd = {}
        nie_target = sum(1 for v in data.values()
                         if v.get("score", 0) >= 0.7 and v.get("halo_slug"))
        nie_proc = len(dd)
        nie_found = sum(1 for v in dd.values() if v.get("nie"))
        nie_recent = [{"name": (prices_name(data, k) or k), "nie": v.get("nie", ""),
                       "mfr": v.get("manufacturer", "")}
                      for k, v in list(dd.items())[-9:][::-1]]
        nie = {"target": nie_target or TOTAL, "processed": nie_proc, "found": nie_found,
               "done": nie_target and nie_proc >= nie_target, "recent": nie_recent}

    return {
        "total": TOTAL, "processed": processed, "confident": confident,
        "ranged": ranged, "nomatch": nomatch,
        "rate_per_min": round(rate * 60, 1), "eta_sec": eta,
        "done": processed >= TOTAL, "recent": recent, "nie": nie,
    }

_names = {}
def prices_name(prices_data, our_slug):
    """Best-effort display name for a product slug (Halodoc name from the price record)."""
    rec = prices_data.get(our_slug)
    return rec.get("halo_name") if rec else None

PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Scrape Progress — Tourist Pharmacy</title>
<style>
 :root{--paper:#faf4ea;--ink:#2a241d;--soft:#5c5346;--terra:#c0613b;--jungle:#244736;--brass:#b08b4f;--line:#e3d6c0;--green:#2f7d4f}
 *{box-sizing:border-box;margin:0}
 body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--paper);color:var(--ink);
  background-image:radial-gradient(1000px 500px at 85% -10%,rgba(192,97,59,.08),transparent 60%),radial-gradient(800px 450px at -10% 110%,rgba(36,71,54,.08),transparent 60%);
  min-height:100vh;padding:clamp(1rem,4vw,3rem)}
 .wrap{max-width:880px;margin:0 auto}
 h1{font-family:Georgia,serif;color:var(--jungle);font-size:clamp(1.6rem,4vw,2.4rem);letter-spacing:-.01em}
 .sub{color:var(--soft);margin-top:.25rem}
 .live{display:inline-flex;align-items:center;gap:.5rem;font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.12em;color:var(--terra);margin-top:1rem}
 .dot{width:10px;height:10px;border-radius:50%;background:var(--terra);animation:pulse 1.3s infinite}
 .dot.done{background:var(--green);animation:none}
 @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(192,97,59,.5)}70%{box-shadow:0 0 0 12px rgba(192,97,59,0)}100%{box-shadow:0 0 0 0 rgba(192,97,59,0)}}
 .bar{height:26px;background:#fff;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin:1.5rem 0 .5rem;box-shadow:inset 0 1px 3px rgba(0,0,0,.05)}
 .fill{height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,var(--terra),var(--brass));transition:width .8s cubic-bezier(.4,0,.2,1);
  background-size:40px 40px;background-image:linear-gradient(90deg,var(--terra),var(--brass)),linear-gradient(45deg,rgba(255,255,255,.18) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.18) 50%,rgba(255,255,255,.18) 75%,transparent 75%);animation:stripes 1s linear infinite}
 @keyframes stripes{to{background-position:40px 0,0 0}}
 .pct{font-family:Georgia,serif;font-size:clamp(2.4rem,8vw,4rem);color:var(--jungle);line-height:1}
 .pctrow{display:flex;align-items:baseline;gap:.75rem;flex-wrap:wrap}
 .pctrow small{color:var(--soft);font-size:1rem}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin:1.75rem 0}
 .card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.1rem 1.25rem;box-shadow:0 2px 8px rgba(42,36,29,.05)}
 .card .n{font-family:Georgia,serif;font-size:1.9rem;color:var(--terra)}
 .card.g .n{color:var(--green)}.card.j .n{color:var(--jungle)}
 .card .l{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--soft);margin-top:.25rem}
 h2{font-family:Georgia,serif;color:var(--jungle);font-size:1.2rem;margin:1.5rem 0 .75rem}
 .feed{display:grid;gap:.4rem}
 .row{display:flex;justify-content:space-between;gap:1rem;background:#fff;border:1px solid var(--line);border-radius:10px;padding:.6rem .9rem;font-size:.9rem;animation:in .4s ease}
 @keyframes in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
 .row .nm{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .row .pr{color:var(--soft);white-space:nowrap}
 .badge{font-size:.7rem;font-weight:700;padding:.1rem .45rem;border-radius:99px;background:#eef6ef;color:var(--green)}
 .badge.lo{background:#fbeae8;color:#b3261e}
 .ctrl{font-size:.7rem;color:#b3261e;font-weight:700}
 .foot{color:var(--soft);font-size:.8rem;margin-top:1.5rem}
 @media(prefers-reduced-motion:reduce){.dot,.fill{animation:none}.row{animation:none}}
</style></head><body><div class=wrap>
 <h1>Halodoc Scrape</h1>
 <div class=sub>Live progress &middot; Tourist Pharmacy catalog</div>

 <!-- ACTIVE PHASE: NIE lookup. Shown on top while running so it isn't hidden below the
      finished price panel. -->
 <section id=niewrap style="display:none;margin-top:1.5rem">
  <h2 style="color:var(--terra)">▶ Now running · NIE / BPOM lookup</h2>
  <div class=sub style="margin-bottom:.5rem">Marketing-authorization numbers &amp; manufacturers from Halodoc</div>
  <div class=live><span class=dot id=niedot></span><span id=nielivetxt>Scraping…</span></div>
  <div class=pctrow><span class=pct id=niepct>0%</span><small id=niecount>0 / 0</small></div>
  <div class=bar><div class=fill id=niefill></div></div>
  <div class=grid>
   <div class="card g"><div class=n id=niefound>0</div><div class=l>NIE numbers found</div></div>
   <div class=card><div class=n id=nieproc>0</div><div class=l>Processed</div></div>
  </div>
  <h2>Latest NIEs</h2>
  <div class=feed id=niefeed></div>
 </section>

 <section id=pricewrap style="margin-top:2rem">
  <h2 id=priceh>Prices</h2>
  <div class=live><span class=dot id=dot></span><span id=livetxt>Scraping…</span></div>
  <div class=pctrow><span class=pct id=pct>0%</span><small id=count>0 / 0 products</small></div>
  <div class=bar><div class=fill id=fill></div></div>
  <div class=grid>
   <div class="card g"><div class=n id=confident>0</div><div class=l>Confident matches</div></div>
   <div class="card j"><div class=n id=ranged>0</div><div class=l>Price ranges</div></div>
   <div class=card><div class=n id=nomatch>0</div><div class=l>No match yet</div></div>
   <div class="card j"><div class=n id=eta>—</div><div class=l>ETA &middot; <span id=rate>0</span>/min</div></div>
  </div>
  <h2>Latest matches</h2>
  <div class=feed id=feed></div>
 </section>

 <div class=foot>Auto-refreshes every 10s. Close this tab anytime — the scrapes keep running.</div>
</div>
<script>
const fmtIdr=n=>n?('Rp '+Number(n).toLocaleString('id-ID')):'';
const fmtEta=s=>{if(s==null)return '—';if(s<60)return s+'s';const m=Math.round(s/60);return m<60?m+'m':(Math.floor(m/60)+'h '+(m%60)+'m')};
async function tick(){
 let s;try{s=await (await fetch('/status',{cache:'no-store'})).json()}catch(e){return}
 const pct=s.total?Math.round(100*s.processed/s.total):0;
 document.getElementById('pct').textContent=pct+'%';
 document.getElementById('fill').style.width=pct+'%';
 document.getElementById('count').textContent=s.processed.toLocaleString()+' / '+s.total.toLocaleString()+' products';
 document.getElementById('confident').textContent=s.confident.toLocaleString();
 document.getElementById('ranged').textContent=s.ranged.toLocaleString();
 document.getElementById('nomatch').textContent=s.nomatch.toLocaleString();
 document.getElementById('rate').textContent=s.rate_per_min;
 document.getElementById('eta').textContent=s.done?'Done':fmtEta(s.eta_sec);
 const dot=document.getElementById('dot'),lt=document.getElementById('livetxt');
 if(s.done){dot.classList.add('done');lt.textContent='Complete'}else{lt.textContent='Scraping…'}
 const feed=document.getElementById('feed');
 feed.innerHTML=s.recent.map(r=>{
   const lo=r.score<0.7;const ctrl=r.ctrl&&r.ctrl!=='not_controlled_substance';
   const price=r.min?(r.max>r.min?fmtIdr(r.min)+' – '+fmtIdr(r.max):fmtIdr(r.min)):'—';
   return `<div class=row><span class=nm>${r.name}${ctrl?' <span class=ctrl>⚠ controlled</span>':''}</span>`+
          `<span class=pr>${price} <span class="badge ${lo?'lo':''}">${(r.score).toFixed(2)}</span></span></div>`;
 }).join('');
 // NIE phase panel
 const nw=document.getElementById('niewrap');
 if(s.nie){nw.style.display='';const e=s.nie;
   const np=e.target?Math.round(100*e.processed/e.target):0;
   document.getElementById('niepct').textContent=np+'%';
   document.getElementById('niefill').style.width=np+'%';
   document.getElementById('niecount').textContent=e.processed.toLocaleString()+' / '+e.target.toLocaleString();
   document.getElementById('niefound').textContent=e.found.toLocaleString();
   document.getElementById('nieproc').textContent=e.processed.toLocaleString();
   const nd=document.getElementById('niedot'),nl=document.getElementById('nielivetxt');
   if(e.done){nd.classList.add('done');nl.textContent='Complete'}else{nl.textContent='Scraping…'}
   document.getElementById('niefeed').innerHTML=e.recent.map(r=>
     `<div class=row><span class=nm>${r.name}</span><span class=pr>${r.mfr||''} <span class="badge ${r.nie?'':'lo'}">${r.nie||'—'}</span></span></div>`).join('');
 }
}
tick();setInterval(tick,10000);
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/status"):
            body = json.dumps(status()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(body)
        else:
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.end_headers(); self.wfile.write(body)

if __name__ == "__main__":
    print(f"Dashboard: http://localhost:{PORT}  (total products: {TOTAL})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
