"use client";

import { useState } from "react";
import type { Lang } from "@/lib/api";
import { calcKpi } from "@/lib/api";
import { KPI_LABELS, STRINGS } from "@/lib/strings";

export default function KpiView({ lang }: { lang: Lang }) {
  const T = STRINGS[lang];
  const fields = KPI_LABELS[lang];
  const metricKeys = Object.keys(fields);

  const [metric, setMetric] = useState(metricKeys[0]);
  const [values, setValues] = useState<Record<string, number>>({});
  const [result, setResult] = useState<string | null>(null);
  const [resultMetric, setResultMetric] = useState<string | null>(null);
  const [benchmark, setBenchmark] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateMetric(m: string) {
    setMetric(m);
    setValues({});
    setResult(null);
    setBenchmark(null);
    setError(null);
  }

  async function handleCalculate() {
    setLoading(true);
    setError(null);
    try {
      const res = await calcKpi(
        metric,
        values.value_a ?? 0,
        values.value_b ?? 0,
        values.value_c ?? null,
        lang
      );
      setResult(res.result);
      setResultMetric(res.metric);
      setBenchmark(res.benchmark);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <header className="px-8 py-6 border-b border-[var(--border)]">
        <div className="text-xs section-number mb-1">03 — {T.navKpi}</div>
        <h2 className="font-display text-2xl">{T.kpiHeader}</h2>
        <p className="text-sm text-[var(--muted)] mt-2">{T.kpiCaption}</p>
      </header>

      <div className="px-8 py-6 max-w-xl space-y-5">
        <div>
          <label className="block text-xs section-number mb-2">{T.kpiMetricLabel}</label>
          <select
            value={metric}
            onChange={(e) => updateMetric(e.target.value)}
            className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
          >
            {metricKeys.map((k) => (
              <option key={k} value={k}>
                {k.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {fields[metric].map(([field, label]) => (
          <div key={field}>
            <label className="block text-xs text-[var(--muted)] mb-2">{label}</label>
            <input
              type="number"
              step="any"
              value={values[field] ?? (field === "value_c" ? 0.8 : 0)}
              onChange={(e) =>
                setValues((v) => ({ ...v, [field]: parseFloat(e.target.value) || 0 }))
              }
              className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
            />
          </div>
        ))}

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="px-5 py-3 rounded-md bg-[var(--accent)] text-black text-sm font-medium disabled:opacity-50"
        >
          {T.kpiCalcButton}
        </button>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {result && (
          <div className="rounded-md border border-[var(--accent-dim)] bg-[var(--surface-2)] px-4 py-3 text-sm">
            {resultMetric && (
              <p className="text-xs text-[var(--muted)] mb-1">
                metric computed by backend: <span className="text-[var(--accent)]">{resultMetric}</span>
              </p>
            )}
            {result}
          </div>
        )}

        {benchmark && (
          <details className="text-sm" open>
            <summary className="cursor-pointer text-xs section-number">{T.kpiBenchmark}</summary>
            <pre className="mt-2 whitespace-pre-wrap text-[var(--muted)] text-xs leading-relaxed">
              {benchmark}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
