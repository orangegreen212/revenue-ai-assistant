"use client";

import { useEffect, useState } from "react";
import { getLiveMetrics, type LiveMetrics } from "@/lib/api";

export default function LiveMetricsCard() {
  const [data, setData] = useState<LiveMetrics | null | "error">(null);

  useEffect(() => {
    getLiveMetrics()
      .then(setData)
      .catch(() => setData("error"));
  }, []);

  if (data === "error") return null;
  if (!data) {
    return (
      <div className="px-5 py-4 border-t border-[var(--border)] text-xs text-[var(--muted)]">
        No live snapshot yet
      </div>
    );
  }

  return (
    <div className="px-5 py-4 border-t border-[var(--border)]">
      <div className="text-xs section-number mb-2">Live · as of {data.as_of}</div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="text-[var(--muted)]">MRR</div>
          <div className="text-[var(--foreground)]">${data.mrr.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[var(--muted)]">Customers</div>
          <div className="text-[var(--foreground)]">{data.active_customers}</div>
        </div>
        {data.mom_mrr_growth_pct != null && (
          <div>
            <div className="text-[var(--muted)]">MoM growth</div>
            <div className={data.mom_mrr_growth_pct >= 0 ? "text-[var(--accent)]" : "text-red-400"}>
              {data.mom_mrr_growth_pct}%
            </div>
          </div>
        )}
        {data.logo_churn_rate_pct != null && (
          <div>
            <div className="text-[var(--muted)]">Logo churn</div>
            <div className="text-[var(--foreground)]">{data.logo_churn_rate_pct}%</div>
          </div>
        )}
      </div>
    </div>
  );
}
