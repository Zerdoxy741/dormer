import { env } from "cloudflare:workers";

// Reçoit les diagnostics envoyés par Dormer et crée un ticket dans le dépôt GitHub privé.
// La clé GitHub reste ici (secret Cloudflare) : l'app n'en contient plus aucune, donc personne
// ne peut l'en extraire pour lire les diagnostics des autres.
// Rien n'est journalisé : le contenu ne fait que passer.

const MAX_TITLE = 200;
const MAX_BODY = 60_000;
const KEEP_DAYS = 365; // durée de conservation annoncée sur la page de confidentialité

const gh = (path: string, init: RequestInit = {}) =>
	fetch(`https://api.github.com${path}`, {
		...init,
		headers: {
			Accept: "application/vnd.github+json",
			Authorization: `Bearer ${env.GITHUB_TOKEN}`,
			"User-Agent": "Dormer-Diagnostics",
			"Content-Type": "application/json",
			...init.headers,
		},
	});

const json = (data: unknown, status = 200) =>
	new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });

async function receive(request: Request): Promise<Response> {
	if (request.method !== "POST") return json({ error: "method" }, 405);
	if (!request.headers.get("User-Agent")?.startsWith("Dormer-Diagnostics"))
		return json({ error: "client" }, 403);

	// Une adresse ne peut envoyer que quelques diagnostics par minute (contre le spam)
	const ip = request.headers.get("CF-Connecting-IP") ?? "?";
	const { success } = await env.LIMIT.limit({ key: ip });
	if (!success) return json({ error: "rate" }, 429);

	const raw = await request.text();
	if (raw.length > MAX_BODY + MAX_TITLE + 1000) return json({ error: "size" }, 413);
	let data: { title?: unknown; body?: unknown };
	try {
		data = JSON.parse(raw);
	} catch {
		return json({ error: "json" }, 400);
	}
	const { title, body } = data;
	if (typeof title !== "string" || typeof body !== "string" || !title.trim() || !body.trim())
		return json({ error: "fields" }, 400);
	if (title.length > MAX_TITLE || body.length > MAX_BODY) return json({ error: "size" }, 413);
	if (!body.startsWith("## Diagnostic Dormer")) return json({ error: "format" }, 400);

	const res = await gh(`/repos/${env.REPO}/issues`, {
		method: "POST",
		body: JSON.stringify({ title, body }),
	});
	if (res.status !== 201) return json({ error: "github", status: res.status }, 502);
	const issue = (await res.json()) as { number?: number };
	return json({ number: issue.number ?? 0 }, 201);
}

/// Une fois par jour : supprime les diagnostics de plus d'un an.
async function purge(): Promise<void> {
	const before = new Date(Date.now() - KEEP_DAYS * 86_400_000).toISOString().slice(0, 10);
	const q = encodeURIComponent(`repo:${env.REPO} is:issue created:<${before}`);
	const res = await gh(`/search/issues?q=${q}&per_page=50`);
	if (!res.ok) return;
	const { items = [] } = (await res.json()) as { items?: { number: number; node_id: string }[] };
	for (const issue of items) {
		const del = await gh("/graphql", {
			method: "POST",
			body: JSON.stringify({
				query: "mutation($id: ID!) { deleteIssue(input: { issueId: $id }) { clientMutationId } }",
				variables: { id: issue.node_id },
			}),
		});
		const out = (await del.json().catch(() => ({}))) as { errors?: unknown[] };
		if (del.ok && !out.errors) continue;
		// La clé n'a pas le droit de supprimer : on efface au moins le contenu et on ferme le ticket
		await gh(`/repos/${env.REPO}/issues/${issue.number}`, {
			method: "PATCH",
			body: JSON.stringify({
				title: "[effacé]",
				body: "Diagnostic effacé après un an.",
				state: "closed",
			}),
		});
	}
}

// ── Statistiques anonymes ──────────────────────────────────────────────────────────────────
// L'app envoie au plus : un « install » au tout premier lancement, un « update » quand la version
// change, un « active » par jour d'utilisation, et la réponse à « Tout marche bien ? ». Aucun identifiant, aucune adresse IP
// gardée : on n'incrémente que des compteurs par jour (ex. 2026-11-26 / install = 4).

