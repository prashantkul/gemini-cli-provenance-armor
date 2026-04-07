# 07_multi_agent_governance.md: Multi-Agent Orchestration and Governance

## Background
Gemini CLI increasingly relies on a multi-agent architecture where a primary orchestrator delegates tasks to specialized sub-agents (e.g., `codebase_investigator`, `generalist`). This research area focuses on the security implications of this delegation, specifically how permissions are inherited, how data is shared between agents, and how to prevent a compromised sub-agent from escalating its privileges.

## Threat Vectors
- **Privilege Escalation**: A sub-agent inheriting more permissions than intended by the user or the parent agent, or bypassing the parent's constraints.
- **Cross-Agent Data exfiltration**: A sub-agent passing sensitive data (e.g., environment variables, session tokens) to a parent agent or another sub-agent that should not have access to that information.
- **Confused Deputy Attack**: A parent agent tricking a more privileged sub-agent into performing an action that the parent agent itself is not authorized to do.
- **Resource Exhaustion (Recursive Delegation)**: A sub-agent spawning an excessive number of further sub-agents, leading to a denial-of-service or unexpected cloud costs.

## Mitigation Strategies
- **Granular Permission Scoping**: Implementing a system where each sub-agent is initialized with a strictly defined, least-privilege permission set.
- **Isolated Contexts**: Ensuring each sub-agent operates within its own isolated context, with explicit controls over what data is shared back to the orchestrator.
- **Inter-Agent Audit Logging**: Recording all communication between agents, including the full request and response payloads, to enable forensic analysis.
- **Deterministic Handshake Protocols**: Using a secure, verifiable handshake when a sub-agent is created to ensure it is a trusted component.

## Proposed Research Tasks
1. **Inheritance Model Analysis**: Research and define a formal model for how security policies should be inherited or restricted during agent delegation.
2. **Data Leakage Benchmarking**: Develop a suite of tests to measure how effectively PII and secrets are filtered during inter-agent communication.
3. **Sub-Agent Sandboxing**: Investigate the feasibility of running sub-agents in even more restricted environments (e.g., WASM or isolated containers) than the primary agent.
