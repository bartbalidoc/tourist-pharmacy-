# Updating & pushing Tourist Pharmacy

Plain-English guide to getting code from this folder **up to GitHub** and **live on the droplet**.
You do not need to be a git expert — copy the commands in order.

- **GitHub repo:** https://github.com/bartbalidoc/tourist-pharmacy-
- **Live review site:** the DigitalOcean droplet (see [DEPLOY_REVIEW.md](DEPLOY_REVIEW.md) for the server setup)
- **Two machines are involved:**
  1. **Here (your laptop / VS Code)** — where you edit code and push to GitHub.
  2. **The droplet** — where the live site runs. It *pulls* from GitHub and rebuilds.

```
  [ VS Code ] --push--> [ GitHub ] --pull--> [ Droplet ] --> live site
```

---

## Part 1 — One-time setup (do this once, ever)

You only do this the very first time. After that, jump to Part 2.

### 1a. Connect this folder to GitHub
```bash
# install GitHub's login tool if you don't have it (Ubuntu/WSL):
#   sudo apt install gh        (mac: brew install gh)

gh auth login          # choose: GitHub.com → HTTPS → login with browser
```

```bash
cd "/home/barthofstee555/vs code /Tourist Pharmacy Website"
git remote add origin https://github.com/bartbalidoc/tourist-pharmacy-.git
git branch -M main
```

### 1b. First push (replaces the old site in the repo)
> ⚠️ The repo currently holds the **old** site. This overwrites it with the new build. That's the plan
> ("replace the live site, behind login"), but it is the one irreversible step — make sure you mean it.
```bash
git push -u origin main --force
```
After this, `--force` is **not** needed again. Future pushes are just `git push`.

### 1c. First deploy on the droplet
SSH in and follow [DEPLOY_REVIEW.md](DEPLOY_REVIEW.md) once (clone, `.env`, `npm install`, `npm run build`,
`pm2 start`). After that, updates are just the short loop in Part 3.

---

## Part 2 — Everyday: push a change to GitHub

Whenever you've edited something here and want to save it to GitHub:

```bash
cd "/home/barthofstee555/vs code /Tourist Pharmacy Website"

git add -A                          # stage every change
git commit -m "Short note: what you changed and why"
git push                            # send it to GitHub
```

That's it. Three commands. Examples of good commit messages:
- `git commit -m "Fix doxycycline price showing wrong USD amount"`
- `git commit -m "Add new antibiotic products from supplier list"`
- `git commit -m "Reword About page hero per team feedback"`

**Before you commit, sanity-check what's going out** (optional but smart):
```bash
git status            # lists what changed
```

> 🔐 **Secrets are safe automatically.** `.env` (your passwords + OpenAI key), the raw supplier CSVs, and
> the pharmacy PDFs are all in `.gitignore`, so `git add -A` will never upload them. Don't remove those
> lines from `.gitignore`.

---

## Part 3 — Make the change go live (on the droplet)

Pushing to GitHub does **not** update the live site by itself — the droplet has to pull and rebuild.
SSH into the droplet and run:

```bash
cd /var/www/tourist-pharmacy        # wherever you cloned it
git pull                            # get the latest code from GitHub
npm install                         # only needed if dependencies changed
npm run build                       # rebuild the ~3,500 pages
pm2 restart tourist-review          # restart the server with the new build
```

Tip: save that as a one-liner on the droplet so a deploy is a single command:
```bash
git pull && npm install && npm run build && pm2 restart tourist-review
```

The new version is live the moment `pm2 restart` finishes. Check `pm2 logs tourist-review` if anything
looks off.

---

## Part 4 — Pulling reviewer feedback back into VS Code

Reviewers' notes are written into `feedback/` **on the droplet**. To work on them here:

- **If you set `FEEDBACK_GIT=1`** in the droplet's `.env`: the droplet auto-commits each note and pushes
  it. Just run `git pull` here and the new `feedback/*.md` files appear. *(The droplet needs git auth for
  this — same `gh auth login` step, done once on the droplet.)*
- **Otherwise (manual):** copy them down whenever you want:
  ```bash
  scp -r root@YOUR_DROPLET_IP:/var/www/tourist-pharmacy/feedback ./
  ```

You can always read live feedback in the browser at `https://<your-review-domain>/feedback` (behind the login).

---

## Quick reference card

| I want to… | Where | Command |
|---|---|---|
| Save my edits to GitHub | VS Code | `git add -A && git commit -m "…" && git push` |
| Make it live | Droplet (SSH) | `git pull && npm install && npm run build && pm2 restart tourist-review` |
| See what I changed | VS Code | `git status` |
| Get reviewer feedback locally | VS Code | `git pull` (if `FEEDBACK_GIT=1`) or `scp -r …/feedback ./` |
| Turn the feedback tab off (go public) | VS Code | set `REVIEW_MODE = false` in `src/lib/site.ts`, then push + redeploy |

---

## If something goes wrong

- **`git push` rejected ("fetch first" / "behind")** — someone (or the droplet) pushed first. Run
  `git pull --rebase`, resolve any conflicts it lists, then `git push` again.
- **Push asks for a password and fails** — your login expired. Run `gh auth login` again.
- **Live site didn't change after deploy** — you forgot `npm run build` or `pm2 restart` on the droplet.
  Re-run the Part 3 one-liner.
- **Accidentally committed a secret** — tell me; don't push. We rotate the key and rewrite the commit.
- **Not sure if it's safe to push** — run `git status` and read the list. If you see `.env` in it,
  **stop** and check `.gitignore` (it should be there). Ask me if unsure.
