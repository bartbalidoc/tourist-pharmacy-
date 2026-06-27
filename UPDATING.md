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

## Part 3 — Going live is now automatic ✨

**You don't have to do anything to deploy.** The droplet runs the review site as a Docker container
(`/root/tourist-review`) and a cron job checks GitHub **every 2 minutes**. When it sees a new commit on
`main`, it automatically pulls, rebuilds the container, and health-checks it. So:

> **Push to GitHub → it's live within ~2 minutes. No console, no SSH, nothing to run.**

How it works (for reference — you don't run these):
- `deploy.sh` (in this repo, lives on the droplet) = pull + rebuild + health-check, with a lock so it
  never runs twice at once.
- cron line on the droplet: `*/2 * * * * /root/tourist-review/deploy.sh --quiet-if-noop`
- A deploy only happens when there's actually a new commit; otherwise the cron does nothing.

**Want it live *immediately* instead of waiting up to 2 min?** Ask Claude — it has deploy access and can
run `deploy.sh` on the droplet on demand. Or, if you're on the droplet console yourself:
```bash
/root/tourist-review/deploy.sh        # deploy right now
```

Check deploy history anytime: `cat /var/log/tp-deploy.log` on the droplet.

---

## Part 4 — Pulling reviewer feedback back into VS Code

Reviewers' notes are written into `feedback/` **on the droplet**. To work on them here:

- **If you set `FEEDBACK_GIT=1`** in the droplet's `.env`: the droplet auto-commits each note and pushes
  it. Just run `git pull` here and the new `feedback/*.md` files appear. *(The droplet needs git auth for
  this — same `gh auth login` step, done once on the droplet.)*
- **Otherwise (manual):** copy them down whenever you want:
  ```bash
  scp -r root@206.189.200.138:/root/tourist-review/feedback ./
  ```

You can always read live feedback in the browser at `http://206.189.200.138:8080/feedback` (behind the login).

### The feedback → fix → live loop
1. Team uses the **Feedback** tab on the live site → notes (AI-structured) land in `feedback/` on the droplet.
2. You review them (browser `/feedback`, or pull the files down) and decide what to change.
3. Claude implements the fix and pushes → the droplet **auto-deploys within ~2 min** (or instantly on request).
4. Team refreshes and sees the change. Repeat.

---

## Quick reference card

| I want to… | Where | Command |
|---|---|---|
| Save my edits to GitHub | VS Code | `git add -A && git commit -m "…" && git push` |
| Make it live | — | **Automatic** — happens within ~2 min of pushing (or ask Claude to deploy now) |
| See what I changed | VS Code | `git status` |
| Get reviewer feedback locally | VS Code | `scp -r root@206.189.200.138:/root/tourist-review/feedback ./` |
| See deploy history | Droplet | `cat /var/log/tp-deploy.log` |
| Turn the feedback tab off (go public) | VS Code | set `REVIEW_MODE = false` in `src/lib/site.ts`, then push (auto-deploys) |

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
