# ScholarProof

Find scholarships that are real - and right for you.

ScholarProof is a Kaggle AI Agents: Intensive Vibe Coding Capstone project for the Agents for Good track.

## Problem

International students do not need another messy scholarship list. They need to know whether an opportunity is real, current, official, and actually applicable to their profile before spending time applying.

ScholarProof answers questions like:

- Is this scholarship real?
- Is it from an official source?
- Is it current?
- Can my country apply?
- Does my degree level match?
- Does my field match?
- Is the funding enough?
- Is the deadline still open?
- Do I need a separate application?
- Am I wasting time?

## Solution

ScholarProof uses a focused agent workflow to:

1. Collect a lightweight student profile.
2. Find candidate scholarships.
3. Verify official sources.
4. Extract eligibility rules.
5. Match rules against the student profile.
6. Produce conservative verdicts with evidence.
7. Draft clarification emails when rules are unclear.
8. Save simple verified results.

## Core Rule

Unclear beats wrong.

ScholarProof never marks a scholarship as `eligible` unless official evidence proves the key eligibility rules.

## Student-Facing Statuses

| Internal status | UI label | Meaning |
|---|---|---|
| `eligible` | Strong Fit | Official source found and key rules match the profile. |
| `unclear` | Needs Clarification | Relevant, but one or more important rules are unclear. |
| `not_eligible` | Not for You | Official source contains a blocking rule. |
| `unverified` | Unverified Lead | Found online, but no acceptable official source proves it yet. |

## Why Agents Are Needed

Scholarship verification is a multi-step reasoning workflow:

- Discovery finds possible opportunities.
- Source verification separates official proof from aggregators.
- Eligibility extraction turns messy pages into structured rules.
- Profile matching checks fit against student details.
- Conservative verdicting prevents false confidence.
- Clarification drafting helps students ask the right follow-up questions.

A single generic chatbot would be too vague. ScholarProof uses bounded agents and tools so each step is auditable.

## Architecture

```mermaid
flowchart TD
    UI["Student UI"] --> API["Backend API"]
    API --> ROOT["Root Orchestrator Agent"]
    ROOT --> FINDER["Finder Agent"]
    ROOT --> VERIFIER["Verifier Agent"]
    ROOT --> EMAIL["Clarification Email Skill"]
    FINDER --> TOOLS["MCP-style Tool Server"]
    VERIFIER --> TOOLS
    EMAIL --> TOOLS
    TOOLS --> DB["SQLite Database"]
    TOOLS --> LOGS["Audit Logs"]
    TOOLS --> FIXTURES["Offline Fixtures"]
    API --> EVALS["Evaluation Runner"]
```

## Course Concepts Demonstrated

| Concept | Demonstration |
|---|---|
| Agent / multi-agent system using ADK | Root Orchestrator, Finder Agent, Verifier Agent. |
| MCP Server | MCP-style tool layer exposing structured scholarship tools. |
| Antigravity | Demo steps and video workflow in `docs/antigravity_demo_steps.md`. |
| Security features | Source gate, prompt-injection detection, no auto-send, no auto-submit, audit log. |
| Deployability | Docker, `.env.example`, `/health`, deployment guide. |
| Agent Skills | Four skills in `.agent/skills/`. |

## MVP Screens

- Profile
- Find Scholarships
- Eligibility Checker
- Evidence Panel
- Draft Email
- Saved Results

## Setup

The current implementation includes the planning docs, fixture-backed core verification engine,
eval harness, FastAPI backend API, MCP-style tool layer, and ADK-style agent layer in offline
fixture mode.

Install API dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the backend API:

```bash
python -m scholarproof
```

The API starts at:

```text
http://127.0.0.1:8000
```

Useful API routes:

- `GET /health`
- `POST /api/profile`
- `GET /api/profile/{profile_id}`
- `POST /api/search-scholarships`
- `POST /api/verify-scholarship`
- `GET /api/evidence/{verification_id}`
- `POST /api/draft-email`
- `POST /api/save-result`
- `GET /api/saved-results/{profile_id}`
- `GET /api/audit/{verification_id}`

