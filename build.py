#!/usr/bin/env python3
"""Builds the static site into _site/ from posts/*.md, pages/*.html and site.json.

Run locally:  pip install markdown && python build.py && python -m http.server -d _site
On GitHub this runs automatically (.github/workflows/deploy.yml).
"""
import datetime as dt
import html
import json
import math
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = SITE["domain"].rstrip("/")
MONTHS = ["január", "február", "március", "április", "május", "június", "július",
          "augusztus", "szeptember", "október", "november", "december"]
NAV = [("/", "Kezdőlap"), ("/cikkek/", "Cikkek"), ("/kapcsolat/", "Kapcsolat")]
esc = lambda s: html.escape(str(s), quote=True)


def hu_date(d):
    return f"{d.year}. {MONTHS[d.month - 1]} {d.day}."


def abs_url(path):
    return path if path.startswith("http") else BASE + "/" + path.lstrip("/")


def local(path):
    """images/x.jpg -> /images/x.jpg (leaves full URLs alone)."""
    if not path or re.match(r"^(https?:)?//|^/", path):
        return path
    return "/" + path.lstrip("./")


# ---------- Markdown ----------
YT = re.compile(r"^\s*<?(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)"
                r"([A-Za-z0-9_-]{11})[^\s>]*>?\s*$")
IMG_LINE = re.compile(r'^\s*!\[([^\]]*)\]\(\s*([^\s)]+)(?:\s+"([^"]*)")?\s*\)\s*$')


def youtube_block(vid):
    return (f'<div class="yt" data-id="{vid}"><button type="button" class="yt-btn">'
            f'<span class="yt-play" aria-hidden="true"></span>'
            f'<span class="yt-txt"><b>YouTube-videó lejátszása</b>'
            f'<small>A lejátszás betölti a YouTube (Google) tartalmát. '
            f'<a href="/adatvedelem/#sutik">Részletek</a></small></span></button>'
            f'<noscript><a href="https://www.youtube.com/watch?v={vid}">Videó megnyitása a YouTube-on</a></noscript></div>')


def preprocess(text):
    """Lines with only a YouTube link -> video embed; lines with only an image -> figure."""
    out = []
    for line in text.split("\n"):
        m = YT.match(line)
        if m:
            out += ["", youtube_block(m.group(1)), ""]
            continue
        m = IMG_LINE.match(line)
        if m:
            alt, src, cap = m.groups()
            fig = f'<figure><img src="{esc(local(src))}" alt="{esc(alt)}" loading="lazy" decoding="async">'
            if cap:
                fig += f"<figcaption>{esc(cap)}</figcaption>"
            out += ["", fig + "</figure>", ""]
            continue
        out.append(line)
    return "\n".join(out)


def postprocess(h):
    # > **Tévhit:** ...  /  > **Valóság:** ...  -> coloured boxes
    def box(m):
        inner = m.group(1)
        low = inner.lower()
        cls = "myth" if "<strong>tévhit" in low else "fact" if re.search(r"<strong>(valóság|tény)", low) else "note"
        return f'<blockquote class="{cls}">{inner}</blockquote>'
    h = re.sub(r"<blockquote>(.*?)</blockquote>", box, h, flags=re.S)
    # external links open safely
    h = re.sub(r'<a href="(https?://(?!edzestevhitek\.hu)[^"]+)"', r'<a href="\1" rel="noopener" target="_blank"', h)
    # inline images (not on their own line) also get lazy loading + absolute path
    h = re.sub(r'<img alt="([^"]*)" src="(?!/|https?:)([^"]+)"', lambda m: f'<img alt="{m.group(1)}" src="/{m.group(2)}" loading="lazy"', h)
    # make h2 linkable
    def anchor(m):
        slug = re.sub(r"[^a-z0-9]+", "-", strip_accents(re.sub("<.*?>", "", m.group(1)).lower())).strip("-")
        return f'<h2 id="{slug}">{m.group(1)}</h2>'
    return re.sub(r"<h2>(.*?)</h2>", anchor, h)


def strip_accents(s):
    return s.translate(str.maketrans("áéíóöőúüű", "aeiooouuu"))


