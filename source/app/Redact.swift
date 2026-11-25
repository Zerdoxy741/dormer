import Foundation

/// Nettoie le texte d'un diagnostic avant qu'il quitte le Mac : rien de personnel ne doit partir.
/// Les journaux sont aussi écrits sans contenu personnel (voir `fileKind`), mais les anciens journaux
/// et les rapports de plantage peuvent encore en contenir : tout passe par `text` au moment de l'envoi.
enum Redact {
    /// Remplace tout ce qui peut identifier la personne : dossier personnel, nom d'utilisateur, prénom,
    /// adresses e-mail, liens, adresses Bluetooth/MAC, adresses IP et identifiants (UUID).
    static func text(_ s: String, home: String, names: [String]) -> String {
        var r = s
        if !home.isEmpty { r = r.replacingOccurrences(of: home, with: "~") }
        r = regex(r, #"/Users/[^/\s"']+"#, "/Users/[utilisateur]")
        r = regex(r, #"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"#, "[e-mail]")
        r = regex(r, #"(?i)\b(?:https?|ftp|file)://[^\s"'\]\)>]+"#, "[lien]")
        r = regex(r, #"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b"#, "[adresse]")
        r = regex(r, #"\b(?:\d{1,3}\.){3}\d{1,3}\b"#, "[ip]")
        r = regex(r, #"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"#, "[id]")
        for n in names where n.count >= 3 {
            r = regex(r, "(?i)\\b" + NSRegularExpression.escapedPattern(for: n) + "\\b", "[prénom]")
        }
        return r
    }

    /// Noms d'appareils qui contiennent un prénom : « AirPods de Léa », « iPhone d'Hugo », « Tom’s AirPods ».
    static func deviceNames(_ s: String) -> String {
        var r = regex(s, #"\b([Dd]e|of) \p{Lu}[\p{L}\-]+"#, "$1 [prénom]")
        r = regex(r, #"\b([Dd]['’])\p{Lu}[\p{L}\-]+"#, "$1[prénom]")
        return regex(r, #"\b\p{Lu}[\p{L}\-]+['’]s\b"#, "[prénom]'s")
    }

    /// Nom de fichier pour les journaux : seulement son type (« fichier .png »), jamais son nom.
    static func fileKind(_ name: String) -> String {
        let ext = (name as NSString).pathExtension.lowercased()
        return ext.isEmpty || ext.count > 8 ? "fichier" : "fichier .\(ext)"
    }

    /// Une ligne d'un ancien journal qui contient du contenu personnel : on garde l'événement, pas le contenu.
    static func logLine(_ line: String) -> String {
        // Noms de fichiers : « AirDrop : 2 élément(s) ["vacances.jpg", …] »
        var l = regex(line, #"(élément\(s\)) \[(?!"fichier).*\]$"#, "$1")
        l = regex(l, #"(icône (?:remise dans le Dock|du Dock lâchée) : ).*?\.([A-Za-z0-9]{1,8})(?= étagère=|$)"#, "$1fichier .$2")
        l = regex(l, #"(icône (?:remise dans le Dock|du Dock lâchée) : )(?!fichier)[^=]*?(?= étagère=|$)"#, "$1fichier")
        l = regex(l, #"(transfert publié : \S+) (?!fichier).+$"#, "$1")
        // Noms cités dans les messages d'erreur de macOS : « Le fichier “photo.jpg” est introuvable »
        l = regex(l, #"“[^”]*”"#, "“[nom]”")
        // Descriptions d'images et texte lu sur l'écran
        l = regex(l, #"(?<!erreur )\b(IA|texte) : (?!obtenue$|rien$).+$"#, "$1 : [contenu masqué]")
        // Adresse Bluetooth entre crochets
        l = regex(l, #"(connexion : .*) \[[^\]]*\]$"#, "$1")
        return l
    }

    /// Valeur d'un réglage : seuls les nombres, booléens et petits mots-clés passent ; le reste est masqué.
    static func settingValue(key: String, _ value: Any) -> String? {
        let personal = ["path", "directory", "track", "city", "name", "history", "ask", "pet", "topics", "anki", "shelf", "notifknown", "appoutputs", "volumes", "sender"]
        let low = key.lowercased()
        switch value {
        case is Data: return nil
        case let a as [Any]: return "[\(a.count) éléments]"
        case let d as [String: Any]: return "{\(d.count) clés}"
        case let s as String:
            if personal.contains(where: { low.contains($0) }) { return "[masqué]" }
            let simple = s.range(of: #"^[A-Za-z0-9 ._:+-]{0,40}$"#, options: .regularExpression) != nil
            return simple ? s : "[masqué]"
        default: return "\(value)"
        }
    }

    private static func regex(_ s: String, _ pattern: String, _ template: String) -> String {
        guard let re = try? NSRegularExpression(pattern: pattern) else { return s }
        return re.stringByReplacingMatches(in: s, range: NSRange(s.startIndex..., in: s), withTemplate: template)
    }
}
