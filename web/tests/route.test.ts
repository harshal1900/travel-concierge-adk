import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/chat/route";

const fetchMock = vi.fn();
const SECRET = "super-secret-key";

function req(body: unknown) {
  return new Request("http://localhost/api/chat", { method: "POST", body: JSON.stringify(body) });
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubEnv("API_BASE_URL", "http://api.test/");
  vi.stubEnv("SERVICE_API_KEY", SECRET);
});
afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("POST /api/chat", () => {
  it("forwards to the API with the key server-side and never returns it", async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ agent_text: "hi", a2ui_payload: {} }), { status: 200 }));
    const res = await POST(req({ session_id: "s1", message: "hello" }));
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/chat");
    expect(init.headers["X-API-Key"]).toBe(SECRET);
    expect(JSON.parse(init.body)).toEqual({ session_id: "s1", message: "hello" });
    expect(await res.text()).not.toContain(SECRET);
  });

  it("rejects empty, oversized and malformed input", async () => {
    expect((await POST(req({ session_id: "s", message: " " }))).status).toBe(400);
    expect((await POST(req({ session_id: "s", message: "x".repeat(2001) }))).status).toBe(400);
    expect((await POST(req({ message: "hi" }))).status).toBe(400);
    expect((await POST(new Request("http://localhost/api/chat", { method: "POST", body: "not json" }))).status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("maps upstream errors to friendly messages with the correlation id, no key", async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ detail: "x", correlation_id: "abc" }), { status: 429 }));
    const res = await POST(req({ session_id: "s", message: "hi" }));
    const text = await res.text();
    expect(res.status).toBe(429);
    expect(text).toContain("Too many requests");
    expect(text).toContain("abc");
    expect(text).not.toContain(SECRET);
  });

  it("returns a friendly error when the API is unreachable", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));
    const res = await POST(req({ session_id: "s", message: "hi" }));
    expect(res.status).toBe(502);
    expect((await res.json()).error).toContain("Could not reach");
  });

  it("returns 503 when API_BASE_URL is not configured", async () => {
    vi.stubEnv("API_BASE_URL", "");
    expect((await POST(req({ session_id: "s", message: "hi" }))).status).toBe(503);
  });
});
