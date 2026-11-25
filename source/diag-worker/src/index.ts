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
	if (!request.headers.get("User-Agent")?.startsWith("Dormer-Diagnostics")) return json({ error: "client" }, 403);

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
			body: JSON.stringify({ title: "[effacé]", body: "Diagnostic effacé après un an.", state: "closed" }),
		});
	}
}

export default {
	fetch(request) {
		const url = new URL(request.url);
		if (url.pathname === "/diagnostic") return receive(request);
		return new Response("Dormer diagnostics", { status: 404 });
	},
	async scheduled(_event, _env, ctx) {
		ctx.waitUntil(purge());
	},
} satisfies ExportedHandler;
