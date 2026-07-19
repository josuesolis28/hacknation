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

export interface SocialLink {
  platform: string;
  url: string;
  label?: string;
}

export interface TeamMember {
  name: string;
  role: string;
  relationship: "founder" | "cofounder" | "executive" | "advisor" | string;
  skills: string[];
  area: string;
  profile_url: string;
}

export interface FundingRound {
  investor: string;
  amount: string;
  round_name: string;
  date: string;
}

export type TrafficLight = "green" | "yellow" | "red";

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
  country?: string;
  country_code?: string;
  origin_region?: string;
  origin_confidence?: "confirmed" | "inferred" | "unknown" | string;
  skills?: string[];
  area?: string;
  social_links?: SocialLink[];
  capital_raised?: string;
  capital_note?: string;
  clients?: string[];
  business_model?: string;
  impact_summary?: string;
  impact_metrics?: string[];
  incubation_program?: string;
  tec_related?: boolean;
  business_email?: string;
  section?: string;
  activity_summary?: string;
  round_size?: string;
  pitch?: string;
  other_info?: string;
  traffic_light: TrafficLight;
  team: TeamMember[];
  total_capital: string;
  funding_rounds: FundingRound[];
  revenue_signal: string;
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

export interface ProfileNode {
  name: string;
  role: string;
  relationship: "founder" | "executive" | "advisor" | "company" | string;
  description: string;
  skills?: string[];
  area?: string;
  sources: string[];
}

export interface Citation {
  title: string;
  url: string;
}

export interface ProfileNetwork {
  subject: { name: string; company: string; role: string };
  summary: string;
  nodes: ProfileNode[];
  social_links?: SocialLink[];
  citations: Citation[];
  provider: string;
}
