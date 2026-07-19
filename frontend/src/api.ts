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

export function getAuthConfig(): Promise<{ google_client_id: string }> {
  return fetch("/api/auth/config").then((r) => handle<{ google_client_id: string }>(r));
}

export function loginWithGoogle(credential: string): Promise<{ access_token: string }> {
  return fetch("/api/auth/google", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ credential }),
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

export function getLatestScan(): Promise<{ result: PipelineResult | null }> {
  return fetch("/api/scout/latest", { headers: headers(false) }).then((r) =>
    handle<{ result: PipelineResult | null }>(r),
  );
}

export type DecisionState = "forced" | "discarded" | "clear";

export function getDecisions(): Promise<{ decisions: Record<string, DecisionState> }> {
  return fetch("/api/decisions", { headers: headers(false) }).then((r) =>
    handle<{ decisions: Record<string, DecisionState> }>(r),
  );
}

export function setDecision(company: string, name: string, state: DecisionState): Promise<{ ok: boolean }> {
  return fetch("/api/decisions", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ company, name, state }),
  }).then((r) => handle<{ ok: boolean }>(r));
}

export function decisionKey(company: string, name: string): string {
  return `${company.trim().toLowerCase()}|${name.trim().toLowerCase()}`;
}

export type TicketStatus = "approved" | "rejected" | "follow_up" | "completed" | "clear";

export function getTickets(): Promise<{ tickets: Record<string, TicketStatus> }> {
  return fetch("/api/tickets", { headers: headers(false) }).then((r) =>
    handle<{ tickets: Record<string, TicketStatus> }>(r),
  );
}

export function setTicketStatus(company: string, name: string, status: TicketStatus): Promise<{ ok: boolean }> {
  return fetch("/api/tickets", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ company, name, status }),
  }).then((r) => handle<{ ok: boolean }>(r));
}

export interface CompanyRecord {
  founder: FounderProfile;
  first_seen: string;
  last_seen: string;
  times_seen: number;
}

export function getCompanies(): Promise<{ companies: CompanyRecord[] }> {
  return fetch("/api/companies", { headers: headers(false) }).then((r) =>
    handle<{ companies: CompanyRecord[] }>(r),
  );
}

export interface FormMeta {
  sections: string[];
  round_sizes: string[];
  countries: { name: string; code: string }[];
}

export function getMeta(): Promise<FormMeta> {
  return fetch("/api/meta", { headers: headers(false) }).then((r) => handle<FormMeta>(r));
}

export interface SubmissionTeamMember {
  name: string;
  role: string;
}

export interface SubmissionPayload {
  company: string;
  name: string;
  role: string;
  country: string;
  website: string;
  section: string;
  round_size: string;
  pitch: string;
  extra_text: string;
  video_url: string;
  business_email: string;
  linkedin: string;
  instagram: string;
  x_url: string;
  team: SubmissionTeamMember[];
  pdf: File | null;
}

export function submitStartup(payload: SubmissionPayload): Promise<{ founder: FounderProfile }> {
  const form = new FormData();
  form.set("company", payload.company);
  form.set("name", payload.name);
  form.set("role", payload.role);
  form.set("country", payload.country);
  form.set("website", payload.website);
  form.set("section", payload.section);
  form.set("round_size", payload.round_size);
  form.set("pitch", payload.pitch);
  form.set("extra_text", payload.extra_text);
  form.set("video_url", payload.video_url);
  form.set("business_email", payload.business_email);
  form.set("linkedin", payload.linkedin);
  form.set("instagram", payload.instagram);
  form.set("x_url", payload.x_url);
  form.set("team", JSON.stringify(payload.team.filter((m) => m.name.trim())));
  if (payload.pdf) form.set("pdf", payload.pdf);

  return fetch("/api/submissions", {
    method: "POST",
    headers: headers(false), // sin Content-Type: el navegador pone el boundary del multipart
    body: form,
  }).then((r) => handle<{ founder: FounderProfile }>(r));
}

export type SubmissionStatus = "submitted" | "in_progress" | "approved" | "rejected";

export interface SubmissionFile {
  id: number;
  kind: "pdf" | "image" | "video";
  filename: string;
  content_type: string;
  url: string | null;
}

export function submissionFileUrl(fileId: number): string {
  return `/api/submissions/files/${fileId}`;
}

/** El token va en el header Authorization (no en cookies), así que un
 * <img src=...>/<a href=...> normal no lo puede pedir — hay que traerlo con
 * fetch autenticado y convertirlo a una blob: URL para mostrarlo/abrirlo. */
export async function fetchSubmissionFileBlobUrl(fileId: number): Promise<string> {
  const res = await fetch(submissionFileUrl(fileId), { headers: headers(false) });
  if (!res.ok) throw new Error(res.statusText);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export interface MySubmission {
  company: string;
  name: string;
  created_at: string;
  status: SubmissionStatus;
  founder: FounderProfile | null;
  files: SubmissionFile[];
}

export function getMySubmissions(): Promise<{ submissions: MySubmission[] }> {
  return fetch("/api/submissions/mine", { headers: headers(false) }).then((r) =>
    handle<{ submissions: MySubmission[] }>(r),
  );
}

export function getAllSubmissions(): Promise<{ founders: FounderProfile[] }> {
  return fetch("/api/submissions", { headers: headers(false) }).then((r) =>
    handle<{ founders: FounderProfile[] }>(r),
  );
}
