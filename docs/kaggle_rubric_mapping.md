# Kaggle Rubric Mapping

Source of truth:

- `docs/competition/evaluation_screenshot.png`
- `docs/competition/pitch_rubric_screenshot.png`
- `docs/competition/implementation_rubric_screenshot.png`

## Required Course Concepts

| Kaggle Concept | ScholarProof Mapping | Demonstration |
|---|---|---|
| Agent / multi-agent system using ADK | ADK-style layer in `scholarproof/agents/`: Root Orchestrator Agent + Finder Agent + Verifier Agent + Clarification Email Skill wrapper. | Code |
| MCP Server | MCP-style tool server in `scholarproof/mcp_server/` for search, fetch, source classification, rule extraction, profile matching, verdict generation, saving, audit logging, and prompt-injection detection. | Code |
| Antigravity | Demo workflow showing repo inspection, UI issue fixing, diff review, local run, and browser testing. | Video |
| Security features | Official-source gate, no auto-send, no auto-submit, prompt-injection detection, no sensitive uploads, audit logs. | Code and video |
| Deployability | Dockerfile, `.env.example`, `/health`, deployment docs, fixture demo mode. | Video and docs |
| Agent Skills | Four skills under `.agent/skills/`. | Code and video |

## Pitch Rubric: 30 Points

### Core Concept and Value - 10 Points

ScholarProof is focused on a real student pain: avoiding fake, stale, irrelevant, or unclear scholarship opportunities.

Value:

- Reduces wasted student effort.
- Provides official-source evidence.
- Makes uncertainty visible.
- Helps international students ask better clarification questions.

### YouTube Video Submission - 10 Points

The video should show:

1. Problem statement.
2. Why agents are useful.
3. Architecture.
4. UI demo.
5. Evidence panel.
6. Eval runner.
7. Build tools and Antigravity workflow.

### Writeup - 10 Points

The writeup should explain:

- Problem.
- Solution.
- Architecture.
- Agent/tool design.
- Security design.
- Evals and false eligible gate.
- Limitations.
- Project journey.

## Implementation Rubric: 70 Points

### Technical Implementation - 50 Points

Strong implementation evidence:

- Verification engine before UI polish.
- Conservative verdict policy.
- Structured data models.
- MCP-style tool layer in `scholarproof/mcp_server/` with a registry, manifest, and smoke test.
- ADK-style agent layer in `scholarproof/agents/` with Root Orchestrator, Finder, Verifier, and Clarification Email Skill wrapper.
- Fixture mode for reliable demo.
- Eval runner with `false_eligible_count = 0`.
- Security and audit logging.

### Documentation - 20 Points

Required documentation:

- `README.md`
- `AGENTS.md`
- `specs/scholarproof_system_spec.md`
- `docs/architecture.md`
- `docs/security.md`
- `docs/evaluation.md`
- `docs/deployment.md`
- `docs/video_script.md`
- `docs/kaggle_rubric_mapping.md`
- `docs/antigravity_demo_steps.md`

## No-Secrets Reminder

The implementation rubric screenshot explicitly warns not to include API keys or passwords in code.
