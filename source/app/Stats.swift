import AppKit
import Foundation

/// Statistiques anonymes de Dormer : combien de Mac l'ont installé, combien l'utilisent chaque jour,
/// et si tout marche bien après le premier jour.
///
/// Ce qui part, et rien d'autre :
/// - au tout premier lancement : `{"event":"install","version":"0.8.1","macos":"15.2"}`
/// - au premier lancement d'une nouvelle version : `{"event":"update", …}` (mêmes champs)
/// - au plus une fois par jour d'utilisation : `{"event":"active", …}` (mêmes champs)
/// - une seule fois, après 24 h : `{"ok":true|false,"version":"0.8.1"}` si la personne répond
///
/// Aucun identifiant n'est créé ni envoyé : le serveur (diag-worker, /hello et /feedback) ne fait
/// qu'ajouter 1 à des compteurs du jour. On ne peut donc ni reconnaître un Mac ni relier deux jours.
///
/// Branchement dans l'app :
/// ```swift
/// // applicationDidFinishLaunching, en tout premier (avant que l'app n'écrive ses réglages :
/// // c'est ce qui permet de reconnaître une mise à jour depuis une version sans statistiques)
/// Stats.start(reportProblem: { /* ouvrir Réglages › Général › Signaler un problème… */ })
///
/// // Réglages › Général
/// Toggle("Envoyer des statistiques anonymes", isOn: $statsEnabled)   // @AppStorage(Stats.enabledKey)
/// ```
@MainActor
enum Stats {
	static let enabledKey = "stats.enabled"
	private static let installSentKey = "stats.installSent"
	private static let lastVersionKey = "stats.lastVersion"
	private static let lastActiveDayKey = "stats.lastActiveDay"
	private static let firstLaunchKey = "stats.firstLaunch"
	private static let feedbackDoneKey = "stats.feedbackDone"

	private static let base = URL(string: "https://diag.dormernotch.com")!
	private static let defaults = UserDefaults.standard
	private static var timer: Timer?
	private static var reportProblem: (() -> Void)?
	/// Dormer avait déjà des réglages sur ce Mac avant la première version avec statistiques.
	private static var hadDormerBefore = false

	/// Activé par défaut, coupé par le réglage « Envoyer des statistiques anonymes ».
	static var isEnabled: Bool {
		defaults.object(forKey: enabledKey) as? Bool ?? true
	}

	/// À appeler une fois, au lancement. Dormer reste ouvert des jours entiers : on revérifie
	/// toutes les heures et à chaque réveil du Mac pour compter chaque jour d'utilisation.
	/// À appeler en tout premier (avant que l'app n'écrive ses réglages) : note si Dormer était déjà là.
	static func prepare() {
		hadDormerBefore = hasOtherDormerSettings()
	}

	static func start(reportProblem: @escaping () -> Void) {
		self.reportProblem = reportProblem
		if defaults.object(forKey: firstLaunchKey) == nil {
			defaults.set(Date(), forKey: firstLaunchKey)
		}
		tick()
		timer = Timer.scheduledTimer(withTimeInterval: 3600, repeats: true) { _ in MainActor.assumeIsolated { tick() } }
		NSWorkspace.shared.notificationCenter.addObserver(
			forName: NSWorkspace.didWakeNotification, object: nil, queue: .main
		) { _ in MainActor.assumeIsolated { tick() } }
	}

	private static func tick() {
		guard isEnabled else { return }
		let version = appVersion
		let last = defaults.string(forKey: lastVersionKey)
		if !defaults.bool(forKey: installSentKey) {
			// Première fois avec les statistiques : vraie installation, ou mise à jour depuis
			// une ancienne version de Dormer (ses réglages sont déjà là) ?
			let event = hadDormerBefore ? "update" : "install"
			hello(event) { ok in
				guard ok else { return }
				defaults.set(true, forKey: installSentKey)
				defaults.set(version, forKey: lastVersionKey)
			}
		} else if last != version {
			// Nouvelle version lancée pour la première fois (ou version pas encore notée)
			if last == nil {
				defaults.set(version, forKey: lastVersionKey)
			} else {
				hello("update") { ok in if ok { defaults.set(version, forKey: lastVersionKey) } }
			}
		}
		let today = utcDay()
		if defaults.string(forKey: lastActiveDayKey) != today {
			hello("active") { ok in if ok { defaults.set(today, forKey: lastActiveDayKey) } }
		}
		askFeedbackIfDue()
	}

