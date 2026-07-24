"use client";

import type { Lang } from "@/lib/api";
import { STRINGS } from "@/lib/strings";
import LiveMetricsCard from "./LiveMetricsCard";

export type View = "chat" | "csv" | "kpi" | "admin";

export default function Sidebar({
  view,
  setView,
  lang,
  setLang,
}: {
  view: View;
  setView: (v: View) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
}) {
  const T = STRINGS[lang];

  const navItem = (key: View, label: string, index: string) => (
    <button
      onClick={() => setView(key)}
      className={`w-full text-left px-4 py-3 rounded-md transition-colors flex items-baseline gap-3 ${
        view === key
          ? "bg-[var(--surface-2)] text-[var(--foreground)]"
          : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-[var(--surface)]"
      }`}
    >
      <span className="section-number text-xs">{index}</span>
      <span className="text-sm">{label}</span>
    </button>
  );

  return (
    <aside className="w-64 shrink-0 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col h-full">
      <div className="px-5 py-6 border-b border-[var(--border)]">
        <div className="text-xs section-number mb-1">AI · ANALYST</div>
        <h1 className="font-display text-xl leading-tight">
          {T.brand.split(" ")[0]}{" "}
          <span className="accent-italic">{T.brand.split(" ").slice(1).join(" ")}</span>
        </h1>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItem("chat", T.navChat, "01")}
        {navItem("csv", T.navCsv, "02")}
        {navItem("kpi", T.navKpi, "03")}
        {navItem("admin", "Admin / Logs", "04")}
      </nav>

      <div className="px-5 py-5 border-t border-[var(--border)]">
        <div className="text-xs section-number mb-2">Language / Мова</div>
        <div className="flex rounded-md overflow-hidden border border-[var(--border)] text-sm">
          <button
            onClick={() => setLang("en")}
            className={`flex-1 py-2 ${
              lang === "en" ? "bg-[var(--accent)] text-black font-medium" : "bg-transparent text-[var(--muted)]"
            }`}
          >
            EN
          </button>
          <button
            onClick={() => setLang("uk")}
            className={`flex-1 py-2 ${
              lang === "uk" ? "bg-[var(--accent)] text-black font-medium" : "bg-transparent text-[var(--muted)]"
            }`}
          >
            UK
          </button>
        </div>
      </div>

      <LiveMetricsCard />
    </aside>
  );
}
