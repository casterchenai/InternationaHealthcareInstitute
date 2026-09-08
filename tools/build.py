#!/usr/bin/env python3
"""
IHI site builder.

  python3 tools/build.py            # build everything into the site root

What it does
  1. Renders the Greater Bay Area hub pages from content/pages/*.html fragments (EN + zh).
  2. Renders Insights (news & policy updates) from content/insights/<slug>/{en,zh}.md
     -> /insights/<slug>/ and /zh/insights/<slug>/, plus the two index pages and RSS feeds.
  3. Patches the shared header / mobile menu / footer into the hand-written pages
     (index, zh/index, aboutus, services, compliance-licensing-standards, faq, contactus).
  4. Injects the three latest articles into the home pages (between the latest-insights markers).
  5. Regenerates sitemap.xml with hreflang alternates.

Content conventions
  content/insights/<slug>/en.md   YAML front matter + Markdown body
      title, date (YYYY-MM-DD), tags [hk|cn|gba|macao], excerpt, standfirst (optional),
      sources: [{title, url}], updated (optional)
  content/insights/<slug>/zh.md   same keys, Traditional Chinese
  content/pages/<name>.en.html    <main> inner HTML for a hub page; first line is a JSON
      comment with title/description/canonical/jsonld etc. (see existing files)
"""
import json, os, re, sys, glob, html, datetime, pathlib
import markdown, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://www.interhci.com"
TODAY = datetime.date.today().isoformat()
WA_EN = "https://wa.me/85293808873?text=Hello%20IHI%2C%20I%27d%20like%20a%20free%20licensing%20assessment%20for%20my%20clinic."
WA_ZH = "https://wa.me/85293808873?text=%E4%BD%A0%E5%A5%BD%20IHI%EF%BC%8C%E6%88%91%E6%83%B3%E7%82%BA%E6%88%91%E7%9A%84%E8%A8%BA%E6%89%80%E9%A0%90%E7%B4%84%E5%85%8D%E8%B2%BB%E7%89%8C%E7%85%A7%E8%A9%95%E4%BC%B0%E3%80%82"
ICON = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11.8 11.8 0 0 0 12 0C5.5 0 .2 5.3.2 11.8c0 2.1.5 4.1 1.6 5.9L0 24l6.4-1.7a11.8 11.8 0 0 0 5.6 1.4c6.5 0 11.8-5.3 11.8-11.8 0-3.2-1.2-6.1-3.3-8.4ZM12 21.7c-1.8 0-3.5-.5-5-1.4l-.4-.2-3.8 1 1-3.7-.2-.4a9.7 9.7 0 0 1-1.5-5.2C2.1 6.4 6.5 2 12 2c2.6 0 5.1 1 6.9 2.9a9.7 9.7 0 0 1 2.9 6.9c0 5.5-4.4 9.9-9.8 9.9Zm5.4-7.4c-.3-.1-1.8-.9-2-1-.3-.1-.5-.1-.7.1l-.9 1.2c-.2.2-.3.2-.6.1-.3-.1-1.3-.5-2.4-1.5-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6l.4-.5.3-.5c.1-.2 0-.4 0-.5l-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5.1 4.5.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.8-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.2-.3-.3-.6-.4Z"/></svg>')
FONTS_EN = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap">'
FONTS_ZH = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Source+Sans+3:wght@400;500;600;700&family=Noto+Serif+HK:wght@600;700&family=Noto+Sans+HK:wght@400;500;700&display=swap">'

TAG_LABEL = {"en": {"hk": "Hong Kong", "cn": "Mainland China", "gba": "Greater Bay Area", "macao": "Macao"},
             "zh": {"hk": "香港", "cn": "內地", "gba": "大灣區", "macao": "澳門"}}

