import type {
  AuditEvent,
  DraftEmail,
  Evidence,
  SavedResult,
  ScholarshipCandidate,
  StudentProfile,
  Verification
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep the HTTP status text.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function createProfile(profile: StudentProfile) {
  return request<{ profile: StudentProfile; created: boolean }>("/api/profile", {
    method: "POST",
    body: JSON.stringify(profile)
  });
}

export function searchScholarships(profileId: string, query: string) {
  return request<{
    mode: string;
    profile_id: string | null;
    query: string;
    count: number;
    candidates: ScholarshipCandidate[];
  }>("/api/search-scholarships", {
    method: "POST",
    body: JSON.stringify({ profile_id: profileId, query })
  });
}

export function verifyScholarship(profileId: string, candidate: ScholarshipCandidate) {
  return request<{ verification: Verification }>("/api/verify-scholarship", {
    method: "POST",
    body: JSON.stringify({
      profile_id: profileId,
      fixture_id: candidate.fixture_id,
      candidate_id: candidate.id
    })
  });
}

export function getEvidence(verificationId: string) {
  return request<Evidence>(`/api/evidence/${verificationId}`);
}

export function getAudit(verificationId: string) {
  return request<{ verification_id: string; audit_log: AuditEvent[] }>(`/api/audit/${verificationId}`);
}

export function draftEmail(verificationId: string, studentName?: string, recipient?: string) {
  return request<DraftEmail>("/api/draft-email", {
    method: "POST",
    body: JSON.stringify({
      verification_id: verificationId,
      student_name: studentName,
      recipient
    })
  });
}

export function saveResult(verificationId: string, profileId: string, notes = "") {
  return request<{ saved_result: SavedResult }>("/api/save-result", {
    method: "POST",
    body: JSON.stringify({
      verification_id: verificationId,
      profile_id: profileId,
      notes
    })
  });
}

export function getSavedResults(profileId: string) {
  return request<{ profile_id: string; count: number; saved_results: SavedResult[] }>(
    `/api/saved-results/${profileId}`
  );
}

export { API_BASE_URL };