	// MARK: - « Tout marche bien ? »

	/// Une seule fois, au moins 24 h après le premier lancement. Si l'app a déjà sa propre bulle
	/// dans l'encoche, remplace l'alerte par celle-ci et appelle `sendFeedback(ok:)`.
	private static func askFeedbackIfDue() {
		guard !defaults.bool(forKey: feedbackDoneKey),
			let first = defaults.object(forKey: firstLaunchKey) as? Date,
			Date().timeIntervalSince(first) >= 86_400
		else { return }
		defaults.set(true, forKey: feedbackDoneKey)  // on ne redemande jamais, même sans réponse

		let fr = Locale.preferredLanguages.first?.hasPrefix("fr") ?? false
		let alert = NSAlert()
		alert.messageText = fr ? "Tout marche bien avec Dormer ?" : "Is everything working with Dormer?"
		alert.informativeText =
			fr
			? "Ta réponse est anonyme : elle ajoute juste 1 à un compteur 👍 ou 👎."
			: "Your answer is anonymous: it just adds 1 to a 👍 or 👎 counter."
		alert.addButton(withTitle: fr ? "👍 Oui" : "👍 Yes")
		alert.addButton(withTitle: fr ? "👎 Pas vraiment" : "👎 Not really")
		alert.addButton(withTitle: fr ? "Plus tard" : "Not now")
		NSApp.activate(ignoringOtherApps: true)
		switch alert.runModal() {
		case .alertFirstButtonReturn: sendFeedback(ok: true)
		case .alertSecondButtonReturn:
			sendFeedback(ok: false)
			reportProblem?()  // propose d'envoyer un diagnostic pour comprendre ce qui ne va pas
		default: break
		}
	}

	static func sendFeedback(ok: Bool) {
		guard isEnabled else { return }
		post("/feedback", ["ok": ok, "version": appVersion]) { _ in }
	}

	// MARK: - Envoi

	private static func hello(_ event: String, done: @escaping @MainActor (Bool) -> Void) {
		post("/hello", ["event": event, "version": appVersion, "macos": macOSVersion], done: done)
	}

	private static func post(_ path: String, _ body: [String: Any], done: @escaping @MainActor (Bool) -> Void) {
		var req = URLRequest(url: base.appendingPathComponent(path))
		req.httpMethod = "POST"
		req.timeoutInterval = 15
		req.setValue("application/json", forHTTPHeaderField: "Content-Type")
		req.setValue("Dormer/\(appVersion)", forHTTPHeaderField: "User-Agent")
		req.httpBody = try? JSONSerialization.data(withJSONObject: body)
		// Session éphémère : ni cookie ni cache, rien qui pourrait servir à reconnaître le Mac
		URLSession(configuration: .ephemeral).dataTask(with: req) { _, res, _ in
			let ok = (res as? HTTPURLResponse)?.statusCode == 204
			DispatchQueue.main.async { MainActor.assumeIsolated { done(ok) } }
		}.resume()
	}

	private static var appVersion: String {
		Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0"
	}

	private static var macOSVersion: String {
		let v = ProcessInfo.processInfo.operatingSystemVersion
		return v.patchVersion > 0
			? "\(v.majorVersion).\(v.minorVersion).\(v.patchVersion)" : "\(v.majorVersion).\(v.minorVersion)"
	}

	/// Des réglages de Dormer existaient-ils avant les statistiques ? On ne regarde que les noms
	/// des clés, jamais leur contenu, et rien de tout ça n'est envoyé.
	private static func hasOtherDormerSettings() -> Bool {
		guard defaults.object(forKey: installSentKey) == nil,
			let id = Bundle.main.bundleIdentifier,
			let domain = defaults.persistentDomain(forName: id)
		else { return false }
		let system = ["stats.", "NS", "Apple", "com.apple.", "WebKit"]
		return domain.keys.contains { key in !system.contains { key.hasPrefix($0) } }
	}

	private static func utcDay() -> String {
		let f = DateFormatter()
		f.calendar = Calendar(identifier: .gregorian)
		f.locale = Locale(identifier: "en_US_POSIX")
		f.timeZone = TimeZone(identifier: "UTC")
		f.dateFormat = "yyyy-MM-dd"
		return f.string(from: Date())
	}
}
