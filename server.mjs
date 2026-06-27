// =============================================================================
// Tourist Pharmacy — review server (DigitalOcean droplet)
//
// Serves the static build (dist/) behind a simple login page, and exposes
// POST /api/feedback which AI-structures each note (OpenAI, optional) and writes
// it + an optional screenshot into the feedback/ folder. A gated /feedback page
// lists everything for the team.
//
//   node server.mjs
//
// Env vars:
//   PORT             default 8080
//   SITE_PASSWORD    REQUIRED — the shared review login password
//   SESSION_SECRET   cookie signing secret (set a long random string)
//   OPENAI_API_KEY   optional — enables AI structuring of feedback
//   OPENAI_MODEL     default gpt-4o-mini
//   FEEDBACK_GIT     "1" to git add+commit+push each feedback file (needs git auth)
// =============================================================================
import express from 'express';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { execFile } from 'node:child_process';

// --- minimal .env loader (no dependency) -------------------------------------
// Lets you keep secrets in a local `.env` file (gitignored) instead of exporting
// them by hand. Real environment variables always win over the file.
(() => {
  try {
    const envPath = path.resolve('.env');
    if (!fs.existsSync(envPath)) return;
    for (const raw of fs.readFileSync(envPath, 'utf8').split('\n')) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const eq = line.indexOf('=');
      if (eq === -1) continue;
      const key = line.slice(0, eq).trim();
      let val = line.slice(eq + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch (e) { console.warn('.env load skipped:', e.message); }
})();

const PORT = process.env.PORT || 8080;
const PASSWORD = process.env.SITE_PASSWORD || '';
const SECRET = process.env.SESSION_SECRET || 'change-me-' + (PASSWORD || 'dev');
const OPENAI_KEY = process.env.OPENAI_API_KEY || '';
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';
const GIT_PUSH = process.env.FEEDBACK_GIT === '1';

const DIST = path.resolve('dist');
const FEEDBACK_DIR = path.resolve('feedback');
const SHOTS_DIR = path.join(FEEDBACK_DIR, 'screenshots');
fs.mkdirSync(SHOTS_DIR, { recursive: true });

const TOKEN = crypto.createHmac('sha256', SECRET).update('review:' + PASSWORD).digest('hex');
const app = express();
app.disable('x-powered-by');

// --- tiny cookie parser ------------------------------------------------------
app.use((req, _res, next) => {
  req.cookies = Object.fromEntries((req.headers.cookie || '').split(';').map((c) => {
    const i = c.indexOf('='); return [c.slice(0, i).trim(), decodeURIComponent(c.slice(i + 1))];
  }).filter((p) => p[0]));
  next();
});

const authed = (req) => !PASSWORD || req.cookies.tp_review === TOKEN;

// --- login -------------------------------------------------------------------
function loginPage(error = '') {
  return `<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Tourist Pharmacy — Review access</title><link rel=icon href="/favicon.svg" type="image/svg+xml">
<style>
 body{margin:0;min-height:100vh;display:grid;place-items:center;background:#16365c;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#16243a}
 .card{background:#fff;border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,.3);padding:2.4rem;width:min(380px,92vw);text-align:center}
 img{width:72px;height:72px;margin-bottom:1rem}
 h1{font-size:1.3rem;margin:.2rem 0 .3rem;color:#16365c}
 p{color:#51607a;font-size:.92rem;margin:0 0 1.4rem}
 input{width:100%;box-sizing:border-box;padding:.85rem 1rem;border:1.5px solid #e3e9f1;border-radius:12px;font:inherit;margin-bottom:.8rem}
 input:focus{outline:none;border-color:#16365c;box-shadow:0 0 0 4px #eef3f9}
 button{width:100%;padding:.9rem;border:0;border-radius:999px;background:#e3a52e;color:#16365c;font:inherit;font-weight:800;cursor:pointer}
 button:hover{background:#cf9526}
 .err{color:#dc2626;font-size:.85rem;margin-bottom:.8rem}
</style></head><body>
 <form class=card method=post action="/login">
  <img src="/logo-mark.svg" alt="">
  <h1>Tourist Pharmacy</h1>
  <p>Private review — please enter the access password.</p>
  ${error ? `<div class=err>${error}</div>` : ''}
  <input type=password name=password placeholder="Access password" autofocus required>
  <button type=submit>Enter</button>
 </form></body></html>`;
}
app.get('/login', (req, res) => { if (authed(req)) return res.redirect('/'); res.type('html').send(loginPage()); });
app.post('/login', express.urlencoded({ extended: false }), (req, res) => {
  if (PASSWORD && req.body.password === PASSWORD) {
    res.setHeader('Set-Cookie', `tp_review=${TOKEN}; HttpOnly; SameSite=Lax; Path=/; Max-Age=${60 * 60 * 24 * 14}`);
    return res.redirect('/');
  }
  res.status(401).type('html').send(loginPage('Incorrect password. Try again.'));
});

// --- gate everything below ---------------------------------------------------
app.use((req, res, next) => {
  if (authed(req)) return next();
  if (req.method === 'GET' && (req.headers.accept || '').includes('text/html')) return res.redirect('/login');
  res.status(401).json({ error: 'unauthorized' });
});

// --- feedback API ------------------------------------------------------------
async function structure(message, url) {
  if (!OPENAI_KEY) return null;
  try {
    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_KEY}` },
      body: JSON.stringify({
        model: OPENAI_MODEL, temperature: 0.2, response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: 'You turn raw website feedback into ONE clear, actionable issue for a dev team. Reply ONLY as JSON with keys: title (short imperative), type (one of bug, ux, copy, design, content, idea, question), severity (low, medium, high), summary (1-2 plain sentences), action (concrete suggested fix). Be faithful to the feedback; do not invent.' },
          { role: 'user', content: `Page: ${url}\n\nFeedback:\n${message}` },
        ],
      }),
    });
    const d = await r.json();
    return JSON.parse(d.choices[0].message.content);
  } catch (e) { console.error('OpenAI failed:', e.message); return null; }
}

app.post('/api/feedback', express.json({ limit: '15mb' }), async (req, res) => {
  try {
    const { name = '', message = '', url = '', path: pg = '', screenshot } = req.body || {};
    if (!message.trim()) return res.status(400).json({ error: 'empty' });
    const ts = new Date();
    const id = ts.toISOString().replace(/[:.]/g, '-') + '-' + crypto.randomBytes(3).toString('hex');

    let shotRel = '';
    if (typeof screenshot === 'string' && screenshot.startsWith('data:image')) {
      const b64 = screenshot.split(',')[1];
      fs.writeFileSync(path.join(SHOTS_DIR, `${id}.jpg`), Buffer.from(b64, 'base64'));
      shotRel = `./screenshots/${id}.jpg`;
    }

    const s = await structure(message, url || pg);
    const md =
      `# ${s?.title || 'Feedback'}\n\n` +
      `- **Type:** ${s?.type || '—'}  ·  **Severity:** ${s?.severity || '—'}\n` +
      `- **Page:** ${pg || url}\n` +
      `- **From:** ${name || 'anonymous'}\n` +
      `- **When:** ${ts.toISOString()}\n` +
      (shotRel ? `- **Screenshot:** ${shotRel}\n` : '') +
      (s ? `\n## Summary\n${s.summary || ''}\n\n## Suggested action\n${s.action || ''}\n` : '') +
      `\n## Original feedback\n> ${message.replace(/\n/g, '\n> ')}\n`;
    fs.writeFileSync(path.join(FEEDBACK_DIR, `${id}.md`), md);

    if (GIT_PUSH) {
      execFile('sh', ['-c', `git add feedback && git commit -m "feedback: ${(s?.title || 'note').replace(/"/g, '')}" && git push`],
        (e) => { if (e) console.error('git push failed:', e.message); });
    }
    res.json({ ok: true });
  } catch (e) { console.error(e); res.status(500).json({ error: 'server' }); }
});

