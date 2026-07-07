# Product Logic Audit

This audit checks FundMyDegree for logic loopholes, misleading behavior, and overclaims before Kaggle submission.

Core rule:

```text
Unclear beats wrong.
```

The worst failure is a false `eligible` or false Strong Match.

## Audit Summary

The project is a fixture/offline capstone prototype. It does not search the live web, scrape scholarship pages, call external APIs, or cover every scholarship opportunity.

The main issue found in this pass was that fixture rule labels were previously
trusted too strongly when a user changed their profile or manually verified a
candidate outside search.

That could allow a candidate from the fixture's original profile to remain
`eligible` for a changed profile. This pass added conservative guards for
destination mismatch and key profile mismatches.

## Issues And Fixes

### Search Returned Too Many Fixture Candidates

- File/path: `fundmydegree/api/services.py`
- Severity: high
- Why it matters: a UK-only profile could see Germany-only or Finland-only
  fixtures as candidates.
- Recommended fix: filter fixture candidates by profile target destinations.
- Fixed in this pass: yes.

### Manual Verification Could Bypass Destination Filtering

- File/path: `fundmydegree/core/verdict_engine.py`
- Severity: high
- Why it matters: a Germany-only candidate could be manually verified for a
  UK-only profile and still become `eligible`.
- Recommended fix: add a verifier-level destination guard before eligible can
  be returned.
- Fixed in this pass: yes.

### Missing Destination Evidence Was Not Explicitly Downgraded

- File/path: `fundmydegree/core/verdict_engine.py`
- Severity: medium
- Why it matters: a candidate with unclear country should not be treated as a
  strong fit for a selected destination.
- Recommended fix: add an unclear `study_destination` rule when destination is
  missing.
- Fixed in this pass: yes.

### Profile Matching Relied Mainly On Curated Fixture Statuses

- File/path: `fundmydegree/core/rule_extraction.py`
- Severity: high
- Why it matters: changing nationality, degree level, field, funding need, or
  intake could inherit a stale fixture "matched" label.
- Recommended fix: add conservative profile guards that downgrade unsupported
  matched rules to `unclear` or `blocking`.
- Fixed in this pass: yes.

### Public Docs Needed A Clear Search Explanation

- File/path: `README.md`, `docs/how_search_works.md`
- Severity: medium
- Why it matters: the word "search" can imply live web coverage if not
  explained.
- Recommended fix: document fixture/offline search plainly.
- Fixed in this pass: yes.

### No Dedicated Regression Test Covered Product Logic Edge Cases

- File/path: `scripts/smoke_product_logic.py`
- Severity: medium
- Why it matters: existing evals checked golden fixture cases but not
  changed-profile edge cases.
- Recommended fix: add focused product-logic smoke checks.
- Fixed in this pass: yes.

## Category Review

### 1. Destination Filtering

Status: Fixed.

Search now filters fixture candidates by the saved profile's selected study destinations. Region selection supports the demo Europe region. Country-specific scholarships outside the target destination are excluded unless the candidate is explicitly global/worldwide.

Regression coverage:

- UK profile does not return Germany-only scholarships.
- UK profile does not return Finland-only scholarships.
- MCP search returns the same filtered result set as internal search.

### 2. Nationality Eligibility

Status: Guarded for fixture mode.

The verifier now downgrades matched nationality rules when official fixture evidence names specific countries that do not include the student's nationality. It also blocks obvious non-UK or non-EU/EEA mismatches.

Known limitation:

This is still not a full country-law eligibility parser. The prototype uses conservative fixture guards rather than live official country-list extraction.

### 3. Residence Vs Nationality

Status: Guarded for obvious mismatch.

Residence and nationality remain separate fields in the profile model. Residence evidence is checked separately from nationality evidence. Obvious residence mismatches, such as evidence for applicants outside the UK when the student resides in the UK, are blocked.

Known limitation:

Complex residence-history rules are not implemented.

### 4. Degree Level Matching

Status: Guarded.

The matcher now blocks obvious degree-level mismatches, such as a Bachelor's profile being checked against evidence that only supports Master's study, or a Master's profile being checked against PhD-only evidence.

### 5. Field Of Study Matching

Status: Conservatively guarded.

The matcher no longer treats obviously unrelated fields as proven just because a fixture was previously labeled matched. For example, Business study should not inherit AI/technology evidence as a strong match.

Known limitation:

Broad field taxonomy is intentionally simple. A production system would need provider-specific field mapping and human review for ambiguous programs.

### 6. Funding Scope

Status: Conservatively guarded.

The matcher checks simple percentage evidence. If explicit percentage funding is below the student's stated need, the rule becomes blocking. If the student needs full funding and the evidence does not prove full funding, the rule becomes unclear.

Known limitation:

The prototype does not calculate full cost of attendance, living costs, exchange rates, or net affordability.

### 7. Deadline And Current Cycle

Status: Guarded for cycle mismatch.

If a matched current-cycle or deadline rule mentions a cycle that does not match the student's intended intake, the rule becomes unclear.

Known limitation:

The app does not perform live date refresh. Fixture dates remain demo data.

### 8. Source Trust

Status: Already strong.

Official university, government, and provider domains can support eligibility. Aggregators, blogs, and missing URLs cannot support `eligible`.

Regression coverage:

- Aggregator-only source becomes `unverified`.
- Missing source URL becomes `unverified` or `unclear`, never `eligible`.

### 9. Prompt Injection

Status: Already guarded.

Fetched page text is treated as untrusted content. Prompt-injection-like text is flagged and cannot turn a case eligible. With an otherwise official source, injection flags force `unclear`.

### 10. Manual Verification Route

Status: Fixed.

Manual verification now respects destination and profile guards. It cannot bypass the same conservative verdict rules used by search-driven verification.

### 11. API / Tool / MCP Consistency

Status: Checked.

The FastAPI route, internal tool, Finder Agent, and MCP-compatible wrapper delegate to the same search and verification logic. The product-logic smoke test confirms internal search and MCP search return the same filtered candidates for a UK-only profile.

### 12. Saved Results

Status: No bug found.

Saved results store the verification id, status, student-facing status, notes, and saved timestamp. Saving does not change eligibility.

Known limitation:

Persistence is in-memory for the demo. Restarting the backend clears saved results.

### 13. Clarification Draft

Status: Already guarded.

Clarification email drafting is allowed only for `unclear` cases. It returns a draft with `send_allowed: false`. It never sends automatically.

### 14. UI Wording

Status: Mostly safe.

The UI uses student-friendly labels: Best Matches, Need to Confirm, Not for You, and Couldn't Verify Yet. It does not claim guaranteed eligibility, live web search, or automatic application submission.

Recommended caution for video:

Say "fixture demo search" or "curated demo candidates" when explaining My Matches.

### 15. Docs / README Overclaims

Status: Updated.

Docs now explicitly state fixture/offline mode and no live scraping/API/global coverage. The README points to `docs/how_search_works.md` and the tests include `scripts/smoke_product_logic.py`.

## Known Limitations Not Fixed

- No live official-source connectors.
- No scheduled source refresh.
- No production database or user accounts.
- No full semantic parser for every scholarship rule type.
- No complete global scholarship index.
- No guarantee of admission, funding, eligibility, or scholarship success.

These are scope limits, not hidden features.
