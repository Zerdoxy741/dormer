import { bindings, defineConfig, triggers } from "cf/config";
import * as entrypoint from "./src/index.ts" with { type: "cf-worker" };

export default defineConfig({
	worker: {
		name: "dormer-diagnostics",
		compatibilityDate: "2026-11-23",
		entrypoint,
		domains: ["diag.dormernotch.com"],
		workersDev: false,
		env: {
			REPO: bindings.text("Zerdoxy741/dormer-diagnostics"),
			// Clé GitHub limitée aux tickets du dépôt privé : `cf workers secrets put GITHUB_TOKEN`
			GITHUB_TOKEN: bindings.secret(),
			// 3 envois par minute et par adresse
			LIMIT: bindings.rateLimit({ namespace: "1001", simple: { limit: 3, period: 60 } }),
			// Compteurs anonymes par jour (installations, jours actifs, avis) : aucune donnée personnelle
			STATS: bindings.d1(),
			// Clé pour lire /stats : `cf workers secrets put STATS_KEY`
			STATS_KEY: bindings.secret(),
		},
		triggers: [triggers.scheduled({ schedule: "17 4 * * *" })],
	},
});
