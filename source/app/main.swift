import Foundation

// Tests du nettoyage des diagnostics, copiés des tests de Dormer.
// Lancer :  swiftc Redact.swift main.swift -o redact-tests && ./redact-tests

var failures = 0, count = 0
func expectEqual<T: Equatable>(_ got: T, _ want: T, _ what: String) {
    count += 1
    if got != want { failures += 1; print("✗ \(what) : attendu \(want), obtenu \(got)") }
}

// MARK: Nettoyage des diagnostics (rien de personnel ne doit partir)

let home = "/Users/lea"
expectEqual(Redact.text("/Users/lea/Downloads/x.pdf et /Users/bob/a", home: home, names: ["lea"]), "~/Downloads/x.pdf et /Users/[utilisateur]/a", "chemins")
expectEqual(Redact.text("écris à lea.martin@gmail.com", home: home, names: []), "écris à [e-mail]", "e-mail")
expectEqual(Redact.text("vu sur https://site.fr/a?b=1 ok", home: home, names: []), "vu sur [lien] ok", "lien")
expectEqual(Redact.text("AirPods [40-b3-fa-52-f9-81]", home: home, names: []), "AirPods [[adresse]]", "adresse Bluetooth")
expectEqual(Redact.text("id 0F3A2B1C-1111-2222-3333-444455556666", home: home, names: []), "id [id]", "UUID")
expectEqual(Redact.text("Salut Léa", home: home, names: ["Léa"]), "Salut [prénom]", "prénom de la personne")
expectEqual(Redact.text("macOS 27.2.0 build 42", home: home, names: []), "macOS 27.2.0 build 42", "versions gardées")
expectEqual(Redact.deviceNames("AirPods Pro de Léa"), "AirPods Pro de [prénom]", "appareil de quelqu'un")
expectEqual(Redact.deviceNames("iPhone d'Hugo"), "iPhone d'[prénom]", "appareil d'Hugo")
expectEqual(Redact.deviceNames("Tom’s AirPods"), "[prénom]'s AirPods", "appareil anglais")
expectEqual(Redact.deviceNames("AirPods Pro"), "AirPods Pro", "appareil sans prénom")
expectEqual(Redact.fileKind("Relevé bancaire.PDF"), "fichier .pdf", "type de fichier seulement")
expectEqual(Redact.logLine(#"t AirDrop : 1 élément(s) ["vacances.jpg"]"#), "t AirDrop : 1 élément(s)", "anciens noms de fichiers")
expectEqual(Redact.logLine(#"t AirDrop : 1 élément(s) ["fichier .jpg"]"#), #"t AirDrop : 1 élément(s) ["fichier .jpg"]"#, "nouveau format gardé")
expectEqual(Redact.logLine("t icône du Dock lâchée : Mon CV.pages étagère=true airdrop=false"), "t icône du Dock lâchée : fichier .pages étagère=true airdrop=false", "icône du Dock")
expectEqual(Redact.logLine("t transfert publié : upload Mon CV.pages"), "t transfert publié : upload", "ancien transfert")
expectEqual(Redact.logLine("t IA : Photo de Léa à la plage"), "t IA : [contenu masqué]", "description d'image")
expectEqual(Redact.logLine("t IA : description de 42 caractères"), "t IA : [contenu masqué]", "longueur masquée aussi")
expectEqual(Redact.logLine("t IA : obtenue"), "t IA : obtenue", "nouveau format IA gardé")
expectEqual(Redact.logLine("t texte : « Mon relevé »"), "t texte : [contenu masqué]", "texte lu à l'écran")
expectEqual(Redact.logLine("t texte : rien"), "t texte : rien", "aucun texte lu")
expectEqual(Redact.logLine("t erreur IA : May contain unsafe content"), "t erreur IA : May contain unsafe content", "erreurs gardées")
expectEqual(Redact.logLine("t connexion : AirPods Pro [40-b3-fa-52-f9-81]"), "t connexion : AirPods Pro", "adresse retirée")
expectEqual(Redact.logLine("t copie impossible : Le fichier “secret.txt” est introuvable"), "t copie impossible : Le fichier “[nom]” est introuvable", "nom dans une erreur")
expectEqual(Redact.settingValue(key: "lastDownloadPath", "/Users/lea/a.pdf"), "[masqué]", "chemin masqué")
expectEqual(Redact.settingValue(key: "weatherCity", "Lyon"), "[masqué]", "ville masquée")
expectEqual(Redact.settingValue(key: "clockFormat", "HH:mm"), "HH:mm", "mot-clé gardé")
expectEqual(Redact.settingValue(key: "notes", "Une phrase libre, avec des virgules"), "[masqué]", "texte libre masqué")
expectEqual(Redact.settingValue(key: "askHistory", ["a", "b"]), "[2 éléments]", "liste : nombre seulement")

print(failures == 0 ? "Tests : \(count) réussis" : "Tests : \(failures) échec(s) sur \(count)")
exit(failures == 0 ? 0 : 1)
