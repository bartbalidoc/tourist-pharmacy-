# Deploying the private review site (DigitalOcean droplet)

This is the **password-gated review build** — the public site stays static (see [DEPLOY.md](DEPLOY.md)),
but the review site runs a small **Node server** (`server.mjs`) so it can:

1. Put the whole site **behind a login page** (not ready for the world yet).
2. Collect reviewer **feedback into the `feedback/` folder** here in the repo, AI-structured into a
   clear, actionable issue (title · type · severity · summary · suggested fix) with an optional screenshot.

The floating **Feedback** tab (left edge of every page) only appears while `REVIEW_MODE = true` in
[src/lib/site.ts](src/lib/site.ts). Flip it to `false` for the public launch.

---

## What you need
- A DigitalOcean droplet (Ubuntu) — you have one.
- SSH access to it.
- Node 18+ on the droplet.
- A domain or subdomain pointing at the droplet (e.g. `review.touristpharmacy.com`). Optional but
  recommended so you get HTTPS.

---

## 1. Get the code onto the droplet

```bash
ssh root@YOUR_DROPLET_IP

# install Node 20 if it isn't there yet
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs git nginx

# clone the repo (this is the new build — see the GitHub step below)
cd /var/www
git clone https://github.com/bartbalidoc/tourist-pharmacy-.git tourist-pharmacy
cd tourist-pharmacy
```

## 2. Configure secrets

```bash
cp .env.example .env
nano .env      # set SITE_PASSWORD, SESSION_SECRET, OPENAI_API_KEY
```
- `SITE_PASSWORD` — the one password you give your reviewers.
- `SESSION_SECRET` — run `openssl rand -hex 32` and paste the result.
- `OPENAI_API_KEY` — from the simple Asana board (optional; without it feedback is saved verbatim).

## 3. Build and run

```bash
npm install
npm run build          # produces dist/ (~3,500 pages)
npm run serve          # starts server.mjs on PORT (8080)
```

Visit `http://YOUR_DROPLET_IP:8080` — you should hit the login page.

## 4. Keep it running (pm2)

```bash
npm i -g pm2
pm2 start server.mjs --name tourist-review
pm2 save && pm2 startup     # restarts on reboot
```

Logs: `pm2 logs tourist-review`. Restart after a rebuild: `npm run build && pm2 restart tourist-review`.

## 5. HTTPS via nginx (recommended)

```nginx
# /etc/nginx/sites-available/tourist-review
server {
  server_name review.touristpharmacy.com;
  client_max_body_size 20m;          # screenshots can be a few MB
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
  }
}
```
```bash
ln -s /etc/nginx/sites-available/tourist-review /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d review.touristpharmacy.com   # free HTTPS
```

---

## Getting the feedback back into VS Code
Reviewers' notes are written to `feedback/<timestamp>.md` (+ `feedback/screenshots/`). Two ways to pull
them to your machine:

- **Automatic:** set `FEEDBACK_GIT=1` in `.env` (and configure git auth on the droplet). Each note is
  committed + pushed; you just `git pull` locally.
- **Manual:** `scp -r root@YOUR_DROPLET_IP:/var/www/tourist-pharmacy/feedback ./` whenever you want them.

You can also browse them live at `https://review.touristpharmacy.com/feedback` (behind the same login).

---

## Going public later
1. Set `REVIEW_MODE = false` in [src/lib/site.ts](src/lib/site.ts) (hides the feedback tab).
2. Rebuild. For the public site you don't need the Node server at all — host `dist/` statically per
   [DEPLOY.md](DEPLOY.md), or keep the droplet and just remove `SITE_PASSWORD` to drop the login gate.
