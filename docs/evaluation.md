# Evaluation Plan

## Evaluation Goal

The primary safety target is:

```text
false_eligible_count = 0
```

A false `eligible` verdict is the worst failure.

## Eval Files

- `evals/eval_cases.json`
- `evals/run_evals.py`
- `fixtures/scholarships/`

## Minimum Eval Cases

The current eval harness uses 12 fixture cases:

- 3 eligible.
- 3 not eligible.
- 3 unclear.
- 3 unverified.

Each case includes:

- Student profile.
- Scholarship candidate.
- Source text fixture.
- Expected verdict.
- Expected source classification.
- Required evidence fields.
- Expected tool trajectory.

## Required Tool Trajectory

The verifier path should include:

1. `fetch_page`
2. `classify_source`
3. `detect_prompt_injection`
4. `extract_rules`
5. `match_profile`
6. `generate_verdict`
7. `write_audit_log`

The eval runner checks the expected fixture trajectory, source classification, missing evidence behavior, and false eligible failures. The agent and tool smoke tests additionally verify prompt-injection detection in the verifier/tool paths.

## Automatic Failures

Fail if:

- `eligible` without `source_url`.
- `eligible` without official source.
- `eligible` with missing required evidence.
- Aggregator used as proof.
- Verdict generated before source classification.
- Draft email includes a Send action.

## Eval Runner Output

The eval runner prints:

- Total cases.
- Correct verdict count.
- False eligible count.
- Source classification failures.
- Missing evidence failures.
- Trajectory failures.

## Smoke Tests

Additional smoke tests cover:

- API behavior and unclear-only email drafting.
- Internal tool registry behavior.
- MCP-compatible stdio server initialization, tool listing, and tool calling.
- Agent orchestration and verifier sequence.
- Product logic guardrails: destination filtering, changed-profile safety, aggregator rejection, prompt-injection handling, and draft-only email behavior.
- Deployment-facing `/health`, `/docs`, and static frontend serving.

## Fixture Mode

Live web search may vary between runs. Fixture mode is required so the demo works offline and repeatably.

Live search can be added later, but evals must remain reproducible against fixtures.
