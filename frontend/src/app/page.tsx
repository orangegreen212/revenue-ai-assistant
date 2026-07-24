"use client";

import { useState } from "react";
import Sidebar, { type View } from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import CsvView from "@/components/CsvView";
import KpiView from "@/components/KpiView";
import AdminView from "@/components/AdminView";
import type { Lang } from "@/lib/api";

export default function Home() {
  const [view, setView] = useState<View>("chat");
  const [lang, setLang] = useState<Lang>("en");

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <Sidebar view={view} setView={setView} lang={lang} setLang={setLang} />
      <main className="flex-1 min-w-0">
        {view === "chat" && <ChatView lang={lang} />}
        {view === "csv" && <CsvView lang={lang} />}
        {view === "kpi" && <KpiView lang={lang} />}
        {view === "admin" && <AdminView />}
      </main>
    </div>
  );
}