def render_md(text):
    return postprocess(markdown.markdown(preprocess(text), extensions=["extra", "sane_lists"], output_format="html"))


def front_matter(text):
    meta = {}
    if text.startswith("---"):
        _, fm, text = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"')
    return meta, text.strip()


# ---------- Layout ----------
def layout(*, title, body, path, description=None, image=None, og_type="website", extra_head="", body_class=""):
    full_title = title if title == SITE["name"] else f"{title} – {SITE['name']}"
    desc = description or SITE["description"]
    img = abs_url(image or SITE["default_image"])
    nav = "".join(
        f'<a href="{u}"{" aria-current=\"page\"" if (path == u or (u != "/" and path.startswith(u))) else ""}>{t}</a>'
        for u, t in NAV)
    year = dt.date.today().year
    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:locale" content="hu_HU">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:image" content="{esc(img)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['name'])}" href="/feed.xml">
<link rel="preload" href="/assets/fonts/archivo-latin-wdth-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
{extra_head}</head>
<body class="{body_class}">
<a class="skip" href="#tartalom">Ugrás a tartalomra</a>
<header class="site"><div class="w bar">
<a class="brand" href="/" aria-label="{esc(SITE['name'])} – kezdőlap"><span class="b1">Edzés</span><span class="b2">tévhitek</span></a>
<button id="mb" aria-label="Menü" aria-expanded="false" aria-controls="nv"><span></span><span></span><span></span></button>
<nav id="nv" aria-label="Fő navigáció">{nav}</nav>
</div></header>
<main id="tartalom">
{body}
</main>
<footer class="site"><div class="w">
<div class="f-top">
<div><a class="brand sm" href="/"><span class="b1">Edzés</span><span class="b2">tévhitek</span></a>
<p>{esc(SITE['tagline'])}.</p></div>
<nav aria-label="Lábléc"><a href="/cikkek/">Cikkek</a><a href="/kapcsolat/">Kapcsolat</a><a href="/adatvedelem/">Adatvédelem és sütik</a><a href="#" id="ck">Süti beállítások</a><a href="/feed.xml">RSS</a></nav>
</div>
<p class="disc">Az oldal tartalma általános tájékoztatás, nem helyettesíti az orvosi, dietetikusi vagy edzői személyes tanácsot. Egészségügyi panasz esetén kérdezd meg az orvosodat.</p>
<p class="copy">© {year} {esc(SITE['name'])}</p>
</div></footer>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""


def card(p, big=False):
    img = (f'<div class="c-img"><img src="{esc(local(p["cover"]))}" alt="{esc(p.get("cover_alt", ""))}" loading="lazy" decoding="async"></div>'
           if p.get("cover") else "")
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"][:2])
    return (f'<article class="card{" big" if big else ""}"><a href="{p["url"]}">{img}<div class="c-body">'
            f'<div class="meta">{tags}<time datetime="{p["date"]}">{hu_date(p["date"])}</time></div>'
            f'<h3>{esc(p["title"])}</h3><p>{esc(p["summary"])}</p>'
            f'<span class="more">Elolvasom <span aria-hidden="true">→</span></span></div></a></article>')


def cards(posts):
    if not posts:
        return '<p class="empty">Hamarosan érkeznek az első cikkek.</p>'
    return '<div class="cards">' + "".join(card(p, i == 0) for i, p in enumerate(posts)) + "</div>"


