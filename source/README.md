# Code public de Dormer : le diagnostic

Dormer n'est pas open source, mais le code qui touche à tes données quand tu envoies un diagnostic est publié ici, pour que tu puisses vérifier ce que dit la [page de confidentialité](https://dormernotch.com/fr/confidentialite/).

- **[app/Redact.swift](app/Redact.swift)** : le nettoyage fait sur ton Mac avant l'envoi. Il retire les chemins, ton nom d'utilisateur, les e-mails, les liens, les adresses Bluetooth et IP, les noms de fichiers, les prénoms dans les noms d'appareils, le contenu des images et les textes libres des réglages. Ses tests sont dans [app/main.swift](app/main.swift) :
  ```
  cd app && swiftc Redact.swift main.swift -o redact-tests && ./redact-tests
  ```
- **[app/Stats.swift](app/Stats.swift)** : les statistiques anonymes. Au premier lancement, puis au plus une fois par jour, l'app envoie seulement « installé », « mis à jour » ou « actif aujourd'hui » avec la version de Dormer et de macOS, et une seule fois la réponse à « Tout marche bien ? ». Aucun identifiant. Se coupe dans **Réglages › Général**.
- **[diag-worker/](diag-worker/)** : le petit service Cloudflare de `diag.dormernotch.com`. Il reçoit le diagnostic, crée un ticket dans un dépôt GitHub privé (la clé GitHub reste chez Cloudflare, jamais dans l'app), limite les envois contre le spam, ne journalise rien et efface chaque diagnostic après un an. Pour les statistiques (`/hello`, `/feedback`), il ajoute seulement 1 à des compteurs du jour.

Ce code est copié du dépôt de Dormer à chaque modification. Licence : [MIT](LICENSE).

---

# Dormer's public code: diagnostics

Dormer isn't open source, but the code that handles your data when you send a diagnostic is published here so you can check what the [privacy page](https://dormernotch.com/privacy/) says: `app/Redact.swift` (cleaning done on your Mac before sending, with tests), `app/Stats.swift` (anonymous install/update/daily-use counts and the one-time "Is everything working?" answer, no identifier) and `diag-worker/` (the Cloudflare service behind `diag.dormernotch.com`). MIT licensed.
