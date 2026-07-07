# FundMyDegree System Architecture

## Architecture

```text
Student UI
  -> Backend API
    -> Root Orchestrator Agent
      -> Finder Agent
      -> Verifier Agent
      -> Clarification Email Skill
    -> Internal tool registry
    -> MCP-compatible stdio wrapper
    -> In-memory fixture store
    -> Audit logs
    -> Evaluation runner
```

## Agent Boundary

Use only:

1. Root Orchestrator Agent.
2. Finder Agent.
3. Verifier Agent.
4. Clarification Email Skill.

Do not create separate agents for every small step.

## Responsibilities

### Root Orchestrator Agent

- Reads user request.
- Reads student profile.
- Routes search requests to Finder Agent.
- Routes candidates to Verifier Agent.
- Never produces final eligibility without Verifier Agent output.
- Maintains session state.

### Finder Agent

- Searches fixture/offline candidate scholarships.
- Returns structured candidate data.
- Does not decide eligibility.
- Does not call anything "Strong Match".
- Can return official candidates and aggregator leads separately.

### Verifier Agent

Internally handles:

- Source verification.
- Eligibility rule extraction.
- Profile matching.
- Conservative verdicting.
- Evidence generation.

### Clarification Email Skill

- Runs only when status is `unclear`.
- Drafts a polite email.
- Never sends email.
- UI must not include a Send button.

## Tool Registry And MCP-Compatible Wrapper

The app and agents use the internal tool registry directly. The repository also includes a minimal MCP-compatible stdio wrapper around the same tools for demo/client compatibility.

Tools:

- `search_scholarships`
- `fetch_page`
- `classify_source`
- `extract_rules`
- `match_profile`
- `generate_verdict`
- `save_result`
- `write_audit_log`
- `detect_prompt_injection`

All tools return structured JSON.
