#!/usr/bin/env python3
"""Build the Dormer website's generated files.

Edit docs/index.html (the English page, which also carries the French text in
<span lang="fr"> tags), then run:

    python3 scripts/build.py

It rewrites:
  - the SEO block (<!--seo--> … <!--/seo-->) in docs/index.html: hreflang links,
    language redirect, and structured data (app, video, FAQ built from the page's FAQ)
  - docs/fr/index.html, the French page
  - docs/compare/ and docs/fr/compare/ (old URLs redirected in docs/_redirects)
  - docs/sitemap.xml
  - the Dormer Pro price (<!--pro-price--> … <!--/pro-price-->) and the comparison table prices,
    from data/prices.json (kept up to date by scripts/sync_prices.py)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://dormernotch.com"
DOWNLOAD = "https://github.com/Zerdoxy741/dormer/releases/latest/download/Dormer.zip"
BUY = "https://buy.polar.sh/polar_cl_i0J4wAjf6ZKOnhGaEk4EFbYijV0jW689W7zpv001BK6"
LASTMOD = "2026-11-25"
FILM_DATE = "2026-11-25"

PRICES = json.loads((ROOT.parent / "data" / "prices.json").read_text())["apps"]


def money(amount: float, currency: str, lang: str) -> str:
    sym = {"EUR": "€", "USD": "$", "CHF": "CHF "}.get(currency, currency + " ")
    n = f"{amount:.2f}".removesuffix(".00")
    if lang == "fr":
        return f"{n.replace('.', ',')}\u00a0{sym.strip()}"
    return f"{sym}{n}" if currency in ("EUR", "USD") else f"{n} {currency}"


def price_text(name: str, lang: str) -> str:
    """Short price of the full version, for the comparison table."""
    p = PRICES[name]
    if "lifetime" not in p:
        return "Free" if lang == "en" else "Gratuit"
    s = money(p["lifetime"], p["currency"], lang)
    if p.get("minimum"):
        s = ("from " if lang == "en" else "dès ") + s
    if p.get("monthly"):
        s += (" or " if lang == "en" else " ou ") + money(p["monthly"], p["currency"], lang) + ("/mo" if lang == "en" else "/mois")
    return s


def pro_price_block() -> str:
    p = PRICES["Dormer"]
    return (f'<!--pro-price--><span lang="en">{money(p["lifetime"], p["currency"], "en")}</span>'
            f'<span lang="fr">{money(p["lifetime"], p["currency"], "fr")}</span><!--/pro-price-->')


def set_pro_price(page: str) -> str:
    return re.sub(r"<!--pro-price-->.*?<!--/pro-price-->", lambda _: pro_price_block(), page, flags=re.S)


PAGES = {  # language -> URL path
    "home": {"en": "/", "fr": "/fr/"},
    "alt": {"en": "/compare/", "fr": "/fr/compare/"},
}

TEXT = {
    "en": {
        "title": "Dormer — Dynamic Island for your Mac's notch",
        "desc": ("Dormer turns your MacBook notch into a living Dynamic Island: music player, Shazam, "
                 "listen together with nearby Macs, AirDrop shelf, clipboard history, per-app volume, "
                 "ChatGPT & Claude, and a pixel cat that lives in your notch."),
        "keywords": ("MacBook notch app, Dynamic Island Mac, notch music player, macOS notch, AirDrop shelf, "
                     "clipboard history Mac, per-app volume, NotchNook alternative"),
        "og_title": "Dormer — your notch, wide awake",
        "og_desc": "A Dynamic Island for your MacBook notch, with a pixel cat that lives in it.",
        "locale": "en_US",
        "app_desc": "A Dynamic Island for your MacBook notch: music, Shazam, AirDrop shelf, AI, alerts and a pixel companion.",
        "offer": "Free version, plus a 14-day free trial of Dormer Pro",
        "film_name": "Dormer — two minutes in the notch",
        "film_desc": "A 2-minute film showing Dormer on a MacBook: music, AI, widgets, messages and the pixel cat that lives in the notch.",
    },
    "fr": {
        "title": "Dormer — Dynamic Island pour l'encoche de ton Mac",
        "desc": ("Dormer transforme l'encoche de ton MacBook en Dynamic Island : lecteur de musique, Shazam, "
                 "écoute à plusieurs entre Mac, étagère AirDrop, historique du presse-papiers, volume par app, "
                 "ChatGPT et Claude, et un chat en pixels qui vit dans l'encoche."),
        "keywords": ("app encoche MacBook, Dynamic Island Mac, notch Mac, encoche Mac musique, étagère AirDrop, "
                     "presse-papiers Mac, volume par application, alternative à NotchNook"),
        "og_title": "Dormer — ta notch, enfin réveillée",
        "og_desc": "Une Dynamic Island pour l'encoche de ton MacBook, avec un chat en pixels qui vit dedans.",
        "locale": "fr_FR",
        "app_desc": "Une Dynamic Island pour l'encoche de ton MacBook : musique, Shazam, étagère AirDrop, IA, alertes et un compagnon en pixels.",
        "offer": "Version gratuite, plus 14 jours d'essai gratuit de Dormer Pro",
        "film_name": "Dormer — deux minutes dans la notch",
        "film_desc": "Un film de 2 minutes qui montre Dormer sur un MacBook : musique, IA, widgets, messages et le chat en pixels qui vit dans l'encoche.",
    },
}


def strip(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def faq_items(page: str, lang: str):
    items = []
    for d in re.findall(r"<details>(.*?)</details>", page, re.S):
        q = re.search(rf'<summary>.*?<span lang="{lang}">(.*?)</span>', d, re.S)
        a = re.search(rf'<p>.*?<span lang="{lang}">(.*?)</span>', d, re.S)
        if q and a:
            items.append({"@type": "Question", "name": strip(q.group(1)),
                          "acceptedAnswer": {"@type": "Answer", "text": strip(a.group(1))}})
    return items


def alternates(key: str) -> str:
    p = PAGES[key]
    return "\n".join([
        f'<link rel="alternate" hreflang="en" href="{SITE}{p["en"]}">',
        f'<link rel="alternate" hreflang="fr" href="{SITE}{p["fr"]}">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}{p["en"]}">',
    ])


# Sends a visitor to the language they chose (or their browser's language on a
# first visit to the English page). Crawlers have no saved choice and an English
# browser, so they always get the page they asked for.
REDIRECT = """<script>(function(){var P=document.documentElement.lang,p=null;try{p=localStorage.getItem('lang')}catch(e){}
if(!p&&P==='en'&&/^fr/i.test(navigator.language||''))p='fr';
if(p&&p!==P&&location.protocol!=='file:'){var u={en:'/',fr:'/fr/'};var here=location.pathname;
if(here===u[P])location.replace(u[p]+location.hash);}})();</script>"""


def seo_block(page: str, lang: str) -> str:
    t = TEXT[lang]
    url = SITE + PAGES["home"][lang]
    graph = [
        {"@type": "SoftwareApplication", "name": "Dormer", "url": url, "image": f"{SITE}/icon.png",
         "operatingSystem": "macOS 14.2+", "applicationCategory": "UtilitiesApplication",
         "description": t["app_desc"], "downloadUrl": DOWNLOAD, "inLanguage": lang,
         "offers": [{"@type": "Offer", "price": "0", "priceCurrency": "EUR", "description": t["offer"]},
                    {"@type": "Offer", "name": "Dormer Pro", "price": f'{PRICES["Dormer"]["lifetime"]:.2f}',
                     "priceCurrency": PRICES["Dormer"]["currency"], "url": BUY}]},
        {"@type": "VideoObject", "name": t["film_name"], "description": t["film_desc"],
         "thumbnailUrl": f"{SITE}/film/poster.jpg", "uploadDate": FILM_DATE, "duration": "PT2M13S",
         "contentUrl": f"{SITE}/film/dormer.mp4", "embedUrl": f"{url}#film", "inLanguage": lang},
        {"@type": "FAQPage", "inLanguage": lang, "mainEntity": faq_items(page, lang)},
    ]
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    return f"<!--seo-->\n{alternates('home')}\n{REDIRECT}\n<script type=\"application/ld+json\">\n{ld}\n</script>\n<!--/seo-->"


def set_seo(page: str, lang: str) -> str:
    return re.sub(r"<!--seo-->.*?<!--/seo-->", lambda _: seo_block(page, lang), page, flags=re.S)


def meta(page: str, attr: str, name: str, value: str) -> str:
    pat = rf'(<meta {attr}="{re.escape(name)}" content=")[^"]*(">)'
    assert re.search(pat, page), name
    return re.sub(pat, lambda m: m.group(1) + html.escape(value, quote=True) + m.group(2), page, count=1)


def french(page: str) -> str:
    t = TEXT["fr"]
    s = page.replace('<html lang="en">', '<html lang="fr">', 1)
    s = re.sub(r"<title>.*?</title>", f"<title>{html.escape(t['title'], quote=False)}</title>", s, count=1)
    s = meta(s, "name", "description", t["desc"])
    s = meta(s, "name", "keywords", t["keywords"])
    s = meta(s, "property", "og:title", t["og_title"])
    s = meta(s, "property", "og:description", t["og_desc"])
    s = meta(s, "property", "og:url", f"{SITE}/fr/")
    s = s.replace(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/fr/">', 1)
    s = s.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="fr_FR">', 1)
    s = s.replace('<a class="lang" id="lang" href="/fr/" hreflang="fr" aria-label="Version française">FR</a>',
                  '<a class="lang" id="lang" href="/" hreflang="en" aria-label="English version">EN</a>', 1)
    # the French page sits one folder down: make asset paths absolute
    for a, b in [('href="favicon.png"', 'href="/favicon.png"'), ('src="icon.png"', 'src="/icon.png"'),
                 ('poster="film/poster.jpg"', 'poster="/film/poster.jpg"'), ('src="film/dormer.mp4"', 'src="/film/dormer.mp4"')]:
        s = s.replace(a, b)
    s = s.replace('href="/compare/"', 'href="/fr/compare/"')
    return set_seo(s, "fr")


# ───────────────────────── comparison page ("Comparatif") ─────────────────────────
# Facts about other apps come from their official websites, checked on CHECKED.
# "—" means "not mentioned on their site", never "proven missing": say so on the page.
CHECKED = {"en": "November 25, 2026", "fr": "25 novembre 2026"}
APPS = ["Dormer", "NotchNook", "Alcove", "DynamicLake", "DynamicHorizon", "Boring Notch", "Atoll"]
SOURCES = {"NotchNook": "https://lo.cafe/notchnook", "Alcove": "https://tryalcove.com",
           "DynamicLake": "https://www.dynamiclake.com", "DynamicHorizon": "https://www.dynamichorizon.app",
           "Boring Notch": "https://github.com/TheBoredTeam/boring.notch", "Atoll": "https://github.com/Ebullioscopic/Atoll"}
Y, N = True, False
# (key, values in APPS order). Text values are shown as-is.
MATRIX = [
    ("only", [
        ("pet",     [Y, N, N, N, N, N, N]),
        ("party",   [Y, N, N, N, N, N, N]),
        ("reply",   [Y, N, N, N, N, N, N]),
        ("codes",   [Y, N, N, N, N, N, N]),
        ("aiscreen",[Y, N, N, N, N, N, N]),
        ("shazam",  [Y, N, N, N, N, N, N]),
        ("mixvol",  [Y, N, N, N, N, N, N]),
    ]),
    ("common", [
        ("music",   [Y, Y, Y, Y, Y, Y, Y]),
        ("lyrics",  [Y, Y, N, N, Y, N, N]),
        ("shelf",   [Y, Y, N, Y, N, Y, N]),
        ("clip",    [Y, Y, N, N, N, N, Y]),
        ("notifs",  [Y, N, Y, Y, Y, N, N]),
        ("calls",   [Y, N, N, Y, N, N, N]),
        ("cal",     [Y, Y, N, Y, N, Y, Y]),
        ("timer",   [Y, Y, N, Y, Y, N, Y]),
    ]),
    ("price", [
        ("free",    [Y, N, N, N, N, Y, Y]),
        ("price",   ["$price"] * 7),
        ("trial",   ["14 d", "48 h", "72 h", "yes", N, "—", "—"]),
        ("macos",   ["14.2+", "14.6+", "15+", N, "14.6+", "14+", "14+"]),
    ]),
]

ALT = {
    "en": {
        "nav": "Compare", "nav_home": "Home",
        "title": "Mac notch apps compared: Dormer vs NotchNook, Alcove, DynamicLake, Boring Notch & Atoll",
        "desc": ("Dormer, NotchNook, Alcove, DynamicLake, DynamicHorizon, Boring Notch and Atoll side by side: "
                 "features, free versions, trials and what only Dormer does."),
        "h1": "Dormer next to the other notch apps.",
        "lead": ("Every notch app plays your music. Here's how the best-known ones compare, feature by feature, "
                 "and the seven things you'll only find in Dormer."),
        "groups": {"only": "Only in Dormer", "common": "What most of them do", "price": "Price and setup"},
        "rows": {"pet": "Pixel companion with a pet game", "party": "Listen together with nearby Macs",
                 "reply": "Reply to messages from the notch", "codes": "Verification codes, copied in one click",
                 "aiscreen": "AI that sees your screen (Claude, ChatGPT)", "shazam": "Shazam in the notch",
                 "mixvol": "A volume for every app",
                 "music": "Music controls", "lyrics": "Synced lyrics", "shelf": "File shelf & AirDrop",
                 "clip": "Clipboard history", "notifs": "Notifications in the notch", "calls": "Calls",
                 "cal": "Calendar", "timer": "Timer",
                 "free": "Free version", "price": "Price of the full version", "trial": "Free trial of the paid version", "macos": "Works from macOS"},
        "trial_words": {"14 d": "14 days", "yes": "Yes"},
        "yes": "Yes", "no": "Not mentioned",
        "note": ("Based on each app's official website, checked on {date}. A dash means the feature isn't mentioned there, "
                 "not that it can't exist. Spotted a mistake? Tell us on GitHub."),
        "price_note": ("Regular prices, without sales. Dormer, NotchNook and DynamicLake prices are checked automatically every day "
                       "(confirmed on {auto}); the others were checked by hand on {manual}."),
        "sources": "Sources",
        "only_h": "The seven things only Dormer does",
        "only": [("A pixel companion", "A cat (or dog, bunny, robot, ghost) lives in your notch. Feed it, level it up, play hide-and-seek, throw it a ball. You can turn it off."),
                 ("Listen together", "Friends nearby see your song in their notch and listen in sync, with Spotify or Apple Music. No server, no account."),
                 ("Reply from the notch", "A message lands in the notch: type your answer right there and send it, without opening Messages."),
                 ("Verification codes", "A code from a text or an email shows up in the notch. One click copies it."),
                 ("An AI that sees your screen", "Ask Claude or ChatGPT from the notch, with a screenshot attached so it knows what you mean. One click turns that off."),
                 ("Shazam", "What's this song? The notch listens and names it."),
                 ("A volume for every app", "Turn the browser down and keep the music up, right from the notch.")],
        "pick_h": "Which one should you pick?",
        "pick": ("If you want something free and open source with the basics, Boring Notch and Atoll are good picks. "
                 "If you want the most in your notch, plus a companion and the longest free trial of the paid apps, "
                 "try Dormer: the free version stays free, and every download includes 14 days of Pro."),
        "cta": "Download Dormer for Mac", "home": "Back to Dormer", "meta": "For MacBooks with a notch, on macOS 14.2 or later.",
        "lang_label": "FR", "lang_aria": "Version française", "download": "Download",
    },
    "fr": {
        "nav": "Comparatif", "nav_home": "Accueil",
        "title": "Comparatif des apps de notch pour Mac : Dormer, NotchNook, Alcove, DynamicLake, Boring Notch, Atoll",
        "desc": ("Dormer, NotchNook, Alcove, DynamicLake, DynamicHorizon, Boring Notch et Atoll côte à côte : "
                 "fonctions, versions gratuites, essais, et ce que seul Dormer fait."),
        "h1": "Dormer face aux autres apps de notch.",
        "lead": ("Toutes les apps de notch jouent ta musique. Voici comment les plus connues se comparent, fonction par fonction, "
                 "et les sept choses que tu ne trouveras que dans Dormer."),
        "groups": {"only": "Seulement dans Dormer", "common": "Ce que la plupart font", "price": "Prix et installation"},
        "rows": {"pet": "Compagnon en pixels avec un jeu", "party": "Écouter ensemble avec les Mac proches",
                 "reply": "Répondre aux messages depuis la notch", "codes": "Codes de vérification copiés en un clic",
                 "aiscreen": "IA qui voit ton écran (Claude, ChatGPT)", "shazam": "Shazam dans la notch",
                 "mixvol": "Un volume par app",
                 "music": "Commandes de musique", "lyrics": "Paroles synchronisées", "shelf": "Étagère de fichiers et AirDrop",
                 "clip": "Historique du presse-papiers", "notifs": "Notifications dans la notch", "calls": "Appels",
                 "cal": "Calendrier", "timer": "Minuteur",
                 "free": "Version gratuite", "price": "Prix de la version complète", "trial": "Essai gratuit de la version payante", "macos": "Marche à partir de macOS"},
        "trial_words": {"14 d": "14 jours", "yes": "Oui"},
        "yes": "Oui", "no": "Non mentionné",
        "note": ("D'après le site officiel de chaque app, consulté le {date}. Un tiret veut dire que la fonction n'y est pas mentionnée, "
                 "pas forcément qu'elle n'existe pas. Une erreur ? Dis-le-nous sur GitHub."),
        "price_note": ("Prix normaux, hors promotions. Les prix de Dormer, NotchNook et DynamicLake sont vérifiés automatiquement chaque jour "
                       "(confirmés le {auto}) ; les autres ont été relevés à la main le {manual}."),
        "sources": "Sources",
        "only_h": "Les sept choses que seul Dormer fait",
        "only": [("Un compagnon en pixels", "Un chat (ou chien, lapin, robot, fantôme) vit dans ta notch. Nourris-le, fais-le monter de niveau, jouez à cache-cache, lance-lui une balle. Tu peux le désactiver."),
                 ("Écouter ensemble", "Tes amis proches voient ton morceau dans leur notch et l'écoutent en même temps, avec Spotify ou Musique. Sans serveur, sans compte."),
                 ("Répondre depuis la notch", "Un message arrive dans la notch : tape ta réponse directement dedans et envoie, sans ouvrir Messages."),
                 ("Codes de vérification", "Un code reçu par SMS ou par mail s'affiche dans la notch. Un clic le copie."),
                 ("Une IA qui voit ton écran", "Pose ta question à Claude ou ChatGPT depuis la notch, avec une capture de l'écran pour qu'il comprenne. Un clic coupe ça."),
                 ("Shazam", "C'est quoi ce morceau ? La notch écoute et te le dit."),
                 ("Un volume par app", "Baisse le navigateur et garde la musique, directement depuis la notch.")],
        "pick_h": "Lequel choisir ?",
        "pick": ("Si tu veux du gratuit et open source avec l'essentiel, Boring Notch et Atoll sont de bons choix. "
                 "Si tu veux le plus de choses dans ta notch, un compagnon en prime et le plus long essai gratuit des apps payantes, "
                 "essaie Dormer : la version gratuite reste gratuite, et chaque téléchargement inclut 14 jours de Pro."),
        "cta": "Télécharger Dormer pour Mac", "home": "Retour à Dormer", "meta": "Pour MacBook avec encoche, sous macOS 14.2 ou plus récent.",
        "lang_label": "EN", "lang_aria": "English version", "download": "Télécharger",
    },
}

ALT_CSS = """:root{--sky:#1b2147;--sky2:#141936;--deep:#0f1330;--lamp:#ffcf70;--lamp-ink:#241c33;--ink:#f3ead8;--mist:#b3b8da;--faint:#8a91bb;--line:rgba(243,234,216,.13);--line2:rgba(243,234,216,.24);--serif:"Young Serif",Georgia,serif;--sans:"Figtree",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html{overflow-x:clip;background:var(--deep);scrollbar-color:#6b4a5a var(--deep)}
body{background:linear-gradient(180deg,var(--sky) 0,var(--sky) 900px,var(--sky2) 2200px,var(--deep) 100%);color:var(--ink);font:17px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
::selection{background:var(--lamp);color:var(--lamp-ink)}
:focus-visible{outline:2px solid var(--lamp);outline-offset:3px;border-radius:6px}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
.narrow{max-width:820px}
nav{position:sticky;top:0;z-index:5;background:rgba(27,33,71,.94);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;gap:16px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-family:var(--serif);font-size:21px}
.brand img{width:30px;height:30px;border-radius:8px}
.sp{margin-left:auto}
.lang{display:inline-block;border:1px solid var(--line2);border-radius:8px;padding:4px 9px;font-size:13px;font-weight:600;color:var(--mist)}
.lang:hover{color:var(--ink);border-color:var(--ink)}
.navlink{font-size:15px;font-weight:600;color:var(--mist)}
.navlink:hover,.navlink[aria-current]{color:var(--lamp)}
.btn{display:inline-flex;align-items:center;gap:9px;border-radius:12px;padding:14px 22px;font-weight:600;font-size:16px;background:var(--lamp);color:var(--lamp-ink);transition:background .2s,box-shadow .2s}
.btn:hover{background:#ffdb8f;box-shadow:0 10px 28px -8px rgba(255,207,112,.55)}
.btn.sm{padding:9px 15px;font-size:14.5px;border-radius:10px}
header{padding:84px 0 20px}
h1,h2{font-family:var(--serif);font-weight:400;letter-spacing:-.012em;text-wrap:balance}
h1{font-size:clamp(38px,5.8vw,68px);line-height:1.02;max-width:16ch}
.lead{color:var(--mist);font-size:19px;margin-top:20px;max-width:62ch}
section{padding:56px 0}
h2{font-size:clamp(28px,3.4vw,38px);line-height:1.12;margin-bottom:22px}
/* the matrix */
.tablewrap{position:relative;margin-top:44px;overflow-x:auto;border-radius:16px;border:1px solid var(--line)}
table.cmp{width:100%;min-width:900px;border-collapse:separate;border-spacing:0;font-size:15px}
.cmp th,.cmp td{padding:13px 12px;border-bottom:1px solid var(--line);text-align:center;vertical-align:middle}
.cmp thead th{font-weight:600;font-size:14.5px;color:var(--mist);padding-top:18px;padding-bottom:16px;position:sticky;top:0}
.cmp tbody th{text-align:left;font-weight:500;color:var(--ink);position:sticky;left:0;background:var(--sky);z-index:1;min-width:250px;box-shadow:1px 0 0 var(--line)}
.cmp thead th:first-child{position:sticky;left:0;background:var(--sky);z-index:2}
.cmp .us{background:rgba(255,207,112,.1)}
.cmp thead th.us{color:var(--lamp);font-family:var(--serif);font-weight:400;font-size:19px}
.cmp tr.grp th{background:var(--sky2);color:var(--lamp);font-family:var(--serif);font-weight:400;font-size:18px;padding-top:20px;text-align:left}
.cmp tr.grp td{background:var(--sky2)}
.cmp tr.grp td.us{background:rgba(255,207,112,.1)}
.cmp tr:last-child th,.cmp tr:last-child td{border-bottom:0}
.yes{display:inline-block;width:12px;height:7px;border-left:2.4px solid currentColor;border-bottom:2.4px solid currentColor;transform:translateY(-3px) rotate(-45deg);color:#8ee3b4}
.us .yes{color:var(--lamp)}
.no{color:rgba(243,234,216,.28)}
.txt{color:var(--mist);font-variant-numeric:tabular-nums}
.us .txt{color:var(--lamp);font-weight:600}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.note{color:var(--faint);font-size:14px;margin-top:16px;max-width:80ch}
.src{color:var(--faint);font-size:14px;margin-top:6px}
.src a{text-decoration:underline;text-underline-offset:3px}
.src a:hover{color:var(--ink)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:30px 48px}
.card{border-top:1px solid var(--line2);padding-top:18px}
.card h3{font-size:18px;font-weight:600;margin-bottom:6px}.card p{color:var(--mist);font-size:16px}
.pick p{color:var(--mist);max-width:65ch}
.final{text-align:center;padding:40px 0 110px}
.final .meta{color:var(--faint);font-size:14px;margin-top:16px}
footer{border-top:1px solid var(--line);padding:30px 0 44px;font-size:14.5px;color:var(--faint)}
footer .wrap{display:flex;gap:20px;flex-wrap:wrap}
footer a:hover{color:var(--ink)}
@media (max-width:640px){.cards{grid-template-columns:1fr}header{padding-top:56px}.wrap{padding:0 18px}.brand span{display:none}nav .wrap{gap:12px}.cmp tbody th{min-width:150px;font-size:14px}.cmp th,.cmp td{padding:11px 9px}}"""


def day(iso: str, lang: str) -> str:
    import datetime
    d = datetime.date.fromisoformat(iso)
    months = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
              "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]}
    m = months[lang][d.month - 1]
    return f"{m} {d.day}, {d.year}" if lang == "en" else f"{d.day} {m} {d.year}"


def alt_page(lang: str) -> str:
    t = ALT[lang]
    other = "fr" if lang == "en" else "en"
    url = SITE + PAGES["alt"][lang]
    home = PAGES["home"][lang]
    e = lambda x: html.escape(x, quote=False)
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": t["title"], "url": url,
                     "description": t["desc"], "inLanguage": lang,
                     "about": {"@type": "SoftwareApplication", "name": "Dormer", "url": SITE + home,
                               "operatingSystem": "macOS 14.2+", "applicationCategory": "UtilitiesApplication"}},
                    ensure_ascii=False)

    def cell(v, i):
        cls = ' class="us"' if i == 0 else ""
        if v == "$price":
            return f'<td{cls}><span class="txt">{e(price_text(APPS[i], lang))}</span></td>'
        if v is True:
            return f'<td{cls}><span class="yes" aria-hidden="true"></span><span class="sr">{t["yes"]}</span></td>'
        if v is False or v == "—":
            return f'<td{cls}><span class="no" aria-hidden="true">—</span><span class="sr">{t["no"]}</span></td>'
        return f'<td{cls}><span class="txt">{e(t["trial_words"].get(v, v))}</span></td>'

    head = '<th scope="col"><span class="sr">—</span></th>' + "".join(
        f'<th scope="col"{" class=\"us\"" if i == 0 else ""}>{e(a)}</th>' for i, a in enumerate(APPS))
    body = ""
    for g, rows in MATRIX:
        body += f'<tr class="grp"><th scope="rowgroup">{e(t["groups"][g])}</th>' + "".join(
            f'<td{" class=\"us\"" if i == 0 else ""}></td>' for i in range(len(APPS))) + "</tr>"
        for key, vals in rows:
            body += f'<tr><th scope="row">{e(t["rows"][key])}</th>' + "".join(cell(v, i) for i, v in enumerate(vals)) + "</tr>"
    only = "".join(f'<div class="card"><h3>{e(a)}</h3><p>{e(b)}</p></div>' for a, b in t["only"])
    sources = ", ".join(f'<a href="{u}" rel="nofollow noopener">{e(n)}</a>' for n, u in SOURCES.items())
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t['title'])}</title>
<meta name="description" content="{html.escape(t['desc'], quote=True)}">
<meta name="theme-color" content="#1b2147">
<link rel="icon" href="/favicon.png">
<link rel="canonical" href="{url}">
{alternates('alt')}
<meta property="og:title" content="{html.escape(t['title'], quote=True)}">
<meta property="og:description" content="{html.escape(t['desc'], quote=True)}">
<meta property="og:image" content="{SITE}/banner.png">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Dormer">
<meta property="og:locale" content="{TEXT[lang]['locale']}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{ld}
</script>
<link rel="preconnect" href="https://fonts.bunny.net">
<link rel="stylesheet" href="https://fonts.bunny.net/css?family=young-serif:400|figtree:400,500,600,700&display=swap">
<style>
{ALT_CSS}
</style>
</head>
<body>
<nav><div class="wrap">
  <a class="brand" href="{home}"><img src="/icon.png" alt=""><span>Dormer</span></a>
  <span class="sp"></span>
  <a class="lang" href="{PAGES['alt'][other]}" hreflang="{other}" aria-label="{t['lang_aria']}" onclick="try{{localStorage.setItem('lang','{other}')}}catch(e){{}}">{t['lang_label']}</a>
  <a class="navlink" href="{home}">{e(t['nav_home'])}</a>
  <a class="btn sm" href="{DOWNLOAD}">{e(t['download'])}</a>
</div></nav>
<header><div class="wrap">
  <h1>{e(t['h1'])}</h1>
  <p class="lead">{e(t['lead'])}</p>
  <div class="tablewrap" role="region" aria-label="{e(t['nav'])}" tabindex="0">
    <table class="cmp"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>
  </div>
  <p class="note">{e(t['note'].format(date=CHECKED[lang]))} {e(t['price_note'].format(auto=day(max(a['checked'] for a in PRICES.values() if a.get('sync')), lang), manual=day(min(a['checked'] for a in PRICES.values() if not a.get('sync')), lang)))}</p>
  <p class="src">{t['sources']}{' :' if lang == 'fr' else ':'} {sources}</p>
</div></header>
<main class="wrap narrow">
  <section><h2>{e(t['only_h'])}</h2><div class="cards">{only}</div></section>
  <section class="pick"><h2>{e(t['pick_h'])}</h2><p>{e(t['pick'])}</p></section>
  <div class="final">
    <a class="btn" href="{DOWNLOAD}">{e(t['cta'])}</a>
    <p class="meta">{e(t['meta'])}</p>
  </div>
</main>
<footer><div class="wrap">
  <span>© 2026 Dormer</span>
  <a href="{home}">{e(t['home'])}</a>
  <a href="https://github.com/Zerdoxy741/dormer">GitHub</a>
  <a href="{BUY}">Dormer Pro</a>
</div></footer>
</body>
</html>
"""


def sitemap() -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in PAGES.values():
        for lang in ("en", "fr"):
            out.append(f"  <url><loc>{SITE}{p[lang]}</loc><lastmod>{LASTMOD}</lastmod>")
            for l2 in ("en", "fr"):
                out.append(f'    <xhtml:link rel="alternate" hreflang="{l2}" href="{SITE}{p[l2]}"/>')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{p["en"]}"/>')
            out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def write(rel: str, content: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print("wrote", path.relative_to(ROOT.parent))


def main():
    src = (ROOT / "index.html").read_text()
    assert "<!--seo-->" in src, "docs/index.html needs a <!--seo--><!--/seo--> block in <head>"
    if '<meta property="og:locale"' not in src:
        src = src.replace('<meta property="og:site_name" content="Dormer">',
                          '<meta property="og:site_name" content="Dormer">\n<meta property="og:locale" content="en_US">', 1)
    src = set_pro_price(src)
    write("index.html", src)  # keep the source in sync with the price
    en = set_seo(src, "en")
    write("index.html", en)
    write("fr/index.html", french(en))
    write("compare/index.html", alt_page("en"))
    write("fr/compare/index.html", alt_page("fr"))
    write("sitemap.xml", sitemap())


if __name__ == "__main__":
    main()
