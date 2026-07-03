import {
  AlertTriangle,
  Bookmark,
  CheckCircle2,
  Clipboard,
  Copy,
  ExternalLink,
  FileText,
  GraduationCap,
  Mail,
  RefreshCw,
  Save,
  Search,
  ShieldCheck,
  UserRound,
  XCircle
} from "lucide-react";
import { FormEvent, ReactNode, useMemo, useState } from "react";
import {
  API_BASE_URL,
  createProfile,
  draftEmail,
  getAudit,
  getEvidence,
  getSavedResults,
  saveResult,
  searchScholarships,
  verifyScholarship
} from "./api";
import type {
  AuditEvent,
  CandidateResult,
  DraftEmail,
  Evidence,
  Rule,
  SavedResult,
  ScholarshipCandidate,
  StudentProfile,
  VerdictStatus,
  Verification
} from "./types";

type Screen = "profile" | "find" | "checker" | "evidence" | "draft" | "saved";

const documentOptions = [
  "transcript",
  "degree certificate",
  "grading scale",
  "CV",
  "SOP",
  "reference letters",
  "English test",
  "passport",
  "offer letter"
];

const screenItems: Array<{ id: Screen; label: string; icon: JSX.Element }> = [
  { id: "profile", label: "Profile", icon: <UserRound size={18} /> },
  { id: "find", label: "Find Scholarships", icon: <Search size={18} /> },
  { id: "checker", label: "Eligibility Checker", icon: <ShieldCheck size={18} /> },
  { id: "evidence", label: "Evidence Panel", icon: <FileText size={18} /> },
  { id: "draft", label: "Draft Email", icon: <Mail size={18} /> },
  { id: "saved", label: "Saved Results", icon: <Bookmark size={18} /> }
];

const statusMeta: Record<
  VerdictStatus,
  { label: string; section: string; className: string; icon: JSX.Element }
> = {
  eligible: {
    label: "Strong Fit",
    section: "Best Verified Matches",
    className: "status-eligible",
    icon: <CheckCircle2 size={16} />
  },
  unclear: {
    label: "Needs Clarification",
    section: "Needs Clarification",
    className: "status-unclear",
    icon: <AlertTriangle size={16} />
  },
  not_eligible: {
    label: "Not for You",
    section: "Not for You",
    className: "status-not-eligible",
    icon: <XCircle size={16} />
  },
  unverified: {
    label: "Unverified Lead",
    section: "Unverified Leads",
    className: "status-unverified",
    icon: <FileText size={16} />
  }
};

const defaultProfile: StudentProfile = {
  nationality: "Sri Lanka",
  residence: "Sri Lanka",
  fee_status: "international",
  degree_level: "Master's",
  field: "Artificial Intelligence",
  intake: "2026/27",
  target_regions: ["United Kingdom", "Germany", "Sweden", "Finland"],
  funding_need_percent: 40,
  need_living_stipend: true,
  academic_level: "upper second equivalent",
  work_experience_years: 1,
  research_experience: false,
  documents_available: ["CV", "transcript"]
};

