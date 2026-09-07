# International Healthcare Institute — website

Static rebuild of [interhci.com](https://www.interhci.com/) for GitHub Pages.
Keeps the original brand (logo, white editorial layout, clinic photography) and
content, and adds the technical SEO the Squarespace site was missing.

## Structure

```
/                                  Home
/aboutus/                          About Us
/services/                         Services (anchors: #clinic-licensing, #day-procedure-centre,
                                   #staff-training, #system-design, #workflow)
/compliance-licensing-standards/   Cap 633 compliance guide
/faq/                              FAQ (native <details>, FAQPage schema)
/contactus/                        Contact form + map
/assets/css/site.css               Single stylesheet, no framework
/assets/js/site.js                 Mobile nav toggle, FAQ deep-linking (2 KB)
/assets/img/                       Logo, OG image, clinic photos (from original site)
sitemap.xml · robots.txt · 404.html · .nojekyll
```

URL paths match the original Squarespace site exactly, so existing backlinks and
Google index entries carry over without redirects.

## SEO work done

- Unique, keyword-led `<title>` and `<meta description>` per page (original had one
  190-character title on every page).
- One `<h1>` per page and a proper h2/h3 outline (original FAQ had six `<h1>`s).
- Canonical URLs, Open Graph and Twitter Card tags on every page.
- JSON-LD: `Organization` + `ProfessionalService` (address, geo, hours, phone),
  `WebSite`, `BreadcrumbList` on every sub-page, `ItemList` of `Service` +
  `HowTo` on Services, `Article` + `Legislation` on Compliance, `FAQPage` with all
  10 Q&As (eligible for FAQ rich results).
- Descriptive `alt` text on every image (all were empty before), explicit
  `width`/`height` to avoid layout shift, `loading="lazy"` below the fold,
  `fetchpriority="high"` on the logo and hero.
- Internal linking between pages and section anchors; every dead
  "Learn More" `href="#"` on the old site now points somewhere real.
- Semantic landmarks (`header`, `nav`, `main`, `article`, `footer`, `address`),
  skip link, keyboard-friendly nav, `aria-current`.
- `sitemap.xml` (with image extension) and `robots.txt`.
- No Squarespace runtime: page weight drops from ~2 MB of JS to a few KB.

## Contact form

GitHub Pages can't process forms. `contactus/index.html` posts to a Formspree
endpoint — replace `FORM_ENDPOINT` in the form `action` with your Formspree /
Basin / Getform ID. Until then, submitting opens the visitor's email client
addressed to info@interhci.com with the fields pre-filled.

## Custom domain

To serve at `www.interhci.com`: add a `CNAME` file containing `www.interhci.com`,
set the same value under Settings → Pages → Custom domain, and point the DNS
CNAME for `www` at `casterchenai.github.io`. All canonical/OG URLs already use
the production domain.

## Local preview

```
cd site && python -m http.server 8000
```