NAV = {
  "en": [("services/", "Services", "services"), ("greater-bay-area/", "Greater Bay Area", "gba"),
         ("insights/", "Insights", "insights"), ("faq/", "FAQ", "faq"), ("contactus/", "Contact", "contactus")],
  "zh": [("zh/#services", "服務", "services"), ("zh/greater-bay-area/", "大灣區", "gba"),
         ("zh/insights/", "資訊", "insights"), ("zh/#faq", "常見問題", "faq"), ("zh/#contact", "聯絡我們", "contactus")],
}
MOBILE = {
  "en": [("", "Home"), ("aboutus/", "About Us"), ("services/", "Services"), ("greater-bay-area/", "Greater Bay Area"),
         ("greater-bay-area/invest-in-hong-kong/", "— Invest in Hong Kong"), ("greater-bay-area/invest-in-mainland-china/", "— Invest in Mainland China"),
         ("greater-bay-area/policies/", "— Policy tracker"), ("insights/", "Insights: news & policy"),
         ("compliance-licensing-standards/", "Compliance & Licensing Standards"), ("faq/", "FAQ"), ("contactus/", "Contact Us")],
  "zh": [("zh/", "首頁"), ("zh/#services", "服務"), ("zh/greater-bay-area/", "大灣區跨境醫療投資"),
         ("zh/greater-bay-area/invest-in-hong-kong/", "— 投資香港醫療"), ("zh/greater-bay-area/invest-in-mainland-china/", "— 投資內地醫療"),
         ("zh/greater-bay-area/policies/", "— 政策追蹤"), ("zh/insights/", "資訊：新聞與政策"), ("zh/#faq", "常見問題"), ("zh/#contact", "聯絡我們"),
         ("aboutus/", "About Us (EN)"), ("faq/", "Full FAQ (EN)")],
}

def rel(depth, path):
    return ("../" * depth) + path if path else ("../" * depth if depth else "./")

def header(lang, depth, current):
    r = lambda p: rel(depth, p)
    wa = WA_EN if lang == "en" else WA_ZH
    brand_small = "International Healthcare Institute" if lang == "en" else "國際醫療學院 International Healthcare Institute"
    aria_home = "International Healthcare Institute — home" if lang == "en" else "國際醫療學院 — 首頁"
    CUR = ' aria-current="page"'
    nav = "\n".join(f'      <a href="{r(h)}"{CUR if k == current else ""}>{t}</a>' for h, t, k in NAV[lang])
    mob = "\n".join(f'    <a class="item" href="{r(h)}">{t}</a>' for h, t in MOBILE[lang])
    if lang == "en":
        lang_sw = f'<a href="{r("")}" aria-current="true" lang="en">EN</a>\n        <a href="{r("zh/")}" lang="zh-Hant" hreflang="zh-Hant">繁</a>'
        lang_sw_m = f'<a href="{r("")}" aria-current="true">EN</a><a href="{r("zh/")}" lang="zh-Hant">繁</a>'
        home = r("")
    else:
        lang_sw = f'<a href="{r("")}" lang="en" hreflang="en">EN</a>\n        <a href="{r("zh/")}" aria-current="true" lang="zh-Hant">繁</a>'
        lang_sw_m = f'<a href="{r("")}" lang="en">EN</a><a href="{r("zh/")}" aria-current="true">繁</a>'
        home = r("zh/")
    menu_label = "Menu" if lang == "en" else "選單"
    nav_label = "Primary" if lang == "en" else "主導覽"
    return f'''<header class="top">
  <div class="wrap top-inner">
    <a class="brand" href="{home}" aria-label="{aria_home}">
      <img src="{r("assets/img/logo.png")}" width="40" height="40" alt="" fetchpriority="high">
      <span class="brand-text"><b>IHI</b><small>{brand_small}</small></span>
    </a>
    <nav class="nav" aria-label="{nav_label}">
{nav}
    </nav>
    <div class="top-actions">
      <div class="lang" aria-label="Language">
        {lang_sw}
      </div>
      <a class="btn btn-wa btn-sm" href="{wa}" rel="noopener" target="_blank">{ICON} WhatsApp</a>
      <button class="menu-btn" aria-expanded="false" aria-controls="mobile-menu" aria-label="{menu_label}"><span></span></button>
    </div>
  </div>
  <div class="mobile-menu" id="mobile-menu">
{mob}
    <div class="row">
      <div class="lang">{lang_sw_m}</div>
      <a class="btn btn-wa btn-sm" href="{wa}" rel="noopener" target="_blank">WhatsApp</a>
    </div>
  </div>
</header>'''

