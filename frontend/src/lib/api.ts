const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

// ------------------------------------------------------------------ //
//  Auth (Milestone D) — bearer token + demo accounts
// ------------------------------------------------------------------ //
const TOKEN_KEY = "bv_token";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "Administrator" | "Creator" | "Reviewer";
  org_id: string;
  auth_provider?: "password" | "google";
}

// Demo credentials for the NOVA TECH judging workspace (not production secrets).
export const DEMO_CREDS: Record<string, { email: string; password: string }> = {
  Administrator: { email: "admin@novatech.demo", password: "Admin@2026" },
  Creator: { email: "creator@novatech.demo", password: "Creator@2026" },
  Reviewer: { email: "reviewer@novatech.demo", password: "Reviewer@2026" },
};

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function setToken(t: string) {
  try { localStorage.setItem(TOKEN_KEY, t); } catch { /* ignore */ }
}
export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}
export function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function login(email: string, password: string): Promise<AuthUser> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    // fetch() rejects only on a network-level failure (server down, CORS, DNS).
    throw new Error(`Can't reach the server. Make sure the backend is running at ${API_BASE.replace(/\/api\/v1\/?$/, "")}.`);
  }
  if (res.status === 401) throw new Error("Invalid email or password. Try a demo account below.");
  if (!res.ok) throw new Error(`Sign-in failed (server error ${res.status}). Please try again.`);
  const data = await res.json();
  setToken(data.access_token);
  return data.user as AuthUser;
}

export async function register(payload: {
  full_name: string;
  email: string;
  password: string;
}): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = "Could not create account.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) msg = body.detail[0].msg;
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  const data = await res.json();
  setToken(data.access_token);
  return data.user as AuthUser;
}

// Whether the server has Google OAuth configured (client id + secret present).
export async function fetchGoogleAuthStatus(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/google/status`, { cache: "no-store" });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data.configured);
  } catch {
    return false;
  }
}

// Full-page redirect entry point for the Google authorization-code flow.
export function googleLoginUrl(): string {
  return `${API_BASE}/auth/google/login`;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const t = getToken();
  if (!t) return null;
  const res = await fetch(`${API_BASE}/auth/me`, { headers: { ...authHeaders() }, cache: "no-store" });
  if (!res.ok) { clearToken(); return null; }
  return res.json();
}

// Ensure a session with the given demo role (logs in if needed or role differs).
export async function ensureDemoLogin(role: "Administrator" | "Creator" | "Reviewer"): Promise<AuthUser> {
  const current = await fetchCurrentUser();
  if (current && current.role === role) return current;
  const creds = DEMO_CREDS[role];
  return login(creds.email, creds.password);
}

export interface HealthInfo {
  status: string;
  service: string;
  tagline: string;
  version: string;
  database: string;
  timestamp: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  guidelines_count: number;
  rules_count: number;
  facts_count: number;
}

export interface BrandRule {
  id: string;
  org_id: string;
  category: string;
  title: string;
  rule_text: string;
  severity: "CRITICAL" | "WARNING" | "SUGGESTION";
  source_document?: string;
  page_reference?: number;
  is_active: boolean;
  is_confirmed: boolean;
  created_at: string;
}

export interface ApprovedFact {
  id: string;
  org_id: string;
  category: string;
  fact_key: string;
  fact_value: string;
  verification_source: string;
  notes?: string;
  created_at: string;
}

export interface TerminologyRule {
  id: string;
  org_id: string;
  prohibited_term: string;
  preferred_term: string;
  explanation: string;
  is_active: boolean;
  created_at: string;
}

export interface BrandGuideline {
  id: string;
  org_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  total_pages: number;
  status: string;
  created_at: string;
}

export interface Finding {
  id: string;
  submission_id: string;
  issue_category: string;
  severity: "CRITICAL" | "WARNING" | "SUGGESTION";
  original_text: string;
  explanation: string;
  rule_reference: string;
  evidence_source: string;
  confidence: number;
  suggested_correction: string;
  is_applied: boolean;
  analysis_engine?: string;
  created_at: string;
}

export interface ClaimVerification {
  id: string;
  submission_id: string;
  claim_text: string;
  status: "Supported" | "Unsupported" | "Contradicted" | "Outdated" | "Needs Human Review";
  category: string;
  explanation: string;
  evidence_text?: string;
  source_reference?: string;
  confidence: number;
  created_at: string;
}

export interface Submission {
  id: string;
  org_id: string;
  title: string;
  content: string;
  version: number;
  status: string;
  author_name: string;
  author_role: string;
  overall_score: number;
  findings: Finding[];
  claim_verifications: ClaimVerification[];
  created_at: string;
  updated_at: string;
}

export interface BrandPassport {
  id: string;
  passport_number: string;
  submission_id: string;
  brand_name: string;
  content_title: string;
  content_hash: string;
  guideline_version: string;
  verification_status: string;
  final_score: number;
  audited_by: string;
  passport_data: Record<string, any>;
  issued_at: string;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  task_name: string;
  status: string;
  execution_time_ms: number;
  tokens_used: number;
  input_preview: string;
  output_preview: string;
  event_details: Record<string, any>;
  created_at: string;
}

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchWorkspaces(): Promise<Organization[]> {
  const res = await fetch(`${API_BASE}/brand/workspaces`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load workspaces");
  return res.json();
}

export async function fetchGuidelines(orgId: string = "nova-tech-org-001"): Promise<BrandGuideline[]> {
  const res = await fetch(`${API_BASE}/brand/guidelines?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load guidelines");
  return res.json();
}

export async function uploadGuideline(orgId: string, file: File): Promise<BrandGuideline> {
  const formData = new FormData();
  formData.append("org_id", orgId);
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/brand/guidelines/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload guideline");
  return res.json();
}

