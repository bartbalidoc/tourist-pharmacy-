# Services, APIs & keys

Every external service this project uses, what each key is for, the **env-var name** it goes in, and
where to get/manage it. **No secret values live in this file** — actual values are in the gitignored
`SECRETS.local.md` (your machine only) and in the droplet's `.env`. This doubles as a reusable checklist
for spinning up the same stack on another project.

> 🔐 **Golden rule:** keys go in `.env` (gitignored) or your secret store — **never** in committed
> files. This repo is public; a committed key is a leaked key.

---

## Keys & where they go

| Service | Env var | Used for | Where to get / manage it | Cost |
|---|---|---|---|---|
| **OpenAI** | `OPENAI_API_KEY` | AI-structuring reviewer feedback into a clear issue (server.mjs) | https://platform.openai.com/api-keys | pay-per-use (tiny; gpt-4o-mini) |
| OpenAI model | `OPENAI_MODEL` | which model (default `gpt-4o-mini`) | n/a (just a name) | — |
| **Review login** | `SITE_PASSWORD` | the shared password reviewers type to enter | you choose it | free |
| **Cookie signing** | `SESSION_SECRET` | signs the login cookie (`openssl rand -hex 32`) | you generate it | free |
| **Feedback auto-commit** | `FEEDBACK_GIT` | `1` = droplet commits+pushes each note (needs git auth) | optional | free |
| **ExchangeRate-API** | `CURRENCY_API_KEY` *(currently in `src/lib/site.ts`)* | live USD↔IDR rates on product pages | https://www.exchangerate-api.com (free tier) | free tier |
| **GitHub** | — (PAT used once for push) | hosts the repo + is the deploy source | https://github.com/settings/tokens (`repo` scope) | free |
| **DigitalOcean droplet** | — (root SSH) | hosts the review container | https://cloud.digitalocean.com | the droplet's plan |

**No-key dependencies** (loaded from CDNs, nothing to configure): html2canvas (screenshots), Google Fonts
(Plus Jakarta Sans). **WhatsApp** funnel uses a plain number (`WHATSAPP` in `src/lib/site.ts`), not an API.

> ⚠️ `CURRENCY_API_KEY` is currently hardcoded in `src/lib/site.ts` (free-tier, low-sensitivity). For a
> stricter setup, move it to an env var like the others.

---

## The `.env` (what the review server reads)

Copy `.env.example` → `.env` and fill in values. The server (`server.mjs`) reads it via a tiny built-in
loader; in Docker it's passed through `env_file: .env`.

```
SITE_PASSWORD=          # required — reviewer login password
SESSION_SECRET=         # openssl rand -hex 32
OPENAI_API_KEY=         # optional — feedback saved verbatim without it
OPENAI_MODEL=gpt-4o-mini
FEEDBACK_GIT=           # 1 to auto commit+push feedback; empty otherwise
PORT=8080
```

---

## Reuse this stack on another project

The "private review site with AI feedback + auto-deploy" pattern is portable. To replicate:

1. **Site** — any static/SSR build that outputs a folder (`dist/`). Drop in `server.mjs` (login gate +
   `/api/feedback`) and `FeedbackWidget` (the floating tab).
2. **Secrets** — `cp .env.example .env`, fill in `SITE_PASSWORD`, `SESSION_SECRET`, `OPENAI_API_KEY`.
3. **Container** — reuse `Dockerfile` + `docker-compose.yml` (change the container name + port).
4. **Host** — on the droplet: `git clone`, create `.env`, `docker compose up -d --build`. It runs
   isolated alongside other apps (own port, own container).
5. **Auto-deploy** — copy `deploy.sh` and add the cron line:
   `*/2 * * * * /path/to/deploy.sh --quiet-if-noop >> /var/log/<name>-deploy.log 2>&1`
6. **Expose** — direct `http://<ip>:<port>` (fast) or an nginx server block + subdomain + certbot (clean URL + HTTPS).

See [UPDATING.md](UPDATING.md) for the day-to-day push→live workflow and [DEPLOY_REVIEW.md](DEPLOY_REVIEW.md)
for the full droplet runbook.
