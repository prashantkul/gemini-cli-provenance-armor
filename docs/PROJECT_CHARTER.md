# Project: Gemini CLI Provenance Armor

**Gemini CLI: Provenance Armor** is a Causal-first security architecture designed to harden AI-driven development against Indirect Prompt Injection (IPI) and unauthorized tool usage. By combining mathematical **Causal Attribution** with **High-Signal Provenance Visualization**, it ensures that a human's instructions remain the sole "Cause" of every high-stakes action.

## 1. Vision Statement
To transform the Gemini CLI from a system of static, "vibes-based" security into a transparent, mathematically-verifiable environment where every tool call is audited for its **Causal Origin** and its **Potential Impact**.

## 2. The Three Core Pillars

### I. Causal Detection (The Armor)
*   **The Backend:** Integrates the **Causal Armor** middleware to perform **Leave-One-Out (LOO) Scoring** on all privileged tool calls.
*   **The Goal:** Mathematically detect when an untrusted data source (e.g., a malicious `README.md`) has "hijacked" the agent's logic by becoming the dominant cause of an action.
*   **Key Mechanism:** The **"Sanitize-and-Retry"** loop, which strips instructions from poisoned data while preserving raw facts.

### II. Local Redaction (The Filter)
*   **The Guardrail:** A high-speed, on-the-wire interceptor that sits between local tools and the Gemini API.
*   **The Goal:** Prevent **Data Leakage** of PII, secrets, and proprietary code before it ever leaves the user's machine.
*   **Key Mechanism:** **Hybrid Scanning** using deterministic Regex and local Tiny-LLMs (e.g., `phi-3-mini`) for context-aware redaction.

### III. High-Signal UX (The Provenance)
*   **The Frontend:** A transparent UI that visualizes the **"Why"** and **"Where"** behind every proposed command.
*   **The Goal:** Eliminate **Confirmation Fatigue** by transforming the "Black Box" of AI decision-making into an explainable **Provenance Map**.
*   **Key Mechanism:** **Causal Source Highlighting** and **Blast Radius Indicators** that show the user exactly which file triggered a command and what its impact will be.

## 3. The Security Roadmap (12-Document Deep Dive)

This project is backed by a comprehensive 12-document security research repository:
*   **Architecture:** [Threat Vector Map](./THREAT_VECTOR_MAP.md), [Causal Armor Integration](./CAUSAL_ARMOR_INTEGRATION.md), [Audit Logging Guide](./AUDIT_LOGGING_GUIDE.md).
*   **Core Research:** [Intent-Aware Policies (#08)](./08_temporal_policy_enforcement.md), [MCP Security Gateway (#09)](./09_mcp_security.md), [HITL UX Hardening (#10)](./10_hitl_ux_hardening.md).
*   **Advanced Defense:** [Plan Mode Adversarial (#11)](./11_plan_mode_adversarial.md), [Data Leakage Prevention (#04)](./04_data_leakage_prevention.md).

## 4. Implementation Priorities
1.  **Phase 1: Causal Interceptor** – Deploy the LOO scoring middleware for `run_shell_command`.
2.  **Phase 2: Provenance UI** – Implement the "Causal Source" highlighting in the tool confirmation prompt.
3.  **Phase 3: Redaction Engine** – Integrate the local PII/Secret scanner for all outgoing tool results.

---
*Charter generated on April 6, 2026, based on the Gemini CLI Security Research Repository.*
