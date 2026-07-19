import type { FounderProfile, PipelineResult } from "./types";

let accessToken = sessionStorage.getItem("vcbrain_token") ?? "";

export function setAccessToken(token: string) {
  accessToken = token;
  sessionStorage.setItem("vcbrain_token", token);
}

export function clearAccessToken() {
  accessToken = "";
  sessionStorage.removeItem("vcbrain_token");
}

export function hasAccessToken() {
  return Boolean(accessToken);
}

function headers(json = true): HeadersInit {
  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };
}

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
    headers: headers(),
    body: JSON.stringify({ query, max_results: maxResults ?? null }),
  }).then((r) => handle<PipelineResult>(r));
}

export function runMaschmeyerScout(maxResults = 3): Promise<PipelineResult> {
  return fetch(`/api/scout/maschmeyer?max_results=${maxResults}`, {
    method: "POST",
    headers: headers(false),
  }).then((r) => handle<PipelineResult>(r));
}

export function generateOutreach(
  founder: FounderProfile,
): Promise<{ message: string; provider: string }> {
  return fetch("/api/outreach", {
    method: "POST",
    headers: headers(),
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

export function login(username: string, password: string): Promise<{ access_token: string }> {
  return fetch("/api/auth/login", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ username, password }),
  }).then((r) => handle<{ access_token: string }>(r));
}

export function translateText(text: string, language: "es" | "en" | "de"): Promise<{ text: string }> {
  return fetch("/api/translate", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ text, language }),
  }).then((r) => handle<{ text: string }>(r));
}

export function translateBatch(
  texts: string[],
  language: "es" | "en" | "de",
): Promise<{ texts: string[] }> {
  return fetch("/api/translate/batch", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ texts, language }),
  }).then((r) => handle<{ texts: string[]; language: string }>(r));
}

export function fetchHealth(): Promise<{ default_language?: string; languages?: string[] }> {
  return fetch("/api/health").then((r) => handle<{ default_language?: string; languages?: string[] }>(r));
}
