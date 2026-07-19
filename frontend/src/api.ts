import type { FounderProfile, PipelineResult } from "./types";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* cuerpo no-JSON */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function runScout(query: string, maxResults?: number): Promise<PipelineResult> {
  return fetch("/api/scout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, max_results: maxResults ?? null }),
  }).then((r) => handle<PipelineResult>(r));
}

export function runMaschmeyerScout(maxResults = 3): Promise<PipelineResult> {
  return fetch(`/api/scout/maschmeyer?max_results=${maxResults}`, {
    method: "POST",
  }).then((r) => handle<PipelineResult>(r));
}

export function generateOutreach(
  founder: FounderProfile,
): Promise<{ message: string; provider: string }> {
  return fetch("/api/outreach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: founder.name,
      company: founder.company,
      role: founder.role,
      signals: founder.signals,
      justification: founder.justification,
      evidence: founder.evidence,
    }),
  }).then((r) => handle<{ message: string; provider: string }>(r));
}
