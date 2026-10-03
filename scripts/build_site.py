"""Build TopContractReview's static Cloudflare site and complete downloads."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import json
import shutil
import tempfile
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile, ZIP_DEFLATED
from package_release import package, VERSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "website/public"
ORIGIN = "https://topcontractreview.com"


def shell(title, description, body, route):
    items = [("workflow", "How it works"), ("forms", "Review forms"),
             ("library", "The package"), ("get-started", "Get started")]
    links = "".join(f'<a href="/{slug}/" data-n="{i:02}"'
                    + (' aria-current="page"' if route == slug else "")
                    + f'>{label}</a>' for i, (slug, label) in enumerate(items, 1))
    url = ORIGIN + ("/" if not route else "/" + route + "/")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} — TopContractReview</title><meta name="description" content="{escape(description, quote=True)}">
<link rel="canonical" href="{url}"><meta property="og:type" content="website"><meta property="og:site_name" content="TopContractReview">
<meta property="og:title" content="{escape(title, quote=True)} — TopContractReview"><meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:url" content="{url}"><meta name="twitter:card" content="summary"><meta name="referrer" content="no-referrer">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/app.css"><script defer src="/app.js"></script></head>
<body><a class="skip-link" href="#main">Skip to content</a><header class="nav"><div class="nav-inner">
<a class="brand" href="/">TopContractReview</a><button class="menu-btn" aria-label="Toggle navigation" aria-expanded="false" aria-controls="navlinks">☰</button>
<nav class="links" id="navlinks" aria-label="Main navigation">{links}</nav></div></header>
<main id="main">{body}</main><footer><div class="wrap"><div class="footer-inner"><a class="brand" href="/">TopContractReview</a>
<nav class="footer-links" aria-label="Footer navigation"><a href="/about/">About</a><a href="/safety/">Using AI carefully</a><a href="/verification/">Method & validation</a><a href="https://github.com/sps18209/contract-check">Source</a></nav></div>
<p class="footer-note">Contract Check · Development edition {VERSION} · Drafting and issue spotting with human review. No contract-upload form. No attorney-client relationship is created. If an attorney has not reviewed the complete agreement, seek attorney review before anyone signs.</p>
<p class="footer-note">© 2026 TopContractReview. Website design adapted from TopDWI under its <a href="/LICENSE-CODE">MIT code license</a>.</p></div></footer></body></html>'''


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def validate():
    parsed = {}
    for page in OUT.rglob("*.html"):
        parser = Links()
        parser.feed(page.read_text())
        parsed[page] = parser
    for page, parser in parsed.items():
        for link in parser.links:
            uri = urlsplit(link)
            if uri.scheme or uri.netloc:
                continue
            if not uri.path:
                target = page
            else:
                target = OUT / unquote(uri.path).lstrip("/")
                if uri.path.endswith("/"):
                    target /= "index.html"
            assert target.exists(), (str(page), link)
            if uri.fragment and target in parsed:
                assert unquote(uri.fragment) in parsed[target].ids, (str(page), link)
    with ZipFile(OUT / "downloads/contract-check-direct-upload.zip") as z:
        assert "SKILL.md" in z.namelist()
        assert len([n for n in z.namelist() if n.startswith("assets/forms/")]) == 4
    with ZipFile(OUT / "downloads/contract-check-claude-skill.zip") as z:
        assert "contract-check/SKILL.md" in z.namelist()
        assert "contract-check/references/enforcement-analysis.md" in z.namelist()
    print(f"Verified {len(parsed)} HTML pages, internal links, fragments, and complete downloads.")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "website/static", OUT)
    pages = json.loads((ROOT / "website/pages.json").read_text())
    skill = (ROOT / "skill/SKILL.md").read_text()
    home = (ROOT / "website/home.html").read_text()
    (OUT / "index.html").write_text(shell(
        "Know where the draft changes the deal",
        "Compare a contract with the deal you intended. Record passage-linked findings, your choices, and controlled revisions with Contract Check.",
        home, ""))
    for route, page in pages.items():
        directory = OUT / route
        directory.mkdir()
        body = page["body"].replace("@@SKILL_SOURCE@@", escape(skill))
        (directory / "index.html").write_text(shell(page["title"], page["description"], body, route))
    body = '<section><div class="wrap"><h1>Page not found.</h1><p>This address does not match a page on TopContractReview.</p><a class="btn btn-primary" href="/">Return home →</a></div></section>'
    (OUT / "404.html").write_text(shell("Page not found", "Return to TopContractReview.", body, ""))
    shutil.copytree(ROOT / "skill", OUT / "resources")
    downloads = OUT / "downloads"
    downloads.mkdir()
    with tempfile.TemporaryDirectory() as temporary:
        package(temporary)
        for name in ("contract-check-direct-upload.zip", "contract-check-plugin.zip", "contract-check-2026-development.zip", "contract-check-claude-skill.zip", "SHA256SUMS.txt"):
            shutil.copy(Path(temporary) / name, downloads / name)
        shutil.copy(Path(temporary) / "contract-check-2026-development.zip", downloads / "contract-check.skill")
    urls = [ORIGIN + "/"] + [ORIGIN + "/" + slug + "/" for slug in pages]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join("<url><loc>" + url + "</loc></url>" for url in urls) + "</urlset>")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + ORIGIN + "/sitemap.xml\n")
    (OUT / "llms.txt").write_text("# TopContractReview\n\nContract Check is a development skill and Python engine for deliberate contract review. No contract-upload service is operated on this website.\n\n" + "\n".join("- " + url for url in urls) + "\n")
    validate()
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / "topcontractreview-site.zip"
        config = json.loads((ROOT / "wrangler.jsonc").read_text())
        config["assets"]["directory"] = "./public"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as z:
            for file in sorted(OUT.rglob("*")):
                if file.is_file():
                    z.write(file, "topcontractreview/public/" + file.relative_to(OUT).as_posix())
            z.writestr("topcontractreview/wrangler.jsonc", json.dumps(config, indent=2))
            z.writestr("topcontractreview/package.json", json.dumps({"name":"topcontractreview","private":True,"scripts":{"deploy":"wrangler deploy","dev":"wrangler dev"},"devDependencies":{"wrangler":"^4"}}))
            z.writestr("topcontractreview/DEPLOY.md", "Deploy from this directory with npm install then npx wrangler deploy. Sign into your Cloudflare account first. The configured custom domains must be in that account. This package contains the complete rendered site and skill downloads.\n")
        shutil.copy(archive, ROOT / "website/topcontractreview-site.zip")


if __name__ == "__main__":
    build()
