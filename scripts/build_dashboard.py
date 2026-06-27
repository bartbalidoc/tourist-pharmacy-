#!/usr/bin/env python3
"""Live build-progress dashboard. Open http://localhost:8765

Reads scripts/build_status.json (updated by the build agent as it works) and shows the
go-live checklist with statuses + a live activity log. No external network.
"""
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
STATUS = "scripts/build_status.json"

def status():
    try:
        d = json.load(open(STATUS, encoding="utf-8"))
    except Exception:
        d = {"title": "Build", "tasks": [], "log": []}
    tasks = d.get("tasks", [])
    done = sum(1 for t in tasks if t.get("status") == "done")
    total = len(tasks) or 1
    d["_done"] = done
    d["_total"] = len(tasks)
    d["_pct"] = round(100 * done / total)
    d["_active"] = next((t["name"] for t in tasks if t.get("status") == "active"), None)
    d["_all_done"] = done == len(tasks) and len(tasks) > 0
    return d

PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Build Progress — Tourist Pharmacy</title>
<style>
 :root{--paper:#faf4ea;--ink:#2a241d;--soft:#5c5346;--terra:#c0613b;--jungle:#244736;--brass:#b08b4f;--line:#e3d6c0;--green:#2f7d4f}
 *{box-sizing:border-box;margin:0}
 body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--paper);color:var(--ink);
  background-image:radial-gradient(1000px 500px at 85% -10%,rgba(192,97,59,.08),transparent 60%),radial-gradient(800px 450px at -10% 110%,rgba(36,71,54,.08),transparent 60%);
  min-height:100vh;padding:clamp(1rem,4vw,3rem)}
 .wrap{max-width:840px;margin:0 auto}
 h1{font-family:Georgia,serif;color:var(--jungle);font-size:clamp(1.7rem,4vw,2.5rem);letter-spacing:-.01em}
 .sub{color:var(--soft);margin-top:.25rem}
 .live{display:inline-flex;align-items:center;gap:.5rem;font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.12em;color:var(--terra);margin-top:1.1rem}
 .dot{width:10px;height:10px;border-radius:50%;background:var(--terra);animation:pulse 1.3s infinite}
 .dot.done{background:var(--green);animation:none}
 @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(192,97,59,.5)}70%{box-shadow:0 0 0 12px rgba(192,97,59,0)}100%{box-shadow:0 0 0 0 rgba(192,97,59,0)}}
 .pctrow{display:flex;align-items:baseline;gap:.75rem;flex-wrap:wrap;margin-top:.4rem}
 .pct{font-family:Georgia,serif;font-size:clamp(2.2rem,7vw,3.4rem);color:var(--jungle);line-height:1}
 .pctrow small{color:var(--soft)}
 .bar{height:22px;background:#fff;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin:1.2rem 0 1.8rem;box-shadow:inset 0 1px 3px rgba(0,0,0,.05)}
 .fill{height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,var(--terra),var(--brass));transition:width .8s cubic-bezier(.4,0,.2,1)}
 .tasks{display:grid;gap:.6rem}
 .task{display:flex;align-items:flex-start;gap:.9rem;background:#fff;border:1px solid var(--line);border-radius:14px;padding:.85rem 1.1rem;box-shadow:0 2px 8px rgba(42,36,29,.05)}
 .task.active{border-color:var(--terra);box-shadow:0 0 0 2px rgba(192,97,59,.15)}
 .ic{flex:none;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-size:.85rem;font-weight:700;margin-top:1px}
 .ic.done{background:#eef6ef;color:var(--green)}
 .ic.active{background:#fbe6df;color:var(--terra)}
 .ic.pending{background:#f1ece2;color:var(--soft)}
 .ic.skipped{background:#f1ece2;color:var(--soft)}
 .tname{font-weight:700}
 .tdetail{color:var(--soft);font-size:.86rem;margin-top:.1rem}
 .task.pending .tname{color:var(--soft)}
 .spin{display:inline-block;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
 h2{font-family:Georgia,serif;color:var(--jungle);font-size:1.2rem;margin:2rem 0 .75rem}
 .log{background:#1c2b22;color:#cfe3d5;border-radius:14px;padding:1rem 1.2rem;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;line-height:1.7;max-height:320px;overflow:auto}
 .log div{white-space:pre-wrap}.log div:last-child{color:#fff}
 .done-banner{background:var(--green);color:#fff;border-radius:14px;padding:1.1rem 1.3rem;font-weight:700;margin-bottom:1.5rem;display:none}
 .foot{color:var(--soft);font-size:.8rem;margin-top:1.5rem}
 @media(prefers-reduced-motion:reduce){.dot,.fill,.spin{animation:none}}
</style></head><body><div class=wrap>
 <h1 id=title>Build Progress</h1>
 <div class=sub id=subtitle></div>
 <div class=live><span class=dot id=dot></span><span id=livetxt>Working…</span></div>
 <div class=pctrow><span class=pct id=pct>0%</span><small id=count>0 / 0 tasks</small></div>
 <div class=bar><div class=fill id=fill></div></div>
 <div class=done-banner id=banner>🎉 All build tasks complete — the site is ready to go live.</div>
 <div class=tasks id=tasks></div>
 <h2>Activity log</h2>
 <div class=log id=log></div>
 <div class=foot>Auto-refreshes every 4s · <code>scripts/build_status.json</code></div>
</div>
<script>
const ICON={done:'✓',active:'<span class=spin>◐</span>',pending:'•',skipped:'–'};
async function tick(){
 let s;try{s=await (await fetch('/status',{cache:'no-store'})).json()}catch(e){return}
 document.getElementById('title').textContent=s.title||'Build Progress';
 document.getElementById('subtitle').textContent=s.subtitle||'';
 document.getElementById('pct').textContent=s._pct+'%';
 document.getElementById('fill').style.width=s._pct+'%';
 document.getElementById('count').textContent=s._done+' / '+s._total+' tasks';
 const dot=document.getElementById('dot'),lt=document.getElementById('livetxt');
 if(s._all_done){dot.classList.add('done');lt.textContent='Complete';document.getElementById('banner').style.display='block';}
 else{lt.textContent=s._active?('Working · '+s._active):'Working…';}
 document.getElementById('tasks').innerHTML=(s.tasks||[]).map(t=>
   `<div class="task ${t.status}"><span class="ic ${t.status}">${ICON[t.status]||'•'}</span>`+
   `<div><div class=tname>${t.name}</div><div class=tdetail>${t.detail||''}</div></div></div>`).join('');
 const log=document.getElementById('log');
 log.innerHTML=(s.log||[]).map(l=>`<div>${l}</div>`).join('');
 log.scrollTop=log.scrollHeight;
}
tick();setInterval(tick,4000);
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/status"):
            body = json.dumps(status()).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
        else:
            body = PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, must-revalidate"); self.end_headers(); self.wfile.write(body)

if __name__ == "__main__":
    print(f"Build dashboard: http://localhost:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
