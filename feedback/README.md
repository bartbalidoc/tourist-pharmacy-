# Feedback

Reviewer feedback collected from the live review site lands here — one markdown file per note
(AI-structured into a clear title, type, severity, summary, and suggested action), with any
screenshot under `screenshots/`.

- The floating **Feedback** tab on the review site (left edge) posts to `POST /api/feedback`
  (handled by `server.mjs`), which writes the file here.
- Browse them in the app at `/feedback` (behind the login), or read the files directly in VS Code.
- To pull droplet feedback into your local repo, set `FEEDBACK_GIT=1` on the server (auto commits
  + pushes), or `scp -r <droplet>:/path/feedback ./`.

This folder is intentionally committed (with `.gitkeep`) so the structure exists; the generated
`*.md` and `screenshots/*` are the actual feedback.
