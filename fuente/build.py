"""Builds the site into publicar/: every page in fuente/pages wrapped in the same header and footer.

    python fuente/build.py

Pages are plain HTML fragments. The first line of each is its title:  <!-- title: Install -->
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "fuente"
OUT = ROOT / "publicar"
REPO = "https://github.com/kimba23/models-in-motion"

NAV = [("Install", "install.html"), ("Tools", "tools.html"),
       ("1 Abundance", "sessions/01-abundance.html"), ("2 Pulse", "sessions/02-pulse.html")]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<header class="top">
  <a class="name" href="{up}index.html">Models in Motion</a>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>Models in Motion · Fridays, fall 2026 · <a href="{repo}">the scripts and this site on GitHub</a></footer>
</body>
</html>
"""


def build():
    OUT.mkdir(exist_ok=True)
    for old in OUT.iterdir():                    # empty it (a test server may be sitting in it)
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    shutil.copy(SRC / "style.css", OUT / "style.css")
    for folder in ("scripts", "downloads"):
        shutil.copytree(ROOT / folder, OUT / folder)
    for page in sorted((SRC / "pages").rglob("*.html")):
        rel = page.relative_to(SRC / "pages")
        up = "../" * (len(rel.parts) - 1)
        body = page.read_text(encoding="utf-8")
        m = re.match(r"<!--\s*title:\s*(.*?)\s*-->", body)
        title = f"{m.group(1)} · Models in Motion" if m else "Models in Motion"
        nav = "".join(f'<a href="{up}{href}">{name}</a>' for name, href in NAV)
        html = PAGE.format(title=title, up=up, nav=nav, body=body.replace("{up}", up).replace("{repo}", REPO), repo=REPO)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        print(rel)


build()
