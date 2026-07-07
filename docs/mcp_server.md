# MCP Server

FundMyDegree uses an internal local tool registry at runtime for simplicity. The FastAPI app and agents call this registry directly.

The repo also includes a minimal MCP-compatible stdio server wrapper around the same tools. The wrapper exists to demonstrate the MCP Server concept for the capstone demo without changing the product runtime path.

This is not production MCP infrastructure. It is a small JSON-RPC stdio wrapper that supports the methods needed for the demo:

- `initialize`
- `tools/list`
- `tools/call`

## Run The MCP-Compatible Server

```bash
python -m fundmydegree.mcp_server.protocol_server
```

The server reads JSON-RPC messages from stdin and writes JSON-RPC responses to stdout.

## Smoke Test

```bash
python -B scripts/smoke_mcp_protocol.py
```

Expected output:

```text
FundMyDegree MCP protocol smoke
initialize: ok
tools/list: 9 tools
tools/call classify_source: ok
passed: true
```

## Exposed Tools

- `search_scholarships`
- `fetch_page`
- `classify_source`
- `extract_rules`
- `match_profile`
- `generate_verdict`
- `detect_prompt_injection`
- `save_result`
- `write_audit_log`

## Safety Boundaries

- The MCP wrapper uses fixture/offline data.
- It does not add live web search.
- It does not expose secrets.
- It does not send email.
- It does not submit applications.
- It does not upload or process sensitive student documents.
- It delegates verdicts to the existing conservative verifier.

## Implementation Notes

The official `mcp` Python SDK was not installed in the local environment during
this pass, so the project includes a small direct JSON-RPC stdio implementation
instead of adding a fragile dependency at the deadline.

The smoke test proves the wrapper can initialize, list tools, and call an
existing tool over stdio.
