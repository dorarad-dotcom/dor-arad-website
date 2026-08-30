#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site generator for dngchain.finance / Dor Arad (HE default + /en)."""
import re, os, json, html as htmlmod

# Portable paths: this file lives at <repo_root>/_generator/build.py, so the
# site root is one directory up, and content sources sit alongside this file.
# This makes the generator work identically in dev and after a fresh
# `git clone` of the repo (e.g. from a scheduled automation run).
_GEN_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_GEN_DIR)
CONTENT = os.path.join(_GEN_DIR, 'content')
ALL_PAGES = []  # (he_path, en_path) pairs collected as pages are written, for sitemap.xml

# ---------------------------------------------------------------- helpers --
def esc(s):
    return htmlmod.escape(s, quote=False)

def inline(text):
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text

def md_to_html(md):
    lines = md.strip('\n').split('\n')
    out = []
    para = []
    items = []
    def flush_para():
        if para:
            t = ' '.join(x.strip() for x in para).strip()
            if t:
                out.append('<p>' + inline(t) + '</p>')
            para.clear()
    def flush_list():
        if items:
            out.append('<ul>' + ''.join('<li>' + inline(i) + '</li>' for i in items) + '</ul>')
            items.clear()
    for raw in lines:
        line = raw.rstrip()
        if line.startswith('## '):
            flush_para(); flush_list()
            out.append('<h2>' + inline(line[3:].strip()) + '</h2>')
        elif line.strip().startswith('- '):
            flush_para()
            items.append(line.strip()[2:])
        elif line.strip() == '':
            flush_para(); flush_list()
        else:
            flush_list()
            para.append(line)
    flush_para(); flush_list()
    return '\n'.join(out)

def word_count(md):
    return len(re.findall(r'\S+', re.sub(r'^##.*$', '', md, flags=re.M)))

def read_time(md, lang):
    wpm = 150 if lang == 'he' else 200
    n = max(1, round(word_count(md) / wpm))
    return n

def parse_article(path):
    text = open(path, encoding='utf-8').read()
    he_raw = text.split('===EN===')[0].split('===HE===')[1]
    en_raw = text.split('===EN===')[1]
    def parse_lang(part):
        lines = part.strip('\n').split('\n')
        title, meta, body = '', '', []
        mode = None
        for line in lines:
            if line.startswith('TITLE:'):
                title = line[len('TITLE:'):].strip()
            elif line.startswith('META:'):
                meta = line[len('META:'):].strip()
            elif line.startswith('BODY:'):
                mode = 'body'
            elif mode == 'body':
                body.append(line)
        return {'title': title, 'meta': meta, 'body_md': '\n'.join(body).strip('\n')}
    return parse_lang(he_raw), parse_lang(en_raw)

# ------------------------------------------------------------- site data --
CONTACT = {
    'website_display': 'dngchain.finance',
    'website_href': 'https://dngchain.finance',
    'email': 'contact@dngchain.finance',
    'phone_display': '+972 50-775-5020',
    'phone_href': 'tel:+972507755020',
    'whatsapp_href': 'https://wa.me/972507755020',
    'whatsapp_label_he': 'וואטסאפ עסקי — Dor Arad',
    'whatsapp_label_en': 'WhatsApp Business — Dor Arad',
}

SITE_NAME_HE = "דור ארד — חקירות בלוקצ'יין ומודיעין דיגיטלי"
SITE_NAME_EN = "Dor Arad — Blockchain Investigation & Digital Intelligence"

