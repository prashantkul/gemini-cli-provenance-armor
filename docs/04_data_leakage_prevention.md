# 04_data_leakage_prevention.md: Data Leakage and Redaction Research

## Background
Gemini CLI interacts with sensitive data, including source code, logs, and environment variables. There is a risk that this information could be inadvertently sent to the LLM (Large Language Model), potentially violating privacy regulations (GDPR/CCPA) or leaking company secrets. Preventing this leakage requires local, "on-the-wire" filtering.

## Threat Vectors
- **PII Leakage**: Accidentally sending names, emails, phone numbers, or other Personally Identifiable Information (PII) to the LLM.
- **Secret Exfiltration**: Passing API keys, database credentials, or private SSH keys discovered in files or environment variables to the model.
- **Proprietary Data**: Sending highly sensitive or proprietary source code that should never leave the local machine.
- **Verbose Tool Output**: Tools like `ls -R` or `grep` might return large amounts of unintended data that the agent then passes to the LLM.

## Mitigation Strategies

### 1. Local Redaction Middleware (On-the-Wire Interception)
This strategy places a security "valve" between the tool execution layer and the Gemini API, ensuring sensitive data is redacted locally.

*   **Mechanism**:
    *   **Tool-Output Interceptor**: Every result from a tool (e.g., `read_file`, `grep`, `mcp_call`) is passed through the middleware before being appended to the conversation history.
    *   **Multi-Stage Filtering**:
        *   **Stage 1: Regex Scanner**: High-speed matching for deterministic patterns (e.g., `[A-Z0-9]{20}` for AWS keys, `[0-9]{4}-[0-9]{4}-...` for Credit Cards).
        *   **Stage 2: Named Entity Recognition (NER)**: A local Tiny-LLM or specialized library (e.g., `spaCy`) identifies names, locations, and organization-specific identifiers.
        *   **Stage 3: Delta Masking**: If a tool returns a file that is already known to the user (e.g., a source file), only the "newly read" parts are scanned to save performance.
    *   **Placeholder Injection**: Redacted text is replaced with a semantic placeholder (e.g., `[REDACTED_API_KEY]`) so the LLM knows the *type* of data that was there without seeing the value.
*   **Pros**: Prevents secrets from ever reaching the model's training logs or cloud infrastructure.
*   **Cons**: Can increase latency; high-volume tools (e.g., `ls -R`) can overwhelm the scanner.

### 2. Environment Variable Masking (Secure Process Spawning)
Ensures that when the CLI spawns a subprocess (e.g., via `run_shell_command`), the model cannot inadvertently read sensitive environment variables.

*   **Mechanism**:
    *   **Whitelisted Env Propagation**: Instead of passing the entire host environment to the sandbox, the CLI only propagates a minimal, whitelisted set of variables (e.g., `PATH`, `LANG`, `PWD`).
    *   **Shadow Masking**: Any sensitive variable found in a command string (e.g., `echo $GITHUB_TOKEN`) is intercepted by the CLI and redacted from the log history sent to the LLM.
*   **Pros**: Minimizes the attack surface for environment-based secret theft.
*   **Cons**: May break scripts that rely on complex or non-standard environment variables.

### 3. Differential Privacy for Log Export
Ensures that when telemetry logs are exported to centralized storage (e.g., GCP Logging), they are anonymized at the source.

*   **Mechanism**:
    *   **Local Aggregation**: Metrics and events are aggregated locally over a window of time before being exported.
    *   **Noise Injection**: Adding statistical noise to numeric telemetry data to prevent "re-identification" of specific user patterns.
*   **Pros**: Complies with GDPR/CCPA for enterprise auditing while preserving system privacy.
*   **Cons**: Reduces the granular accuracy of debugging logs for developers.

## Proposed Research Tasks
1. **Redaction Engine Performance**: Evaluate the latency impact of running complex regex-based redaction on every tool output before it's sent to the LLM.
2. **Secret Detection Benchmarks**: Compare the effectiveness of different open-source secret scanning tools (e.g., `gitleaks`, `trufflehog`) for local integration.
3. **Data Anonymization Study**: Research methods for anonymizing PII in log files while still providing enough context for the LLM to perform debugging tasks.
4. **Local LLM Pre-Scrubbing**: Investigate using a small, local LLM (like TinyLlama) to identify and redact sensitive information before it reaches the cloud-based model.
