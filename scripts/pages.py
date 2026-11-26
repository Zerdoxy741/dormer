"""Pages Confidentialité, Mentions légales, Conditions d'utilisation et Versions (FR et EN), générées par build.py.

Le texte se modifie ici ; les fichiers de docs/ sont réécrits à chaque `python3 scripts/build.py`.
Le journal des versions vient de data/releases.json (mis à jour par release.sh dans le dépôt de l'app).
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://dormernotch.com"
UPDATED = {"en": "Updated November 26, 2026", "fr": "Mis à jour le 26 novembre 2026"}
CONTACT = '<a href="mailto:info@dormernotch.com">info@dormernotch.com</a>'
# Polices hébergées sur le site (docs/fonts/), déclarées en ligne : rien ne bloque l'affichage.
FONT_HEAD = ('<link rel="preload" href="/fonts/young-serif-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
             '<link rel="preload" href="/fonts/figtree-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
             '<link rel="preload" href="/fonts/figtree-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
             '<style>' + (Path(__file__).resolve().parent / "fonts.css").read_text().strip() + '</style>')
CERT_SHA256 = "01:19:CA:20:48:E5:6E:A9:2A:A3:A7:BF:A0:16:26:B9:9C:23:57:00:12:7B:69:78:B7:00:5A:7C:EC:6F:76:8C"
CERT_NAME = "Notchy Local Signing"
BREW = "brew install --cask zerdoxy741/dormer/dormer"
SOURCE = "https://github.com/Zerdoxy741/dormer/tree/main/source"
_PRO = json.loads((ROOT.parent / "data" / "prices.json").read_text())["apps"]["Dormer"]
PRICE = {"en": f"€{_PRO['lifetime']:.2f}".replace(".00", ""), "fr": f"{_PRO['lifetime']:.2f}".replace(".00", "").replace(".", ",") + "\u00a0€"}

PATHS = {
    "privacy": {"en": "/privacy/", "fr": "/fr/confidentialite/"},
    "legal": {"en": "/legal/", "fr": "/fr/mentions-legales/"},
    "terms": {"en": "/terms/", "fr": "/fr/conditions/"},
    "changelog": {"en": "/changelog/", "fr": "/fr/versions/"},
}

LABELS = {
    "privacy": {"en": "Privacy", "fr": "Confidentialité"},
    "legal": {"en": "Legal notice", "fr": "Mentions légales"},
    "terms": {"en": "Terms of use", "fr": "Conditions d'utilisation"},
    "changelog": {"en": "Versions", "fr": "Versions"},
}


def _css() -> str:
    src = (ROOT / "fr" / "compare" / "index.html").read_text()
    base = src[src.index(":root{"):src.index("/* the matrix */")]
    foot = src[src.index("footer{"):src.index("@media")]
    return base + foot + """.doc h2{margin-top:44px}.doc h2:first-child{margin-top:0}.doc h3{font-size:18px;font-weight:600;margin-top:22px}
.doc p,.doc li{color:var(--mist);max-width:68ch}.doc p+p{margin-top:12px}.doc ul{margin:10px 0 0 22px}.doc li{margin-top:6px}
.doc strong{color:var(--ink);font-weight:600}.doc a{text-decoration:underline;text-underline-offset:3px}.doc a:hover{color:var(--ink)}
.doc code{font-size:14px;background:rgba(243,234,216,.08);border-radius:6px;padding:2px 6px;word-break:break-all}
.doc pre{background:rgba(243,234,216,.06);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:10px;overflow-x:auto;font-size:14px;color:var(--ink)}
.updated{color:var(--faint);font-size:14px;margin-top:14px}
.rel{border-top:1px solid var(--line);padding-top:22px;margin-top:26px}.rel:first-of-type{border-top:0;margin-top:0;padding-top:0}
.rel h3{margin-top:0;font-family:var(--serif);font-weight:400;font-size:24px}.rel .when{color:var(--faint);font-size:14px;margin-top:2px}
.rel .sum{color:var(--faint);font-size:13.5px;margin-top:10px}
@media (max-width:640px){header{padding-top:56px}.wrap{padding:0 18px}.brand span{display:none}nav .wrap{gap:12px}}
"""


def _page(key: str, lang: str, title: str, desc: str, h1: str, lead: str, body: str) -> str:
    other = "fr" if lang == "en" else "en"
    home = "/" if lang == "en" else "/fr/"
    p = PATHS[key]
    footer = "".join(f'\n  <a href="{PATHS[k][lang]}">{LABELS[k][lang]}</a>' for k in PATHS if k != key)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Dormer</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="theme-color" content="#1b2147">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon-96.png?v=2" type="image/png" sizes="96x96">
<link rel="icon" href="/logo.svg?v=2" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<link rel="canonical" href="{SITE}{p[lang]}">
<link rel="alternate" hreflang="en" href="{SITE}{p['en']}">
<link rel="alternate" hreflang="fr" href="{SITE}{p['fr']}">
<link rel="alternate" hreflang="x-default" href="{SITE}{p['en']}">
{FONT_HEAD}
<style>
{_css()}</style>
</head>
<body>
<nav><div class="wrap">
  <a class="brand" href="{home}" aria-label="Dormer"><img src="/icon-64.png?v=2" alt="" width="32" height="32"><span>Dormer</span></a>
  <span class="sp"></span>
  <a class="lang" href="{p[other]}" hreflang="{other}" onclick="try{{localStorage.setItem('lang','{other}')}}catch(e){{}}">{other.upper()}</a>
  <a class="navlink" href="{home}">{"Home" if lang == "en" else "Accueil"}</a>
</div></nav>
<header><div class="wrap narrow">
  <h1>{h1}</h1>
  <p class="lead">{lead}</p>
  <p class="updated">{UPDATED[lang]}</p>
</div></header>
<main class="wrap narrow doc">
<section>
{body}
</section>
</main>
<footer><div class="wrap">
  <span>© 2026 Dormer</span>
  <a href="{home}">{"Back to Dormer" if lang == "en" else "Retour à Dormer"}</a>{footer}
  <a href="https://github.com/Zerdoxy741/dormer">GitHub</a>
</div></footer>
</body>
</html>
"""


