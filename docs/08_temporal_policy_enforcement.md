# 08_temporal_policy_enforcement.md: Intent-Aware and State-Based Policies

## Background
Current security policies in Gemini CLI are largely static (e.g., "deny all write access to .env"). This research aims to develop "temporal" or "intent-aware" policies where a tool call's authorization depends on the current conversation context, previous actions, and the explicit intent of the user.

## Threat Vectors
- **Context Hijacking**: Manipulating the conversation context (via prompt injection) to trick the policy engine into thinking a dangerous command is actually a safe, user-requested action.
- **State Manipulation**: Attempting to bypass a sequence-based security check by injecting or removing history from the conversation context.
- **Intent Misinterpretation**: The LLM misinterpreting a user's vaguely-worded request as a command to execute a high-risk tool.
- **Policy Drift**: A situation where a once-safe authorization is inappropriately reused in a new, more dangerous context.

## Mitigation Strategies

### 1. Intent Embedding Comparison (Semantic Mapping)
This strategy uses vector embeddings to mathematically represent the "semantic distance" between a user's initial instruction and a proposed tool call.

*   **Mechanism**:
    *   **Prompt Embedding**: When a user provides a high-level instruction (e.g., "Fix the typo in README.md"), the CLI generates a vector embedding ($\vec{U}$) of this string using a local model (e.g., `sentence-transformers`).
    *   **Tool-Call Embedding**: For every proposed tool call (e.g., `read_file(path="~/.ssh/id_rsa")`), the CLI generates a corresponding vector embedding ($\vec{T}$) of the tool name and its arguments.
    *   **Cosine Similarity Check**: The CLI calculates the cosine similarity: $S = \frac{\vec{U} \cdot \vec{T}}{\|\vec{U}\| \|\vec{T}\|}$.
    *   **Threshold Enforcement**: If $S$ falls below a configurable threshold (e.g., 0.65), the action is blocked or flagged for manual user confirmation, even if the tool is globally "allowed."
*   **Pros**: Fast, local execution, avoids LLM hallucination in the verification path.
*   **Cons**: May struggle with complex, multi-step reasoning where the tool call is logically distant from the initial ask.

### 2. Contextual Guardrails (LLM-in-the-Middle Verification)
A secondary, highly-constrained "Guardrail LLM" acts as an independent auditor for every tool call.

*   **Mechanism**:
    *   **Audit Prompt**: Before executing a tool, the CLI sends a concise prompt to a local, low-latency LLM (e.g., `Gemma 2b` or `Llama-3-8B-Instruct`).
    *   **Input**: `User Instruction: {original_ask} | Proposed Action: {tool_name}({args}) | Conversation History (Summary): {history}`.
    *   **Question**: "Does the proposed action directly serve the user's instruction? Answer only 'YES' or 'NO' with a one-sentence justification."
    *   **Enforcement**: If the Guardrail LLM returns 'NO', the CLI intercepts the call and prompts the user: "Warning: This action (e.g., `curl attacker.com`) does not appear to align with your original request ('Fix typo'). Do you still want to proceed?"
*   **Pros**: High reasoning capability, understands context better than simple embeddings.
*   **Cons**: Adds latency to every tool call, requires a local model to be resident in memory.

### 3. State-Locked Permissions (Dynamic Permission Sets)
This strategy implements "Least Privilege" by dynamically narrowing the available toolset based on the detected phase of the task.

*   **Mechanism**:
    *   **Intent Classification**: At the start of a session, the CLI classifies the user's intent into a "Permission Profile" (e.g., `READ_ONLY`, `REFACTOR`, `SYSTEM_CONFIG`, `NETWORK_ACCESS`).
    *   **Permission Masking**:
        *   If the profile is `REFACTOR`, the CLI applies a temporary mask that allows `read_file`, `replace`, and `run_shell_command("npm test")` but explicitly denies `curl`, `wget`, or any shell command modifying `/etc/` or `~/.ssh/`.
    *   **Phase Transitions**: As the task progresses (e.g., moving from "Research" to "Execution"), the CLI can request the user to "unlock" the next permission set.
*   **Pros**: Robust protection against "Valid Tool, Malicious Purpose" attacks.
*   **Cons**: Can be intrusive to the user experience if the classification is too narrow or the task is multifaceted.

### 4. Causal Attribution (Causal Armor Strategy)
This is the most advanced "Gold Standard" approach, moving from semantic similarity to **quantitative causal inference**. It treats security as a signal-to-noise problem where the User Request is the "signal" and Untrusted Data is the "noise."

*   **Mechanism (Causal Inference via LOO)**:
    *   **Decomposition**: The CLI decomposes the current context into three distinct spans: **User Request ($U$)**, **Conversation History ($H$)**, and **Untrusted Tool Spans ($S$)** (e.g., contents of a read file or web page).
    *   **LOO (Leave-One-Out) Scoring**: For any proposed high-risk tool call ($A$), the CLI calculates its log-probability $P(A)$ across different context permutations:
        *   Full context probability: $P(A | U, H, S)$
        *   Probability without User Request: $P(A | H, S)$
        *   Probability without Untrusted Data: $P(A | U, H)$
    *   **Dominance Detection**: The CLI measures the **Causal Influence** of each span. If removing the Untrusted Data ($S$) causes a significantly larger drop in $P(A)$ than removing the User Request ($U$), it indicates that the **untrusted data has hijacked the agent's logic**.
    *   **Sanitization & Regeneration**: Instead of a hard block, the CLI "sanitizes" the untrusted data—stripping hidden instructions while preserving raw data—and redacts the agent's "poisoned" Chain-of-Thought before allowing it to regenerate a safe action.
*   **Pros**: Mathematical precision; detects attacks regardless of phrasing; preserves utility by sanitizing instead of blocking.
*   **Cons**: Requires access to log-probabilities; higher computational cost due to multiple forward passes (can be mitigated via local "Proxy Providers").

## 5. Proposed "Causal Policy" TOML Schema

To implement these dynamic guardrails, the Gemini CLI policy engine can be extended with causal-aware fields:

```toml
[[policy]]
tool = "run_shell_command"
allow = true

# Enable advanced Intent-Aware & Causal Guardrails
[policy.causal_armor]
enabled = true
margin_tau = 0.5            # Causal dominance threshold
untrusted_inputs = ["read_file", "web_fetch", "mcp_call"]
privileged_patterns = ["rm", "curl", "chmod", "env", "ssh"]

# Fallback behavior if causal dominance is detected
on_violation = "sanitize_and_retry" # options: "block", "ask_user", "sanitize_and_retry"
```

## Proposed Research Tasks
1. **Intent-to-Policy Mapping**: Develop algorithms for accurately translating natural language intent into formal, verifiable policy rules.
2. **Conversation History Delta Analysis**: Research techniques for identifying sudden, suspicious shifts in conversation context that might indicate a hijacking attempt.
3. **Temporal Policy Engine Prototype**: Build a prototype of a state-aware policy engine and test its resilience against context manipulation attacks.