def footer(lang, depth):
    r = lambda p: rel(depth, p)
    wa = WA_EN if lang == "en" else WA_ZH
    if lang == "en":
        links = [("services/#clinic-licensing", "Clinic licensing"), ("services/#day-procedure-centre", "Day procedure centres"),
                 ("compliance-licensing-standards/", "Cap. 633 compliance"), ("greater-bay-area/", "Greater Bay Area investment"), ("insights/", "Insights")]
        sub = [("", "Home"), ("aboutus/", "About IHI"), ("services/", "All services"), ("greater-bay-area/invest-in-hong-kong/", "Invest in Hong Kong"),
               ("greater-bay-area/invest-in-mainland-china/", "Invest in Mainland China"), ("greater-bay-area/policies/", "Policy tracker"),
               ("compliance-licensing-standards/", "Compliance & licensing standards"), ("faq/", "FAQ"), ("contactus/", "Contact form"),
               ("insights/feed.xml", "RSS"), ("zh/", "繁體中文")]
        copy = "International Healthcare Institute 國際醫療學院 · interhci.com"
        aria = "Chat with IHI on WhatsApp"
    else:
        links = [("services/#clinic-licensing", "診所牌照"), ("services/#day-procedure-centre", "日間醫療中心"),
                 ("compliance-licensing-standards/", "第633章合規"), ("zh/greater-bay-area/", "大灣區投資"), ("zh/insights/", "資訊")]
        sub = [("zh/", "首頁"), ("zh/greater-bay-area/invest-in-hong-kong/", "投資香港醫療"), ("zh/greater-bay-area/invest-in-mainland-china/", "投資內地醫療"),
               ("zh/greater-bay-area/policies/", "政策追蹤"), ("zh/insights/", "新聞與政策"), ("aboutus/", "關於 IHI（英文）"), ("faq/", "常見問題（英文）"),
               ("contactus/", "聯絡表格"), ("zh/insights/feed.xml", "RSS"), ("", "English")]
        copy = "國際醫療學院 International Healthcare Institute · interhci.com"
        aria = "透過 WhatsApp 聯絡 IHI"
    ZH_ATTR, EN_ATTR = ' lang="zh-Hant"', ' lang="en"'
    li = lambda items: "\n".join(f'      <li><a href="{r(h)}"{ZH_ATTR if t == "繁體中文" else ""}{EN_ATTR if t == "English" else ""}>{t}</a></li>' for h, t in items)
    return f'''<footer class="foot">
  <div class="wrap foot-inner">
    <p style="margin:0">&copy; <span class="year">{TODAY[:4]}</span> {copy}</p>
    <ul class="links">
{li(links)}
    </ul>
    <ul class="sub">
{li(sub)}
    </ul>
  </div>
</footer>

<a class="wa-fab" href="{wa}" rel="noopener" target="_blank" aria-label="{aria}">{ICON}</a>'''

def head(lang, depth, m):
    """m: dict(title, description, path (site-relative, e.g. 'insights/'), alt (path of other language or None),
             og_type, jsonld (list), robots (optional), image (optional))"""
    r = lambda p: rel(depth, p)
    url = SITE + "/" + m["path"]
    alt = m.get("alt")
    if lang == "en":
        hl = f'<link rel="alternate" hreflang="en" href="{url}">\n'
        if alt: hl += f'<link rel="alternate" hreflang="zh-Hant-HK" href="{SITE}/{alt}">\n'
        hl += f'<link rel="alternate" hreflang="x-default" href="{url}">'
        loc, loc_alt, fonts, htmllang = "en_HK", "zh_HK", FONTS_EN, "en"
    else:
        hl = f'<link rel="alternate" hreflang="zh-Hant-HK" href="{url}">\n'
        if alt: hl += f'<link rel="alternate" hreflang="en" href="{SITE}/{alt}">\n<link rel="alternate" hreflang="x-default" href="{SITE}/{alt}">'
        loc, loc_alt, fonts, htmllang = "zh_HK", "en_HK", FONTS_ZH, "zh-Hant-HK"
    image = m.get("image", "assets/img/og-image.png")
    jsonld = "\n".join(f'<script type="application/ld+json">\n{json.dumps(j, ensure_ascii=False, indent=1)}\n</script>' for j in m.get("jsonld", []))
    return f'''<!DOCTYPE html>
<html lang="{htmllang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(m["title"])}</title>
<meta name="description" content="{html.escape(m["description"])}">
<link rel="canonical" href="{url}">
{hl}
<meta name="theme-color" content="#0b4a9b">
<meta name="robots" content="{m.get("robots", "index,follow,max-image-preview:large")}">
<meta property="og:type" content="{m.get("og_type", "website")}">
<meta property="og:site_name" content="International Healthcare Institute 國際醫療學院">
<meta property="og:locale" content="{loc}">
<meta property="og:locale:alternate" content="{loc_alt}">
<meta property="og:title" content="{html.escape(m.get("og_title", m["title"]))}">
<meta property="og:description" content="{html.escape(m["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(m.get("og_title", m["title"]))}">
<meta name="twitter:description" content="{html.escape(m["description"])}">
<meta name="twitter:image" content="{SITE}/{image}">
<link rel="icon" href="{r("favicon.ico")}" sizes="any">
<link rel="apple-touch-icon" href="{r("apple-touch-icon.png")}">
<link rel="alternate" type="application/rss+xml" title="IHI Insights" href="{r("insights/feed.xml" if lang == "en" else "zh/insights/feed.xml")}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<link rel="stylesheet" href="{r("assets/css/site.css")}">
{jsonld}
</head>'''