# ---------------------------------------------------------------- Confidentialité

PRIVACY = {
"fr": f"""<h2>L'essentiel</h2>
<p>Pour toute question sur tes données : {CONTACT}.</p>
<p>Dormer n'a pas de compte et pas de publicité. Il ne te suit pas : la seule chose qu'il envoie de lui-même, ce sont des <a href="#statistiques">compteurs anonymes</a> (« une installation de plus », « une mise à jour de plus », « un Mac de plus a utilisé Dormer aujourd'hui »), sans aucun identifiant, et tu peux les couper. Presque tout reste sur ton Mac. Quand une fonction a besoin d'Internet, elle n'envoie que le strict nécessaire, et seulement si tu l'as activée.</p>

<h2>Les autorisations demandées</h2>
<p>macOS te demande chaque autorisation au moment où une fonction en a besoin. Tu peux en refuser : seules les fonctions concernées ne marcheront pas.</p>
<ul>
<li><strong>Accessibilité :</strong> pour afficher le volume et la luminosité dans la notch à la place des fenêtres de macOS, et suivre les appels et ChatGPT. Dormer ne lit pas ce que tu tapes.</li>
<li><strong>Son du Mac :</strong> pour animer l'égaliseur au rythme de la musique. Le son est analysé en direct, rien n'est enregistré.</li>
<li><strong>Musique et Spotify :</strong> pour afficher et contrôler le morceau en cours.</li>
<li><strong>Calendrier et Rappels :</strong> pour tes prochains événements et pour reporter un rappel depuis la notch. Rien ne quitte ton Mac.</li>
<li><strong>Micro (facultatif) :</strong> seulement pour Shazam, quelques secondes, quand tu le demandes.</li>
<li><strong>Position (facultatif) :</strong> pour la météo, arrondie à environ 1 km.</li>
<li><strong>Bluetooth et réseau local :</strong> pour l'animation de tes AirPods et pour trouver les Mac proches qui ont Dormer (Écouter ensemble).</li>
<li><strong>Enregistrement de l'écran (facultatif) :</strong> seulement si tu actives « voir l'écran » quand tu poses une question à Claude ou ChatGPT, ou « Il regarde ton écran » pour le compagnon. Dans ce second cas, l'image est décrite par l'IA d'Apple directement sur ton Mac, puis oubliée : rien n'est envoyé. Les deux options sont désactivées par défaut.</li>
</ul>

<h2>Le presse-papiers</h2>
<p>L'historique du presse-papiers reste en mémoire : il n'est jamais écrit sur le disque, jamais envoyé, et il disparaît quand tu quittes Dormer. Il ignore les mots de passe : les copies que les gestionnaires de mots de passe marquent comme confidentielles, et tout ce qui est copié depuis le Trousseau, l'app Mots de passe, 1Password, Bitwarden, KeePassXC, Dashlane, LastPass, Proton Pass et quelques autres. Tu peux le désactiver dans les réglages.</p>

<h2>Le diagnostic</h2>
<p>Quand tu cliques sur <strong>Réglages › Général › Signaler un problème…</strong>, puis sur <strong>Envoyer</strong>, Dormer envoie un diagnostic à son créateur. Rien ne part sans ce clic, et tu peux relire tout le contenu avant l'envoi.</p>
<p><strong>Ce qui part :</strong></p>
<ul>
<li>ce que tu écris, et ton prénom si tu le donnes (c'est facultatif) ;</li>
<li>les versions de Dormer et de macOS, le modèle du Mac, la langue ;</li>
<li>les autorisations accordées à Dormer (Accessibilité, Calendrier) ;</li>
<li>les réglages de Dormer : nombres, interrupteurs et petits mots-clés seulement ;</li>
<li>les derniers journaux de Dormer et le résumé de son dernier plantage, s'il y en a un.</li>
</ul>
<p><strong>Ce qui est retiré avant l'envoi :</strong> les noms de fichiers, les chemins, ton nom d'utilisateur et ton nom complet, les adresses e-mail, les liens, les adresses Bluetooth et IP, les prénoms dans les noms d'appareils (« AirPods de… »), le contenu de tes images et du texte lu à l'écran, le contenu du presse-papiers, et les textes libres des réglages (ville, morceau, nom du compagnon…). <a href="{SOURCE}">Le code qui fait ce nettoyage est public.</a></p>
<p><strong>La signature :</strong> chaque diagnostic porte une signature comme <code>D-7F3A-91C2</code>. Elle est tirée au hasard sur ton Mac et sert seulement à regrouper tes diagnostics. Elle n'a aucun lien avec ton Mac ni avec toi.</p>
<p><strong>Où il va :</strong> le diagnostic passe par <code>diag.dormernotch.com</code>, un petit service hébergé chez Cloudflare qui ne garde rien et ne journalise pas le contenu. Il est ensuite rangé dans un dépôt privé sur GitHub (GitHub, Inc., États-Unis), que seul le créateur de Dormer peut lire. Ton adresse IP sert seulement à limiter le nombre d'envois par minute, contre le spam. Elle n'est pas enregistrée avec le diagnostic.</p>
<p><strong>Combien de temps :</strong> chaque diagnostic est effacé automatiquement un an après son envoi, ou plus tôt si tu le demandes.</p>
<p><strong>Pourquoi :</strong> pour comprendre et corriger le problème que tu signales. C'est la seule utilisation, avec ton accord, que tu donnes en cliquant sur Envoyer.</p>

<h2 id="statistiques">Statistiques anonymes</h2>
<p>Pour savoir combien de personnes utilisent Dormer, l'app envoie à <code>diag.dormernotch.com</code> :</p>
<ul>
<li>au tout premier lancement : « installé », avec la version de Dormer et de macOS ;</li>
<li>au premier lancement après une mise à jour : « mis à jour », avec la nouvelle version ;</li>
<li>au plus une fois par jour où tu utilises Dormer : « actif aujourd'hui », avec les mêmes versions ;</li>
<li>si tu réponds à la question « Tout marche bien ? » posée une seule fois après ton premier jour : 👍 ou 👎, avec la version de Dormer.</li>
</ul>
<p><strong>Rien d'autre :</strong> pas d'identifiant, pas de numéro de série, pas de nom, pas de réglages. Le service ne fait qu'ajouter 1 à un compteur du jour (par exemple « 26 novembre : 12 Mac actifs »). Ton adresse IP sert seulement à limiter les envois contre le spam et n'est pas enregistrée. Il est donc impossible de savoir qui a envoyé quoi, ni de relier deux jours entre eux. <a href="https://github.com/Zerdoxy741/dormer/tree/main/source">Le code est public.</a></p>
<p><strong>Pour couper :</strong> <strong>Réglages › Général › Envoyer des statistiques anonymes</strong>.</p>

<h2>Le site dormernotch.com</h2>
<p>Le site utilise Cloudflare Web Analytics pour compter ses visites : nombre de pages vues, pays, navigateur, site d'où vient le visiteur. Il n'y a ni cookie ni suivi d'une page à l'autre ou d'un site à l'autre, et aucune donnée n'est utilisée pour te reconnaître ni pour de la publicité. On ne voit que des totaux.</p>

<h2>Les fonctions qui utilisent Internet</h2>
<ul>
<li><strong>Mises à jour :</strong> Dormer demande à GitHub s'il existe une nouvelle version, et n'installe une mise à jour que si elle est signée avec le même certificat que l'app installée.</li>
<li><strong>Licence Pro :</strong> ta clé de licence est vérifiée auprès de Polar, qui gère les achats.</li>
<li><strong>Météo :</strong> la position approximative du Mac (à environ 1 km près) ou le nom de la ville est envoyé à Open-Meteo.</li>
<li><strong>Paroles et pochettes :</strong> le titre et l'artiste du morceau sont envoyés à lrclib.net et à la recherche iTunes d'Apple.</li>
<li><strong>Shazam :</strong> une empreinte du son, et non l'enregistrement, est envoyée à Shazam (Apple) pour reconnaître le morceau.</li>
<li><strong>Poser une question à Claude ou ChatGPT :</strong> la question part par l'outil Claude Code ou ChatGPT installé sur ton Mac, avec ton propre compte. Dormer n'a pas de serveur entre les deux. Une capture de l'écran n'est jointe que si tu as activé « voir l'écran ».</li>
<li><strong>Écouter ensemble :</strong> les Mac se parlent directement, chiffrés, sur le réseau local ou en Bluetooth. Aucun serveur n'est utilisé.</li>
</ul>

<h2>Tes droits</h2>
<p>Tu peux demander à voir, corriger ou effacer tes diagnostics à tout moment. Écris à {CONTACT} en donnant ta signature (affichée dans la fenêtre du diagnostic). Pour obtenir une nouvelle signature, efface les réglages de Dormer. Tu peux aussi adresser une réclamation à la CNIL.</p>
<p>Le responsable de ces données est l'éditeur de Dormer : voir les <a href="{PATHS['legal']['fr']}">mentions légales</a>.</p>""",

"en": f"""<h2>The short version</h2>
<p>Questions about your data: {CONTACT}.</p>
<p>Dormer has no account and no ads. It doesn't track you: the only thing it sends on its own is <a href="#statistics">anonymous counts</a> ("one more install", "one more update", "one more Mac used Dormer today"), with no identifier, and you can turn them off. Almost everything stays on your Mac. When a feature needs the internet, it sends only what it needs, and only if you turned it on.</p>

<h2>Permissions</h2>
<p>macOS asks for each permission when a feature needs it. You can say no: only the features that need it won't work.</p>
<ul>
<li><strong>Accessibility:</strong> to show volume and brightness in the notch instead of macOS's own overlays, and to follow calls and ChatGPT. Dormer doesn't read what you type.</li>
<li><strong>Mac's sound:</strong> to move the equalizer with the music. The sound is analyzed live; nothing is recorded.</li>
<li><strong>Music and Spotify:</strong> to show and control the current song.</li>
<li><strong>Calendar and Reminders:</strong> for your next events and to snooze a reminder from the notch. Nothing leaves your Mac.</li>
<li><strong>Microphone (optional):</strong> only for Shazam, for a few seconds, when you ask.</li>
<li><strong>Location (optional):</strong> for the weather, rounded to about 1 km.</li>
<li><strong>Bluetooth and local network:</strong> for the AirPods animation and to find nearby Macs running Dormer (Listen together).</li>
<li><strong>Screen recording (optional):</strong> only if you turn on "see the screen" when asking Claude or ChatGPT, or "It looks at your screen" for the companion. In that second case, Apple's on-device AI describes the image on your Mac, then forgets it: nothing is sent. Both options are off by default.</li>
</ul>

<h2>Clipboard</h2>
<p>Clipboard history stays in memory: it's never written to disk, never sent, and it's gone when you quit Dormer. It skips passwords: copies that password managers mark as concealed, and anything copied from Keychain Access, the Passwords app, 1Password, Bitwarden, KeePassXC, Dashlane, LastPass, Proton Pass and a few others. You can turn it off in settings.</p>

<h2>Diagnostics</h2>
<p>When you click <strong>Settings › General › Report a problem…</strong> and then <strong>Send</strong>, Dormer sends a diagnostic to its creator. Nothing leaves without that click, and you can read everything before it's sent.</p>
<p><strong>What's sent:</strong></p>
<ul>
<li>what you write, and your first name if you give it (optional);</li>
<li>Dormer and macOS versions, Mac model, language;</li>
<li>permissions granted to Dormer (Accessibility, Calendar);</li>
<li>Dormer's settings: numbers, switches and short keywords only;</li>
<li>Dormer's recent logs and a summary of its last crash, if any.</li>
</ul>
<p><strong>Removed before sending:</strong> file names, paths, your user name and full name, email addresses, links, Bluetooth and IP addresses, first names in device names ("Anna's AirPods"), the content of your images and of on-screen text, clipboard content, and free text in settings (city, song, companion name…). <a href="{SOURCE}">The code that does this cleaning is public.</a></p>
<p><strong>The signature:</strong> each diagnostic carries a signature like <code>D-7F3A-91C2</code>. It's drawn at random on your Mac and only groups your diagnostics together. It has no link to your Mac or to you.</p>
<p><strong>Where it goes:</strong> the diagnostic passes through <code>diag.dormernotch.com</code>, a small service hosted by Cloudflare that keeps nothing and doesn't log the content. It's then stored in a private GitHub repository (GitHub, Inc., United States) that only Dormer's creator can read. Your IP address is only used to limit sends per minute against spam. It isn't stored with the diagnostic.</p>
<p><strong>How long:</strong> each diagnostic is deleted automatically one year after it was sent, or sooner if you ask.</p>
<p><strong>Why:</strong> to understand and fix the problem you report. That's its only use, with the consent you give by clicking Send.</p>

<h2 id="statistics">Anonymous statistics</h2>
<p>To know how many people use Dormer, the app sends to <code>diag.dormernotch.com</code>:</p>
<ul>
<li>on the very first launch: "installed", with the Dormer and macOS versions;</li>
<li>on the first launch after an update: "updated", with the new version;</li>
<li>at most once per day you use Dormer: "active today", with the same versions;</li>
<li>if you answer the "Is everything working?" question, asked once after your first day: 👍 or 👎, with the Dormer version.</li>
</ul>
<p><strong>Nothing else:</strong> no identifier, no serial number, no name, no settings. The service only adds 1 to a counter for the day (for example "November 26: 12 active Macs"). Your IP address is only used to limit sends against spam and isn't stored. So there is no way to know who sent what, or to link two days together. <a href="https://github.com/Zerdoxy741/dormer/tree/main/source">The code is public.</a></p>
<p><strong>To turn it off:</strong> <strong>Settings › General › Send anonymous statistics</strong>.</p>

<h2>The dormernotch.com website</h2>
<p>The website uses Cloudflare Web Analytics to count visits: page views, country, browser, referring site. There are no cookies and no tracking across pages or sites, and no data is used to recognize you or for ads. Only totals are visible.</p>

<h2>Features that use the internet</h2>
<ul>
<li><strong>Updates:</strong> Dormer asks GitHub whether a new version exists, and only installs an update signed with the same certificate as the installed app.</li>
<li><strong>Pro license:</strong> your license key is checked with Polar, which handles purchases.</li>
<li><strong>Weather:</strong> the Mac's approximate location (to about 1 km) or the city name is sent to Open-Meteo.</li>
<li><strong>Lyrics and artwork:</strong> the song title and artist are sent to lrclib.net and Apple's iTunes search.</li>
<li><strong>Shazam:</strong> a sound fingerprint, not the recording, is sent to Shazam (Apple) to recognize the song.</li>
<li><strong>Asking Claude or ChatGPT:</strong> the question goes through the Claude Code or ChatGPT tool installed on your Mac, with your own account. Dormer has no server in between. A screenshot is attached only if you turned on "see the screen".</li>
<li><strong>Listen together:</strong> Macs talk directly, encrypted, over the local network or Bluetooth. No server is used.</li>
</ul>

<h2>Your rights</h2>
<p>You can ask to see, correct or delete your diagnostics at any time. Email {CONTACT} with your signature (shown in the diagnostic window). To get a new signature, reset Dormer's settings. You can also complain to your data protection authority.</p>
<p>The controller of this data is Dormer's publisher: see the <a href="{PATHS['legal']['en']}">legal notice</a>.</p>""",
}

