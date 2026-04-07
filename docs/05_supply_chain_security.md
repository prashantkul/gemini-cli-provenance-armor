# 05_supply_chain_security.md: Supply Chain Integrity Research

## Background
Gemini CLI's architecture includes subagents and skills, which can be built-in or provided by third parties. These extensions have broad access to the workspace. If the delivery mechanism or the components themselves are compromised, it could lead to severe security breaches. Ensuring their integrity through checksums and signing is essential.

## Threat Vectors
- **Malicious Subagent Injection**: A third-party subagent that is intentionally designed to perform malicious actions (e.g., data exfiltration, backdoors).
- **Compromised Repositories**: An attacker compromises the repository where subagents or skills are hosted and replaces a legitimate extension with a malicious one.
- **Dependency Hijacking**: A legitimate subagent or skill that depends on an external package that has been taken over by an attacker.
- **Update Poisoning**: A malicious update for a subagent or skill that is automatically installed by Gemini CLI.

## Mitigation Strategies
- **Component Signing**: Using digital signatures (e.g., Sigstore or GPG) for all built-in and official subagents/skills to verify their origin and integrity.
- **Checksum Verification**: Verifying the SHA-256 checksum of every component before it's loaded or executed by the CLI.
- **Permission Scoping**: Implementing a "sandbox" for subagents that restricts their access to specific tools or directories based on their declared capabilities.
- **Secure Component Registry**: Establishing a vetted registry for third-party subagents and skills with mandatory security reviews.

## Proposed Research Tasks
1. **Signing Infrastructure Design**: Design a robust PKI (Public Key Infrastructure) or use a modern, keyless signing system for subagents and skills.
2. **Component Sandboxing**: Research techniques for isolating subagents and limiting their access to only the tools they explicitly require.
3. **Dependency Analysis**: Develop a tool to scan the dependency trees of all built-in subagents and identify any vulnerabilities or suspicious packages.
4. **Registry Security Policy**: Define a comprehensive security policy for third-party subagent submissions, including automated and manual review processes.
