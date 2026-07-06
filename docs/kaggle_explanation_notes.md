# Kaggle Explanation Notes

These notes are written for the final Kaggle writeup and video. They describe what FundMyDegree actually does today.

## 1. What Problem Does FundMyDegree Solve?

International students often spend hours opening scholarship links only to discover late that the opportunity does not fit their nationality, degree level, field, funding need, intake, or fee status. Some links are official, some are aggregator posts, and some are too unclear to trust.

FundMyDegree helps answer a practical question:

```text
Is this scholarship worth my time?
```

It does this by checking a scholarship candidate against a student profile, source trust, and eligibility evidence before labeling it as a strong match.

## 2. How Does Search Work In This Prototype?

Search is fixture/offline in the current Kaggle prototype.

The app loads curated scholarship candidates from `evals/eval_cases.json` and supporting fixture pages in `fixtures/scholarships/`. A text query can filter by name, provider, country, or URL. When a saved profile is present, search also filters by selected study destination.

After candidates are found, the verifier checks each one and groups results into:

- Strong Match
- Need to Confirm
- Not for You
- Couldn't Verify Yet

## 3. Does It Search The Whole Internet?

No.

FundMyDegree does not search every scholarship opportunity online. It does not claim complete coverage. The current prototype demonstrates the workflow using curated fixture data so judges can run the same evals and get the same results.

## 4. Why Use Fixture/Offline Data?

Fixture/offline data makes the capstone reproducible.

It lets the project show the core agent behavior without depending on live websites changing, scraping failures, rate limits, API keys, or network access. It also makes the safety evals clear: the same 12 cases can be tested repeatedly, and the false eligible count must remain 0.

## 5. How Is It Different From A Normal Scholarship Website?

A normal scholarship website mostly helps with discovery. It lists links and leaves the student to check whether each scholarship actually applies.

FundMyDegree adds a fit-checking layer:

- starts from a student profile;
- checks whether a source is official enough to support eligibility;
- compares eligibility rules against the student profile;
- refuses to call unclear cases eligible;
- explains what fits, what needs confirmation, and what blocks the match;
- drafts a clarification email only when the result is unclear.

The value is not "AI search." The value is profile-aware matching plus source checking plus conservative eligibility reasoning.

## 6. What Makes It Agentic?

FundMyDegree uses an ADK-style multi-agent workflow:

- The Root Orchestrator coordinates the student profile, search query, Finder Agent, and Verifier Agent.
- The Finder Agent returns structured scholarship candidates and never decides eligibility.
- The Verifier Agent follows a fixed tool trajectory: fetch fixture page, classify source, detect prompt injection, extract rules, match profile, generate verdict, and write audit log.
- The clarification helper drafts an email only for unclear cases and never sends it.

The tools are also exposed through an internal registry and a minimal MCP-compatible stdio wrapper.

## 7. What Are The Limitations?

Current limitations:

- fixture/offline demo data only;
- no live global scholarship search;
- no live scraping;
- no external scholarship APIs;
- no account system;
- no persistent database;
- no sensitive document upload;
- no auto-send email;
- no portal autofill or application submission;
- no guarantee of admission, funding, eligibility, or scholarship success.

Final decisions always belong to the scholarship provider, university, or funder.

## 8. What Would Be Added In Production?

A production version could add:

- live official-source connectors;
- scholarship provider APIs where available;
- scheduled source refresh;
- official country-list and deadline refresh;
- human review for high-risk scholarship updates;
- persistent database;
- user accounts;
- broader regional coverage;
- clearer provider-specific field mapping;
- stronger monitoring for policy and source changes.

Those are future work. They are not part of the current capstone MVP.