# ---------------------------------------------------------------- Mentions légales

LEGAL = {
"fr": f"""<h2>Éditeur</h2>
<p><strong>Yanis Ziani</strong>, particulier, France.<br>Contact : {CONTACT}</p>
<p>Directeur de la publication : Yanis Ziani.</p>

<h2>Hébergement</h2>
<p><strong>Site dormernotch.com et service de diagnostic :</strong> Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, États-Unis.</p>
<p><strong>Téléchargements et code public :</strong> GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis.</p>

<h2>Ventes de Dormer Pro</h2>
<p>Les achats de Dormer Pro sont encaissés par Polar (polar.sh), qui agit comme revendeur : c'est Polar qui facture, perçoit la TVA et gère les remboursements, selon ses propres conditions affichées au moment de l'achat. Voir aussi les <a href="{PATHS['terms']['fr']}">conditions d'utilisation</a>.</p>

<h2>Données personnelles</h2>
<p>Voir la page <a href="{PATHS['privacy']['fr']}">Confidentialité</a>.</p>

<h2>Propriété intellectuelle</h2>
<p>Le nom Dormer, son icône, l'application et le contenu de ce site appartiennent à Yanis Ziani, sauf mention contraire. Le code publié dans le <a href="{SOURCE}">dossier source</a> est sous licence MIT.</p>""",

"en": f"""<h2>Publisher</h2>
<p><strong>Yanis Ziani</strong>, individual, France.<br>Contact: {CONTACT}</p>
<p>Publication director: Yanis Ziani.</p>

<h2>Hosting</h2>
<p><strong>dormernotch.com and the diagnostics service:</strong> Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, United States.</p>
<p><strong>Downloads and public code:</strong> GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, United States.</p>

<h2>Dormer Pro sales</h2>
<p>Dormer Pro purchases are processed by Polar (polar.sh), acting as reseller: Polar invoices, collects VAT and handles refunds, under its own terms shown at checkout. See also the <a href="{PATHS['terms']['en']}">terms of use</a>.</p>

<h2>Personal data</h2>
<p>See the <a href="{PATHS['privacy']['en']}">Privacy</a> page.</p>

<h2>Intellectual property</h2>
<p>The Dormer name, its icon, the app and this site's content belong to Yanis Ziani unless stated otherwise. The code published in the <a href="{SOURCE}">source folder</a> is MIT-licensed.</p>""",
}