def page(lang, depth, current, meta, body, extra=""):
    skip = "Skip to content" if lang == "en" else "跳至內容"
    return f'''{head(lang, depth, meta)}
<body>
<a class="skip-link" href="#main">{skip}</a>

{header(lang, depth, current)}

<main id="main" class="inner">
{body}
</main>

{footer(lang, depth)}

<script src="{rel(depth, "assets/js/site.js")}" defer></script>
{extra}
</body>
</html>
'''

def breadcrumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + "/" + p} for i, (n, p) in enumerate(items)]}

def write(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  wrote", path)

# ---------------------------------------------------------------- hub pages
def build_pages():
    print("Hub pages")
    for frag in sorted(glob.glob(str(ROOT / "content/pages/*.html"))):
        name = os.path.basename(frag)                       # greater-bay-area.en.html
        stem, lang = name.rsplit(".", 2)[0], name.rsplit(".", 2)[1]
        raw = open(frag, encoding="utf-8").read()
        m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->", raw, re.S)
        meta = json.loads(m.group(1)); body = raw[m.end():]
        out = meta["path"] + "index.html"
        depth = meta["path"].count("/")
        meta.setdefault("jsonld", [])
        write(out, page(lang, depth, meta.get("current", "gba"), meta, body))

# ---------------------------------------------------------------- insights
MD = markdown.Markdown(extensions=["tables", "attr_list", "sane_lists", "smarty"], output_format="html5")

def load_md(path):
    raw = open(path, encoding="utf-8").read()
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm)
    MD.reset()
    return meta, MD.convert(body.strip())

def articles():
    out = []
    for d in sorted(glob.glob(str(ROOT / "content/insights/*/"))):
        slug = os.path.basename(d.rstrip("/\\"))
        en, en_html = load_md(os.path.join(d, "en.md"))
        zh, zh_html = (load_md(os.path.join(d, "zh.md")) if os.path.exists(os.path.join(d, "zh.md")) else (None, None))
        out.append({"slug": slug, "en": en, "en_html": en_html, "zh": zh, "zh_html": zh_html})
    out.sort(key=lambda a: a["en"]["date"], reverse=True)
    return out

def fmt_date(d, lang):
    d = datetime.date.fromisoformat(str(d))
    return d.strftime("%-d %B %Y") if lang == "en" else f"{d.year}年{d.month}月{d.day}日"

def tags_html(tags, lang):
    return " ".join(f'<span class="tag {t}">{TAG_LABEL[lang][t]}</span>' for t in tags)

