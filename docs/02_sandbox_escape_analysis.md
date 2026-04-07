# 02_sandbox_escape_analysis.md: Sandbox Escape and Isolation Analysis

## Background
Gemini CLI executes shell commands and scripts directly on the user's host machine. While this provides power and flexibility, it presents significant security risks if the agent is manipulated into performing malicious actions. Current implementations rely on OS-level sandboxing (macOS `sandbox-exec` and Windows "Low Mandatory Level").

## Threat Vectors
- **Platform-Specific Escapes**: Vulnerabilities in macOS `sandbox-exec` or Windows LML that allow escaping to higher privilege levels.
- **Resource Exhaustion**: Malicious commands that consume 100% CPU or disk space to perform a Denial of Service (DoS) attack.
- **Environment Variable Leakage**: Processes running in the sandbox might still access sensitive global environment variables or local network services.
- **Symlink Attacks**: Exploiting the sandbox by creating symlinks to files outside the restricted directory before the sandbox is fully enforced.

## Mitigation Strategies
- **Containerization (Docker/gVisor)**: Moving tool execution to a Docker container or gVisor sandbox to provide kernel-level isolation from the host.
- **Fine-Grained Permissions**: Implementing a capability-based system where the user grants specific tool access (e.g., "Allow `npm install` but deny `curl`").
- **Network Isolation**: Using virtual network namespaces to block all external network access from the sandbox except for explicitly allowed domains.
- **Static Analysis of Commands**: Pre-scanning shell commands for suspicious patterns or disallowed utilities before they are executed.

## Proposed Research Tasks
1. **Comparative Benchmarking**: Compare the performance and security overhead of macOS `sandbox-exec` versus a lightweight Docker-based runner.
2. **Escape POCs**: Develop proof-of-concept scripts that attempt to bypass existing sandbox boundaries on different OS platforms.
3. **Wasm Tooling**: Investigate the feasibility of running certain subagents or skills within a WebAssembly (Wasm) runtime for enhanced isolation.
4. **Policy-Driven Isolation**: Design a system where the sandbox strictness dynamically increases based on the risk level of the current task.