# ---------------------------------------------------------------- Conditions d'utilisation

TERMS = {
"fr": f"""<h2>L'essentiel</h2>
<p>En installant ou en utilisant Dormer, tu acceptes ces conditions. Elles sont courtes : Dormer est gratuit, Dormer Pro s'achète une seule fois, et tu peux arrêter de l'utiliser quand tu veux. Une question : {CONTACT}.</p>

<h2>Qui fournit Dormer</h2>
<p>Dormer est créé et publié par Yanis Ziani, particulier en France (voir les <a href="{PATHS['legal']['fr']}">mentions légales</a>).</p>

<h2>Dormer gratuit et Dormer Pro</h2>
<ul>
<li><strong>Gratuit :</strong> la notch, la musique, le calendrier, la météo et les autres fonctions de base restent gratuites, sans limite de durée.</li>
<li><strong>Essai :</strong> à la première installation, toutes les fonctions Pro sont ouvertes pendant 14 jours, sans carte bancaire. À la fin de l'essai, les fonctions Pro se mettent en pause ; tes réglages sont gardés.</li>
<li><strong>Dormer Pro :</strong> {PRICE['fr']}, payé une seule fois, sans abonnement. Le prix affiché au moment de l'achat fait foi.</li>
<li><strong>Mises à jour :</strong> les versions publiées après ton achat restent incluses, sans nouveau paiement.</li>
</ul>

<h2>L'achat</h2>
<p>Les achats sont encaissés par <strong>Polar</strong> (polar.sh), qui agit comme revendeur officiel : Polar établit la facture, perçoit la TVA et traite les remboursements, selon ses propres conditions affichées au moment du paiement. Si tu as un problème avec un achat, écris aussi à {CONTACT} : je t'aiderai à le régler.</p>

<h2>Ta clé de licence</h2>
<ul>
<li>Après l'achat, tu reçois une clé de licence par e-mail. Elle est personnelle : tu peux l'utiliser sur tes propres Mac, dans la limite indiquée au moment de l'achat.</li>
<li>Tu ne peux pas la revendre, la partager publiquement ni la distribuer.</li>
<li>Pour changer de Mac, clique sur « Retirer de ce Mac » dans les réglages de Dormer, puis active la clé sur le nouveau.</li>
<li>Une clé obtenue par fraude, ou remboursée, peut être désactivée.</li>
</ul>

<h2>Ce que tu peux faire avec Dormer</h2>
<p>Tu peux utiliser Dormer sur tes Mac, pour un usage personnel ou professionnel. Tu ne peux pas contourner le système de licence, ni revendre ou redistribuer l'app modifiée en la présentant comme Dormer. Le code publié dans le <a href="{SOURCE}">dossier source</a> reste sous licence MIT, qui a ses propres règles.</p>

<h2>Les services d'autres sociétés</h2>
<p>Certaines fonctions s'appuient sur des services tiers que tu choisis d'utiliser : Spotify et Musique d'Apple, Shazam, la météo, ChatGPT et Claude (avec ton propre compte), Polar pour les achats. Ces services ont leurs propres conditions, et Dormer n'est affilié à aucun d'eux. Les fonctions d'IA du compagnon utilisent l'IA d'Apple directement sur ton Mac : rien n'est envoyé. Le détail des données est sur la page <a href="{PATHS['privacy']['fr']}">Confidentialité</a>.</p>

<h2>Garantie et responsabilité</h2>
<p>Dormer est fourni tel quel, par une seule personne. Je fais de mon mieux pour qu'il marche bien et sans danger, mais je ne peux pas garantir qu'il sera toujours sans erreur, ni qu'il marchera avec toutes les futures versions de macOS. Dans la limite permise par la loi, ma responsabilité est limitée au montant que tu as payé pour Dormer Pro. Rien dans ces conditions ne retire les droits que la loi te donne en tant que consommateur.</p>

<h2>Changements</h2>
<p>Ces conditions peuvent évoluer, par exemple si une fonction change. La date en haut de la page indique la dernière version. Un changement ne retire jamais ce que tu as déjà acheté.</p>

<h2>Droit applicable</h2>
<p>Ces conditions sont soumises au droit français. En cas de désaccord, écris d'abord à {CONTACT} pour trouver une solution à l'amiable. Si tu habites dans l'Union européenne, tu gardes les protections de la loi de ton pays.</p>""",

"en": f"""<h2>The short version</h2>
<p>By installing or using Dormer, you agree to these terms. They're short: Dormer is free, Dormer Pro is a one-time purchase, and you can stop using it whenever you like. Questions: {CONTACT}.</p>

<h2>Who provides Dormer</h2>
<p>Dormer is made and published by Yanis Ziani, an individual in France (see the <a href="{PATHS['legal']['en']}">legal notice</a>).</p>

<h2>Free Dormer and Dormer Pro</h2>
<ul>
<li><strong>Free:</strong> the notch, music, calendar, weather and the other core features stay free, with no time limit.</li>
<li><strong>Trial:</strong> on first install, every Pro feature is open for 14 days, no card needed. When the trial ends, Pro features pause; your settings are kept.</li>
<li><strong>Dormer Pro:</strong> {PRICE['en']}, paid once, no subscription. The price shown at checkout is the one that applies.</li>
<li><strong>Updates:</strong> versions released after your purchase stay included, at no extra cost.</li>
</ul>

<h2>Buying</h2>
<p>Purchases are processed by <strong>Polar</strong> (polar.sh), acting as Merchant of Record: Polar issues the invoice, collects VAT and handles refunds, under its own terms shown at checkout. If you have a problem with a purchase, also write to {CONTACT} and I'll help sort it out.</p>

<h2>Your license key</h2>
<ul>
<li>After buying, you get a license key by email. It's personal: you can use it on your own Macs, up to the limit shown at checkout.</li>
<li>You can't resell it, share it publicly or distribute it.</li>
<li>To move to a new Mac, click “Remove from this Mac” in Dormer's settings, then activate the key on the new one.</li>
<li>A key obtained by fraud, or refunded, may be deactivated.</li>
</ul>

<h2>What you can do with Dormer</h2>
<p>You can use Dormer on your Macs, for personal or work use. You can't bypass the license system, or resell or redistribute a modified app presented as Dormer. The code published in the <a href="{SOURCE}">source folder</a> stays under the MIT license, which has its own rules.</p>

<h2>Other companies' services</h2>
<p>Some features rely on third-party services you choose to use: Spotify and Apple Music, Shazam, weather, ChatGPT and Claude (with your own account), and Polar for purchases. These services have their own terms, and Dormer isn't affiliated with any of them. The companion's AI features use Apple's on-device AI on your Mac: nothing is sent. Data details are on the <a href="{PATHS['privacy']['en']}">Privacy</a> page.</p>

<h2>Warranty and liability</h2>
<p>Dormer is provided as is, by one person. I do my best to make it work well and safely, but I can't promise it will always be free of bugs, or that it will work with every future macOS version. To the extent the law allows, my liability is limited to what you paid for Dormer Pro. Nothing in these terms takes away the rights the law gives you as a consumer.</p>

<h2>Changes</h2>
<p>These terms may change, for example when a feature changes. The date at the top of the page shows the latest version. A change never takes away something you've already bought.</p>

<h2>Governing law</h2>
<p>These terms are governed by French law. If there's a disagreement, write to {CONTACT} first so we can settle it amicably. If you live in the European Union, you keep the protections of your own country's law.</p>""",
}