# ---------------------------------------------------------------- SEO/JSON-LD --
def jsonld_script(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'

def person_org_graph(lang):
    """Site-wide Person + ProfessionalService entity graph, embedded on every
    page so search engines consistently associate 'Dor Arad' / 'דור ארד' with
    this one entity regardless of which page they crawl first."""
    person = {
        "@type": "Person",
        "@id": CONTACT['website_href'] + "/#person",
        "name": "Dor Arad",
        "alternateName": "דור ארד",
        "url": CONTACT['website_href'] + ('/about.html' if lang == 'he' else '/en/about.html'),
        "jobTitle": "Blockchain Investigator" if lang == 'en' else "חוקר בלוקצ'יין",
        "email": "mailto:" + CONTACT['email'],
        "telephone": CONTACT['phone_href'].replace('tel:', ''),
        "worksFor": {"@id": CONTACT['website_href'] + "/#org"},
        "knowsAbout": ["Blockchain Forensics", "Cryptocurrency Investigation", "Digital Asset Tracing",
                        "AML Compliance", "DeFi Fraud"],
    }
    org = {
        "@type": "ProfessionalService",
        "@id": CONTACT['website_href'] + "/#org",
        "name": SITE_NAME_HE if lang == 'he' else SITE_NAME_EN,
        "url": CONTACT['website_href'] + ('/' if lang == 'he' else '/en/'),
        "image": CONTACT['website_href'] + f"/assets/covers/default-{lang}.png",
        "telephone": CONTACT['phone_href'].replace('tel:', ''),
        "email": CONTACT['email'],
        "founder": {"@id": CONTACT['website_href'] + "/#person"},
        "address": {"@type": "PostalAddress", "addressLocality": "Tel Aviv", "addressCountry": "IL"},
        "areaServed": "Worldwide",
    }
    return {"@context": "https://schema.org", "@graph": [person, org]}

def breadcrumb_jsonld(lang, items):
    """items: list of (name, url_path) tuples, url_path relative (e.g. '/articles.html')."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name,
             "item": CONTACT['website_href'] + path}
            for i, (name, path) in enumerate(items)
        ],
    }

def article_jsonld(lang, a, canonical_path, image_path):
    lg = a['he'] if lang == 'he' else a['en']
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": lg['title'],
        "description": lg['meta'],
        "image": [CONTACT['website_href'] + image_path],
        "author": {"@id": CONTACT['website_href'] + "/#person"},
        "publisher": {"@id": CONTACT['website_href'] + "/#org"},
        "datePublished": a['date'] + "T08:00:00+03:00",
        "dateModified": a.get('date_modified', a['date']) + "T08:00:00+03:00",
        "mainEntityOfPage": {"@type": "WebPage", "@id": CONTACT['website_href'] + canonical_path},
        "inLanguage": lang,
        "url": CONTACT['website_href'] + canonical_path,
    }

ARTICLES_META = [
    {'slug': 'tracing-stolen-crypto-onchain', 'file': 'article-1-tracing-stolen-crypto-onchain.txt',
     'tag_he': 'חקירות', 'tag_en': 'Investigations', 'date': '2026-08-03'},
    {'slug': 'crypto-scam-red-flags', 'file': 'article-2-crypto-scam-red-flags.txt',
     'tag_he': 'מדריך', 'tag_en': 'Guide', 'date': '2026-08-07'},
    {'slug': 'court-ready-blockchain-evidence', 'file': 'article-3-court-ready-blockchain-evidence.txt',
     'tag_he': 'משפטי', 'tag_en': 'Legal', 'date': '2026-08-11'},
    {'slug': 'defi-fraud-attack-vectors', 'file': 'article-4-defi-fraud-attack-vectors.txt',
     'tag_he': 'DeFi', 'tag_en': 'DeFi', 'date': '2026-08-14'},
    {'slug': 'crypto-aml-compliance', 'file': 'article-5-crypto-aml-compliance.txt',
     'tag_he': 'ציות', 'tag_en': 'Compliance', 'date': '2026-08-18'},
]

MONTHS_HE = ['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר']
MONTHS_EN = ['January','February','March','April','May','June','July','August','September','October','November','December']

def fmt_date(iso, lang):
    y, m, d = iso.split('-')
    mi = int(m) - 1
    if lang == 'he':
        return f"{int(d)} ב{MONTHS_HE[mi]} {y}"
    return f"{MONTHS_EN[mi]} {int(d)}, {y}"

for a in ARTICLES_META:
    he, en = parse_article(os.path.join(CONTENT, a['file']))
    a['he'] = he
    a['en'] = en
    a['he']['body_html'] = md_to_html(he['body_md'])
    a['en']['body_html'] = md_to_html(en['body_md'])
    a['he']['read_min'] = read_time(he['body_md'], 'he')
    a['en']['read_min'] = read_time(en['body_md'], 'en')

NAV_HE = [('בית', '/'), ('אודות', '/about.html'), ('מאמרים', '/articles.html')]
NAV_EN = [('Home', '/en/'), ('About', '/en/about.html'), ('Articles', '/en/articles.html')]

def counterpart(path_he=None, path_en=None):
    return path_he, path_en

# ------------------------------------------------------------- page shell --
def page_shell(lang, title, description, active, body_html, he_path, en_path,
                og_image=None, extra_jsonld=None, page_type='website'):
    ALL_PAGES.append((he_path, en_path))
    dir_attr = 'rtl' if lang == 'he' else 'ltr'
    nav = NAV_HE if lang == 'he' else NAV_EN
    contact_href = '/#contact' if lang == 'he' else '/en/#contact'
    logo_sub = "/ חקירות בלוקצ'יין" if lang == 'he' else '/ Blockchain Investigations'
    logo_home = '/' if lang == 'he' else '/en/'
    cta_label = 'לפנייה ראשונית' if lang == 'he' else 'Start an Inquiry'
    lang_switch_label = 'EN' if lang == 'he' else 'עברית'
    lang_switch_href = en_path if lang == 'he' else he_path
    nav_html = []
    for label, href in nav:
        cls = ' class="active"' if href == active else ''
        nav_html.append(f'<a href="{href}"{cls}>{label}</a>')
    nav_html.append(f'<a href="{contact_href}">{"צור קשר" if lang=="he" else "Contact"}</a>')
    nav_html = ''.join(nav_html)

    mobile_nav_html = []
    for label, href in nav:
        mobile_nav_html.append(f'<a href="{href}">{label}</a>')
    mobile_nav_html.append(f'<a href="{contact_href}">{"צור קשר" if lang=="he" else "Contact"}</a>')
    mobile_nav_html.append(f'<a href="{lang_switch_href}">{lang_switch_label}</a>')
    mobile_nav_html = ''.join(mobile_nav_html)

    footer_line1 = (
        f"© <span class=\"js-year\"></span> דור ארד — חקירות בלוקצ'יין. כל הפניות חסויות."
        if lang == 'he' else
        f"© <span class=\"js-year\"></span> Dor Arad — Blockchain Investigations. All inquiries confidential."
    )
    footer_loc = 'תל אביב, ישראל' if lang == 'he' else 'Tel Aviv, Israel'

    canonical_path = he_path if lang == 'he' else en_path
    canonical_url = CONTACT['website_href'] + canonical_path
    og_image_path = og_image or f"/assets/covers/default-{lang}.png"
    og_image_url = CONTACT['website_href'] + og_image_path
    og_locale = 'he_IL' if lang == 'he' else 'en_US'
    og_locale_alt = 'en_US' if lang == 'he' else 'he_IL'
    site_name = SITE_NAME_HE if lang == 'he' else SITE_NAME_EN

    jsonld_blocks = [jsonld_script(person_org_graph(lang))]
    if extra_jsonld:
        for block in extra_jsonld:
            jsonld_blocks.append(jsonld_script(block))
    jsonld_html = '\n'.join(jsonld_blocks)

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{dir_attr}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="canonical" href="{canonical_url}" />
<link rel="alternate" hreflang="he" href="{CONTACT['website_href']}{he_path}" />
<link rel="alternate" hreflang="en" href="{CONTACT['website_href']}{en_path}" />
<link rel="alternate" hreflang="x-default" href="{CONTACT['website_href']}{he_path}" />
<meta name="author" content="Dor Arad" />
<meta name="robots" content="index, follow" />
<meta name="google-site-verification" content="W56qTSOBcC-iWpSfH_w7RyGFwVgAuu3zhHUlNZvI8qY" />
<meta property="og:site_name" content="{site_name}" />
<meta property="og:type" content="{page_type}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{description}" />
<meta property="og:url" content="{canonical_url}" />
<meta property="og:image" content="{og_image_url}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="{og_locale}" />
<meta property="og:locale:alternate" content="{og_locale_alt}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{description}" />
<meta name="twitter:image" content="{og_image_url}" />
{jsonld_html}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230a0e14'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%2335e0a1'/%3E%3C/svg%3E" />
<link rel="stylesheet" href="/assets/style.css" />
</head>
<body>

<canvas id="netCanvas"></canvas>
<div class="grid-overlay"></div>

<header>
  <div class="wrap">
    <a class="logo" href="{logo_home}"><span class="logo-dot"></span>DOR ARAD <span class="logo-sub">{logo_sub}</span></a>
    <nav class="main-nav">{nav_html}</nav>
    <div class="header-actions">
      <a href="{lang_switch_href}" class="lang-switch">{lang_switch_label}</a>
      <a href="{contact_href}" class="btn btn-solid">{cta_label}</a>
      <button class="mobile-nav-toggle" aria-label="menu">&#9776;</button>
    </div>
  </div>
</header>
<div class="mobile-nav">{mobile_nav_html}</div>

<main>
{body_html}
</main>

<footer>
  <div class="wrap">
    <p>{footer_line1}</p>
    <p>{footer_loc}</p>
  </div>
</footer>

<script src="/assets/main.js"></script>
</body>
</html>
"""

def write_page(rel_path, html_content):
    full = os.path.join(ROOT, rel_path.lstrip('/'))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print('wrote', rel_path)

# ================================================================ HOME =====
def home_body(lang):
    he = lang == 'he'
    services = [
        ('01', 'מעקב אחר עסקאות קריפטו' if he else 'Crypto Transaction Tracking',
         'מעקב מקצה לקצה אחר תנועת מטבעות קריפטוגרפיים בין ארנקים, בורסות ושירותי ערבוב, על פני רשתות הבלוקצ\'יין המרכזיות. כל שלב בתנועה מתועד ומבוסס בעובדות.' if he else
         'End-to-end tracing of cryptocurrency movement across wallets, exchanges, and mixers on major blockchain networks. Every hop in the trail is documented and fact-based.'),
        ('02', 'איתור נכסים וכספים' if he else 'Asset & Fund Tracing',
         'זיהוי ומיפוי של כספים גנובים, מולבנים או מוסתרים, וההגעה לנקודות שבהן ניתן לפעול להשבתם. מתאים גם למקרי הונאה עסקית ומחלוקות אזרחיות.' if he else
         'Identifying and mapping stolen, laundered, or hidden digital assets to the points where recovery action becomes possible — including business fraud and civil disputes.'),
        ('03', 'חקירת הונאות וגניבה' if he else 'Fraud & Theft Investigations',
         'חקירת הונאות השקעה, פריצות לבורסות, rug pulls וגניבה פנימית, עם בניית שרשרת ראייתית ברורה על השרשרת ומחוצה לה.' if he else
         'Investigating investment scams, exchange hacks, rug pulls, and insider theft, building a clear evidentiary chain both on-chain and off.'),
        ('04', 'ניתוח ארנקים פורנזי' if he else 'Forensic Wallet Analysis',
         'ניתוח מעמיק של פעילות ארנק, קלאסטרינג של כתובות וניתוח חשיפת צד-נגדי, לצורך בדיקת נאותות או הליך משפטי.' if he else
         'Deep-dive analysis of wallet activity, address clustering, and counterparty exposure — for due diligence or litigation support.'),
        ('05', 'תמיכה בציות ורגולציה' if he else 'Compliance Support',
         'הערכת סיכון און-צ\'יין ודירוג ארנקים לתמיכה בחובות AML/KYC ובדיווח רגולטורי, עבור עסקים שנוגעים בנכסים דיגיטליים.' if he else
         'On-chain risk assessment and wallet risk scoring to support AML/KYC obligations and regulatory reporting for crypto-touching businesses.'),
        ('06', 'דוחות כשירים לבית משפט' if he else 'Court-Ready Reporting',
         'תרגום ממצאים גולמיים לדוח מובנה, שקוף מבחינה מתודולוגית, המתאים לשימוש משפטי ולחקירה נגדית.' if he else
         'Translating raw findings into a structured, methodologically transparent report suitable for legal use and cross-examination.'),
    ]
    services_html = ''.join(
        f'<div class="card"><div class="num">{n}</div><h3>{t}</h3><p>{d}</p></div>' for n, t, d in services
    )

    articles_preview = ARTICLES_META[:3]
    articles_html = ''
    for a in articles_preview:
        lg = a['he'] if he else a['en']
        href = f"/articles/{a['slug']}.html" if he else f"/en/articles/{a['slug']}.html"
        tag = a['tag_he'] if he else a['tag_en']
        read_lbl = f"{lg['read_min']} דק' קריאה" if he else f"{lg['read_min']} min read"
        articles_html += f"""<a class="article-card" href="{href}">
          <div class="tag">{tag}</div>
          <h3>{esc(lg['title'])}</h3>
          <p>{esc(lg['meta'])}</p>
          <div class="meta"><span>{fmt_date(a['date'], lang)}</span><span>{read_lbl}</span></div>
        </a>"""

    if he:
        return f"""
  <section class="hero wrap">
    <div>
      <div class="eyebrow">חקירות בלוקצ'יין ומודיעין דיגיטלי</div>
      <h1>הופכים נתוני בלוקצ'יין ל<span class="accent">ראיות קבילות בבית משפט.</span></h1>
      <p class="lead">
        דור ארד מספק שירותי חקירת בלוקצ'יין ומודיעין דיגיטלי עצמאיים - מעקב אחר תנועת קריפטו, איתור נכסים גנובים,
        חקירת הונאות ותמיכה בציות רגולטורי - עבור רשויות אכיפת חוק, עורכי דין, רואי חשבון, עסקים ולקוחות פרטיים
        ברחבי העולם. כל תיק מלווה במתודולוגיה שקופה, תיעוד קפדני ודיסקרטיות מלאה, מרגע הפנייה הראשונה ועד לדוח הסופי.
      </p>
      <div class="hero-actions">
        <a href="#contact" class="btn btn-solid">לפנייה ראשונית</a>
        <a href="#services" class="btn">השירותים שלנו</a>
      </div>
      <div class="hero-meta">
        <div><strong>8+ שנים</strong>ניסיון יזמי בפינטק ובקריפטו</div>
        <div><strong>24/7</strong>זמינות למקרים דחופים</div>
        <div><strong>100%</strong>דיסקרטיות מלאה בכל תיק</div>
      </div>
    </div>
  </section>

  <section id="services">
    <div class="wrap">
      <div class="eyebrow">שירותים</div>
      <h2>ניתוח בלוקצ'יין ברמה פורנזית, בנוי לתוצאות אמיתיות.</h2>
      <p class="section-sub">כל תיק מותאם אישית - ממעקב אחר ארנק בודד ועד לחקירת השבת נכסים רב-שרשרתית מלאה.</p>
      <div class="grid-3">{services_html}</div>
    </div>
  </section>

  <section id="who-we-serve">
    <div class="wrap">
      <div class="eyebrow">מי אנחנו משרתים</div>
      <h2>גורמים שצריכים בהירות - לא רק נתונים.</h2>
      <div class="clients-row">
        <div class="pill">רשויות אכיפת חוק</div>
        <div class="pill">עורכי דין וליטיגטורים</div>
        <div class="pill">רואי חשבון ומבקרים</div>
        <div class="pill">עסקים ומוסדות</div>
        <div class="pill">לקוחות פרטיים</div>
      </div>
      <div class="discretion">
        <strong>&gt; discretion.status</strong> — כל תיק מטופל בסודיות מוחלטת. הממצאים משותפים אך ורק עם הגורם הפונה,
        והדיווח בנוי כך שיעמוד בביקורת בהקשר משפטי, רגולטורי או של אכיפת חוק.
      </div>
    </div>
  </section>

  <section id="process">
    <div class="wrap">
      <div class="eyebrow">תהליך העבודה</div>
      <h2>מסלול מובנה מהפנייה הראשונה ועד לדוח הסופי.</h2>
      <div class="process-list">
        <div class="process-item"><div class="step">01</div><div><h3>קליטה חסויה</h3><p>אתם משתפים את רקע התיק, כתובות ארנק, מספרי עסקה או כל הקשר רלוונטי, בכפוף להסכם סודיות במידת הצורך.</p></div></div>
        <div class="process-item"><div class="step">02</div><div><h3>היקף והתקשרות</h3><p>מגדירים יחד את היקף החקירה, לוח הזמנים והיעדים, לפני תחילת העבודה בפועל.</p></div></div>
        <div class="process-item"><div class="step">03</div><div><h3>חקירה על השרשרת</h3><p>מעקב עסקאות, קלאסטרינג וניתוח חוצה-רשתות, באמצעות נתוני בלוקצ'יין וכלי חקירה מקצועיים.</p></div></div>
        <div class="process-item"><div class="step">04</div><div><h3>דיווח ומסירה</h3><p>הממצאים מרוכזים לדוח ברור, מובנה וכשיר לבית משפט, עם תיעוד תומך מלא.</p></div></div>
      </div>
    </div>
  </section>

  <section id="about-teaser">
    <div class="wrap">
      <div class="eyebrow">מי אני</div>
      <h2>יזם פינטק שהפך לחוקר בלוקצ'יין.</h2>
      <p class="section-sub">
        מעל שמונה שנים בעולמות הפינטק, הקריפטו וה-DeFi - כמייסד קרן גידור קריפטו, חברת ייעוץ פיננסי וחברת SaaS - נותנים לי זווית ראייה נדירה על איך כסף דיגיטלי אמור לזוז, ולכן גם על איך לזהות מתי הוא לא.
      </p>
      <div class="hero-actions" style="margin-top:32px;"><a href="/about.html" class="btn">קראו את הסיפור המלא</a></div>
    </div>
  </section>

  <section id="articles-teaser">
    <div class="wrap">
      <div class="eyebrow">תובנות ומאמרים</div>
      <h2>כתבות מקצועיות מהשטח.</h2>
      <p class="section-sub">מדריכים וניתוחים בנושאי חקירת בלוקצ'יין, הונאות קריפטו וציות רגולטורי - מאת דור ארד.</p>
      <div class="article-grid">{articles_html}</div>
      <div class="hero-actions" style="margin-top:32px;"><a href="/articles.html" class="btn">לכל המאמרים</a></div>
    </div>
  </section>

  <section id="contact">
    <div class="wrap">
      <div class="eyebrow">צור קשר</div>
      <h2>התחילו פנייה חסויה.</h2>
      <p class="section-sub">אפשר לפנות ישירות, או לשלוח את פרטי התיק בטופס למטה. כל פנייה מטופלת בסודיות מלאה.</p>
      <div class="contact-grid">
        <div class="contact-list">
          <a href="{CONTACT['phone_href']}"><span class="ico">&#9742;</span> {CONTACT['phone_display']}</a>
          <a href="mailto:{CONTACT['email']}"><span class="ico">&#9993;</span> {CONTACT['email']}</a>
          <a href="{CONTACT['whatsapp_href']}" target="_blank" rel="noopener"><span class="ico">&#9737;</span> {CONTACT['whatsapp_label_he']}</a>
          <a href="{CONTACT['website_href']}"><span class="ico">&#9673;</span> {CONTACT['website_display']}</a>
          <div><span class="ico">&#9670;</span> תל אביב, ישראל — זמין ברחבי העולם</div>
        </div>
        <form name="inquiry-he" method="POST" data-netlify="true" netlify-honeypot="bot-field">
          <input type="hidden" name="form-name" value="inquiry-he" />
          <p style="display:none"><label>Don't fill this out: <input name="bot-field" /></label></p>
          <div class="field"><label for="name-he">שם</label><input id="name-he" name="name" type="text" required /></div>
          <div class="field"><label for="email-he">אימייל</label><input id="email-he" name="email" type="email" required /></div>
          <div class="field"><label for="message-he">פרטי הפנייה</label><textarea id="message-he" name="message" required></textarea></div>
          <button type="submit" class="btn btn-solid" style="align-self:flex-start; cursor:pointer;">שליחה</button>
        </form>
      </div>
    </div>
  </section>
"""
    else:
        return f"""
  <section class="hero wrap">
    <div>
      <div class="eyebrow">Blockchain Investigation &amp; Digital Intelligence</div>
      <h1>Turning blockchain data into <span class="accent">court-ready evidence.</span></h1>
      <p class="lead">
        Dor Arad provides independent blockchain investigation and digital intelligence services — crypto
        transaction tracking, stolen asset tracing, fraud investigations, and regulatory compliance support —
        for law enforcement, legal teams, accountants, businesses, and private clients worldwide. Every engagement
        is built on transparent methodology, rigorous documentation, and complete discretion, from first contact
        through to the final report.
      </p>
      <div class="hero-actions">
        <a href="#contact" class="btn btn-solid">Start an Inquiry</a>
        <a href="#services" class="btn">View Services</a>
      </div>
      <div class="hero-meta">
        <div><strong>8+ yrs</strong>fintech &amp; blockchain venture experience</div>
        <div><strong>24/7</strong>available for urgent engagements</div>
        <div><strong>100%</strong>confidential, discretion-first process</div>
      </div>
    </div>
  </section>

  <section id="services">
    <div class="wrap">
      <div class="eyebrow">Services</div>
      <h2>Forensic-grade blockchain analysis, built for real-world outcomes.</h2>
      <p class="section-sub">Every engagement is tailored to the case — from a single wallet trace to a full multi-chain fund recovery investigation.</p>
      <div class="grid-3">{services_html}</div>
    </div>
  </section>

  <section id="who-we-serve">
    <div class="wrap">
      <div class="eyebrow">Who We Serve</div>
      <h2>Trusted by parties who need clarity, not just data.</h2>
      <div class="clients-row">
        <div class="pill">Law Enforcement</div>
        <div class="pill">Legal Teams &amp; Litigators</div>
        <div class="pill">Accountants &amp; Auditors</div>
        <div class="pill">Businesses &amp; Institutions</div>
        <div class="pill">Private Clients</div>
      </div>
      <div class="discretion">
        <strong>&gt; discretion.status</strong> — every engagement is handled under strict confidentiality.
        Findings are shared only with the engaging party, and reporting is structured to withstand
        scrutiny in legal, regulatory, or law-enforcement contexts.
      </div>
    </div>
  </section>

  <section id="process">
    <div class="wrap">
      <div class="eyebrow">Process</div>
      <h2>A structured path from first contact to final report.</h2>
      <div class="process-list">
        <div class="process-item"><div class="step">01</div><div><h3>Confidential Intake</h3><p>You share the case background, wallet addresses, transaction hashes, or relevant context under NDA if required.</p></div></div>
        <div class="process-item"><div class="step">02</div><div><h3>Scoping &amp; Engagement</h3><p>Investigation scope, timeline, and objectives are defined and agreed before work begins.</p></div></div>
        <div class="process-item"><div class="step">03</div><div><h3>On-Chain Investigation</h3><p>Transaction tracing, clustering, and cross-chain analysis using on-chain data and investigative tooling.</p></div></div>
        <div class="process-item"><div class="step">04</div><div><h3>Reporting &amp; Delivery</h3><p>Findings are compiled into a clear, structured, court-ready report with supporting evidence.</p></div></div>
      </div>
    </div>
  </section>

  <section id="about-teaser">
    <div class="wrap">
      <div class="eyebrow">Who I Am</div>
      <h2>A fintech entrepreneur turned blockchain investigator.</h2>
      <p class="section-sub">
        Eight-plus years across fintech, crypto, and DeFi — as founder of a crypto hedge fund, a financial
        consulting practice, and a SaaS company — give me a rare vantage point on how digital money is supposed
        to move, and exactly how to spot it when it doesn't.
      </p>
      <div class="hero-actions" style="margin-top:32px;"><a href="/en/about.html" class="btn">Read the Full Story</a></div>
    </div>
  </section>

  <section id="articles-teaser">
    <div class="wrap">
      <div class="eyebrow">Insights &amp; Articles</div>
      <h2>Field notes from the frontline.</h2>
      <p class="section-sub">Guides and analysis on blockchain investigation, crypto fraud, and regulatory compliance — written by Dor Arad.</p>
      <div class="article-grid">{articles_html}</div>
      <div class="hero-actions" style="margin-top:32px;"><a href="/en/articles.html" class="btn">View All Articles</a></div>
    </div>
  </section>

  <section id="contact">
    <div class="wrap">
      <div class="eyebrow">Contact</div>
      <h2>Start a confidential inquiry.</h2>
      <p class="section-sub">Reach out directly, or send the details of your case below. All inquiries are treated as confidential.</p>
      <div class="contact-grid">
        <div class="contact-list">
          <a href="{CONTACT['phone_href']}"><span class="ico">&#9742;</span> {CONTACT['phone_display']}</a>
          <a href="mailto:{CONTACT['email']}"><span class="ico">&#9993;</span> {CONTACT['email']}</a>
          <a href="{CONTACT['whatsapp_href']}" target="_blank" rel="noopener"><span class="ico">&#9737;</span> {CONTACT['whatsapp_label_en']}</a>
          <a href="{CONTACT['website_href']}"><span class="ico">&#9673;</span> {CONTACT['website_display']}</a>
          <div><span class="ico">&#9670;</span> Tel Aviv, Israel — available worldwide</div>
        </div>
        <form name="inquiry-en" method="POST" data-netlify="true" netlify-honeypot="bot-field">
          <input type="hidden" name="form-name" value="inquiry-en" />
          <p style="display:none"><label>Don't fill this out: <input name="bot-field" /></label></p>
          <div class="field"><label for="name-en">Name</label><input id="name-en" name="name" type="text" required /></div>
          <div class="field"><label for="email-en">Email</label><input id="email-en" name="email" type="email" required /></div>
          <div class="field"><label for="message-en">Case details</label><textarea id="message-en" name="message" required></textarea></div>
          <button type="submit" class="btn btn-solid" style="align-self:flex-start; cursor:pointer;">Send Inquiry</button>
        </form>
      </div>
    </div>
  </section>
"""

write_page('/index.html', page_shell('he',
    "דור ארד — חקירות בלוקצ'יין ומודיעין דיגיטלי",
    "שירותי חקירת בלוקצ'יין ומודיעין דיגיטלי - מעקב אחר קריפטו גנוב, חקירת הונאות, ניתוח ארנקים פורנזי ותמיכה בציות. עבור רשויות אכיפת חוק, עורכי דין ולקוחות פרטיים.",
    '/', home_body('he'), '/', '/en/'))

write_page('/en/index.html', page_shell('en',
    "Dor Arad — Blockchain Investigation & Digital Intelligence",
    "Independent blockchain investigation and digital intelligence services - crypto transaction tracking, fraud investigations, forensic wallet analysis, and compliance support for law enforcement, legal teams, and private clients.",
    '/en/', home_body('en'), '/', '/en/'))

# =============================================================== ABOUT =====
TIMELINE = [
    ('2007–2012', 'שירות צבאי — סיירת דובדבן', 'לוחם ומפקד; שיתוף פעולה עם יחידת 8200 על פיתוח מודיעיני של ציוד טכני.',
                   'Military Service — Duvdevan Special Forces', 'Combat soldier and commander; collaborated with Unit 8200 on intelligence development of tactical equipment.'),
    ('2013–2017', 'תואר בהנדסת חשמל, שנקר', 'שליש עליון של המחזור; התמחות במערכות תקשורת מתקדמות.',
                   'B.Sc. Electrical Engineering, Shenkar', 'Top 3% of class; specialization in advanced communication systems.'),
    ('2015–2019', 'מייסד-שותף, DNG Technologies', 'חברת IoT; שני סבבי גיוס הון ופטנט בינלאומי לחדשנות IoT.',
                   'Co-Founder, DNG Technologies', 'IoT company; secured two funding rounds and a worldwide IoT patent.'),
    ('2019–היום', 'מייסד ומנכ"ל, Venture Chic', 'קרן גידור קריפטו וייעוץ פיננסי; DeFi, מוצרי EMI ובנקאות חלופית.',
                   'Founder & CEO, Venture Chic', 'Crypto hedge fund and financial consulting; DeFi, EMI products, and alternative banking.'),
    ('2019–היום', 'מייסד, Everest Smart Living', 'ייעוץ לפיתוח SaaS ומערכות CRM מותאמות אישית.',
                   'Founder, Everest Smart Living', 'Consulting for SaaS development and custom CRM systems.'),
    ('היום', 'חקירות בלוקצ\'יין ומודיעין דיגיטלי', 'עבודה עצמאית עם רשויות אכיפת חוק, עורכי דין ולקוחות פרטיים.',
             'Blockchain Investigations & Digital Intelligence', 'Independent practice serving law enforcement, legal teams, and private clients.'),
]

def about_body(lang):
    he = lang == 'he'
    timeline_html = ''
    for yr, t_he, d_he, t_en, d_en in TIMELINE:
        t, d = (t_he, d_he) if he else (t_en, d_en)
        timeline_html += f'<div class="timeline-item"><div class="yr">{yr}</div><div class="desc"><h4>{t}</h4><p>{d}</p></div></div>'

    if he:
        prose = """
<div class="prose">
<p>דור ארד הוא חוקר בלוקצ'יין עצמאי ויזם טכנולוגיה עם מעל שמונה שנות ניסיון בעולמות הפינטק, הקריפטו וה-DeFi. הדרך שלו לחקירות בלוקצ'יין לא התחילה במשטרה או בחברת סייבר - היא התחילה מהצד השני של השולחן: כמייסד וכמנכ"ל של קרן גידור קריפטו וחברת ייעוץ פיננסי (Venture Chic), שם עבד שנים עם מוצרי EMI, פתרונות בנקאות חלופית, DeFi וחוזים חכמים מותאמים אישית. הבנה מעמיקה כזו של איך כסף דיגיטלי אמור לזוז היא בדיוק מה שמאפשר לזהות במהירות מתי הוא זז בצורה שלא אמורה.</p>
<p>לצד קרן הגידור, דור ייסד גם את Everest Smart Living, חברת ייעוץ לפיתוח תוכנות SaaS ומערכות CRM מותאמות אישית, וקודם לכן היה שותף-מייסד ב-DNG Technologies, חברת IoT שגייסה שני סבבי מימון וזכתה בפטנט בינלאומי. כל אחד מהמיזמים האלה חידד יכולת שונה - ניהול מוצר, בנייה טכנית וניהול סיכונים פיננסיים - שכולן משמשות אותו כיום בעבודת החקירה.</p>
<p>לפני העולם העסקי, דור שירת בצה"ל כלוחם ומפקד בסיירת דובדבן, ועבד גם עם יחידת 8200 על פיתוח מודיעיני של ציוד טכני. השירות הזה השריש בו גישה שיטתית לעבודה תחת לחץ ותשומת לב לפרטים - תכונות שמתורגמות ישירות לעבודת חקירה שבה טעות קטנה יכולה לשנות את כל התיק.</p>
<p>היום דור מתמקד באופן מלא בחקירות בלוקצ'יין ומודיעין דיגיטלי: איתור כספים גנובים, חקירת הונאות קריפטו, ניתוח ארנקים פורנזי, ותמיכה בציות עבור עסקים שנוגעים בנכסים דיגיטליים. הוא עובד עם רשויות אכיפת חוק, משרדי עורכי דין, רואי חשבון, עסקים ולקוחות פרטיים - תמיד באותה גישה: מתודולוגיה שקופה, תיעוד קפדני ודיסקרטיות מוחלטת.</p>
<p>אם אתם מתמודדים עם מקרה שדורש חקירת בלוקצ'יין רצינית, אשמח לשמוע ולבחון יחד את הצעדים הבאים.</p>
</div>
<div class="hero-actions"><a href="/#contact" class="btn btn-solid">לפנייה ראשונית</a><a href="/articles.html" class="btn">קראו את המאמרים</a></div>
"""
        stats = """
<div class="stat-box"><div class="stat-num">8+</div><div class="stat-label">שנות יזמות בפינטק ובקריפטו</div></div>
<div class="stat-box"><div class="stat-num">4</div><div class="stat-label">מיזמים שהוקמו ונוהלו</div></div>
<div class="stat-box"><div class="stat-num">$30M+</div><div class="stat-label">גויסו במהלך הקריירה היזמית</div></div>
"""
        return f"""
  <section class="page-header wrap">
    <div class="breadcrumb"><a href="/">בית</a> / אודות</div>
    <div class="eyebrow">אודות</div>
    <h1>יזם פינטק שהפך לחוקר בלוקצ'יין.</h1>
    <p class="lead">שמונה שנים בצד השני של השולחן - בונה ומנהל מוצרים פיננסיים בקריפטו - לפני שהפך את אותה מומחיות לעבודת חקירה.</p>
  </section>
  <section>
    <div class="wrap about-grid">
      <div>{prose}</div>
      <div>
        {stats}
        <div class="timeline">{timeline_html}</div>
      </div>
    </div>
  </section>
"""
    else:
        prose = """
<div class="prose">
<p>Dor Arad is an independent blockchain investigator and technology entrepreneur with over eight years of experience across fintech, crypto, and DeFi. His path into blockchain investigation didn't start at a police department or a cybersecurity firm — it started on the other side of the table, as founder and CEO of a crypto hedge fund and financial consulting practice (Venture Chic), where he spent years working with EMI products, alternative banking solutions, DeFi, and custom smart contracts. That depth of understanding of how digital money is supposed to move is exactly what makes it possible to quickly spot when it isn't.</p>
<p>Alongside the hedge fund, Dor also founded Everest Smart Living, a consulting firm for SaaS development and custom CRM systems, and previously co-founded DNG Technologies, an IoT company that secured two funding rounds and a worldwide patent. Each venture sharpened a different skill — product management, technical execution, and financial risk management — all of which now feed directly into his investigative work.</p>
<p>Before the business world, Dor served in the IDF as a combat soldier and commander in the Duvdevan special-forces unit, and worked with Unit 8200 on the intelligence development of tactical equipment. That service instilled a systematic approach to working under pressure and close attention to detail — qualities that translate directly into investigative work, where a small error can change the entire case.</p>
<p>Today Dor focuses exclusively on blockchain investigation and digital intelligence: tracing stolen funds, investigating crypto fraud, forensic wallet analysis, and compliance support for businesses that touch digital assets. He works with law enforcement, law firms, accountants, businesses, and private clients — always with the same approach: transparent methodology, rigorous documentation, and complete discretion.</p>
<p>If you're facing a case that needs a serious blockchain investigation, I'm glad to hear about it and talk through the next steps.</p>
</div>
<div class="hero-actions"><a href="/en/#contact" class="btn btn-solid">Start an Inquiry</a><a href="/en/articles.html" class="btn">Read the Articles</a></div>
"""
        stats = """
<div class="stat-box"><div class="stat-num">8+</div><div class="stat-label">years in fintech &amp; crypto entrepreneurship</div></div>
<div class="stat-box"><div class="stat-num">4</div><div class="stat-label">ventures founded and operated</div></div>
<div class="stat-box"><div class="stat-num">$30M+</div><div class="stat-label">raised across his entrepreneurial career</div></div>
"""
        return f"""
  <section class="page-header wrap">
    <div class="breadcrumb"><a href="/en/">Home</a> / About</div>
    <div class="eyebrow">About</div>
    <h1>A fintech entrepreneur turned blockchain investigator.</h1>
    <p class="lead">Eight years on the other side of the table — building and running financial products in crypto — before turning that expertise into investigative work.</p>
  </section>
  <section>
    <div class="wrap about-grid">
      <div>{prose}</div>
      <div>
        {stats}
        <div class="timeline">{timeline_html}</div>
      </div>
    </div>
  </section>
"""

write_page('/about.html', page_shell('he',
    "אודות דור ארד — חוקר בלוקצ'יין",
    "דור ארד - יזם פינטק וקריפטו עם מעל שמונה שנות ניסיון, כיום חוקר בלוקצ'יין עצמאי המתמחה באיתור נכסים, חקירת הונאות ותמיכה בציות.",
    '/about.html', about_body('he'), '/about.html', '/en/about.html',
    extra_jsonld=[breadcrumb_jsonld('he', [('בית', '/'), ('אודות', '/about.html')])]))

write_page('/en/about.html', page_shell('en',
    "About Dor Arad — Blockchain Investigator",
    "Dor Arad - a fintech and crypto entrepreneur with 8+ years of experience, now an independent blockchain investigator specializing in asset tracing, fraud investigations, and compliance support.",
    '/en/about.html', about_body('en'), '/about.html', '/en/about.html',
    extra_jsonld=[breadcrumb_jsonld('en', [('Home', '/en/'), ('About', '/en/about.html')])]))

# ============================================================= ARTICLES ====
def articles_listing_body(lang):
    he = lang == 'he'
    cards = ''
    for a in ARTICLES_META:
        lg = a['he'] if he else a['en']
        href = f"/articles/{a['slug']}.html" if he else f"/en/articles/{a['slug']}.html"
        tag = a['tag_he'] if he else a['tag_en']
        read_lbl = f"{lg['read_min']} דק' קריאה" if he else f"{lg['read_min']} min read"
        cards += f"""<a class="article-card" href="{href}">
          <div class="tag">{tag}</div>
          <h3>{esc(lg['title'])}</h3>
          <p>{esc(lg['meta'])}</p>
          <div class="meta"><span>{fmt_date(a['date'], lang)}</span><span>{read_lbl}</span></div>
        </a>"""
    if he:
        return f"""
  <section class="page-header wrap">
    <div class="breadcrumb"><a href="/">בית</a> / מאמרים</div>
    <div class="eyebrow">מאמרים</div>
    <h1>תובנות מהשטח על חקירות בלוקצ'יין.</h1>
    <p class="lead">מדריכים וניתוחים מקצועיים בנושאי חקירת קריפטו, הונאות, DeFi וציות רגולטורי - כתובים על ידי דור ארד.</p>
  </section>
  <section><div class="wrap"><div class="article-grid">{cards}</div></div></section>
"""
    else:
        return f"""
  <section class="page-header wrap">
    <div class="breadcrumb"><a href="/en/">Home</a> / Articles</div>
    <div class="eyebrow">Articles</div>
    <h1>Field notes on blockchain investigation.</h1>
    <p class="lead">Professional guides and analysis on crypto investigations, fraud, DeFi, and regulatory compliance — written by Dor Arad.</p>
  </section>
  <section><div class="wrap"><div class="article-grid">{cards}</div></div></section>
"""

write_page('/articles.html', page_shell('he',
    "מאמרים — דור ארד, חקירות בלוקצ'יין",
    "מדריכים וניתוחים מקצועיים בנושאי חקירת קריפטו, הונאות, DeFi וציות רגולטורי, מאת דור ארד.",
    '/articles.html', articles_listing_body('he'), '/articles.html', '/en/articles.html',
    extra_jsonld=[breadcrumb_jsonld('he', [('בית', '/'), ('מאמרים', '/articles.html')])]))

write_page('/en/articles.html', page_shell('en',
    "Articles — Dor Arad, Blockchain Investigations",
    "Professional guides and analysis on crypto investigations, fraud, DeFi, and regulatory compliance, written by Dor Arad.",
    '/en/articles.html', articles_listing_body('en'), '/articles.html', '/en/articles.html',
    extra_jsonld=[breadcrumb_jsonld('en', [('Home', '/en/'), ('Articles', '/en/articles.html')])]))

# ========================================================= ARTICLE PAGES ===
def article_body(lang, a):
    he = lang == 'he'
    lg = a['he'] if he else a['en']
    tag = a['tag_he'] if he else a['tag_en']
    read_lbl = f"{lg['read_min']} דק' קריאה" if he else f"{lg['read_min']} min read"
    breadcrumb = (f'<div class="breadcrumb"><a href="/">בית</a> / <a href="/articles.html">מאמרים</a> / {esc(lg["title"])}</div>' if he
                  else f'<div class="breadcrumb"><a href="/en/">Home</a> / <a href="/en/articles.html">Articles</a> / {esc(lg["title"])}</div>')
    cta = (f"""<div class="article-cta"><div><h3>נתקלתם במקרה דומה?</h3><p>אשמח לשמוע על התיק שלכם ולבחון יחד את הצעדים הבאים - בדיסקרטיות מלאה.</p></div><a href="/#contact" class="btn btn-solid">צרו קשר</a></div>"""
           if he else
           f"""<div class="article-cta"><div><h3>Facing a similar situation?</h3><p>I'm glad to hear about your case and talk through the next steps — in complete confidence.</p></div><a href="/en/#contact" class="btn btn-solid">Get in Touch</a></div>""")
    author_label = 'דור ארד' if he else 'Dor Arad'
    published_label = 'פורסם ב' if he else 'Published'
    return f"""
  <section class="page-header wrap">
    {breadcrumb}
    <div class="eyebrow">{tag}</div>
    <h1>{esc(lg['title'])}</h1>
    <div class="article-meta-row">
      <div class="author-chip"><span class="author-avatar">DA</span><span>{author_label}</span></div>
      <span>{published_label} {fmt_date(a['date'], lang)}</span>
      <span>{read_lbl}</span>
    </div>
  </section>
  <section style="padding-top:0;">
    <div class="wrap">
      <div class="prose">{lg['body_html']}</div>
      <div class="prose">{cta}</div>
    </div>
  </section>
"""

for a in ARTICLES_META:
    he_path = f"/articles/{a['slug']}.html"
    en_path = f"/en/articles/{a['slug']}.html"
    he_img = f"/assets/covers/{a['slug']}-he.png"
    en_img = f"/assets/covers/{a['slug']}-en.png"
    write_page(he_path, page_shell('he',
        f"{a['he']['title']} — דור ארד",
        a['he']['meta'],
        '/articles.html', article_body('he', a),
        he_path, en_path, og_image=he_img, page_type='article',
        extra_jsonld=[
            article_jsonld('he', a, he_path, he_img),
            breadcrumb_jsonld('he', [('בית', '/'), ('מאמרים', '/articles.html'), (a['he']['title'], he_path)]),
        ]))
    write_page(en_path, page_shell('en',
        f"{a['en']['title']} — Dor Arad",
        a['en']['meta'],
        '/en/articles.html', article_body('en', a),
        he_path, en_path, og_image=en_img, page_type='article',
        extra_jsonld=[
            article_jsonld('en', a, en_path, en_img),
            breadcrumb_jsonld('en', [('Home', '/en/'), ('Articles', '/en/articles.html'), (a['en']['title'], en_path)]),
        ]))

# ================================================================ SEO FILES =
def write_sitemap():
    seen = set()
    urls = []
    for he_path, en_path in ALL_PAGES:
        for path, lang, alt in [(he_path, 'he', en_path), (en_path, 'en', he_path)]:
            if path in seen:
                continue
            seen.add(path)
            urls.append((path, he_path, en_path))
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path, he_path, en_path in urls:
        parts.append('  <url>')
        parts.append(f'    <loc>{CONTACT["website_href"]}{path}</loc>')
        parts.append(f'    <xhtml:link rel="alternate" hreflang="he" href="{CONTACT["website_href"]}{he_path}" />')
        parts.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{CONTACT["website_href"]}{en_path}" />')
        parts.append('  </url>')
    parts.append('</urlset>')
    write_page('/sitemap.xml', '\n'.join(parts))

def write_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {CONTACT['website_href']}/sitemap.xml
"""
    write_page('/robots.txt', content)

write_sitemap()
write_robots()

print("\nDone. Site generated at:", ROOT)

