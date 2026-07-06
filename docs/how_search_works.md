# How Search Works

FundMyDegree does not claim to index every scholarship on the internet. The current Kaggle prototype uses fixture/offline scholarship data so the agent workflow can be tested reproducibly.

## Short Answer

When a student clicks Find scholarships or opens My Matches, the scholarship candidates come from `evals/eval_cases.json` and the matching fixture files under `fixtures/scholarships/`.

The current system:

- Searches fixture/offline data only.
- Does not scrape live websites.
- Does not call external scholarship APIs.
- Does not use a browser crawler.
- Does not claim complete global scholarship coverage.
- Demonstrates the workflow using curated demo scholarship cases.

## Exact Data Flow

1. The UI creates a student profile through `POST /api/profile`.
2. The UI calls `POST /api/search-scholarships` with the profile id and optional text query.
3. `fundmydegree/api/services.py` loads `evals/eval_cases.json`.
4. Each candidate is filtered by:
   - optional text query across name, provider, country, and URL;
   - selected study destination when a saved profile is provided.
5. The UI then calls `POST /api/verify-scholarship` for each returned fixture candidate.
6. Verification loads the local fixture page JSON through the same tool path used by agents.
7. The verifier classifies the source, checks prompt-injection flags, loads fixture rules, matches them against the profile, and generates a conservative verdict.

The internal tool `search_scholarships` calls the same backend service. The MCP-compatible `tools/call` path also delegates to the same tool registry, so MCP search behavior matches the app search behavior.

## What `fetch_page` Means

In this prototype, `fetch_page` does not fetch a live website. It loads a local fixture JSON file from `fixtures/scholarships/` and returns structured page-like content:

- URL
- provider
- page text
- fixture rules
- candidate
- profile

The name is kept because it mirrors the tool shape a production version would use, but the current implementation is intentionally offline.

## Field Handling

Destination is handled in two places:

- Search filters out country-specific fixtures that are outside the student's selected study destinations.
- Verification also refuses an eligible verdict if a manually verified candidate is outside the student's selected destinations.

Nationality, residence, fee status, degree level, field, funding need, and intake are handled during verification. The fixture rules contain structured evidence and a curated starting status. The matcher then applies conservative profile guards so a changed profile cannot blindly inherit a fixture's old matched label.

Examples:

- A UK-only profile should not receive Germany-only or Finland-only candidates in search.
- A Germany candidate manually verified for a UK-only profile becomes `not_eligible`, not `eligible`.
- Missing destination evidence becomes `unclear` before a result can be considered a strong match.
- Aggregator-only sources become `unverified`.
- Missing country, degree, funding, or other required evidence becomes `unclear`.
- Blocking official rules become `not_eligible`.

## Difference From A Normal Scholarship Website

A normal scholarship website usually lists links. It may help a student discover opportunities, but it often leaves the hard work to the student:

- open every link;
- decide whether the source is official;
- check nationality, residence, degree, field, funding, and deadline rules;
- decide whether an unclear listing is worth more time.

FundMyDegree adds a fit-checking layer:

- starts from a student profile;
- filters fixture candidates by selected study destination;
- checks whether the source is official enough to support eligibility;
- reads structured eligibility evidence from fixtures;
- compares rules against the student profile;
- gives a conservative verdict: `eligible`, `unclear`, `not_eligible`, or `unverified`;
- explains why the scholarship looks like a match, needs confirmation, is not for the student, or could not be verified;
- drafts a clarification email only for unclear cases;
- never sends email automatically.

The agentic value is not just search. The value is profile-aware matching, source checking, eligibility reasoning, conservative verdicting, explanation, and a safe next step.

## Current Limitations

This is a capstone prototype, not a complete scholarship search engine.

- Coverage is limited to curated fixture data.
- No live global scholarship search is implemented.
- No live scraping is implemented.
- No external scholarship API connector is implemented.
- Fixture rules are curated for reproducible demos and evals.
- Final eligibility, admission, and funding decisions always belong to universities, funders, and scholarship providers.
