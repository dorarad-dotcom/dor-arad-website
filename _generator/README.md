# Site generator — dngchain.finance (Dor Arad)

This folder is the static-site generator for the live site at
https://dngchain.finance, deployed via Netlify's GitHub auto-deploy
(push to `main` → Netlify rebuilds and publishes automatically, no
build command, publish directory = repo root).

Read this file fully before making any change. It exists so a fresh,
memory-less session (e.g. a scheduled automation run) can pick up the
system correctly.

## Layout

- `build.py` — the generator. Reads `content/*.txt`, renders every HTML
  page (Hebrew at the repo root, English under `/en/`), and writes
  `sitemap.xml` + `robots.txt`. Also owns all SEO output: title/meta
  tags, Open Graph + Twitter Card tags, and JSON-LD (Person +
  ProfessionalService entity graph on every page, Article +
  BreadcrumbList on article pages).
- `cover_gen.py` — generates unique, on-brand 1200x630 PNG cover/OG
  images (dark background, procedurally-seeded blockchain-network
  motif, title overlay) with no external API or network dependency.
  Uses DejaVu Sans (`/usr/share/fonts/truetype/dejavu/`), which
  correctly renders Hebrew via Pillow's `raqm` text layout — if a
  future environment lacks this font, install `fonts-dejavu-core`
  first (`apt-get install -y fonts-dejavu-core`) rather than
  substituting a font that hasn't been checked for Hebrew coverage.
- `generate_all_covers.py` — batch-runs `cover_gen.generate_cover()`
  for every article in `ARTICLES_META` plus the two generic
  `default-he.png` / `default-en.png` covers used by non-article pages.
- `content/article-N-<slug>.txt` — one file per article, both
  languages in one file, format below.
- `RUN_LOG.md` — append-only log of what each scheduled run did
  (or why it skipped). Check this before starting a new run so you
  don't repeat a topic or duplicate a slug.

## Content file format

```
===HE===
TITLE: <Hebrew title>
META: <Hebrew meta description, ~150-160 chars>
BODY:
<Hebrew body in the light markdown build.py understands:
## for H2 headings, - for bullet list items, **bold**, blank
line = paragraph break>

===EN===
TITLE: <English title>
META: <English meta description>
BODY:
<English body, same light-markdown rules>
```

Read 1-2 existing files in `content/` before writing new ones —
match their tone (professional, forensic, first-person-adjacent
authority, concrete and specific, no filler) and structure (a short
intro, several `##` sections, often a bulleted checklist, a closing
takeaway). `build.py`'s `read_time()` assumes 150 words/minute for
Hebrew and 200 words/minute for English — a genuine 5-minute read
needs roughly 750+ Hebrew words or 1000+ English words. Check word
count before finalizing; don't pad with filler to hit the number.

## Adding new articles (the recurring workflow)

1. Read `RUN_LOG.md` and the `ARTICLES_META` list in `build.py` to
   see what's already been published, so new pieces don't repeat a
   topic.
2. For each new article: pick a kebab-case English slug, write the
   `content/article-N-<slug>.txt` file (both languages, full
   parallel translations — not summaries of each other), and add an
   entry to `ARTICLES_META` in `build.py`:
   ```python
   {'slug': 'your-slug', 'file': 'article-N-your-slug.txt',
    'tag_he': 'תגית', 'tag_en': 'Tag', 'date': 'YYYY-MM-DD'},
   ```
   Reuse an existing tag pair where it fits (Investigations/חקירות,
   Guide/מדריך, Legal/משפטי, DeFi/DeFi, Compliance/ציות) or add a new
   one (e.g. News/חדשות) if none fit. Never edit or remove an
   existing entry or its content file.
3. From this folder: `python3 generate_all_covers.py` (regenerates
   covers for all articles — safe, deterministic, idempotent) then
   `python3 build.py` (regenerates every page, sitemap, robots.txt).