def article_page(a, lang, all_articles):
    meta = a[lang]; body = a[lang + "_html"]
    slug = a["slug"]
    path = f"insights/{slug}/" if lang == "en" else f"zh/insights/{slug}/"
    alt = (f"zh/insights/{slug}/" if a["zh"] else None) if lang == "en" else f"insights/{slug}/"
    depth = path.count("/")
    r = lambda p: rel(depth, p)
    date = str(meta["date"]); updated = str(meta.get("updated", date))
    words = len(re.sub(r"<[^>]+>", " ", body).split()) if lang == "en" else len(re.sub(r"<[^>]+>", "", body))
    reading = max(1, round(words / (220 if lang == "en" else 450)))
    reading_txt = f"{reading} min read" if lang == "en" else f"閱讀約 {reading} 分鐘"
    src_items = "".join(f'<li><a href="{s["url"]}" rel="noopener" target="_blank">{html.escape(s["title"])}</a></li>' for s in meta.get("sources", []))
    sources = f'<aside class="sources"><h2>{"Sources" if lang == "en" else "資料來源"}</h2><ol>{src_items}</ol></aside>' if src_items else ""
    disclaimer = ("This article summarises public policy announcements for general information and is not legal advice. Requirements change; confirm the current position with the relevant authority or with IHI before acting."
                  if lang == "en" else "本文整理公開政策資訊，僅供一般參考，並非法律意見。相關要求或會變更，行動前請向有關機構或 IHI 核實最新情況。")
    cta = (f'<div class="cta-inline"><div><b>Planning a facility in Hong Kong or the Greater Bay Area?</b><span>Get a free assessment of the licence pathway and timeline for your project.</span></div><a class="btn btn-wa" href="{WA_EN}" rel="noopener" target="_blank">{ICON} WhatsApp IHI</a></div>'
           if lang == "en" else f'<div class="cta-inline"><div><b>正在籌劃香港或大灣區的醫療項目？</b><span>免費評估您項目的牌照路徑及時間表。</span></div><a class="btn btn-wa" href="{WA_ZH}" rel="noopener" target="_blank">{ICON} WhatsApp 聯絡 IHI</a></div>')
    # related: same tag, other slugs
    rel_items = [b for b in all_articles if b["slug"] != slug and (b[lang]) and set(b[lang]["tags"]) & set(meta["tags"])][:3]
    if not rel_items: rel_items = [b for b in all_articles if b["slug"] != slug and b[lang]][:3]
    related = "".join(f'<li><a href="{r(("insights/" if lang == "en" else "zh/insights/") + b["slug"] + "/")}">{html.escape(b[lang]["title"])}</a></li>' for b in rel_items)
    side_title = "Related" if lang == "en" else "相關文章"
    hub_title = "Guides" if lang == "en" else "指南"
    hub_links = ([("greater-bay-area/", "Greater Bay Area hub"), ("greater-bay-area/invest-in-hong-kong/", "Invest in Hong Kong"), ("greater-bay-area/invest-in-mainland-china/", "Invest in Mainland China"), ("greater-bay-area/policies/", "Policy tracker")]
                 if lang == "en" else [("zh/greater-bay-area/", "大灣區跨境醫療"), ("zh/greater-bay-area/invest-in-hong-kong/", "投資香港醫療"), ("zh/greater-bay-area/invest-in-mainland-china/", "投資內地醫療"), ("zh/greater-bay-area/policies/", "政策追蹤")])
    hubs = "".join(f'<li><a href="{r(h)}">{t}</a></li>' for h, t in hub_links)
    back = ("All insights" if lang == "en" else "所有資訊")
    idx = r("insights/" if lang == "en" else "zh/insights/")
    body_html = f'''<div class="wrap">
  <div class="article-layout">
    <article class="article">
      <header>
        <p class="meta"><a href="{idx}">{back}</a> · <time datetime="{date}">{fmt_date(date, lang)}</time> · {tags_html(meta["tags"], lang)} · {reading_txt}</p>
        <h1>{html.escape(meta["title"])}</h1>
        {f'<p class="standfirst">{html.escape(meta["standfirst"])}</p>' if meta.get("standfirst") else ""}
      </header>
      <div class="article-body">
{body}
      </div>
      {cta}
      {sources}
      <p class="disclaimer">{disclaimer}{(" Last reviewed " + fmt_date(updated, lang) + ".") if lang == "en" else ("最後覆核：" + fmt_date(updated, lang) + "。")}</p>
    </article>
    <aside class="side">
      <h2>{side_title}</h2>
      <ul>{related}</ul>
      <h2>{hub_title}</h2>
      <ul>{hubs}</ul>
    </aside>
  </div>
</div>'''
    jsonld = [
        {"@context": "https://schema.org", "@type": "NewsArticle",
         "headline": meta["title"], "description": meta["excerpt"], "datePublished": date, "dateModified": updated,
         "inLanguage": "en" if lang == "en" else "zh-Hant-HK",
         "mainEntityOfPage": SITE + "/" + path, "image": SITE + "/assets/img/og-image.png",
         "author": {"@type": "Organization", "name": "International Healthcare Institute", "url": SITE + "/"},
         "publisher": {"@id": SITE + "/#organization"},
         "keywords": ", ".join(TAG_LABEL[lang][t] for t in meta["tags"]),
         "citation": [s["url"] for s in meta.get("sources", [])]},
        {"@context": "https://schema.org", **breadcrumbs([("Home" if lang == "en" else "首頁", "" if lang == "en" else "zh/"),
                                                             ("Insights" if lang == "en" else "資訊", "insights/" if lang == "en" else "zh/insights/"),
                                                             (meta["title"], path)])},
    ]
    pm = {"title": meta["title"] + (" | IHI Insights" if lang == "en" else " | IHI 資訊"), "description": meta["excerpt"], "path": path, "alt": alt,
          "og_type": "article", "og_title": meta["title"], "jsonld": jsonld}
    write(path + "index.html", page(lang, depth, "insights", pm, body_html))

