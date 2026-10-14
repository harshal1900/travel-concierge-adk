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

type ChatMessage = { role: "user" | "assistant"; text: string; isError?: boolean };

export default function Home() {
  const sessionId = useRef<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function send() {
    const text = input.trim();
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
      setMessages((m) => [...m, { role: "assistant", text: data.agent_text }]);
    } catch (error) {
      const text = error instanceof Error ? error.message : "Something went wrong.";
      setMessages((m) => [...m, { role: "assistant", text, isError: true }]);
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
            <p className="text-muted-foreground">
              Ask about sightseeing or dining in a city, e.g. “Plan a day in Tokyo with sightseeing and dinner”.
            </p>
          )}
          {messages.map((m, i) => (
            <Message key={i} className={m.role === "user" ? "justify-end" : ""}>
              <MessageContent
                markdown={m.role === "assistant" && !m.isError}
                className={m.isError ? "text-destructive" : undefined}
              >
                {m.isError ? `Error: ${m.text}` : m.text}
              </MessageContent>
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
      <PromptInput value={input} onValueChange={setInput} onSubmit={send} isLoading={isLoading}>
        <PromptInputTextarea aria-label="Message" placeholder="Where are you headed?" />
        <PromptInputActions className="justify-end">
          <Button onClick={send} disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </PromptInputActions>
      </PromptInput>
    </main>
  );
}
