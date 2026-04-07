# 03_policy_engine_logic.md: Policy Engine and Precedence Analysis

## Background
Gemini CLI uses a TOML-based policy engine to define which tools are allowed or denied in different contexts. Policies can be defined at multiple levels: Admin (global/machine-wide), User (home directory), and Workspace (project-specific). Ensuring correct resolution and preventing "fail-open" states is critical for security.

## Threat Vectors
- **Policy Overriding**: A malicious workspace-level policy trying to override a restricted admin-level policy (e.g., an admin-level `deny run_shell_command` being ignored in favor of a workspace-level `allow`).
- **Conflict Ambiguity**: A situation where both allow and deny rules apply to the same tool, leading to unexpected behavior if the conflict resolution logic is flawed.
- **Fail-Open Default**: If the policy engine fails to load or encounters an error, it defaults to a permissive state rather than a restrictive one.
- **Inconsistent Parsing**: Subtle differences in how TOML is parsed across different environments, potentially leading to security bypasses through specialized formatting.

## Mitigation Strategies
- **Hierarchical Precedence**: Strict enforcement of policy order: Admin > User > Workspace. Deny rules at a higher level must always override allow rules at a lower level.
- **Fail-Safe Implementation**: The system should default to a "deny-all" state if the policy engine fails to load or if a tool is not explicitly allowed.
- **Policy Integrity Checks**: Sign policies or use checksums to ensure they haven't been tampered with.
- **Admin-Only Lockout**: Provide a mechanism for administrators to lock certain policies, making them immutable by user or workspace-level changes.

## Proposed Research Tasks
1. **Precedence Logic Audit**: Perform a formal logic audit of the policy resolution algorithm to ensure that no "deny" at a higher level can be bypassed by an "allow" at a lower level.
2. **Error Handling Robustness**: Unit and integration testing of the policy loader to verify that errors always result in a secure, restrictive state.
3. **Admin Policy Implementation**: Design and implement a "global admin policy" feature that can be pushed to multiple machines and cannot be modified by local users.
4. **Policy Visualization Tool**: Create a tool to help users and admins understand the effective policy for a given directory, highlighting any potential conflicts.
