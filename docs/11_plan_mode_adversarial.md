# 11_plan_mode_adversarial.md: Adversarial Attacks on Plan Mode

## Background
Plan Mode in Gemini CLI allows the agent to design a multi-step execution strategy before any tools are called. This research focuses on "plan poisoning," where a malicious instruction is hidden within a long-running plan, and the design of a verification engine to ensure plans align with user intent.

## Threat Vectors
- **Plan Poisoning (Step Hiding)**: Inserting a malicious action (e.g., `git push` to an external repository) deep within a long, benign-looking plan.
- **Plan Drift**: A plan that starts off safe but gradually shifts towards a harmful state through subsequent updates and refinements.
- **Ambiguous Plan Steps**: Using vague or misleading language in a plan that appears safe to a human but can be interpreted as authorized for a malicious tool call.
- **State-Based Plan Manipulation**: Trick the agent into believing that certain prerequisites have been met, thereby authorizing dangerous subsequent steps.

## Mitigation Strategies

### 1. Causal Attribution for Plans (The "Plan Audit" Phase)
Before a multi-step plan is presented to the user, the CLI performs a "Causal Dry-Run" to audit each individual step.

*   **Mechanism**:
    *   **Step Decomposition**: For a generated 10-step plan, the CLI treats each step ($P_i$) as a proposed action.
    *   **Log-Prob Analysis**: Using the **Causal Armor** LOO methodology, the CLI calculates the causal influence of the User Request ($U$) vs. Untrusted Data ($S$) for each step.
    *   **Poison Step Flagging**: Any step where the Causal Influence of $S$ is dominant ($S > U$) is marked as "Poisoned."
    *   **User Visualization**: The plan is displayed with the poisoned steps highlighted in **Red**, accompanied by the provenance of the injection (e.g., "Triggered by malicious content in `README.md`").
*   **Pros**: Detects hidden malicious intent before any tool is actually executed.
*   **Cons**: Analyzing a large plan (e.g., 50+ steps) adds significant latency to the planning phase.

### 2. Recursive Plan Re-Verification (Commitment Checkpoints)
To prevent "approval fatigue" from 10-step plans, the CLI enforces dynamic re-verification as the plan is executed.

*   **Mechanism**:
    *   **Hash-Based Integrity**: When the user approves a plan, the CLI generates a hash of the entire sequence.
    *   **Runtime Drift Detection**: Before executing Step $i$, the CLI re-verifies that the model's current "Chain of Thought" and the next tool call still match the hash of the original Step $i$.
    *   **Adaptive Interrupts**: If the agent's logic "drifts" from the approved plan—or if new untrusted data is read during execution—the CLI forces a pause and requires the user to re-approve the remaining steps.
*   **Pros**: Protects against "Live Hijacking" where an attack occurs halfway through a legitimate plan.
*   **Cons**: Can result in frequent interruptions during complex, dynamic tasks.

### 3. Plan Sandboxing (Sub-Context Isolation)
The CLI executes the planning phase in a "Low-Trust" context that is isolated from the main session history.

*   **Mechanism**:
    *   **Context Stripping**: During the planning phase, the model is only provided with the **User Request** and a **Summary** of the workspace, rather than the full raw content of untrusted files.
    *   **Draft Verification**: Once the plan is drafted, it is "vetted" by a second, independent LLM (the Guardrail) against the full context to check for hidden instructions.
*   **Pros**: Prevents malicious file content from being "read" into the plan-generation logic in the first place.
*   **Cons**: May reduce the plan's accuracy if the model lacks the granular context needed to design complex steps.

## Proposed Research Tasks
1. **Plan Poisoning Benchmark Suite**: Create a dataset of "poisoned" plans to test the effectiveness of verification techniques.
2. **Multi-Step Plan Delta Analysis**: Research techniques for highlighting the security implications of changes made to an existing plan during a session.
3. **Formal Plan Specification**: Explore using more structured formats (e.g., JSON or a Domain Specific Language) for plans to make them easier to analyze and verify.
