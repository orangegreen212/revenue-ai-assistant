// Called by Vercel Cron on a schedule (see vercel.json). Vercel Cron can only
// hit routes inside this Next.js app, so this route is a thin proxy that
// forwards to the FastAPI backend with the shared refresh secret attached —
// the secret never has to live in the browser or in vercel.json itself.
export async function GET() {
  const backendUrl = process.env.BACKEND_URL;
  const refreshToken = process.env.REFRESH_TOKEN;

  if (!backendUrl || !refreshToken) {
    return Response.json(
      { error: "BACKEND_URL or REFRESH_TOKEN not configured in Vercel env vars." },
      { status: 500 }
    );
  }

  const res = await fetch(`${backendUrl}/api/live-metrics/refresh`, {
    method: "POST",
    headers: { "x-refresh-token": refreshToken },
  });

  const body = await res.json();
  return Response.json(body, { status: res.status });
}
