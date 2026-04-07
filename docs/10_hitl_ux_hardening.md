# 10_hitl_ux_hardening.md: Human-in-the-Loop (HITL) UX Hardening

## Background
Gemini CLI relies on a human-in-the-loop (HITL) model for high-risk actions. This research explores "Explainable Security" and how to design confirmation prompts that provide high-signal information, highlighting the "blast radius" and dangerous parts of proposed shell commands.

## Threat Vectors
- **Confirmation Fatigue**: Users habitually clicking "Yes" to prompts without carefully reading them, especially in long-running tasks.
- **Misleading Explanations**: The agent providing a benign explanation for a malicious command or failing to mention a dangerous argument.
- **Visual Obfuscation**: Hiding a dangerous command argument (e.g., `-f` or `rm -rf`) within a long, complex command string.
- **User Hint Hijacking**: Using a user's instructions to trick them into authorizing an action they didn't intend to perform.

## Mitigation Strategies

### 1. Visualizing Causal Scores (The Provenance Map)
This strategy transforms the "Black Box" of agent decisions into a transparent "Provenance Map" for the user.

*   **Mechanism**:
    *   **Source Highlighting**: When a tool call is intercepted by **Causal Armor**, the CLI identifies the specific untrusted data span ($S$) that caused the "Dominance Shift."
    *   **UI Implementation**: The confirmation prompt highlights the exact file and line number (e.g., `README.md: L42`) in a different color (e.g., Orange) alongside the proposed command.
    *   **Causal Meter**: A visual progress bar showing the relative influence of the User Request ($U$) vs. Untrusted Data ($S$). If $S > U$, the bar turns **Red**.
*   **Pros**: Prevents "Confirmation Fatigue" by providing the *why* behind a security warning.
*   **Cons**: Requires high-precision mapping between context spans and original file locations.

### 2. The "Blast Radius" Indicator (Impact Analysis)
Before a user approves a command, the CLI performs a static "Pre-Flight" check to estimate its potential impact.

*   **Mechanism**:
    *   **Static Analysis**: The CLI parses the proposed shell command (e.g., `rm -rf /`) to identify its "Blast Radius."
    *   **Impact Categories**:
        *   **Files**: Count of files targeted for modification/deletion.
        *   **Network**: Destination URL and protocol (e.g., `CURL to attacker.com`).
        *   **Secrets**: Access to sensitive paths (e.g., `~/.ssh/`, `.env`).
    *   **Visual Warning**: A summary table is presented *before* the confirmation: "Warning: This command will modify 42 files and initiate a network connection to an external IP."
*   **Pros**: Gives the user a clear sense of the "stakes" before they approve an action.
*   **Cons**: Static analysis of complex shell scripts or obfuscated commands can be imprecise.

### 3. Progressive Disclosure (Step-by-Step Approval)
Instead of approving a 10-step plan at once, the CLI enforces a "checkpoint" system for high-risk actions.

*   **Mechanism**:
    *   **High-Risk Tagging**: Tools are tagged with risk levels (e.g., `run_shell_command` = CRITICAL, `list_directory` = LOW).
    *   **Checkpoint Interrupts**: The CLI pauses execution and requires a fresh approval for any step tagged as CRITICAL, even if the user previously approved the overall "Plan."
*   **Pros**: Ensures the user remains "In the Loop" during long-running autonomous tasks.
*   **Cons**: Can be intrusive and slow down the user's workflow.

## Proposed Research Tasks
1. **Confirmation Prompt UX Study**: Conduct user testing to see which prompt designs are most effective at preventing accidental authorization of dangerous commands.
2. **Blast Radius Analysis Engine**: Develop algorithms and heuristics to estimate the potential side-effects of common shell commands and tools.
3. **Explainability Audit**: Research ways to verify that the agent's natural-language explanation of a command is accurate and complete.
