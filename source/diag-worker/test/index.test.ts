import { SELF } from "cloudflare:test";
import { afterEach, expect, it, vi } from "vite-plus/test";

const send = (body: unknown, headers: Record<string, string> = {}) =>
	SELF.fetch("https://diag.dormernotch.com/diagnostic", {
		method: "POST",
		headers: {
			"User-Agent": "Dormer-Diagnostics",
			"CF-Connecting-IP": crypto.randomUUID(),
			...headers,
		},
		body: typeof body === "string" ? body : JSON.stringify(body),
	});

const good = { title: "[D-1234-ABCD] Test", body: "## Diagnostic Dormer\nrien" };

afterEach(() => vi.restoreAllMocks());

it("crée le ticket sur GitHub sans jamais renvoyer la clé", async () => {
	const calls: Request[] = [];
	vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
		calls.push(new Request(input, init));
		return new Response(JSON.stringify({ number: 42 }), { status: 201 });
	});
	const res = await send(good);
	expect(res.status).toBe(201);
	expect(await res.json()).toEqual({ number: 42 });
	expect(calls).toHaveLength(1);
	expect(calls[0].url).toBe("https://api.github.com/repos/Zerdoxy741/dormer-diagnostics/issues");
	expect(calls[0].headers.get("Authorization")).toMatch(/^Bearer /);
});

it("refuse ce qui ne vient pas de Dormer", async () => {
	expect((await send(good, { "User-Agent": "curl/8" })).status).toBe(403);
	expect((await SELF.fetch("https://diag.dormernotch.com/diagnostic")).status).toBe(405);
	expect((await SELF.fetch("https://diag.dormernotch.com/")).status).toBe(404);
});

it("refuse les envois mal formés ou trop gros", async () => {
	const spy = vi.spyOn(globalThis, "fetch");
	expect((await send("pas du json")).status).toBe(400);
	expect((await send({ title: "x" })).status).toBe(400);
	expect((await send({ title: "x", body: "autre chose" })).status).toBe(400);
	expect(
		(await send({ title: "x", body: "## Diagnostic Dormer\n" + "a".repeat(70_000) })).status,
	).toBe(413);
	expect(spy).not.toHaveBeenCalled();
});

it("limite le nombre d'envois par adresse", async () => {
	vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response("{}", { status: 201 }));
	const ip = { "CF-Connecting-IP": "203.0.113.9" };
	const codes = [];
	for (let i = 0; i < 5; i++) codes.push((await send(good, ip)).status);
	expect(codes).toContain(429);
});

const post = (path: string, body: unknown, headers: Record<string, string> = {}) =>
	SELF.fetch(`https://diag.dormernotch.com${path}`, {
		method: "POST",
		headers: { "User-Agent": "Dormer/0.8.1", "CF-Connecting-IP": crypto.randomUUID(), ...headers },
		body: typeof body === "string" ? body : JSON.stringify(body),
	});

it("compte les installations et les jours actifs sans rien envoyer ailleurs", async () => {
	const spy = vi.spyOn(globalThis, "fetch");
	expect((await post("/hello", { event: "install", version: "0.8.1", macos: "15.2" })).status).toBe(
		204,
	);
	expect((await post("/hello", { event: "active", version: "0.8.1", macos: "15.2" })).status).toBe(
		204,
	);
	expect((await post("/hello", { event: "update", version: "0.9", macos: "15.2" })).status).toBe(
		204,
	);
	expect((await post("/feedback", { ok: true, version: "0.8.1" })).status).toBe(204);
	expect((await post("/feedback", { ok: false, version: "0.8.1" })).status).toBe(204);
	expect(spy).not.toHaveBeenCalled();
	const { env } = await import("cloudflare:workers");
	const { results } = await env.STATS.prepare("SELECT metric, n FROM counts ORDER BY metric").all();
	expect(results).toEqual([
		{ metric: "active", n: 1 },
		{ metric: "active:v0.8.1", n: 1 },
		{ metric: "feedback:ko", n: 1 },
		{ metric: "feedback:ko:v0.8.1", n: 1 },
		{ metric: "feedback:ok", n: 1 },
		{ metric: "feedback:ok:v0.8.1", n: 1 },
		{ metric: "install", n: 1 },
		{ metric: "install:v0.8.1", n: 1 },
		{ metric: "macos:15", n: 1 },
		{ metric: "update", n: 1 },
		{ metric: "update:v0.9", n: 1 },
	]);
});

it("refuse les statistiques mal formées", async () => {
	expect(
		(
			await post(
				"/hello",
				{ event: "install", version: "0.8.1", macos: "15" },
				{ "User-Agent": "curl/8" },
			)
		).status,
	).toBe(403);
	expect((await post("/hello", { event: "autre", version: "0.8.1", macos: "15" })).status).toBe(
		400,
	);
	expect(
		(await post("/hello", { event: "install", version: "<script>", macos: "15" })).status,
	).toBe(400);
	expect((await post("/hello", { event: "install", version: "0.8.1", macos: "x" })).status).toBe(
		400,
	);
	expect((await post("/feedback", { ok: "oui", version: "0.8.1" })).status).toBe(400);
	expect((await post("/hello", "a".repeat(600))).status).toBe(413);
	expect((await SELF.fetch("https://diag.dormernotch.com/hello")).status).toBe(405);
});

it("ne montre les statistiques qu'avec la clé", async () => {
	expect((await SELF.fetch("https://diag.dormernotch.com/stats")).status).toBe(401);
	expect(
		(
			await SELF.fetch("https://diag.dormernotch.com/stats", {
				headers: { Authorization: "Bearer faux" },
			})
		).status,
	).toBe(401);
	await post("/hello", { event: "install", version: "0.8.1", macos: "15.2" });
	const res = await SELF.fetch("https://diag.dormernotch.com/stats", {
		headers: { Authorization: "Bearer test-stats-key" },
	});
	expect(res.status).toBe(200);
	const body = (await res.json()) as { totals: Record<string, number> };
	expect(body.totals.install).toBeGreaterThanOrEqual(1);
});
