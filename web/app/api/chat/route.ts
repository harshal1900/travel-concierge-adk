// Server-side proxy: the browser never sees API_BASE_URL or SERVICE_API_KEY.
const TIMEOUT_MS = 60_000;

function fail(message: string, status: number) {
  return Response.json({ error: message }, { status });
}

export async function POST(request: Request) {
  let body: { message?: unknown; session_id?: unknown };
  try {
    body = await request.json();
  } catch {
    return fail("Invalid request.", 400);
  }
  const message = typeof body.message === "string" ? body.message.trim() : "";
  const sessionId = typeof body.session_id === "string" ? body.session_id : "";
  if (!message || message.length > 2000 || !sessionId || sessionId.length > 64) {
    return fail("Please enter a message of up to 2000 characters.", 400);
  }

  const baseUrl = process.env.API_BASE_URL;
  if (!baseUrl) {
    return fail("The chat service is not configured.", 503);
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.SERVICE_API_KEY) {
    headers["X-API-Key"] = process.env.SERVICE_API_KEY;
  }

  try {
    const upstream = await fetch(`${baseUrl.replace(/\/$/, "")}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ session_id: sessionId, message }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store",
    });
    if (!upstream.ok) {
      const messages: Record<number, string> = {
        401: "The chat service is not authorised. Check the server configuration.",
        429: "Too many requests. Please wait a moment and try again.",
        504: "The assistant took too long to answer. Please try again.",
      };
      const detail = await upstream.json().catch(() => ({}));
      const correlationId = typeof detail?.correlation_id === "string" ? detail.correlation_id : undefined;
      return Response.json(
        {
          error: messages[upstream.status] ?? "The assistant could not answer right now. Please try again.",
          correlation_id: correlationId,
        },
        { status: upstream.status === 429 ? 429 : 502 },
      );
    }
    return Response.json(await upstream.json());
  } catch (error) {
    if (error instanceof Error && error.name === "TimeoutError") {
      return fail("The assistant took too long to answer. Please try again.", 504);
    }
    return fail("Could not reach the assistant. Please try again.", 502);
  }
}