def insights_index(arts, lang):
    path = "insights/" if lang == "en" else "zh/insights/"
    depth = path.count("/"); r = lambda p: rel(depth, p)
    items = [a for a in arts if a[lang]]
    def li(a):
        m = a[lang]
        return f'''    <li data-tags="{" ".join(m["tags"])}">
      <time datetime="{m["date"]}">{fmt_date(m["date"], lang)}</time>
      <div>{tags_html(m["tags"], lang)}<h3><a href="{r(path + a["slug"] + "/")}">{html.escape(m["title"])}</a></h3><p>{html.escape(m["excerpt"])}</p></div>
    </li>'''
    lst = "\n".join(li(a) for a in items)
    if lang == "en":
        title = "Insights: healthcare policy updates & news for Hong Kong and the Greater Bay Area"
        h1 = "Insights"; intro = "Policy updates and news that affect clinic, day procedure centre and hospital projects in Hong Kong and across the Greater Bay Area — summarised from official sources, with links so you can read the originals."
        f_all = "All"; rss = "Subscribe by RSS"; desc = "Policy updates and news for healthcare investors and operators in Hong Kong and the Greater Bay Area: Cap. 633 licensing, drug and device regulation, cross-border schemes and mainland market access."
    else:
        title = "資訊：香港及大灣區醫療政策更新與新聞 | IHI 國際醫療學院"
        h1 = "資訊"; intro = "影響香港及大灣區診所、日間醫療中心和醫院項目的政策更新與新聞——根據官方來源整理，並附原文連結。"
        f_all = "全部"; rss = "以 RSS 訂閱"; desc = "香港及大灣區醫療投資者與營運者的政策更新與新聞：第633章發牌、藥械監管、跨境計劃及內地市場准入。"
    filters = f'<a href="#" data-filter="all" aria-current="true">{f_all}</a>' + "".join(f'<a href="#" data-filter="{t}">{TAG_LABEL[lang][t]}</a>' for t in ("hk", "cn", "gba"))
    body = f'''<div class="page-title wrap">
  <p class="eyebrow">{"News & policy" if lang == "en" else "新聞與政策"}</p>
  <h1>{h1}</h1>
  <p>{intro}</p>
</div>
<div class="wrap">
  <div class="filters" id="filters">{filters}<a href="{r(path + "feed.xml")}" style="margin-left:auto">{rss}</a></div>
  <ul class="post-list" id="posts">
{lst}
  </ul>
  <p style="margin-top:2rem;color:var(--muted)">{"Looking for the underlying rules? See the " if lang == "en" else "想查閱背後的規則？請參閱"}<a href="{r("greater-bay-area/policies/" if lang == "en" else "zh/greater-bay-area/policies/")}">{"policy tracker" if lang == "en" else "政策追蹤"}</a>{"." if lang == "en" else "。"}</p>
</div>'''
    extra = '''<script>
(function(){var f=document.getElementById('filters');if(!f)return;f.addEventListener('click',function(e){var a=e.target.closest('a[data-filter]');if(!a)return;e.preventDefault();
f.querySelectorAll('a[data-filter]').forEach(function(x){x.removeAttribute('aria-current')});a.setAttribute('aria-current','true');var t=a.getAttribute('data-filter');
document.querySelectorAll('#posts li').forEach(function(li){li.style.display=(t==='all'||li.getAttribute('data-tags').split(' ').indexOf(t)>-1)?'':'none'});});})();
</script>'''
    jsonld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": h1, "url": SITE + "/" + path, "inLanguage": "en" if lang == "en" else "zh-Hant-HK",
               "isPartOf": {"@id": SITE + "/#website"},
               "hasPart": [{"@type": "NewsArticle", "headline": a[lang]["title"], "url": SITE + "/" + path + a["slug"] + "/", "datePublished": str(a[lang]["date"])} for a in items[:20]]},
              {"@context": "https://schema.org", **breadcrumbs([("Home" if lang == "en" else "首頁", "" if lang == "en" else "zh/"), (h1, path)])}]
    pm = {"title": title, "description": desc, "path": path, "alt": "zh/insights/" if lang == "en" else "insights/", "jsonld": jsonld}
    write(path + "index.html", page(lang, depth, "insights", pm, body, extra))