// --- gated feedback index ----------------------------------------------------
app.get('/feedback', (_req, res) => {
  const files = fs.existsSync(FEEDBACK_DIR)
    ? fs.readdirSync(FEEDBACK_DIR).filter((f) => f.endsWith('.md')).sort().reverse() : [];
  const rows = files.map((f) => {
    const body = fs.readFileSync(path.join(FEEDBACK_DIR, f), 'utf8');
    const title = (body.match(/^# (.+)/) || [, f])[1];
    const meta = (body.match(/- \*\*Type.+/) || [''])[0].replace(/\*\*/g, '');
    return `<li><a href="/feedback/${f}">${title}</a><br><small>${meta} · ${f}</small></li>`;
  }).join('');
  res.type('html').send(`<!doctype html><meta charset=utf-8><title>Feedback (${files.length})</title>
   <style>body{font-family:system-ui;max-width:760px;margin:2rem auto;padding:0 1rem;color:#16243a}h1{color:#16365c}li{margin:.6rem 0}a{color:#0a5f66}small{color:#8893a6}</style>
   <h1>Feedback — ${files.length}</h1><ul>${rows || '<p>No feedback yet.</p>'}</ul>`);
});
app.get('/feedback/:file', (req, res) => {
  const f = path.basename(req.params.file);
  const fp = path.join(FEEDBACK_DIR, f);
  if (!fp.startsWith(FEEDBACK_DIR) || !fs.existsSync(fp)) return res.status(404).end();
  res.type(f.endsWith('.md') ? 'text/markdown' : 'application/octet-stream').send(fs.readFileSync(fp));
});

// --- static site -------------------------------------------------------------
app.use(express.static(DIST, { extensions: ['html'] }));
app.use((_req, res) => {
  const nf = path.join(DIST, '404.html');
  res.status(404).type('html').send(fs.existsSync(nf) ? fs.readFileSync(nf) : 'Not found');
});

app.listen(PORT, () => {
  console.log(`Tourist Pharmacy review server on :${PORT}`);
  if (!PASSWORD) console.warn('⚠  SITE_PASSWORD not set — the site is NOT gated.');
  if (!OPENAI_KEY) console.warn('ℹ  OPENAI_API_KEY not set — feedback saved without AI structuring.');
});