# ---------------------------------------------------------------- Versions et empreintes

VERIFY = {
"fr": f"""<h2>Vérifier ton téléchargement</h2>
<p>Dormer n'est pas notarisé par Apple : c'est pour ça que macOS affiche un avertissement à la première ouverture. Voici comment vérifier que ton fichier vient bien de son créateur et n'a pas été modifié.</p>
<h3>1. L'empreinte du fichier</h3>
<p>Dans le Terminal, dans le dossier où se trouve le fichier :</p>
<pre>shasum -a 256 Dormer.zip</pre>
<p>Le résultat doit être identique à l'empreinte SHA-256 de ta version ci-dessous. Elle est aussi écrite dans les notes de la version sur GitHub.</p>
<h3>2. Le certificat de signature</h3>
<p>Toutes les versions sont signées avec le même certificat, <strong>{CERT_NAME}</strong>. Son empreinte SHA-256 :</p>
<p><code>{CERT_SHA256}</code></p>
<p>Pour la comparer :</p>
<pre>codesign -d --extract-certificates=/tmp/dormer /Applications/Dormer.app
openssl x509 -inform der -in /tmp/dormer0 -noout -fingerprint -sha256</pre>
<p>Dormer fait lui-même cette vérification à chaque mise à jour : il refuse toute nouvelle version qui n'est pas signée avec ce certificat.</p>
<h3>Avec Homebrew</h3>
<pre>{BREW}</pre>
<p>Homebrew vérifie l'empreinte du fichier pour toi. L'avertissement de macOS apparaît quand même à la première ouverture.</p>
<h2>Toutes les versions</h2>""",

"en": f"""<h2>Check your download</h2>
<p>Dormer isn't notarized by Apple: that's why macOS shows a warning the first time you open it. Here's how to check that your file comes from its creator and hasn't been changed.</p>
<h3>1. The file's fingerprint</h3>
<p>In Terminal, in the folder that holds the file:</p>
<pre>shasum -a 256 Dormer.zip</pre>
<p>The result must match the SHA-256 of your version below. It's also written in the version's notes on GitHub.</p>
<h3>2. The signing certificate</h3>
<p>Every version is signed with the same certificate, <strong>{CERT_NAME}</strong>. Its SHA-256 fingerprint:</p>
<p><code>{CERT_SHA256}</code></p>
<p>To compare it:</p>
<pre>codesign -d --extract-certificates=/tmp/dormer /Applications/Dormer.app
openssl x509 -inform der -in /tmp/dormer0 -noout -fingerprint -sha256</pre>
<p>Dormer runs this check itself on every update: it refuses any new version not signed with this certificate.</p>
<h3>With Homebrew</h3>
<pre>{BREW}</pre>
<p>Homebrew checks the file's fingerprint for you. macOS still shows its warning the first time you open it.</p>
<h2>All versions</h2>""",
}