# ---------- Build ----------
def load_posts():
    posts = []
    today = dt.date.today()
    for f in sorted((ROOT / "posts").glob("*.md")):
        if f.name.startswith("_"):
            continue  # _drafts are skipped
        meta, body = front_matter(f.read_text(encoding="utf-8"))
        if meta.get("draft", "").lower() in ("true", "igen", "yes", "1"):
            continue
        d = dt.date.fromisoformat(meta["date"])
        if d > today:
            continue  # scheduled: appears on its date (the daily rebuild publishes it)
        slug = f.stem
        html_body = render_md(body)
        words = len(re.sub("<.*?>", " ", html_body).split())
        posts.append({
            "slug": slug, "url": f"/cikkek/{slug}/", "title": meta["title"], "date": d,
            "updated": dt.date.fromisoformat(meta["updated"]) if meta.get("updated") else None,
            "summary": meta.get("summary", ""), "cover": meta.get("cover", ""),
            "cover_alt": meta.get("cover_alt", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "html": html_body, "minutes": max(1, math.ceil(words / 200)),
            "has_video": 'class="yt"' in html_body,
        })
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def write(path, content):
    target = OUT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build_post(p, posts):
    others = [o for o in posts if o["slug"] != p["slug"]][:3]
    cover = (f'<figure class="cover"><img src="{esc(local(p["cover"]))}" alt="{esc(p["cover_alt"])}" fetchpriority="high"></figure>'
             if p["cover"] else "")
    upd = f' · frissítve: <time datetime="{p["updated"]}">{hu_date(p["updated"])}</time>' if p["updated"] else ""
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
          "description": p["summary"], "datePublished": p["date"].isoformat(),
          "dateModified": (p["updated"] or p["date"]).isoformat(), "inLanguage": "hu",
          "mainEntityOfPage": BASE + p["url"], "image": abs_url(p["cover"] or SITE["default_image"]),
          "publisher": {"@type": "Organization", "name": SITE["name"], "url": BASE + "/"}}
    more = (f'<section class="w related"><h2 class="sec">Még több tévhit</h2>{cards(others)}</section>' if others else "")
    body = f"""<article class="post">
<header class="w post-head">
<p class="kicker"><a href="/cikkek/">← Minden cikk</a></p>
<div class="meta">{tags}</div>
<h1>{esc(p["title"])}</h1>
<p class="lede">{esc(p["summary"])}</p>
<p class="byline"><time datetime="{p["date"]}">{hu_date(p["date"])}</time>{upd} · {p["minutes"]} perc olvasás</p>
</header>
<div class="w">{cover}</div>
<div class="w prose">
{p["html"]}
</div>
</article>
{more}"""
    write(p["url"], layout(title=p["title"], body=body, path=p["url"], description=p["summary"],
                           image=p["cover"] or None, og_type="article",
                           extra_head=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'))


def build_pages(posts):
    for f in sorted((ROOT / "pages").glob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--(.*?)-->", text, re.S)
        meta = {}
        if m:
            for line in m.group(1).strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            text = text[m.end():]
        path = meta.get("url", f"/{f.stem}/")
        text = (text.replace("{{latest_posts}}", cards(posts[: SITE["home_latest_count"]]))
                    .replace("{{all_posts}}", cards(posts))
                    .replace("{{post_count}}", str(len(posts)))
                    .replace("{{formspree_id}}", SITE["formspree_id"])
                    .replace("{{site_name}}", esc(SITE["name"])))
        title = meta.get("title", SITE["name"])
        write(path if path.endswith(".html") else path,
              layout(title=title, body=text, path=path if path != "/404.html" else "/",
                     description=meta.get("description"), body_class=meta.get("class", "")))


def build_feeds(posts, page_urls):
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{BASE}{p['url']}</link><guid>{BASE}{p['url']}</guid>"
        f"<pubDate>{dt.datetime.combine(p['date'], dt.time(8)).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
        f"<description>{esc(p['summary'])}</description></item>" for p in posts[:20])
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(SITE["name"])}</title>'
        f'<link>{BASE}/</link><description>{esc(SITE["description"])}</description><language>hu</language>{items}</channel></rss>',
        encoding="utf-8")
    urls = [(u, None) for u in page_urls] + [(p["url"], p["updated"] or p["date"]) for p in posts]
    sm = "".join(f"<url><loc>{BASE}{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>" for u, d in urls)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>',
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for d in ("assets", "images"):
        shutil.copytree(ROOT / d, OUT / d)
    for f in ("CNAME",):
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, OUT / f)
    (OUT / ".nojekyll").write_text("")
    posts = load_posts()
    for p in posts:
        build_post(p, posts)
    build_pages(posts)
    build_feeds(posts, ["/", "/cikkek/", "/kapcsolat/", "/adatvedelem/"])
    print(f"Kész: {len(posts)} cikk -> {OUT}")


if __name__ == "__main__":
    main()
