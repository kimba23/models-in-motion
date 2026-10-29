# Models in Motion

The class site and the scripts. Seven Fridays, fall 2026.

- `scripts/` — the editing scripts students run on their takes and give to a chat to rewrite.
- `downloads/` — the tools update for the kit (the kit itself is on Dropbox, linked from the site).
- `fuente/pages/` — the pages, as HTML fragments. `fuente/build.py` wraps them into `publicar/`.

Publish (Cloudflare Pages, project `motion`):

    python fuente/build.py
    wrangler pages deploy publicar --project-name motion --branch main --commit-dirty=true