4. **Before committing**, grep the whole repo for the incorrect
   Hebrew spelling `דור ערד` (with an ע) — the correct spelling is
   always `דור ארד` (with an א). This has been emphasized as very
   important by the site owner. If it ever appears, fix it before
   publishing, no exceptions:
   `grep -rl "דור ערד" . --include="*.html" --include="*.py" --include="*.txt"`
   should return nothing.
5. Also sanity-check: every new slug has both a `/articles/<slug>.html`
   and `/en/articles/<slug>.html` file, both are non-empty, and the
   read-time estimate is genuinely ≥5 minutes.
6. Append a dated entry to `RUN_LOG.md` (titles, slugs, and a one-line
   note on sources/research angle).
7. **Publish via GitHub's web upload UI, driven by browser automation
   — NOT `git push`.** This cloud sandbox's git/GitHub network access
   is routed through an Anthropic security proxy that blocks
   authenticated git operations (push, or any token-based API call)
   to repos not pre-authorized for the session — confirmed by direct
   test, not a guess. A Personal Access Token does not get around
   this; don't waste a cycle trying `git push` again.

   What *does* work, confirmed by direct test: the
   `mcp__claude-in-chrome__file_upload` tool CAN upload files that
   live in this sandbox's own local filesystem (e.g. everything this
   generator just wrote under the repo clone) directly to GitHub's
   "Upload files" web page — no native OS file dialog, no user click
   required. That restriction (files must be "shared with the
   session") only blocks files from *other* sources (like the site
   owner's own computer via the device bridge); files this sandbox
   generated itself are fine.

   Procedure per batch of changed/new files destined for the same
   folder:
   1. `navigate` to `https://github.com/dorarad-dotcom/dor-arad-website/upload/main/<folder>`
      (use the repo root, `articles`, `en`, `en/articles`, or
      `assets/covers` as appropriate — GitHub creates the folder if
      it doesn't exist yet).
   2. `find` the file input near "choose your files" to get its
      `ref`, then call `file_upload` with `paths` set to the absolute
      local paths of every file going into that folder (multiple
      paths in one call is fine).
   3. Type a commit message into the "Commit changes" field and click
      "Commit changes".
   4. Repeat per folder (root files, `articles/`, `en/`, `en/articles/`,
      `assets/covers/`, and this `_generator/` folder + `content/`
      subfolder if `build.py`/content files changed).

   This requires the site owner's browser to be reachable and already
   logged into GitHub (via `mcp__claude-in-chrome__*`, which drives
   their real, already-authenticated Chrome session — not a fresh
   login). If the browser tools aren't reachable, or a GitHub page
   requires a login screen (session expired), STOP: do not attempt to
   fill in credentials. Instead, hold the finished content (it's
   already safely committed to this local clone) and send the site
   owner a message explaining the run produced content but couldn't
   publish because their browser wasn't reachable/logged in, and that
   it'll retry at the next scheduled run — or send them a zip via
   `SendUserFile` as a manual fallback.

   No confirmation is required before publishing once QA (constraint
   #4 below, plus the read-time and non-empty-file checks) passes —
   publishing has standing pre-authorization from the site owner (Dor
   Arad) for this recurring content workflow specifically. Netlify
   auto-deploys from GitHub within seconds of a successful commit; no
   further action needed after committing.

## Hard constraints (never violate)

- Hebrew name is always **דור ארד** (with א). Never **דור ערד** (עwith ).
- Never edit, shorten, retitle, or delete any existing article or
  page. Only add new ones.
- Never change `CONTACT` in `build.py` (domain, email, phone,
  WhatsApp label) or the page templates/CSS/JS unless the site owner
  explicitly asks for that in this exact conversation.
- Never fabricate statistics, quotes, or sources. If research for a
  cycle doesn't turn up enough genuinely new/consequential material
  for 3 full articles, fill remaining slots with solid, accurate
  evergreen guides/analysis on the specified subject areas — real
  and useful, not invented "news."
