# Gemini CLI Security Research Index

This directory contains detailed research papers covering various security aspects of Gemini CLI. Each document analyzes a specific problem area, identifies threat vectors, proposes mitigation strategies, and outlines future research tasks.

## Research Papers

0.  **[THREAT_VECTOR_MAP.md](./THREAT_VECTOR_MAP.md)**
    *   **Summary:** A comprehensive, visual mapping and matrix of all potential attack vectors across the Gemini CLI ecosystem.
1.  **[01_indirect_prompt_injection.md](./01_indirect_prompt_injection.md)**
    *   **Summary:** Investigates how malicious content in files or web pages can manipulate the CLI's logic and bypass security policies through prompt injection.
2.  **[AUDIT_LOGGING_GUIDE.md](./AUDIT_LOGGING_GUIDE.md)**
    *   **Summary:** A technical guide for distinguishing between user instructions and the CLI's autonomous actions using the OpenTelemetry-based log schema.
3.  **[02_sandbox_escape_analysis.md](./02_sandbox_escape_analysis.md)**
    *   **Summary:** Evaluates different sandboxing and isolation techniques (OS-level vs. containerization) for running shell commands and tools securely.
4.  **[03_policy_engine_logic.md](./03_policy_engine_logic.md)**
    *   **Summary:** Analyzes the TOML-based policy engine, focusing on rule precedence, conflict resolution, and ensuring a fail-safe (deny-all) state.
5.  **[04_data_leakage_prevention.md](./04_data_leakage_prevention.md)**
    *   **Summary:** Researches local filtering and redaction techniques to prevent PII and secrets from being inadvertently sent to the LLM.
6.  **[05_supply_chain_security.md](./05_supply_chain_security.md)**
    *   **Summary:** Proposes mechanisms for ensuring the integrity of subagents and skills through component signing and checksum verification.
7.  **[06_trusted_folder_integrity.md](./06_trusted_folder_integrity.md)**
    *   **Summary:** Details the security risks associated with the "Trusted Folders" feature and proposes hardening measures against symlink attacks and TOCTOU issues.
8.  **[07_multi_agent_governance.md](./07_multi_agent_governance.md)**
    *   **Summary:** Researching orchestration security, permission inheritance between parent agents and subagents, and preventing cross-agent data exfiltration.
9.  **[08_temporal_policy_enforcement.md](./08_temporal_policy_enforcement.md)**
    *   **Summary:** Investigating intent-aware and state-based policies where tool authorization depends on the current conversation context and user intent.
10. **[09_mcp_security.md](./09_mcp_security.md)**
    *   **Summary:** Analyzing the security of Model Context Protocol (MCP) integrations with external servers and sanitizing incoming data for potential injections.
11. **[10_hitl_ux_hardening.md](./10_hitl_ux_hardening.md)**
    *   **Summary:** Researching "Explainable Security" and high-signal confirmation prompts that highlight the "blast radius" and dangerous parts of proposed shell commands.
12. **[11_plan_mode_adversarial.md](./11_plan_mode_adversarial.md)**
    *   **Summary:** Investigating "plan poisoning" where malicious steps are hidden in long-running multi-step plans, and designing a plan-verification engine.

13. **[12_code_assist_attack_surface.md](./12_code_assist_attack_surface.md)**
    *   **Summary:** Comparative attack surface analysis of Gemini Code Assist (IDE extension) vs. Gemini CLI, covering workspace config injection, implicit context collection, code customization supply chain risks, PR review injection, and IDE extension ecosystem threats.

## Usage
These documents are intended to serve as a roadmap for security improvements and as a reference for developers working on the Gemini CLI codebase.
