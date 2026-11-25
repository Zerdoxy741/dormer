import { SELF } from "cloudflare:test";
import { afterEach, expect, it, vi } from "vite-plus/test";

const send = (body: unknown, headers: Record<string, string> = {}) =>
	SELF.fetch("https://diag.dormernotch.com/diagnostic", {
		method: "POST",
		headers: { "User-Agent": "Dormer-Diagnostics", "CF-Connecting-IP": crypto.randomUUID(), ...headers },
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
	expect((await send({ title: "x", body: "## Diagnostic Dormer\n" + "a".repeat(70_000) })).status).toBe(413);
	expect(spy).not.toHaveBeenCalled();
});

it("limite le nombre d'envois par adresse", async () => {
	vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response("{}", { status: 201 }));
	const ip = { "CF-Connecting-IP": "203.0.113.9" };
	const codes = [];
	for (let i = 0; i < 5; i++) codes.push((await send(good, ip)).status);
	expect(codes).toContain(429);
});
