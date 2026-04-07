# Provenance Armor

**Causal-first security architecture for AI-driven CLI tools.**

Provenance Armor hardens AI agent workflows against Indirect Prompt Injection (IPI) and unauthorized tool usage by combining mathematical **Causal Attribution** with **High-Signal Provenance Visualization**. Every high-stakes action is audited for its causal origin — ensuring a human's instructions remain the sole "Cause" of every tool call.

## Architecture

```mermaid
graph LR
  subgraph " "
    U([User Instruction])
    S([Untrusted Data])
  end

  subgraph "Phase 1: Causal Interceptor"
    LOO["LOO Scorer"]
    CA{"Causal\nAnalyzer"}
    SAN["Sanitize & Retry"]
  end

  subgraph "Phase 3: Redaction Engine"
    R["Regex + NER + Delta Mask"]
  end

  subgraph "Phase 2: Provenance UI"
    UI["Causal Meter\nBlast Radius\nSource Highlight"]
  end

  U --> LOO
  S --> LOO
  LOO --> CA
  CA -->|dominated| SAN -->|cleaned| LOO
  CA -->|safe| R
  R --> UI
  CA -->|safe| ALLOW(( ALLOW ))
  CA -->|dominated| BLOCK(( BLOCK ))

  style U fill:#4CAF50,color:#fff,stroke:#388E3C
  style S fill:#FF5722,color:#fff,stroke:#D84315
  style LOO fill:#7E57C2,color:#fff,stroke:#5E35B1
  style CA fill:#7E57C2,color:#fff,stroke:#5E35B1
  style SAN fill:#7E57C2,color:#fff,stroke:#5E35B1
  style R fill:#FF9800,color:#fff,stroke:#EF6C00
  style UI fill:#00BCD4,color:#fff,stroke:#00838F
  style ALLOW fill:#4CAF50,color:#fff,stroke:#388E3C
  style BLOCK fill:#E91E63,color:#fff,stroke:#AD1457
```

## Three Pillars

### Phase 1 — Causal Interceptor (The Armor)

The **Leave-One-Out (LOO) Scorer** decomposes every tool call context into three components:

| Symbol | Component | Description |
|--------|-----------|-------------|
| **U** | User Request | The human's original instruction |
| **H** | History | Conversation context |
| **S** | Untrusted Data | File contents, web fetches, MCP sources |

It then computes three log-probability scores — `P(A|U,H,S)`, `P(A|H,S)`, `P(A|U,H)` — to measure whether the **user** or **untrusted data** is the dominant cause of the proposed action. If untrusted data dominates (margin > `tau=0.5`), the **Sanitize-and-Retry** loop strips injected instructions and regenerates a clean action.

### Phase 2 — Provenance UI (The Provenance)

Rich terminal visualization that transforms the AI "black box" into an explainable decision:

- **Causal Meter** — bar showing User vs Untrusted influence (green/red)
- **Blast Radius** — static analysis of shell commands (files, network, secrets)
- **Source Highlighting** — exact file:line provenance of dominant spans
- **Risk Badges** — CRITICAL / HIGH / MEDIUM / LOW with progressive disclosure

### Phase 3 — Redaction Engine (The Filter)

Three-stage pipeline intercepting sensitive data before it leaves your machine:

1. **Regex Scanner** — AWS keys, GitHub tokens, SSH keys, credit cards, emails, passwords
2. **NER Scanner** — spaCy-based contextual PII detection (optional)
3. **Delta Mask** — only scans newly-read content to minimize overhead

Plus **Environment Variable Masking** with a strict whitelist (PATH, LANG, PWD, HOME, USER, SHELL).

## Quick Start

```bash
# Install
uv sync

# Run the causal analysis demo (safe scenario)
provenance-armor analyze --demo

# Simulate an IPI attack
provenance-armor analyze --demo --attack

# Redact sensitive data
provenance-armor redact --input "My key is AKIAIOSFODNN7EXAMPLE"

# Validate a policy file
provenance-armor policy --validate .provenance-armor/policy.toml

# View audit logs
provenance-armor audit --tail 20

# Run tests
uv run pytest tests/ -v
```

## Policy Configuration

Policies are TOML files with hierarchical precedence: **Admin > User > Workspace**.

```toml
[[policy]]
tool = "run_shell_command"
allow = true

[policy.causal_armor]
enabled = true
margin_tau = 0.5
untrusted_inputs = ["read_file", "web_fetch", "mcp_call"]
privileged_patterns = ["rm", "curl", "chmod", "env", "ssh"]
on_violation = "sanitize_and_retry"  # "block" | "ask_user" | "sanitize_and_retry"
```

Policy locations:
- **Admin:** `/etc/provenance-armor/policy.toml`
- **User:** `~/.config/provenance-armor/policy.toml`
- **Workspace:** `.provenance-armor/policy.toml`

An admin `deny` can never be overridden. Missing policies fail-safe to **deny-all**.

## Project Structure

```
src/provenance_armor/
  core/         # LOO scorer, causal analyzer, sanitizer, pipeline
  models/       # Dataclasses: context, scoring, tool_call, policy, redaction, audit
  providers/    # Pluggable backends: mock, heuristic, LLM
  policy/       # TOML policy engine with hierarchical resolution
  redaction/    # Regex + NER + delta mask pipeline
  ui/           # Rich-based provenance visualization
  mcp/          # MCP security gateway with instruction stripping
  intent/       # Intent classification and similarity checking
  audit/        # OTel-compatible JSON audit logger
  cli.py        # CLI entry point
```

## Documentation

The project is backed by a [12-document security research repository](docs/INDEX.md) covering threat vectors, causal armor integration, policy engines, data leakage prevention, MCP security, HITL UX hardening, and plan mode adversarial analysis.

## License

MIT