def _day(iso: str, lang: str) -> str:
    import datetime
    d = datetime.date.fromisoformat(iso)
    months = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
              "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]}
    m = months[lang][d.month - 1]
    return f"{m} {d.day}, {d.year}" if lang == "en" else f"{d.day} {m} {d.year}"


def _releases(lang: str) -> str:
    path = ROOT.parent / "data" / "releases.json"
    rels = json.loads(path.read_text()) if path.exists() else []
    out = []
    for r in rels:
        lines = [l.strip() for l in r["notes"].splitlines() if l.strip()]
        bullets = [l.lstrip("•-* ").replace("**", "") for l in lines if l[:1] in "•-*"]
        intro = [l for l in lines if l[:1] not in "•-*" and not l.lower().startswith(("nouveautés", "what's new"))]
        items = bullets or intro
        body = "<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>" if items else ""
        sha = (f'<p class="sum">SHA-256 : <code>{r["sha256"]}</code></p>' if lang == "fr"
               else f'<p class="sum">SHA-256: <code>{r["sha256"]}</code></p>') if r.get("sha256") else ""
        vt = (f'<p class="sum"><a href="{r["virustotal"]}">{"Analyse antivirus (VirusTotal)" if lang == "fr" else "Antivirus scan (VirusTotal)"}</a></p>'
              if r.get("virustotal") else "")
        out.append(f'<div class="rel"><h3>Dormer {html.escape(r["version"])}</h3>'
                   f'<p class="when">{_day(r["date"], lang)} · <a href="{r["url"]}">GitHub</a></p>{body}{sha}{vt}</div>')
    if not out:
        out.append("<p>—</p>")
    note = ("<p>Les notes des versions sont écrites en français.</p>" if lang == "en" else "")
    return note + "\n".join(out)


