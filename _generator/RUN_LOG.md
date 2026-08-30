# Run log

Append-only. One entry per scheduled run (or per manual update), most
recent last. Used by future runs to avoid repeating topics and by the
site owner to audit what got published autonomously.

## 2026-08-30 — initial setup (manual, this session)

- Added SEO infrastructure: sitemap.xml, robots.txt, Open Graph +
  Twitter Card tags, JSON-LD (Person/ProfessionalService graph on
  every page, Article + BreadcrumbList on article pages).
- Generated branded cover images for the 5 launch articles plus
  generic site default covers.
- Moved the generator into `_generator/` inside the repo (portable
  paths) so scheduled runs can clone the repo and use it directly.
- 5 launch articles already published (unchanged, pre-dates this
  log): tracing-stolen-crypto-onchain, crypto-scam-red-flags,
  court-ready-blockchain-evidence, defi-fraud-attack-vectors,
  crypto-aml-compliance.
- Scheduled recurring research-and-publish task set up: Sun/Tue/Thu,
  minimum 3 new articles/news pieces per run, HE+EN, auto-pushed with
  standing pre-authorization (no per-run confirmation).

## 2026-08-30 — Google Search Console connected (manual, this session)

- Registered `https://dngchain.finance/` as a URL-prefix property in
  Google Search Console and verified ownership via the HTML-tag
  method: added `<meta name="google-site-verification" content="...">`
  to `page_shell()`'s `<head>` in `build.py` (site-wide, every page),
  rebuilt, and published. **Do not remove this meta tag** — removing
  it drops verification.
- Submitted `sitemap.xml` in Search Console (16 pages discovered,
  status: Success).
- Requested priority-crawl indexing for the Hebrew home page (`/`)
  and English home page (`/en/`) — both already showed "URL is on
  Google" / discovered via sitemap.
- This supports the site owner's goal of ranking first for "Dor Arad"
  (English) / "דור ארד" (Hebrew) — indexing and ranking take time on
  Google's side; this only completes the setup.