Run evals:

```bash
python evals/run_evals.py
```

Run the API smoke test:

```bash
python scripts/smoke_api.py
```

Run the MCP-style tool smoke test:

```bash
python scripts/smoke_tools.py
```

Run the ADK-style agent smoke test:

```bash
python scripts/smoke_agents.py
```

Run the frontend:

```bash
cd scholarproof/ui
npm.cmd install
npm.cmd run dev
```

The frontend starts at:

```text
http://127.0.0.1:5173
```

Optional frontend build check:

```bash
cd scholarproof/ui
npm.cmd run build
```

UI smoke flow:

1. Create a profile.
2. Search scholarships.
3. Check eligibility.
4. View evidence.
5. Draft an email for a Needs Clarification case.
6. Save a result.

Screenshot capture instructions are in `docs/frontend_screenshots.md`.

List available tools:

```bash
python -m scholarproof.mcp_server list
```

Call one tool from the command line:

```bash
python -m scholarproof.mcp_server call classify_source fixture_id=eligible_01
```

## MCP-Style Tool Layer

The tool layer lives in `scholarproof/mcp_server/` and exposes structured JSON tools for agents:

- `search_scholarships`
- `fetch_page`
- `classify_source`
- `extract_rules`
- `match_profile`
- `generate_verdict`
- `save_result`
- `write_audit_log`
- `detect_prompt_injection`

This demonstrates the Kaggle MCP Server / tool interoperability concept by giving agents a bounded
tool surface with manifest metadata, input schemas, output schemas, and safety notes. The current
limitation is intentional: tools run in fixture/offline mode only, with no live web search.

## ADK-Style Agent Layer

The agent layer lives in `scholarproof/agents/` and demonstrates a bounded multi-agent workflow:

- `RootOrchestratorAgent` accepts a profile and search query, calls Finder, routes candidates to Verifier, and groups verified results.
- `FinderAgent` calls `search_scholarships` and returns structured candidates only. It never decides eligibility.
- `VerifierAgent` calls the MCP tools in order: fetch, classify, injection check, extract, match, verdict, audit.
- `ClarificationEmailSkillWrapper` drafts emails only for `unclear` verification results and never sends them.

This demonstrates the Kaggle Agent / multi-agent system concept while keeping the capstone scope
focused. The current limitation is intentional: agents run in fixture/offline mode only, with no
live web search or application submission.

## Frontend UI

The user-facing UI lives in `scholarproof/ui/` and uses Vite, React, TypeScript, and local CSS.
It connects to the FastAPI backend in fixture mode and includes:

- Profile Wizard.
- Find Scholarships.
- Eligibility Checker.
- Evidence Panel.
- Draft Clarification Email.
- Saved Results.

The frontend does not add authentication, live web search, document upload, email sending, portal
autofill, or application submission.

## Evaluation

The eval runner must include at least 12 fixture cases:

- 3 `eligible`
- 3 `not_eligible`
- 3 `unclear`
- 3 `unverified`

Hard gate:

```text
false_eligible_count = 0
```

## Deployment

Deployment will use:

- Dockerfile
- Optional Docker Compose
- `.env.example`
- `/health` endpoint
- Cloud Run or equivalent deployment instructions

## Security Design

- No API keys in frontend.
- No secrets committed.
- No real sensitive document upload.
- No auto-send.
- No auto-submit.
- Fetched pages treated as untrusted data.
- Prompt injection detection on page text.
- Audit log for all tool calls.

## Limitations

- ScholarProof does not guarantee admission or scholarship success.
- It does not find every scholarship in the world.
- It verifies and ranks discovered opportunities using official-source evidence.
- It does not submit applications.
- It does not send emails.
- It does not replace university admissions offices.
- Ambiguous cases are marked Needs Clarification.
- Live web search may vary, so fixture mode is included for demo reliability.

## Future Work

- Add more official source connectors.
- Add stronger university-domain verification.
- Add multilingual scholarship pages.
- Add user-managed saved searches.
- Add reviewer export packs for advisors.
