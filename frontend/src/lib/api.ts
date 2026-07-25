const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Lang = "en" | "uk";

export interface ChatResponse {
  answer: string;
  sources: Record<string, unknown>[];
  retrieval_note?: string | null;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function sendChat(query: string, lang: Lang): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, lang }),
  });
  return handle<ChatResponse>(res);
}

export async function uploadCsv(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/upload-csv`, {
    method: "POST",
    body: form,
  });
  return handle<{
    file_id: string;
    rows: number;
    columns: string[];
    preview: Record<string, unknown>[];
  }>(res);
}

export async function sendCsvChat(fileId: string, query: string, lang: Lang): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/csv-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, query, lang }),
  });
  return handle<ChatResponse>(res);
}

export async function calcKpi(
  kpiName: string,
  valueA: number,
  valueB: number,
  valueC: number | null,
  lang: Lang
) {
  const res = await fetch(`${API_URL}/api/kpi`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kpi_name: kpiName,
      value_a: valueA,
      value_b: valueB,
      value_c: valueC,
      lang,
    }),
  });
  return handle<{ metric: string; result: string; benchmark: string }>(res);
}

export interface LiveMetrics {
  as_of: string;
  mrr: number;
  arr: number;
  active_customers: number;
  arpu: number | null;
  mrr_prev_month?: number;
  mom_mrr_growth_pct?: number | null;
  logo_churn_rate_pct?: number | null;
  new_customers?: number;
  generated_at: string;
}

export async function getLiveMetrics(): Promise<LiveMetrics | null> {
  const res = await fetch(`${API_URL}/api/live-metrics`);
  if (res.status === 404) return null;
  return handle<LiveMetrics>(res);
}

export interface LogRow {
  id: number;
  created_at: string;
  endpoint: string;
  lang: string | null;
  query_preview: string | null;
  tools_used: string | null;
  latency_ms: number;
  status: string;
  error_message: string | null;
}

export interface AdminStats {
  total_requests: number;
  error_count: number;
  error_rate_pct: number;
  avg_latency_ms: number;
  by_endpoint: { endpoint: string; n: number; avg_ms: number }[];
  by_tools_used: { tools_used: string; n: number }[];
}

export async function getAdminLogs(token: string): Promise<LogRow[]> {
  const res = await fetch(`${API_URL}/api/admin/logs`, {
    headers: { "x-admin-token": token },
  });
  const body = await handle<{ logs: LogRow[] }>(res);
  return body.logs;
}

export async function getAdminStats(token: string): Promise<AdminStats> {
  const res = await fetch(`${API_URL}/api/admin/stats`, {
    headers: { "x-admin-token": token },
  });
  return handle<AdminStats>(res);
}
