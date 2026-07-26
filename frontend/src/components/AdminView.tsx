"use client";

import { useState } from "react";
import { getAdminLogs, getAdminStats, runEvaluation, type AdminStats, type EvalResult, type LogRow } from "@/lib/api";

export default function AdminView() {
  const [token, setToken] = useState("");
  const [logs, setLogs] = useState<LogRow[] | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runEval() {
    setEvalLoading(true);
    setEvalError(null);
    try {
      const result = await runEvaluation(token);
      setEvalResult(result);
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : String(err));
      setEvalResult(null);
    } finally {
      setEvalLoading(false);
    }
  }

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [s, l] = await Promise.all([getAdminStats(token), getAdminLogs(token)]);
      setStats(s);
      setLogs(l);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStats(null);
      setLogs(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <header className="px-8 py-6 border-b border-[var(--border)]">
        <div className="text-xs section-number mb-1">04 — Admin</div>
        <h2 className="font-display text-2xl">Logging &amp; Monitoring</h2>
        <p className="text-sm text-[var(--muted)] mt-2">
          Every /api/chat, /api/csv-chat and /api/kpi call is logged: latency, which tools fired, errors.
        </p>
      </header>

      <div className="px-8 py-6 max-w-3xl space-y-6">
        <div className="flex gap-3">
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Admin token (REFRESH_TOKEN / ADMIN_TOKEN)"
            className="flex-1 bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
          />
          <button
            onClick={load}
            disabled={loading || !token}
            className="px-5 py-3 rounded-md bg-[var(--accent)] text-black text-sm font-medium disabled:opacity-50"
          >
            Load
          </button>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="Total requests" value={stats.total_requests} />
            <StatCard label="Error rate" value={`${stats.error_rate_pct}%`} />
            <StatCard label="Avg latency" value={`${stats.avg_latency_ms} ms`} />
            <StatCard label="Errors" value={stats.error_count} />
          </div>
        )}

        {stats && stats.by_endpoint.length > 0 && (
          <div>
            <p className="text-xs section-number mb-2">By endpoint</p>
            <div className="border border-[var(--border)] rounded-md overflow-hidden text-sm">
              {stats.by_endpoint.map((e) => (
                <div
                  key={e.endpoint}
                  className="flex justify-between px-4 py-2 border-b border-[var(--border)] last:border-0"
                >
                  <span>{e.endpoint}</span>
                  <span className="text-[var(--muted)]">
                    {e.n} calls · {Math.round(e.avg_ms)} ms avg
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {logs && (
          <div>
            <p className="text-xs section-number mb-2">Recent requests</p>
            <div className="overflow-x-auto border border-[var(--border)] rounded-md">
              <table className="text-xs w-full">
                <thead>
                  <tr className="bg-[var(--surface-2)]">
                    <th className="px-3 py-2 text-left">Time</th>
                    <th className="px-3 py-2 text-left">Endpoint</th>
                    <th className="px-3 py-2 text-left">Query</th>
                    <th className="px-3 py-2 text-left">Tools</th>
                    <th className="px-3 py-2 text-left">ms</th>
                    <th className="px-3 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((row) => (
                    <tr key={row.id} className="border-t border-[var(--border)]">
                      <td className="px-3 py-2 whitespace-nowrap">
                        {new Date(row.created_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-2">{row.endpoint}</td>
                      <td className="px-3 py-2 max-w-[200px] truncate">{row.query_preview}</td>
                      <td className="px-3 py-2">{row.tools_used || "—"}</td>
                      <td className="px-3 py-2">{row.latency_ms}</td>
                      <td className={`px-3 py-2 ${row.status === "error" ? "text-red-400" : "text-[var(--accent)]"}`}>
                        {row.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="pt-6 border-t border-[var(--border)]">
          <p className="text-xs section-number mb-2">05 — RAG Retrieval Evaluation</p>
          <p className="text-sm text-[var(--muted)] mb-3">
            Runs the knowledge base questions against the vector store and checks whether the
            expected document appears in the Top-1 / Top-3 retrieved chunks.
          </p>
          <button
            onClick={runEval}
            disabled={evalLoading || !token}
            className="px-5 py-3 rounded-md bg-[var(--accent)] text-black text-sm font-medium disabled:opacity-50"
          >
            {evalLoading ? "Running..." : "Run Evaluation"}
          </button>

          {evalError && <p className="text-red-400 text-sm mt-3">{evalError}</p>}

          {evalResult && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <StatCard label="Top-1 Accuracy" value={`${evalResult.summary.top1_accuracy_pct}%`} />
                <StatCard label="Top-3 Accuracy" value={`${evalResult.summary.top3_accuracy_pct}%`} />
                <StatCard label="Avg Retrieval" value={`${evalResult.summary.avg_retrieval_ms} ms`} />
              </div>
              <div className="overflow-x-auto border border-[var(--border)] rounded-md">
                <table className="text-xs w-full">
                  <thead>
                    <tr className="bg-[var(--surface-2)]">
                      <th className="px-3 py-2 text-left">Question</th>
                      <th className="px-3 py-2 text-left">Expected</th>
                      <th className="px-3 py-2 text-left">Top-1</th>
                      <th className="px-3 py-2 text-left">Top-3</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evalResult.rows.map((row, i) => (
                      <tr key={i} className="border-t border-[var(--border)]">
                        <td className="px-3 py-2 max-w-[280px] truncate">{row.question}</td>
                        <td className="px-3 py-2">{row.expected_document}</td>
                        <td className="px-3 py-2">{row.top1_success ? "✅" : "❌"}</td>
                        <td className="px-3 py-2">{row.top3_success ? "✅" : "❌"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border border-[var(--border)] rounded-md px-4 py-3 bg-[var(--surface)]">
      <div className="text-xs text-[var(--muted)]">{label}</div>
      <div className="font-display text-xl mt-1">{value}</div>
    </div>
  );
}
