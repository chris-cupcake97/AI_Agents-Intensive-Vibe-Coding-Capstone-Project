# FundMyDegree Implementation Plan

This document records the product build order. It is not a feature backlog for expanding the scope.

## 1. Recommended Repo Structure

```text
.agent/skills/
config/
docs/
evals/
fixtures/scholarships/
fundmydegree/
  agents/
  core/
  mcp_server/
  ui/
specs/
deploy/
```

## 2. MVP Implementation Plan

Build verification before UI polish:

1. Repo skeleton and docs.
2. Core data models.
3. Source classifier.
4. Conservative verdict engine.
5. Eval harness.
6. Internal tool registry and MCP-compatible wrapper.
7. Agent layer.
8. Frontend UI.
9. Security polish.
10. Deployability.
11. Public repo polish.

## 3. Data Models

- `StudentProfile`
- `ScholarshipCandidate`
- `OfficialSource`
- `EligibilityRule`
- `VerificationResult`
- `ClarificationEmailDraft`
- `SavedResult`
- `AuditEvent`

## 4. Agent Architecture

Use only:

- Root Orchestrator Agent.
- Finder Agent.
- Verifier Agent.
- Clarification Email Skill.

## 5. Tool Registry / MCP-Compatible Wrapper Design

- `search_scholarships(profile, query)`
- `fetch_page(fixture_id)`
- `classify_source(url)`
- `extract_rules(page_text)`
- `match_profile(profile, rules)`
- `generate_verdict(profile, source, rules)`
- `save_result(result)`
- `write_audit_log(event)`
- `detect_prompt_injection(page_text)`

## 6. Agent Skills Plan

Use four skills:

- `official-source-verification`
- `eligibility-rule-extraction`
- `conservative-verdicting`
- `clarification-email-drafting`

One skill, one job.

## 7. Security Checklist

- No secrets in repo.
- No API keys in frontend.
- `.env.example` only.
- No sensitive document upload.
- No auto-send.
- No auto-submit.
- Fetched pages are untrusted data.
- Prompt injection detection.
- Audit all tool calls.
- Default to `unclear` when evidence is incomplete.

## 8. Evaluation Plan

Hard gate:

```text
false_eligible_count = 0
```

Use fixture cases across eligible, not eligible, unclear, and unverified.

## 9. Build Order

1. Phase 1: Repo skeleton and docs.
2. Phase 2: Core data models.
3. Phase 3: Source classifier.
4. Phase 4: Conservative verdict engine.
5. Phase 5: Eval harness.
6. Phase 6: Internal tool registry and MCP-compatible wrapper.
7. Phase 7: Agent layer.
8. Phase 8: Frontend UI.
9. Phase 9: Security polish.
10. Phase 10: Deployability.
11. Phase 11: Public repo polish.

## 10. Risks And Scope Limits

Risks:

- Official pages may be stale, vague, or contradictory.
- Aggregators may rank above official sources.
- Live web search may vary.
- Students may over-trust unclear advice.

Scope limits:

- No application submission.
- No automatic email sending.
- No real sensitive document upload.
- No generic SOP writer.
- No claim of complete global scholarship coverage.
