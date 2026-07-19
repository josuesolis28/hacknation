export interface CriterionScore {
  name: string;
  weight: number;
  score: number;
  rationale: string;
}

export interface Requirement {
  name: string;
  met: boolean;
  detail: string;
}

export interface Check {
  check_id: string;
  amount_usd: number;
  issued_to: string;
  company: string;
  issued_by: string;
  date: string;
  status: string;
}

export interface FounderProfile {
  name: string;
  company: string;
  role: string;
  founder_score: number;
  justification: string;
  criteria: CriterionScore[];
  requirements: Requirement[];
  evidence: string[];
  signals: string[];
  contact_hint: string;
  decision: "approved" | "rejected";
  feedback: string[];
  check: Check | null;
}

export interface SearchHit {
  title: string;
  url: string;
  content: string;
  score: number;
}

export interface PipelineResult {
  query: string;
  provider_used: string;
  founders: FounderProfile[];
  raw_hits: SearchHit[];
  errors: string[];
}
