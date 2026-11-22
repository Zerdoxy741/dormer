# Dormer

**Ta notch, en mieux.** Dormer transforme l'encoche de ton MacBook en île dynamique : musique, AirDrop, presse-papiers, alertes et plus encore. *(Anciennement Notchy.)*

## Télécharger

👉 **[Télécharger la dernière version](https://github.com/Zerdoxy741/notchy/releases/latest)** (fichier `Dormer-….zip`)

Il faut un MacBook avec une encoche et **macOS 14.2 ou plus récent**.

Tu as déjà Notchy ? Rien à faire : ouvre les réglages › Mises à jour › « Rechercher les mises à jour ». L'app se met à jour et se renomme toute seule en Dormer, tes réglages sont gardés.

## Installer

1. Décompresse le zip et glisse **Dormer.app** dans le dossier **Applications**.
2. Ouvre Dormer. macOS le bloque la première fois (l'app n'est pas sur l'App Store), c'est normal :
   - ouvre **Réglages Système › Confidentialité et sécurité** ;
   - tout en bas, à côté de « Dormer a été bloqué », clique sur **Ouvrir quand même**, puis confirme.
   - Si le bouton n'apparaît pas, colle ceci dans Terminal puis rouvre Dormer :
     ```bash
     xattr -dr com.apple.quarantine /Applications/Dormer.app
     ```
3. Accepte les autorisations au fur et à mesure (Accessibilité, Calendrier, Musique, Bluetooth).

Dormer se lance ensuite tout seul au démarrage du Mac. Les réglages s'ouvrent en survolant la notch, puis l'icône ⚙︎.

## Ce qu'il fait

- 🎵 **Musique** : pochette, lecture, volume, sortie audio, paroles synchronisées et Shazam.
- 📡 **AirDrop et étagère** : glisse un fichier (même depuis le Dock) sur la notch pour le garder ou l'envoyer par AirDrop, avec une animation pendant l'envoi.
- 📋 **Presse-papiers** : tes derniers éléments copiés, un par ligne. Les images reçoivent un titre écrit par Apple Intelligence, directement sur ton Mac.
- 🎧 **AirPods** : animation à la connexion, avec la batterie des écouteurs puis du boîtier.
- 🔔 **Alertes** : batterie, téléchargements, rappels d'événements, appels.
- 🎚️ **MixVol** : le volume de chaque app, depuis la barre des menus.
- ✨ **ChatGPT et Claude** : la notch montre quand une réponse s'écrit et te prévient quand elle est prête.
- 🔄 **Mises à jour** intégrées à l'app.

L'historique du presse-papiers reste en mémoire sur ton Mac et n'est jamais envoyé, pas plus que les images qu'il décrit.

Pour quitter : clic droit sur la notch › Quitter Dormer.
