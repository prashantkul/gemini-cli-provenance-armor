# 06_trusted_folder_integrity.md: Trusted Folder Hardening Research

## Background
The "Trusted Folders" feature allows Gemini CLI to remember user-granted permissions for specific directories. This prevents repeated prompts but introduces a risk if an attacker can manipulate the path resolution or exploit race conditions during the check. Hardening this feature against symlink attacks and path traversal is essential.

## Threat Vectors
- **Symlink Race Condition (TOCTOU)**: An attacker creates a symlink to a sensitive directory *after* the path is checked but *before* the file operation is performed.
- **Path Traversal Attacks**: Exploiting the path resolution logic to bypass the restricted "trusted" boundary using `../` sequences or encoded characters.
- **Trusted Path Confusion**: Creating a directory that looks like a trusted one (e.g., `~/trusted_folder ` with a trailing space) to trick the user into granting permissions.
- **Configuration Corruption**: Modifying the local database or file where "trusted folder" metadata is stored to grant unauthorized access to other directories.

## Mitigation Strategies
- **Canonical Path Resolution**: Resolving all paths to their canonical form (no symlinks, no `..`) before performing any security checks.
- **File Descriptor Pinning**: Opening a file or directory descriptor and performing operations on that descriptor to prevent TOCTOU (Time-of-Check to Time-of-Use) attacks.
- **Metadata Protection**: Protecting the integrity of the trusted folder database using hashing and encryption to prevent unauthorized modifications.
- **Path-Bound Credentials**: Tying certain permissions (like API keys or tokens) specifically to a trusted folder, ensuring they are only available when the agent is operating within that boundary.

## Proposed Research Tasks
1. **Symlink Attack Vectors**: Create a set of "adversarial directory structures" involving complex symlink chains to test the canonicalization logic.
2. **Descriptor-Based API Study**: Evaluate the feasibility of moving all file-based tools in Gemini CLI to use file descriptor-based APIs for enhanced security.
3. **Database Integrity Audit**: Analyze the storage format for trusted folder information and design a mechanism for secure, tamper-proof persistence.
4. **Path Boundary Visualization**: Develop a feature that clearly displays the current "effective trust boundary" to the user, highlighting any potential path confusion risks.