const EVENTS = new Set(["install", "update", "active"]);
const VERSION = /^\d{1,3}(\.\d{1,3}){0,3}$/;
const MACOS = /^\d{2}(\.\d{1,2}){0,2}$/;

let schemaReady = false;
async function count(metrics: string[]): Promise<void> {
	if (!schemaReady) {
		await env.STATS.exec(
			"CREATE TABLE IF NOT EXISTS counts (day TEXT NOT NULL, metric TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, metric))",
		);
		schemaReady = true;
	}
	const day = new Date().toISOString().slice(0, 10);
	const up = env.STATS.prepare(
		"INSERT INTO counts (day, metric, n) VALUES (?1, ?2, 1) ON CONFLICT (day, metric) DO UPDATE SET n = n + 1",
	);
	await env.STATS.batch(metrics.map((m) => up.bind(day, m)));
}

async function readSmall(request: Request): Promise<Record<string, unknown> | Response> {
	if (request.method !== "POST") return json({ error: "method" }, 405);
	if (!request.headers.get("User-Agent")?.startsWith("Dormer"))
		return json({ error: "client" }, 403);
	const ip = request.headers.get("CF-Connecting-IP") ?? "?";
	const { success } = await env.LIMIT.limit({ key: `stats:${ip}` });
	if (!success) return json({ error: "rate" }, 429);
	const raw = await request.text();
	if (raw.length > 500) return json({ error: "size" }, 413);
	try {
		const data = JSON.parse(raw);
		if (data && typeof data === "object" && !Array.isArray(data)) return data;
	} catch {}
	return json({ error: "json" }, 400);
}

/// POST /hello {"event":"install"|"update"|"active","version":"0.8.1","macos":"15.2"}
async function hello(request: Request): Promise<Response> {
	const data = await readSmall(request);
	if (data instanceof Response) return data;
	const { event, version, macos } = data;
	if (typeof event !== "string" || !EVENTS.has(event)) return json({ error: "event" }, 400);
	if (typeof version !== "string" || !VERSION.test(version)) return json({ error: "version" }, 400);
	if (typeof macos !== "string" || !MACOS.test(macos)) return json({ error: "macos" }, 400);
	const metrics = [event, `${event}:v${version}`];
	if (event === "active") metrics.push(`macos:${macos.split(".")[0]}`);
	await count(metrics);
	return new Response(null, { status: 204 });
}

/// POST /feedback {"ok":true|false,"version":"0.8.1"}
async function feedback(request: Request): Promise<Response> {
	const data = await readSmall(request);
	if (data instanceof Response) return data;
	const { ok, version } = data;
	if (typeof ok !== "boolean") return json({ error: "ok" }, 400);
	if (typeof version !== "string" || !VERSION.test(version)) return json({ error: "version" }, 400);
	const m = ok ? "feedback:ok" : "feedback:ko";
	await count([m, `${m}:v${version}`]);
	return new Response(null, { status: 204 });
}

/// GET /stats (Authorization: Bearer <STATS_KEY>) : totaux et détail par jour, pour toi seul.
async function stats(request: Request): Promise<Response> {
	const key = env.STATS_KEY;
	if (!key || request.headers.get("Authorization") !== `Bearer ${key}`)
		return json({ error: "auth" }, 401);
	const exists = await env.STATS.prepare(
		"SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'counts'",
	).first();
	if (!exists) return json({ totals: {}, days: {} });
	const { results } = await env.STATS.prepare(
		"SELECT day, metric, n FROM counts ORDER BY day DESC, metric",
	).all<{
		day: string;
		metric: string;
		n: number;
	}>();
	const totals: Record<string, number> = {};
	const days: Record<string, Record<string, number>> = {};
	for (const { day, metric, n } of results) {
		(days[day] ??= {})[metric] = n;
		if (!metric.startsWith("active") && !metric.startsWith("macos"))
			totals[metric] = (totals[metric] ?? 0) + n;
	}
	return json({ totals, days });
}

export default {
	fetch(request) {
		const url = new URL(request.url);
		if (url.pathname === "/diagnostic") return receive(request);
		if (url.pathname === "/hello") return hello(request);
		if (url.pathname === "/feedback") return feedback(request);
		if (url.pathname === "/stats") return stats(request);
		return new Response("Dormer diagnostics", { status: 404 });
	},
	async scheduled(_event, _env, ctx) {
		ctx.waitUntil(purge());
	},
} satisfies ExportedHandler;
