# edzestevhitek.hu

Blog about gym and food misconceptions (in Hungarian). Static site: you write articles in Markdown, a GitHub Action turns them into pages and publishes them on GitHub Pages.

## Folders
| Path | What it is |
|---|---|
| `posts/` | Articles, one `.md` file each. **The file name is the URL**: `posts/otthoni-edzes-tevhitek.md` → `edzestevhitek.hu/cikkek/otthoni-edzes-tevhitek/` |
| `images/` | Pictures used by articles and pages |
| `pages/` | Home (`fooldal.html`), article list, contact, privacy/cookies, 404 |
| `assets/` | Design (CSS), script (menu, cookie banner, videos, contact form), self-hosted fonts |
| `site.json` | Site name, domain, Formspree ID, how many articles the home page shows |
| `build.py` | The generator. You don't need to touch it. |

## One-time setup
1. Upload everything to the `edzestevhitek` repo (keep `CNAME`).
2. **Settings → Pages → Build and deployment → Source: "GitHub Actions".** (This is different from Vízfigyelő, which used "Deploy from a branch".)
3. In the same Pages screen check that the custom domain is `edzestevhitek.hu`, and turn on "Enforce HTTPS" once it's offered.
4. DNS at your domain registrar, same as for vizesmagyarorszag.hu: four `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`, and a `CNAME` for `www` → `monikaa-hub-beep.github.io`.
5. Contact form: in Formspree create a new form for this site, and put its ID (the part after `/f/`) in `site.json` → `formspree_id`. You can also reuse the Vízfigyelő form ID: messages from this site arrive with the subject "edzestevhitek.hu – új üzenet". If you limited that form to certain domains, add `edzestevhitek.hu` there too.
6. Fill in the `[bracketed]` parts in `pages/adatvedelem.html` (your name, address, email, retention period), then delete the yellow "Tervezet" box at the top. Have it checked by a lawyer if you can.

Every push to `main` rebuilds the site in about a minute (Actions tab shows progress).

## Writing a new article
Create `posts/my-article-slug.md` (lowercase letters, digits, hyphens, no accents):

```markdown
---
title: "A szénhidrát este hízlal?"
date: 2026-12-05
summary: "One or two sentences. Shown on cards, in Google and when shared on Facebook."
cover: images/szenhidrat-borito.jpg
cover_alt: "Short description of the cover image"
tags: Táplálkozás, Fogyás
---

Intro paragraph...

## Subheading

Text with **bold**, *italic* and [a link](https://pubmed.ncbi.nlm.nih.gov/...).
```

- **Quotes:** put text values in "double quotes" (as above). A colon `:` inside unquoted text breaks the header.
- **Newest first:** the home page and the article list are sorted by `date`.
- **Scheduling:** a post with a future `date` stays hidden. The site rebuilds every morning, so it appears automatically on that day.
- **Draft:** add `draft: true` to the header, or start the file name with `_`.
- **Updated article:** add `updated: 2027-01-10`.

### Images
Put the file into `images/`, then on its own line:
```markdown
![What is in the picture (for screen readers and Google)](images/my-photo.jpg "Optional caption under the image")
```
Use JPG for photos and keep them under ~300 KB (resize to ~1600 px wide). Cover images look best in 16:9. Only use photos you took yourself or that have a licence allowing it (e.g. Unsplash, Pexels).

### YouTube videos
Paste the link **on its own line**, nothing else on that line:
```markdown
https://www.youtube.com/watch?v=XXXXXXXXXXX
```
`youtu.be/…` and `youtube.com/shorts/…` links work too. The video appears as a player box. For privacy, nothing loads from YouTube until the visitor presses play (or allowed "Külső média" in the cookie settings).

### Myth / fact boxes
```markdown
> **Tévhit:** The claim people believe.

> **Valóság:** What the research says.

> **Megjegyzés:** Neutral note box.
```

## Preview on your computer (optional)
```
pip install markdown
python build.py
python -m http.server -d _site
```
Then open http://localhost:8000

## Cookies
The site sets no tracking cookies. `assets/site.js` shows the banner and stores the choice in the browser (`et_consent`). If you add analytics later, load it inside `ET.onConsent(c => { if (c.analytics) { ... } })` and update the privacy page first.

## Fonts and illustrations
Archivo and Literata are served from `assets/fonts` (SIL Open Font License, see the `OFL-*.txt` files), so no request goes to Google Fonts. The illustrations in `images/` were made for this site; replace them with your own photos any time (keep the same file names, or update the paths in `pages/fooldal.html` and the article header).
