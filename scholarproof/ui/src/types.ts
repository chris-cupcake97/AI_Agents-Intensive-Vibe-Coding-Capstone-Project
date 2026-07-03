export type VerdictStatus = "eligible" | "unclear" | "not_eligible" | "unverified";

export interface StudentProfile {
  id?: string;
  nationality: string;
  residence: string;
  fee_status: string;
  degree_level: string;
  field: string;
  intake: string;
  target_regions: string[];
  funding_need_percent: number;
  need_living_stipend: boolean;
  academic_level: string;
  work_experience_years: number;
  research_experience: boolean;
  documents_available: string[];
}

export interface ScholarshipCandidate {
  id: string;
  name: string;
  provider: string;
  country: string;
  candidate_url: string;
  fixture_id?: string;
  fixture?: string;
  mode?: string;
  funding_text?: string;
  deadline_text?: string;
}

export interface Rule {
  rule_type: string;
  requirement_text: string;
  evidence_text: string;
  status: string;
  source_url: string;
  confidence: number;
}

export interface AuditEvent {
  step: string;
  tool: string;
  input_summary: string;
  output_summary: string;
  success: boolean;
  timestamp?: string;
}

export interface Verification {
  id: string;
  candidate_id: string;
  profile_id: string;
  status: VerdictStatus;
  student_facing_status: string;
  source_url: string;
  source_official: boolean;
  source_type: string;
  source_reason: string;
  last_checked: string;
  matched_rules: Rule[];
  blocking_rules: Rule[];
  unclear_rules: Rule[];
  missing_required_rules: string[];
  verdict_reason: string;
  security_flags: string[];
  audit_log: AuditEvent[];
}

export interface CandidateResult {
  candidate: ScholarshipCandidate;
  verification?: Verification;
  saving?: boolean;
}

export interface Evidence {
  verification_id: string;
  candidate_id: string;
  profile_id: string;
  status: VerdictStatus;
  student_facing_status: string;
  source: {
    url: string;
    official: boolean;
    type: string;
    reason: string;
  };
  verdict_reason: string;
  matched_rules: Rule[];
  blocking_rules: Rule[];
  unclear_rules: Rule[];
  missing_required_rules: string[];
  security_flags: string[];
}

export interface DraftEmail {
  verification_id: string;
  status: string;
  send_allowed: boolean;
  subject: string;
  body: string;
}

export interface SavedResult {
  id: string;
  profile_id: string;
  verification_id: string;
  candidate_id: string;
  status: VerdictStatus;
  student_facing_status: string;
  notes: string;
  saved_at: string;
}

