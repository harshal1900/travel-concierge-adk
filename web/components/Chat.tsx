"use client";

import { useEffect, useRef, useState } from "react";
import {
  ChatContainerContent,
  ChatContainerRoot,
  ChatContainerScrollAnchor,
} from "@/components/ui/chat-container";
import { Message, MessageContent } from "@/components/ui/message";
import {
  PromptInput,
  PromptInputActions,
  PromptInputTextarea,
} from "@/components/ui/prompt-input";
import { Button } from "@/components/ui/button";
import { ComponentRenderer } from "@/components/ComponentRenderer";
import { isDemoText, parseComponents, type UiComponent } from "@/lib/a2ui";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  components?: UiComponent[];
  isError?: boolean;
};

export const STARTERS = [
  "Plan a day in Tokyo with sightseeing and dinner",
  "Best sushi in Tokyo",
  "What to see in Paris?",
];

const STARTER_HINTS = ["Sights + dinner", "Dining only", "Sightseeing only"];

function Logo() {
  return (
    <span
      className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-sky-500 via-indigo-500 to-violet-500 text-white shadow-md"
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 12l20-9-9 20-2-9-9-2z" />
      </svg>
    </span>
  );
}

function SkeletonCards() {
  return (
    <div role="status" aria-label="Assistant is typing" className="flex flex-col gap-3">
      <span className="sr-only">Assistant is typing</span>
      <div className="h-4 w-48 animate-pulse rounded bg-muted" />
      <div className="grid gap-3 sm:grid-cols-2">
        {[0, 1].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl border bg-muted/50" />
        ))}
      </div>
    </div>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem("theme");
    } catch {}
    const isDark = stored ? stored === "dark" : window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", isDark);
    setDark(isDark); // eslint-disable-line react-hooks/set-state-in-effect
  }, []);
  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {}
  }
  return (
    <Button variant="outline" size="sm" onClick={toggle} aria-pressed={dark} aria-label="Dark mode">
      {dark ? "Dark" : "Light"}
    </Button>
  );
}

export function Chat() {
  const sessionId = useRef<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || isLoading) return;
    sessionId.current ??= crypto.randomUUID(); // one session per chat, created on first send
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setIsLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId.current, message: text }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || typeof data.agent_text !== "string") {
        throw new Error(typeof data.error === "string" ? data.error : "Something went wrong.");
      }
      setMessages((m) => [
        ...m,
        { role: "assistant", text: data.agent_text, components: parseComponents(data.a2ui_payload) },
      ]);
    } catch (error) {
      const message =
        error instanceof TypeError
          ? "Could not reach the assistant. Check your connection and try again."
          : error instanceof Error
            ? error.message
            : "Something went wrong.";
      setMessages((m) => [...m, { role: "assistant", text: message, isError: true }]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-dvh bg-gradient-to-b from-sky-50 via-background to-background dark:from-slate-900 dark:via-background dark:to-background">
      <main className="mx-auto flex h-dvh w-full max-w-3xl flex-col gap-3 px-4 pt-4 pb-4 sm:px-6">
        <header className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Logo />
            <div>
              <h1 className="text-lg leading-tight font-semibold tracking-tight">Smart Travel Concierge</h1>
              <p className="text-xs text-muted-foreground">Sightseeing and dining ideas for any city</p>
            </div>
          </div>
          <ThemeToggle />
        </header>
        <ChatContainerRoot className="flex-1 rounded-2xl">
          <ChatContainerContent className="gap-6 px-1 py-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center gap-6 px-2 pt-8 text-center sm:pt-16">
                <div className="flex flex-col gap-2">
                  <h2 className="bg-gradient-to-r from-sky-600 to-violet-600 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl dark:from-sky-300 dark:to-violet-300">
                    Where to next?
                  </h2>
                  <p className="mx-auto max-w-md text-muted-foreground">
                    Tell me a city and what you are in the mood for. Include the place in your message.
                  </p>
                </div>
                <div className="grid w-full gap-3 sm:grid-cols-3" role="group" aria-label="Starter prompts">
                  {STARTERS.map((s, i) => (
                    <button
                      key={s}
                      type="button"
                      aria-label={s}
                      onClick={() => send(s)}
                      className="rounded-2xl border bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                    >
                      <span className="text-xs font-medium text-muted-foreground">{STARTER_HINTS[i]}</span>
                      <span className="mt-1 block text-sm font-medium">{s}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) =>
              m.role === "user" ? (
                <Message key={i} className="justify-end">
                  <MessageContent className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-primary-foreground">
                    {m.text}
                  </MessageContent>
                </Message>
              ) : (
                <Message key={i} className="items-start">
                  <span
                    className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-sky-500 to-violet-500 text-xs font-bold text-white"
                    aria-hidden="true"
                  >
                    TC
                  </span>
                  <div className="flex min-w-0 flex-1 flex-col gap-4">
                    <MessageContent
                      markdown={!m.isError}
                      className={
                        m.isError
                          ? "rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-destructive"
                          : "rounded-2xl rounded-tl-md border bg-card px-4 py-3 shadow-sm"
                      }
                      role={m.isError ? "alert" : undefined}
                    >
                      {m.isError ? `Error: ${m.text}` : m.text}
                    </MessageContent>
                    {m.components && m.components.length > 0 && <ComponentRenderer components={m.components} />}
                    {!m.isError && isDemoText(m.text) && (
                      <p className="inline-flex w-fit items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                        <span aria-hidden="true">⚠</span> Demo data: sample records, not live information.
                      </p>
                    )}
                  </div>
                </Message>
              ),
            )}
            {isLoading && (
              <Message className="items-start">
                <span className="mt-1 size-8 shrink-0 rounded-full bg-muted" aria-hidden="true" />
                <SkeletonCards />
              </Message>
            )}
            <ChatContainerScrollAnchor />
          </ChatContainerContent>
        </ChatContainerRoot>
        <PromptInput
          value={input}
          onValueChange={setInput}
          onSubmit={() => send(input)}
          isLoading={isLoading}
          className="rounded-2xl border-border/70 bg-card shadow-lg"
        >
          <PromptInputTextarea aria-label="Message" placeholder="Where are you headed?" />
          <PromptInputActions className="justify-end">
            <Button onClick={() => send(input)} disabled={isLoading || !input.trim()} className="rounded-full px-4">
              Send
            </Button>
          </PromptInputActions>
        </PromptInput>
      </main>
    </div>
  );
}