def build(write):
    for lang in ("en", "fr"):
        fr = lang == "fr"
        write(PATHS["privacy"][lang].strip("/") + "/index.html", _page(
            "privacy", lang, LABELS["privacy"][lang],
            "Ce que Dormer envoie, ce qu'il garde sur ton Mac, ses autorisations et le diagnostic." if fr else
            "What Dormer sends, what stays on your Mac, its permissions and diagnostics.",
            LABELS["privacy"][lang],
            "Dormer garde presque tout sur ton Mac. Voici exactement ce qui en sort, et quand." if fr else
            "Dormer keeps almost everything on your Mac. Here is exactly what leaves it, and when.",
            PRIVACY[lang]))
        write(PATHS["legal"][lang].strip("/") + "/index.html", _page(
            "legal", lang, LABELS["legal"][lang],
            "Éditeur, hébergement et ventes de Dormer." if fr else "Dormer's publisher, hosting and sales.",
            LABELS["legal"][lang],
            "Qui publie Dormer, où il est hébergé et qui gère les ventes." if fr else
            "Who publishes Dormer, where it's hosted and who handles sales.",
            LEGAL[lang]))
        write(PATHS["terms"][lang].strip("/") + "/index.html", _page(
            "terms", lang, LABELS["terms"][lang],
            "Les règles d'utilisation de Dormer et de Dormer Pro : essai, achat, licence, garantie." if fr else
            "The rules for using Dormer and Dormer Pro: trial, purchase, license, warranty.",
            LABELS["terms"][lang],
            "Dormer est gratuit ; Dormer Pro s'achète une fois. Voici les règles, en clair." if fr else
            "Dormer is free; Dormer Pro is bought once. Here are the rules, in plain words.",
            TERMS[lang]))
        write(PATHS["changelog"][lang].strip("/") + "/index.html", _page(
            "changelog", lang, "Versions et empreintes" if fr else "Versions and checksums",
            "Ce qui change dans chaque version de Dormer, avec l'empreinte SHA-256 pour vérifier ton téléchargement." if fr else
            "What changed in each Dormer version, with the SHA-256 to check your download.",
            "Versions" if not fr else "Versions",
            "Ce qui change à chaque version, et comment vérifier ton téléchargement." if fr else
            "What changed in each version, and how to check your download.",
            VERIFY[lang] + "\n" + _releases(lang)))