export async function fetchRules(orgId: string = "nova-tech-org-001", category?: string): Promise<BrandRule[]> {
  const url = new URL(`${API_BASE}/brand/rules`);
  url.searchParams.set("org_id", orgId);
  if (category) url.searchParams.set("category", category);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch brand rules");
  return res.json();
}

export async function confirmRule(ruleId: string): Promise<BrandRule> {
  const res = await fetch(`${API_BASE}/brand/rules/${ruleId}/confirm`, {
    method: "PATCH",
  });
  if (!res.ok) throw new Error("Failed to confirm rule");
  return res.json();
}

export async function fetchFacts(orgId: string = "nova-tech-org-001"): Promise<ApprovedFact[]> {
  const res = await fetch(`${API_BASE}/brand/facts?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch approved facts");
  return res.json();
}

export async function fetchTerms(orgId: string = "nova-tech-org-001"): Promise<TerminologyRule[]> {
  const res = await fetch(`${API_BASE}/brand/terms?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch terminology rules");
  return res.json();
}

export async function analyzeContent(payload: {
  org_id: string;
  title: string;
  content: string;
  submission_id?: string;
  author_name?: string;
}): Promise<Submission> {
  const res = await fetch(`${API_BASE}/content/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Content analysis failed");
  return res.json();
}

export async function applyCorrection(payload: {
  submission_id: string;
  finding_id: string;
  target_text: string;
  replacement_text: string;
}): Promise<Submission> {
  const res = await fetch(`${API_BASE}/content/apply-correction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to apply correction");
  return res.json();
}

export async function fetchSubmissions(orgId: string = "nova-tech-org-001"): Promise<Submission[]> {
  const res = await fetch(`${API_BASE}/content/submissions?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch submissions");
  return res.json();
}

export async function fetchSubmissionDetail(id: string): Promise<Submission> {
  const res = await fetch(`${API_BASE}/content/submissions/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch submission detail");
  return res.json();
}

export async function runSampleNovaTest(): Promise<Submission> {
  const res = await fetch(`${API_BASE}/claim/test-sample`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run sample test");
  return res.json();
}

export async function submitApprovalDecision(payload: {
  submission_id: string;
  decision: "Approved" | "Rejected" | "Revision Requested";
  comments: string;
  reviewer_name?: string;
  reviewer_role?: string;
}): Promise<Submission> {
  const res = await fetch(`${API_BASE}/approval/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (res.status === 401) throw new Error("Sign in required to submit a decision.");
  if (res.status === 403) throw new Error("Your role is not permitted to make this decision.");
  if (!res.ok) throw new Error("Failed to submit approval decision");
  return res.json();
}

export async function fetchPassports(): Promise<BrandPassport[]> {
  const res = await fetch(`${API_BASE}/passport/list`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch brand passports");
  return res.json();
}

export async function fetchPassportBySubmission(id: string): Promise<BrandPassport> {
  const res = await fetch(`${API_BASE}/passport/by-submission/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Passport not found for this submission");
  return res.json();
}

export async function fetchAgentStats(): Promise<any> {
  const res = await fetch(`${API_BASE}/agent/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent statistics");
  return res.json();
}

export async function fetchAgentRuns(): Promise<AgentRun[]> {
  const res = await fetch(`${API_BASE}/agent/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent runs");
  return res.json();
}

export interface VisualAnalysis {
  submission: Submission;
  format: string;
  dimensions: { width: number; height: number };
  metrics: {
    pixels_sampled: number;
    chromatic_fraction?: number;
    monochrome_fraction?: number;
    contrast?: number;
    avg_luminance?: number;
    dominant_palette?: { hex: string; proportion: number }[];
  };
  ocr: { available: boolean; text: string | null; reason?: string };
}

export async function analyzeImage(orgId: string, file: File): Promise<VisualAnalysis> {
  const formData = new FormData();
  formData.append("org_id", orgId);
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/visual/analyze`, { method: "POST", body: formData });
  if (res.status === 415) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "This image format is not supported for pixel analysis (use PNG or BMP).");
  }
  if (!res.ok) throw new Error("Visual analysis failed");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Onboarding / setup status (Round 2 / R2-1)
// ------------------------------------------------------------------ //
export interface OnboardingStep {
  key: string;
  label: string;
  done: boolean;
  count: number | null;
  total?: number;
  href: string;
  hint: string;
}
export interface OnboardingStatus {
  org: { id: string; name: string };
  steps: OnboardingStep[];
  completed: number;
  total: number;
  completion: number;
  is_demo: boolean;
}
export async function fetchOnboardingStatus(orgId: string = "nova-tech-org-001"): Promise<OnboardingStatus> {
  const res = await fetch(`${API_BASE}/onboarding/status?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load onboarding status");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Brand Knowledge Graph (Round 2 / R2-2)
// ------------------------------------------------------------------ //
export type GraphNodeType =
  | "brand" | "category" | "guideline" | "evidence" | "rule" | "fact" | "term"
  | "campaign" | "finding" | "claim" | "passport";

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;
  parent: string | null;
  count?: number;
  href?: string;
  meta: Record<string, any>;
}
export interface GraphEdge {
  source: string;
  target: string;
  kind: "contains" | "references";
}
export interface BrandGraph {
  brand: { id: string; name: string };
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: Record<string, number>;
}

export async function fetchBrandGraph(orgId: string = "nova-tech-org-001"): Promise<BrandGraph> {
  const res = await fetch(`${API_BASE}/graph/brand?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load knowledge graph");
  return res.json();
}

export async function fetchRiskRadar(orgId: string = "nova-tech-org-001"): Promise<any> {
  const res = await fetch(`${API_BASE}/radar/metrics?org_id=${orgId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch risk radar metrics");
  return res.json();
}

