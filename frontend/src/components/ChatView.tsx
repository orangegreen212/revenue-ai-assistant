"use client";

import { useState } from "react";
import type { Lang } from "@/lib/api";
import { sendChat } from "@/lib/api";
import { STRINGS } from "@/lib/strings";
import MarkdownMessage from "./MarkdownMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Record<string, unknown>[];
  note?: string | null;
  error?: boolean;
}

export default function ChatView({ lang }: { lang: Lang }) {
  const T = STRINGS[lang];
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const query = input.trim();
    if (!query || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: query }]);
    setLoading(true);
    try {
      const res = await sendChat(query, lang);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources, note: res.retrieval_note },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: err instanceof Error ? err.message : String(err), error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <header className="px-8 py-6 border-b border-[var(--border)]">
        <div className="text-xs section-number mb-1">01 — {T.navChat}</div>
        <h2 className="font-display text-2xl">{T.chatHeader}</h2>
      </header>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-8 py-6 space-y-4">
        {messages.length === 0 && (
          <p className="text-[var(--muted)] text-sm">{T.chatPlaceholder}</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-lg px-4 py-3 ${
                m.role === "user"
                  ? "text-sm whitespace-pre-wrap bg-[var(--accent)] text-black"
                  : m.error
                  ? "text-sm whitespace-pre-wrap bg-red-950 text-red-200 border border-red-800"
                  : "bg-[var(--surface-2)] text-[var(--foreground)] border border-[var(--border)]"
              }`}
            >
              {m.role === "assistant" && !m.error ? (
                <MarkdownMessage content={m.content} />
              ) : (
                m.content
              )}
              {m.note && (
                <p className="mt-2 text-xs text-amber-400 border-t border-amber-900/40 pt-2">
                  ⚠ {m.note}
                </p>
              )}
              {m.role === "assistant" && !m.error && (
                <details className="mt-2 text-xs opacity-70" open={!!(m.sources && m.sources.length > 0)}>
                  <summary className="cursor-pointer">{T.sources}</summary>
                  {m.sources && m.sources.length > 0 ? (
                    <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(m.sources, null, 2)}</pre>
                  ) : (
                    <p className="mt-1">{T.noSources}</p>
                  )}
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-[var(--muted)] text-sm">{T.thinking}</p>}
      </div>

      <div className="px-8 py-5 border-t border-[var(--border)] flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={T.chatPlaceholder}
          className="flex-1 bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="px-5 py-3 rounded-md bg-[var(--accent)] text-black text-sm font-medium disabled:opacity-50"
        >
          {T.send}
        </button>
      </div>
    </div>
  );
}
