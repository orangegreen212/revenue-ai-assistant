"use client";

import { useRef, useState } from "react";
import type { Lang } from "@/lib/api";
import { sendCsvChat, uploadCsv } from "@/lib/api";
import { STRINGS } from "@/lib/strings";

interface Message {
  role: "user" | "assistant";
  content: string;
  error?: boolean;
}

export default function CsvView({ lang }: { lang: Lang }) {
  const T = STRINGS[lang];
  const fileInput = useRef<HTMLInputElement>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [preview, setPreview] = useState<Record<string, unknown>[]>([]);
  const [rows, setRows] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    try {
      const res = await uploadCsv(file);
      setFileId(res.file_id);
      setColumns(res.columns);
      setPreview(res.preview);
      setRows(res.rows);
      setMessages([]);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleSend() {
    const query = input.trim();
    if (!query || loading || !fileId) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: query }]);
    setLoading(true);
    try {
      const res = await sendCsvChat(fileId, query, lang);
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
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
        <div className="text-xs section-number mb-1">02 — {T.navCsv}</div>
        <h2 className="font-display text-2xl">{T.csvHeader}</h2>
      </header>

      <div className="px-8 py-6 border-b border-[var(--border)]">
        <label className="block text-sm text-[var(--muted)] mb-2">{T.csvUploader}</label>
        <input
          ref={fileInput}
          type="file"
          accept=".csv"
          onChange={handleFile}
          className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-[var(--accent)] file:text-black file:text-sm file:font-medium file:cursor-pointer cursor-pointer text-[var(--muted)]"
        />
        {uploadError && <p className="text-red-400 text-xs mt-2">{uploadError}</p>}

        {columns.length > 0 && (
          <div className="mt-4">
            <p className="text-xs section-number mb-2">
              {T.csvPreview} — {rows} rows
            </p>
            <div className="overflow-x-auto border border-[var(--border)] rounded-md">
              <table className="text-xs w-full">
                <thead>
                  <tr className="bg-[var(--surface-2)]">
                    {columns.map((c) => (
                      <th key={c} className="px-3 py-2 text-left font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i} className="border-t border-[var(--border)]">
                      {columns.map((c) => (
                        <td key={c} className="px-3 py-2">
                          {String(row[c])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-8 py-6 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-[var(--accent)] text-black"
                  : m.error
                  ? "bg-red-950 text-red-200 border border-red-800"
                  : "bg-[var(--surface-2)] border border-[var(--border)]"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && <p className="text-[var(--muted)] text-sm">{T.analyzing}</p>}
      </div>

      <div className="px-8 py-5 border-t border-[var(--border)] flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={T.csvPlaceholder}
          disabled={!fileId}
          className="flex-1 bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-4 py-3 text-sm outline-none focus:border-[var(--accent)] disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={loading || !fileId}
          className="px-5 py-3 rounded-md bg-[var(--accent)] text-black text-sm font-medium disabled:opacity-50"
        >
          {T.send}
        </button>
      </div>
    </div>
  );
}