function App() {
  const [screen, setScreen] = useState<Screen>("profile");
  const [profile, setProfile] = useState<StudentProfile>(defaultProfile);
  const [savedProfile, setSavedProfile] = useState<StudentProfile | null>(null);
  const [query, setQuery] = useState("AI");
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [selected, setSelected] = useState<CandidateResult | null>(null);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEvent[]>([]);
  const [draft, setDraft] = useState<DraftEmail | null>(null);
  const [draftRecipient, setDraftRecipient] = useState("Scholarship Office");
  const [savedResults, setSavedResults] = useState<SavedResult[]>([]);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const grouped = useMemo(() => {
    const groups: Record<VerdictStatus, CandidateResult[]> = {
      eligible: [],
      unclear: [],
      not_eligible: [],
      unverified: []
    };
    for (const result of results) {
      const status = result.verification?.status ?? "unverified";
      groups[status].push(result);
    }
    return groups;
  }, [results]);

  const summary = useMemo(() => {
    const verified = results.filter((result) => result.verification);
    return {
      candidates: results.length,
      official: verified.filter((result) => result.verification?.source_official).length,
      eligible: grouped.eligible.length,
      unclear: grouped.unclear.length,
      notEligible: grouped.not_eligible.length,
      unverified: grouped.unverified.length
    };
  }, [grouped, results]);

  const profileChips = savedProfile
    ? [
        ["Nationality", savedProfile.nationality],
        ["Degree", savedProfile.degree_level],
        ["Field", savedProfile.field],
        ["Funding Need", `${savedProfile.funding_need_percent}%`],
        ["Region", savedProfile.target_regions.join(", ")]
      ]
    : [];

  function setField<K extends keyof StudentProfile>(field: K, value: StudentProfile[K]) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  function toggleDocument(name: string) {
    setProfile((current) => {
      const exists = current.documents_available.includes(name);
      return {
        ...current,
        documents_available: exists
          ? current.documents_available.filter((document) => document !== name)
          : [...current.documents_available, name]
      };
    });
  }

  async function withBusy(label: string, action: () => Promise<void>) {
    setBusy(label);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy("");
    }
  }

  async function submitProfile(event: FormEvent) {
    event.preventDefault();
    await withBusy("Saving profile", async () => {
      const response = await createProfile(profile);
      setSavedProfile(response.profile);
      setNotice("Profile saved.");
      setScreen("find");
    });
  }

  async function runSearch() {
    if (!savedProfile?.id) {
      setError("Save a profile first.");
      setScreen("profile");
      return;
    }

    await withBusy("Searching fixtures", async () => {
      const search = await searchScholarships(savedProfile.id!, query);
      const verifiedResults = await Promise.all(
        search.candidates.map(async (candidate) => {
          const verification = await verifyScholarship(savedProfile.id!, candidate);
          return { candidate, verification: verification.verification };
        })
      );
      setResults(verifiedResults);
      setSelected(verifiedResults[0] ?? null);
      setNotice(`${verifiedResults.length} fixture scholarships checked.`);
    });
  }

  async function verifyCandidate(result: CandidateResult) {
    if (!savedProfile?.id) {
      setError("Save a profile first.");
      setScreen("profile");
      return;
    }

    await withBusy("Checking eligibility", async () => {
      const response = await verifyScholarship(savedProfile.id!, result.candidate);
      const next = { ...result, verification: response.verification };
      upsertResult(next);
      setSelected(next);
      setScreen("checker");
    });
  }

  function upsertResult(next: CandidateResult) {
    setResults((current) =>
      current.map((item) => (item.candidate.id === next.candidate.id ? next : item))
    );
  }

  async function openEvidence(result: CandidateResult) {
    const withVerification = result.verification
      ? result
      : await verifyAndReturn(result);
    if (!withVerification.verification) return;

    await withBusy("Loading evidence", async () => {
      const [evidenceResponse, auditResponse] = await Promise.all([
        getEvidence(withVerification.verification!.id),
        getAudit(withVerification.verification!.id)
      ]);
      setSelected(withVerification);
      setEvidence(evidenceResponse);
      setAuditLog(auditResponse.audit_log);
      setScreen("evidence");
    });
  }

  async function verifyAndReturn(result: CandidateResult): Promise<CandidateResult> {
    if (!savedProfile?.id) {
      setError("Save a profile first.");
      setScreen("profile");
      return result;
    }
    const response = await verifyScholarship(savedProfile.id, result.candidate);
    const next = { ...result, verification: response.verification };
    upsertResult(next);
    return next;
  }

  async function rerunSelectedVerification() {
    if (!selected) return;
    await verifyCandidate(selected);
  }

  async function openDraft(result: CandidateResult | null = selected) {
    if (!result?.verification) return;
    if (result.verification.status !== "unclear") {
      setNotice("Draft email is only available for Needs Clarification cases.");
      return;
    }

    await withBusy("Drafting email", async () => {
      const response = await draftEmail(result.verification!.id, "Demo Student", draftRecipient);
      setDraft(response);
      setScreen("draft");
    });
  }

  async function saveCurrentResult(result: CandidateResult | null = selected) {
    if (!savedProfile?.id || !result?.verification) return;
    await withBusy("Saving result", async () => {
      await saveResult(result.verification!.id, savedProfile.id!, "Saved from ScholarProof UI.");
      await refreshSavedResults();
      setNotice("Result saved.");
    });
  }

  async function refreshSavedResults() {
    if (!savedProfile?.id) return;
    const response = await getSavedResults(savedProfile.id);
    setSavedResults(response.saved_results);
  }

  async function goSavedResults() {
    await withBusy("Loading saved results", async () => {
      await refreshSavedResults();
      setScreen("saved");
    });
  }

  async function copyText(value: string) {
    await navigator.clipboard.writeText(value);
    setNotice("Copied.");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <GraduationCap size={22} />
          </div>
          <div>
            <strong>ScholarProof</strong>
            <span>Official evidence first</span>
          </div>
        </div>
        <nav className="nav-list">
          {screenItems.map((item) => (
            <button
              className={`nav-item ${screen === item.id ? "active" : ""}`}
              key={item.id}
              onClick={() => (item.id === "saved" ? void goSavedResults() : setScreen(item.id))}
              type="button"
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          ScholarProof never marks Strong Fit without official evidence.
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Fixture mode</p>
            <h1>{titleForScreen(screen)}</h1>
          </div>
          <div className="topbar-actions">
            <span className="api-pill">API {API_BASE_URL}</span>
            {busy && <span className="busy-pill">{busy}</span>}
          </div>
        </header>

        {(notice || error) && (
          <div className={`message ${error ? "message-error" : "message-info"}`}>
            {error || notice}
          </div>
        )}

        {screen === "profile" && (
          <ProfileWizard
            profile={profile}
            profileChips={profileChips}
            onSubmit={submitProfile}
            onField={setField}
            onToggleDocument={toggleDocument}
          />
        )}

        {screen === "find" && (
          <FindScholarships
            query={query}
            setQuery={setQuery}
            profileChips={profileChips}
            grouped={grouped}
            summary={summary}
            onSearch={runSearch}
            onVerify={verifyCandidate}
            onEvidence={openEvidence}
            onSave={saveCurrentResult}
          />
        )}

        {screen === "checker" && (
          <EligibilityChecker
            result={selected}
            profile={savedProfile}
            onEvidence={openEvidence}
            onSave={saveCurrentResult}
            onDraft={openDraft}
          />
        )}

        {screen === "evidence" && (
          <EvidencePanel
            result={selected}
            evidence={evidence}
            auditLog={auditLog}
            onCopy={copyText}
            onRerun={rerunSelectedVerification}
            onDraft={openDraft}
            onBack={() => setScreen("find")}
          />
        )}

        {screen === "draft" && (
          <DraftEmail
            draft={draft}
            recipient={draftRecipient}
            setRecipient={setDraftRecipient}
            verification={selected?.verification ?? null}
            onCopy={copyText}
            onSave={() => setNotice("Draft saved for demo session.")}
            onBack={() => setScreen("evidence")}
          />
        )}

        {screen === "saved" && (
          <SavedResults
            savedResults={savedResults}
            results={results}
            onEvidence={(saved) => {
              const result = results.find((item) => item.verification?.id === saved.verification_id);
              if (result) void openEvidence(result);
            }}
          />
        )}
      </main>
    </div>
  );
}

function titleForScreen(screen: Screen) {
  return {
    profile: "Profile Wizard",
    find: "Find Scholarships",
    checker: "Eligibility Checker",
    evidence: "Evidence Panel",
    draft: "Draft Clarification Email",
    saved: "Saved Results"
  }[screen];
}

function ProfileWizard({
  profile,
  profileChips,
  onSubmit,
  onField,
  onToggleDocument
}: {
  profile: StudentProfile;
  profileChips: string[][];
  onSubmit: (event: FormEvent) => void;
  onField: <K extends keyof StudentProfile>(field: K, value: StudentProfile[K]) => void;
  onToggleDocument: (name: string) => void;
}) {
  return (
    <section className="grid-two">
      <form className="panel" onSubmit={onSubmit}>
        <div className="panel-header">
          <h2>Student Profile</h2>
          <p>Checklist only. No document upload.</p>
        </div>
        <div className="form-grid">
          <Field label="Nationality">
            <input value={profile.nationality} onChange={(e) => onField("nationality", e.target.value)} />
          </Field>
          <Field label="Residence">
            <input value={profile.residence} onChange={(e) => onField("residence", e.target.value)} />
          </Field>
          <Field label="Fee status">
            <select value={profile.fee_status} onChange={(e) => onField("fee_status", e.target.value)}>
              <option value="international">international</option>
              <option value="home">home</option>
              <option value="unknown">unknown</option>
            </select>
          </Field>
          <Field label="Degree level">
            <select value={profile.degree_level} onChange={(e) => onField("degree_level", e.target.value)}>
              <option>Master's</option>
              <option>PhD</option>
              <option>Bachelor's</option>
            </select>
          </Field>
          <Field label="Field">
            <input value={profile.field} onChange={(e) => onField("field", e.target.value)} />
          </Field>
          <Field label="Intake">
            <input value={profile.intake} onChange={(e) => onField("intake", e.target.value)} />
          </Field>
          <Field label="Target regions">
            <input
              value={profile.target_regions.join(", ")}
              onChange={(e) =>
                onField(
                  "target_regions",
                  e.target.value.split(",").map((item) => item.trim()).filter(Boolean)
                )
              }
            />
          </Field>
          <Field label="Minimum funding need">
            <input
              max={100}
              min={0}
              type="number"
              value={profile.funding_need_percent}
              onChange={(e) => onField("funding_need_percent", Number(e.target.value))}
            />
          </Field>
          <Field label="Academic level">
            <input value={profile.academic_level} onChange={(e) => onField("academic_level", e.target.value)} />
          </Field>
          <Field label="Work experience years">
            <input
              min={0}
              type="number"
              value={profile.work_experience_years}
              onChange={(e) => onField("work_experience_years", Number(e.target.value))}
            />
          </Field>
        </div>
        <div className="check-row">
          <label>
            <input
              checked={profile.need_living_stipend}
              type="checkbox"
              onChange={(e) => onField("need_living_stipend", e.target.checked)}
            />
            Need living stipend
          </label>
          <label>
            <input
              checked={profile.research_experience}
              type="checkbox"
              onChange={(e) => onField("research_experience", e.target.checked)}
            />
            Research experience
          </label>
        </div>
        <div className="checklist">
          {documentOptions.map((document) => (
            <label key={document}>
              <input
                checked={profile.documents_available.includes(document)}
                type="checkbox"
                onChange={() => onToggleDocument(document)}
              />
              {document}
            </label>
          ))}
        </div>
        <button className="primary-button" type="submit">
          <Save size={18} />
          Save Profile
        </button>
      </form>
      <aside className="panel">
        <div className="panel-header">
          <h2>Profile Summary</h2>
          <p>Used for fixture eligibility checks.</p>
        </div>
        <ChipList chips={profileChips.length ? profileChips : [["Draft", "Not saved yet"]]} />
        <div className="evidence-callout">
          Strong Fit is possible only when official source evidence proves every required rule.
        </div>
      </aside>
    </section>
  );
}

function FindScholarships({
  query,
  setQuery,
  profileChips,
  grouped,
  summary,
  onSearch,
  onVerify,
  onEvidence,
  onSave
}: {
  query: string;
  setQuery: (value: string) => void;
  profileChips: string[][];
  grouped: Record<VerdictStatus, CandidateResult[]>;
  summary: Record<string, number>;
  onSearch: () => void;
  onVerify: (result: CandidateResult) => void;
  onEvidence: (result: CandidateResult) => void;
  onSave: (result: CandidateResult) => void;
}) {
  return (
    <section className="content-with-aside">
      <div className="stack">
        <div className="panel">
          <div className="search-row">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="AI, Bristol, DAAD..." />
            <button className="primary-button" type="button" onClick={onSearch}>
              <Search size={18} />
              Search
            </button>
          </div>
          <ChipList chips={profileChips} />
        </div>
        {(["eligible", "unclear", "not_eligible", "unverified"] as VerdictStatus[]).map((status) => (
          <ResultSection
            key={status}
            results={grouped[status]}
            status={status}
            onVerify={onVerify}
            onEvidence={onEvidence}
            onSave={onSave}
          />
        ))}
      </div>
      <aside className="panel sticky-panel">
        <div className="panel-header">
          <h2>Agent Summary</h2>
          <p>Fixture search and verification.</p>
        </div>
        <Metric label="Candidates found" value={summary.candidates} />
        <Metric label="Official sources checked" value={summary.official} />
        <Metric label="Strong fits" value={summary.eligible} />
        <Metric label="Needs clarification" value={summary.unclear} />
        <Metric label="Not for you" value={summary.notEligible} />
        <Metric label="Unverified leads" value={summary.unverified} />
        <div className="safety-note">ScholarProof never marks Strong Fit without official evidence.</div>
      </aside>
    </section>
  );
}

function ResultSection({
  status,
  results,
  onVerify,
  onEvidence,
  onSave
}: {
  status: VerdictStatus;
  results: CandidateResult[];
  onVerify: (result: CandidateResult) => void;
  onEvidence: (result: CandidateResult) => void;
  onSave: (result: CandidateResult) => void;
}) {
  return (
    <section className="panel result-section">
      <div className="section-title-row">
        <h2>{statusMeta[status].section}</h2>
        <span className="count-pill">{results.length}</span>
      </div>
      {results.length === 0 ? (
        <p className="empty-text">No fixture results in this group.</p>
      ) : (
        <div className="card-grid">
          {results.map((result) => (
            <ScholarshipCard
              key={result.candidate.id}
              result={result}
              onEvidence={onEvidence}
              onSave={onSave}
              onVerify={onVerify}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function ScholarshipCard({
  result,
  onVerify,
  onEvidence,
  onSave
}: {
  result: CandidateResult;
  onVerify: (result: CandidateResult) => void;
  onEvidence: (result: CandidateResult) => void;
  onSave: (result: CandidateResult) => void;
}) {
  const { candidate, verification } = result;
  const sourceLabel = verification?.source_official ? "Official source" : "Source not official";
  return (
    <article className="scholarship-card">
      <div className="card-topline">
        <StatusBadge status={verification?.status ?? "unverified"} />
        <span className={`source-pill ${verification?.source_official ? "source-official" : ""}`}>{sourceLabel}</span>
      </div>
      <h3>{candidate.name}</h3>
      <p>{candidate.provider}</p>
      <dl className="compact-list">
        <div>
          <dt>Country</dt>
          <dd>{candidate.country}</dd>
        </div>
        <div>
          <dt>Funding</dt>
          <dd>{candidate.funding_text || fundingFromVerification(verification)}</dd>
        </div>
        <div>
          <dt>Deadline</dt>
          <dd>{candidate.deadline_text || deadlineFromVerification(verification)}</dd>
        </div>
      </dl>
      <div className="button-row">
        <button type="button" onClick={() => onVerify(result)}>
          <ShieldCheck size={16} />
          Check Eligibility
        </button>
        <button type="button" onClick={() => onEvidence(result)} disabled={!verification}>
          <FileText size={16} />
          View Evidence
        </button>
        <button type="button" onClick={() => onSave(result)} disabled={!verification}>
          <Bookmark size={16} />
          Save
        </button>
      </div>
    </article>
  );
}

function EligibilityChecker({
  result,
  profile,
  onEvidence,
  onSave,
  onDraft
}: {
  result: CandidateResult | null;
  profile: StudentProfile | null;
  onEvidence: (result: CandidateResult) => void;
  onSave: (result: CandidateResult) => void;
  onDraft: (result: CandidateResult) => void;
}) {
  if (!result?.verification) {
    return <EmptyPanel title="No scholarship selected" body="Select Check Eligibility from a scholarship card." />;
  }
  const { candidate, verification } = result;
  return (
    <section className="stack">
      <div className="panel checker-hero">
        <div>
          <StatusBadge status={verification.status} />
          <h2>{candidate.name}</h2>
          <p>{candidate.provider} - {candidate.country}</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => onEvidence(result)}>
            <FileText size={16} />
            View Evidence
          </button>
          <button type="button" onClick={() => onSave(result)}>
            <Bookmark size={16} />
            Save Result
          </button>
          <button type="button" disabled={verification.status !== "unclear"} onClick={() => onDraft(result)}>
            <Mail size={16} />
            Draft Clarification Email
          </button>
        </div>
      </div>
      <section className="grid-two">
        <div className="panel">
          <div className="panel-header">
            <h2>Verdict Panel</h2>
            <p>{verification.verdict_reason}</p>
          </div>
          <dl className="compact-list">
            <div>
              <dt>Source</dt>
              <dd>{verification.source_type}</dd>
            </div>
            <div>
              <dt>Official</dt>
              <dd>{verification.source_official ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Last checked</dt>
              <dd>{formatDate(verification.last_checked)}</dd>
            </div>
          </dl>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2>Student Profile</h2>
            <p>{profile?.nationality} - {profile?.degree_level} - {profile?.field}</p>
          </div>
          <ChipList
            chips={[
              ["Residence", profile?.residence ?? ""],
              ["Fee status", profile?.fee_status ?? ""],
              ["Funding need", `${profile?.funding_need_percent ?? 0}%`],
              ["Intake", profile?.intake ?? ""]
            ]}
          />
        </div>
      </section>
      <RuleColumns verification={verification} />
    </section>
  );
}

function EvidencePanel({
  result,
  evidence,
  auditLog,
  onCopy,
  onRerun,
  onDraft,
  onBack
}: {
  result: CandidateResult | null;
  evidence: Evidence | null;
  auditLog: AuditEvent[];
  onCopy: (value: string) => void;
  onRerun: () => void;
  onDraft: (result: CandidateResult) => void;
  onBack: () => void;
}) {
  if (!result?.verification || !evidence) {
    return <EmptyPanel title="Evidence not loaded" body="Open evidence from a verified scholarship card." />;
  }
  const allRules = [...evidence.matched_rules, ...evidence.blocking_rules, ...evidence.unclear_rules];
  return (
    <section className="content-with-aside">
      <div className="stack">
        <div className="panel evidence-source">
          <div>
            <StatusBadge status={evidence.status} />
            <h2>{result.candidate.name}</h2>
            <a href={evidence.source.url || "#"} target="_blank" rel="noreferrer">
              {evidence.source.url || "No official source URL"}
              {evidence.source.url && <ExternalLink size={14} />}
            </a>
          </div>
          <div className="button-row">
            <button type="button" onClick={() => onCopy(evidence.source.url)} disabled={!evidence.source.url}>
              <Copy size={16} />
              Copy Source URL
            </button>
            <button type="button" onClick={onRerun}>
              <RefreshCw size={16} />
              Re-run Verification
            </button>
            <button type="button" disabled={evidence.status !== "unclear"} onClick={() => onDraft(result)}>
              <Mail size={16} />
              Draft Clarification Email
            </button>
            <button type="button" onClick={onBack}>
              <Search size={16} />
              Back to Results
            </button>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2>Source Evidence Summary</h2>
            <p>{evidence.source.reason}</p>
          </div>
          <dl className="compact-list">
            <div>
              <dt>Source type</dt>
              <dd>{evidence.source.type}</dd>
            </div>
            <div>
              <dt>Official</dt>
              <dd>{evidence.source.official ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Last checked</dt>
              <dd>{formatDate(result.verification.last_checked)}</dd>
            </div>
            <div>
              <dt>Security flags</dt>
              <dd>{evidence.security_flags.length ? evidence.security_flags.join(", ") : "None"}</dd>
            </div>
          </dl>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2>Extracted Rules</h2>
            <p>{evidence.verdict_reason}</p>
          </div>
          <RuleList rules={allRules} />
        </div>
      </div>
      <aside className="panel sticky-panel">
        <div className="panel-header">
          <h2>Audit Timeline</h2>
          <p>Tool calls from verification.</p>
        </div>
        <div className="timeline">
          {auditLog.map((event, index) => (
            <div className="timeline-item" key={`${event.tool}-${index}`}>
              <span>{event.step}</span>
              <div>
                <strong>{event.tool}</strong>
                <p>{event.output_summary}</p>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </section>
  );
}

function DraftEmail({
  draft,
  recipient,
  setRecipient,
  verification,
  onCopy,
  onSave,
  onBack
}: {
  draft: DraftEmail | null;
  recipient: string;
  setRecipient: (value: string) => void;
  verification: Verification | null;
  onCopy: (value: string) => void;
  onSave: () => void;
  onBack: () => void;
}) {
  if (!draft || verification?.status !== "unclear") {
    return <EmptyPanel title="No draft available" body="Drafts are only available for Needs Clarification cases." />;
  }
  return (
    <section className="content-with-aside">
      <div className="panel">
        <div className="warning-banner">Draft only - ScholarProof never sends emails automatically.</div>
        <Field label="To">
          <input value={recipient} onChange={(e) => setRecipient(e.target.value)} />
        </Field>
        <Field label="Subject">
          <input readOnly value={draft.subject} />
        </Field>
        <Field label="Email body">
          <textarea readOnly rows={14} value={draft.body} />
        </Field>
        <div className="button-row">
          <button type="button" onClick={() => onCopy(`${draft.subject}\n\n${draft.body}`)}>
            <Copy size={16} />
            Copy Draft
          </button>
          <button type="button" onClick={onSave}>
            <Save size={16} />
            Save Draft
          </button>
          <button type="button" onClick={onBack}>
            <FileText size={16} />
            Back to Evidence
          </button>
        </div>
      </div>
      <aside className="panel sticky-panel">
        <div className="panel-header">
          <h2>Why This Was Drafted</h2>
          <p>Unclear evidence categories.</p>
        </div>
        <ul className="reason-list">
          {verification.unclear_rules.map((rule) => (
            <li key={`${rule.rule_type}-${rule.requirement_text}`}>{labelize(rule.rule_type)}</li>
          ))}
          {verification.missing_required_rules.map((rule) => (
            <li key={rule}>{labelize(rule)}</li>
          ))}
        </ul>
      </aside>
    </section>
  );
}

function SavedResults({
  savedResults,
  results,
  onEvidence
}: {
  savedResults: SavedResult[];
  results: CandidateResult[];
  onEvidence: (saved: SavedResult) => void;
}) {
  const candidateById = new Map(results.map((item) => [item.candidate.id, item.candidate]));
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Saved Results</h2>
        <p>Simple saved verification results.</p>
      </div>
      {savedResults.length === 0 ? (
        <p className="empty-text">No saved results yet.</p>
      ) : (
        <div className="saved-list">
          {savedResults.map((saved) => {
            const candidate = candidateById.get(saved.candidate_id);
            return (
              <article className="saved-card" key={saved.id}>
                <div>
                  <StatusBadge status={saved.status} />
                  <h3>{candidate?.name ?? saved.candidate_id}</h3>
                  <p>{candidate?.country ?? "Fixture result"} - {candidate?.provider ?? saved.student_facing_status}</p>
                </div>
                <dl className="compact-list">
                  <div>
                    <dt>Funding</dt>
                    <dd>{candidate?.funding_text || "See evidence"}</dd>
                  </div>
                  <div>
                    <dt>Deadline</dt>
                    <dd>{candidate?.deadline_text || "See evidence"}</dd>
                  </div>
                  <div>
                    <dt>Last checked</dt>
                    <dd>{formatDate(saved.saved_at)}</dd>
                  </div>
                </dl>
                <button type="button" onClick={() => onEvidence(saved)}>
                  <FileText size={16} />
                  View Evidence
                </button>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function RuleColumns({ verification }: { verification: Verification }) {
  return (
    <section className="rule-grid">
      <div className="panel">
        <h2>Matched Rules</h2>
        <RuleList rules={verification.matched_rules} />
      </div>
      <div className="panel">
        <h2>Blocking Rules</h2>
        <RuleList rules={verification.blocking_rules} />
      </div>
      <div className="panel">
        <h2>Unclear Rules</h2>
        <RuleList rules={verification.unclear_rules} missing={verification.missing_required_rules} />
      </div>
    </section>
  );
}

function RuleList({ rules, missing = [] }: { rules: Rule[]; missing?: string[] }) {
  if (!rules.length && !missing.length) {
    return <p className="empty-text">No rules in this group.</p>;
  }
  return (
    <div className="rule-list">
      {rules.map((rule) => (
        <article className="rule-card" key={`${rule.rule_type}-${rule.requirement_text}`}>
          <span>{labelize(rule.rule_type)}</span>
          <strong>{rule.requirement_text}</strong>
          <p>{rule.evidence_text || "Official evidence missing or unclear."}</p>
        </article>
      ))}
      {missing.map((rule) => (
        <article className="rule-card missing-rule" key={rule}>
          <span>{labelize(rule)}</span>
          <strong>Required evidence missing</strong>
          <p>ScholarProof keeps this unclear until official evidence is available.</p>
        </article>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: VerdictStatus }) {
  const meta = statusMeta[status];
  return (
    <span className={`status-badge ${meta.className}`}>
      {meta.icon}
      {meta.label}
    </span>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function ChipList({ chips }: { chips: string[][] }) {
  return (
    <div className="chip-list">
      {chips.map(([label, value]) => (
        <span className="chip" key={label}>
          <strong>{label}</strong>
          {value}
        </span>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyPanel({ title, body }: { title: string; body: string }) {
  return (
    <section className="panel empty-panel">
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

function formatDate(value?: string) {
  if (!value) return "Not checked";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function labelize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function fundingFromVerification(verification?: Verification) {
  const rule = verification?.matched_rules.find((item) => item.rule_type === "funding_amount");
  return rule?.evidence_text || "See evidence";
}

function deadlineFromVerification(verification?: Verification) {
  const rule = verification?.matched_rules.find((item) => item.rule_type === "deadline");
  return rule?.evidence_text || "See evidence";
}

export default App;