def rss(arts, lang):
    path = "insights/" if lang == "en" else "zh/insights/"
    items = [a for a in arts if a[lang]][:30]
    def item(a):
        m = a[lang]; u = SITE + "/" + path + a["slug"] + "/"
        d = datetime.datetime.combine(datetime.date.fromisoformat(str(m["date"])), datetime.time(9, 0), tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
        return f'''  <item>
    <title>{html.escape(m["title"])}</title>
    <link>{u}</link>
    <guid isPermaLink="true">{u}</guid>
    <pubDate>{d.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
    <description>{html.escape(m["excerpt"])}</description>
    {"".join(f"<category>{html.escape(TAG_LABEL[lang][t])}</category>" for t in m["tags"])}
  </item>'''
    title = "IHI Insights — Hong Kong & Greater Bay Area healthcare policy" if lang == "en" else "IHI 資訊 — 香港及大灣區醫療政策"
    desc = "Policy updates and news for healthcare investors and operators." if lang == "en" else "醫療投資者與營運者的政策更新及新聞。"
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{html.escape(title)}</title>
  <link>{SITE}/{path}</link>
  <atom:link href="{SITE}/{path}feed.xml" rel="self" type="application/rss+xml"/>
  <description>{html.escape(desc)}</description>
  <language>{"en-hk" if lang == "en" else "zh-hk"}</language>
  <lastBuildDate>{datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{chr(10).join(item(a) for a in items)}
</channel>
</rss>
'''
    write(path + "feed.xml", xml)

def latest_block(arts, lang, depth):
    r = lambda p: rel(depth, p)
    path = "insights/" if lang == "en" else "zh/insights/"
    items = [a for a in arts if a[lang]][:3]
    cards = "\n".join(f'''        <article class="post">
          <p class="meta"><time datetime="{a[lang]["date"]}">{fmt_date(a[lang]["date"], lang)}</time> {tags_html(a[lang]["tags"], lang)}</p>
          <h3><a href="{r(path + a["slug"] + "/")}">{html.escape(a[lang]["title"])}</a></h3>
          <p>{html.escape(a[lang]["excerpt"])}</p>
          <a class="link-arrow" href="{r(path + a["slug"] + "/")}">{"Read" if lang == "en" else "閱讀"}</a>
        </article>''' for a in items)
    return cards

def patch_home(arts):
    for lang, f, depth in (("en", "index.html", 0), ("zh", "zh/index.html", 1)):
        p = ROOT / f; s = p.read_text(encoding="utf-8")
        block = latest_block(arts, lang, depth)
        s2 = re.sub(r"(<!-- latest-insights:start -->).*?(<!-- latest-insights:end -->)", lambda m: m.group(1) + "\n" + block + "\n        " + m.group(2), s, flags=re.S)
        if s2 != s: p.write_text(s2, encoding="utf-8"); print("  patched latest insights in", f)

# ---------------------------------------------------------------- patch legacy pages
LEGACY = [("index.html", "en", 0, "home"), ("zh/index.html", "zh", 1, "home"), ("aboutus/index.html", "en", 1, "about"),
          ("services/index.html", "en", 1, "services"), ("compliance-licensing-standards/index.html", "en", 1, "compliance"),
          ("faq/index.html", "en", 1, "faq"), ("contactus/index.html", "en", 1, "contactus")]

def patch_legacy():
    print("Patching shared chrome into hand-written pages")
    for f, lang, depth, cur in LEGACY:
        p = ROOT / f; s = p.read_text(encoding="utf-8")
        h = header(lang, depth, cur)
        if cur == "home":   # home pages use in-page anchors for nav
            if lang == "en":
                h = h.replace('<a href="services/">Services</a>', '<a href="#services">Services</a>').replace('<a href="faq/">FAQ</a>', '<a href="#faq">FAQ</a>').replace('<a href="contactus/">Contact</a>', '<a href="#contact">Contact</a>')
            else:
                h = h.replace('href="zh/#services"', 'href="#services"').replace('href="zh/#faq"', 'href="#faq"').replace('href="zh/#contact"', 'href="#contact"').replace('href="./#services"', 'href="#services"').replace('href="./#faq"', 'href="#faq"').replace('href="./#contact"', 'href="#contact"')
        s2 = re.sub(r"<header class=\"top\">.*?</header>", lambda m: h, s, count=1, flags=re.S)
        s2 = re.sub(r"<footer class=\"foot\">.*?</a>\s*(?=\n\s*<script)", lambda m: footer(lang, depth), s2, count=1, flags=re.S)
        if 'rel="alternate" type="application/rss+xml"' not in s2:
            s2 = s2.replace('<link rel="stylesheet" href="' + rel(depth, "assets/css/site.css") + '">',
                            f'<link rel="alternate" type="application/rss+xml" title="IHI Insights" href="{rel(depth, "insights/feed.xml" if lang == "en" else "zh/insights/feed.xml")}">\n<link rel="stylesheet" href="{rel(depth, "assets/css/site.css")}">')
        if s2 != s: p.write_text(s2, encoding="utf-8"); print("  patched", f)

# ---------------------------------------------------------------- sitemap
def sitemap(arts):
    urls = []
    def add(path, alt, lastmod, freq, prio, img=None):
        urls.append((path, alt, lastmod, freq, prio, img))
    add("", "zh/", TODAY, "weekly", "1.0", ("assets/img/home-hero.webp", "Modern medical clinic interior"))
    add("zh/", "", TODAY, "weekly", "0.9", None)
    for p, alt, prio in (("aboutus/", None, "0.6"), ("services/", None, "0.9"), ("compliance-licensing-standards/", None, "0.9"), ("faq/", None, "0.8"), ("contactus/", None, "0.6")):
        add(p, alt, TODAY, "monthly", prio)
    for p in ("greater-bay-area/", "greater-bay-area/invest-in-hong-kong/", "greater-bay-area/invest-in-mainland-china/", "greater-bay-area/policies/"):
        add(p, "zh/" + p, TODAY, "monthly", "0.9"); add("zh/" + p, p, TODAY, "monthly", "0.8")
    add("insights/", "zh/insights/", TODAY, "weekly", "0.9"); add("zh/insights/", "insights/", TODAY, "weekly", "0.8")
    for a in arts:
        d = str(a["en"].get("updated", a["en"]["date"]))
        add(f"insights/{a['slug']}/", f"zh/insights/{a['slug']}/" if a["zh"] else None, d, "monthly", "0.7")
        if a["zh"]: add(f"zh/insights/{a['slug']}/", f"insights/{a['slug']}/", d, "monthly", "0.6")
    def entry(path, alt, lastmod, freq, prio, img):
        en, zh = (path, alt) if not path.startswith("zh/") else (alt, path)
        links = ""
        if alt is not None:
            links = f'''
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{en}"/>
    <xhtml:link rel="alternate" hreflang="zh-Hant-HK" href="{SITE}/{zh}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/{en}"/>'''
        im = f'\n    <image:image><image:loc>{SITE}/{img[0]}</image:loc><image:title>{img[1]}</image:title></image:image>' if img else ""
        return f'''  <url>
    <loc>{SITE}/{path}</loc>{links}
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>{im}
  </url>'''
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
''' + "\n".join(entry(*u) for u in urls) + "\n</urlset>\n"
    write("sitemap.xml", xml)

if __name__ == "__main__":
    os.chdir(ROOT)
    build_pages()
    print("Insights")
    arts = articles()
    for a in arts:
        article_page(a, "en", arts)
        if a["zh"]: article_page(a, "zh", arts)
    insights_index(arts, "en"); insights_index(arts, "zh")
    rss(arts, "en"); rss(arts, "zh")
    patch_legacy()
    patch_home(arts)
    sitemap(arts)
    print("Done:", len(arts), "articles")
