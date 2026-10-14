"use client";

import { useRef, useState } from "react";
import {
  ChatContainerContent,
  ChatContainerRoot,
  ChatContainerScrollAnchor,
} from "@/components/ui/chat-container";
import { Loader } from "@/components/ui/loader";
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
    <main className="mx-auto flex h-dvh w-full max-w-3xl flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">Smart Travel Concierge</h1>
      <ChatContainerRoot className="flex-1">
        <ChatContainerContent className="gap-4 p-2">
          {messages.length === 0 && (
            <div className="flex flex-col gap-3">
              <p className="text-muted-foreground">
                Ask about sightseeing or dining in a city. Include the place in your message.
              </p>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Starter prompts">
                {STARTERS.map((s) => (
                  <Button key={s} variant="outline" size="sm" onClick={() => send(s)}>
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <Message key={i} className={m.role === "user" ? "justify-end" : ""}>
              <div className="flex max-w-full flex-col gap-3">
                <MessageContent
                  markdown={m.role === "assistant" && !m.isError}
                  className={m.isError ? "text-destructive" : undefined}
                  role={m.isError ? "alert" : undefined}
                >
                  {m.isError ? `Error: ${m.text}` : m.text}
                </MessageContent>
                {m.components && m.components.length > 0 && <ComponentRenderer components={m.components} />}
                {m.role === "assistant" && !m.isError && isDemoText(m.text) && (
                  <p className="text-xs font-medium text-muted-foreground">
                    ⚠ Demo data: sample records, not live information.
                  </p>
                )}
              </div>
            </Message>
          ))}
          {isLoading && (
            <div role="status" aria-label="Assistant is typing">
              <Loader variant="typing" />
            </div>
          )}
          <ChatContainerScrollAnchor />
        </ChatContainerContent>
      </ChatContainerRoot>
      <PromptInput value={input} onValueChange={setInput} onSubmit={() => send(input)} isLoading={isLoading}>
        <PromptInputTextarea aria-label="Message" placeholder="Where are you headed?" />
        <PromptInputActions className="justify-end">
          <Button onClick={() => send(input)} disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </PromptInputActions>
      </PromptInput>
    </main>
  );
}
