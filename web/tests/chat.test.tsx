import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Chat } from "@/components/Chat";
import { PRD_RESPONSE } from "./fixtures";

const fetchMock = vi.fn();

beforeEach(() => vi.stubGlobal("fetch", fetchMock));
afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

const ok = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));

describe("Chat", () => {
  it("shows an empty state with starter prompts", () => {
    render(<Chat />);
    expect(screen.getByRole("button", { name: "Best sushi in Tokyo" })).toBeInTheDocument();
  });

  it("sends a starter and renders both card lists plus the demo notice", async () => {
    fetchMock.mockReturnValue(ok(PRD_RESPONSE));
    render(<Chat />);
    await userEvent.click(screen.getByRole("button", { name: "Plan a day in Tokyo with sightseeing and dinner" }));
    expect(await screen.findByText("Top Attractions in Tokyo")).toBeInTheDocument();
    expect(screen.getByText("Recommended Dining in Tokyo")).toBeInTheDocument();
    expect(screen.getByText(/Demo data/)).toBeInTheDocument();
  });

  it("reuses one session_id across messages", async () => {
    fetchMock.mockImplementation(() => ok(PRD_RESPONSE));
    render(<Chat />);
    const box = screen.getByLabelText("Message");
    await userEvent.type(box, "first");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await screen.findByText("Top Attractions in Tokyo");
    await userEvent.type(box, "second");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const ids = fetchMock.mock.calls.map(([, init]) => JSON.parse(init.body).session_id);
    expect(ids[0]).toBeTruthy();
    expect(ids[0]).toBe(ids[1]);
  });

  it("disables send while empty and while loading", async () => {
    let resolve!: (r: Response) => void;
    fetchMock.mockReturnValue(new Promise<Response>((r) => (resolve = r)));
    render(<Chat />);
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Message"), "hi");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    resolve(new Response(JSON.stringify(PRD_RESPONSE), { status: 200 }));
    await screen.findByText("Top Attractions in Tokyo");
  });

  it("shows a friendly error when the server route reports one", async () => {
    fetchMock.mockReturnValue(Promise.resolve(new Response(JSON.stringify({ error: "Too many requests." }), { status: 429 })));
    render(<Chat />);
    await userEvent.click(screen.getByRole("button", { name: "Best sushi in Tokyo" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Too many requests.");
  });

  it("shows a friendly error when the network is down", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<Chat />);
    await userEvent.click(screen.getByRole("button", { name: "Best sushi in Tokyo" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach the assistant");
  });

  it("does not crash on an unknown component type", async () => {
    fetchMock.mockReturnValue(ok({ agent_text: "Hello", a2ui_payload: { components: [{ type: "Mystery", id: "m" }] } }));
    render(<Chat />);
    await userEvent.click(screen.getByRole("button", { name: "Best sushi in Tokyo" }));
    expect(await screen.findByText("Hello")).toBeInTheDocument();
  });
});
