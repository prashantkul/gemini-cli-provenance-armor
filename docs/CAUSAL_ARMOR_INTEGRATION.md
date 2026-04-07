# Gemini CLI: Causal Armor Integration Architecture

This document illustrates how **Causal Armor** is integrated as a middleware layer within the Gemini CLI to provide mathematically-backed protection against Indirect Prompt Injection (IPI).

## 1. Integration Flowchart

The following diagram shows the lifecycle of a tool call and the specific points where Causal Armor performs its analysis and intervention.

```mermaid
flowchart TD
    %% Styling
    classDef model fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef armor fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef policy fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef critical fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    %% Nodes
    Start([User Instruction Received]):::success
    Model[Model Generates Tool Call Action A]:::model
    
    %% Policy Engine
    Policy{Policy Engine Check}:::policy
    Policy -- Tool is Allowed --> PrivCheck{Is Tool Privileged?}
    Policy -- Tool is Denied --> Block([Block Action]):::critical

    %% Causal Armor Middleware
    PrivCheck -- No --> Execute([Execute Action]):::success
    PrivCheck -- Yes --> ArmorStart[Initiate Causal Armor Analysis]:::armor
    
    ArmorStart --> Decomp[Decompose Context: U, H, S]:::armor
    Decomp --> Scoring[Log-Prob Scoring via Proxy Provider]:::armor
    Scoring --> Attribution[Calculate Causal Influence: U vs S]:::armor
    
    Attribution --> Decision{Dominance Shift Detected?}:::armor
    
    %% Outcomes
    Decision -- No: User is Cause --> Execute
    Decision -- Yes: Data Hijacked --> Sanitize[Trigger Causal Sanitizer]:::critical
    
    Sanitize --> Strip[Strip Instructions from S]:::critical
    Strip --> Redact[Redact Agent CoT]:::critical
    Redact --> Regenerate[Regenerate Action from Clean Context]:::model
    Regenerate --> Model
```

## 3. MCP Security Gateway Integration

The **MCP Security Gateway** acts as the primary ingress point for external context ($S_{mcp}$). It is implemented as an internal middleware that "tags" all data coming from MCP servers (Slack, GitHub, Jira) before it enters the context window.

```mermaid
flowchart LR
    %% Styling
    classDef mcp fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef gateway fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef armor fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;

    %% Nodes
    MCPServer[(External MCP Server)]:::mcp
    Gateway[Gemini CLI MCP Gateway]:::gateway
    Context[(Context Window: U, H, S)]:::armor
    Armor[Causal Armor Scorer]:::armor

    %% Flow
    MCPServer -- Raw Data --> Gateway
    Gateway -- Tagged Data (S_mcp) --> Context
    Context -- U vs S_mcp --> Armor
    Armor -- Dominance Shift? --> Action{Allow / Sanitize}
```

### Key Gateway Functions:
1.  **Provenance Tagging:** Every string returned from an MCP call is wrapped in a metadata tag (e.g., `<mcp_source name="jira_server">...</mcp_source>`). This allows Causal Armor to isolate the specific "untrusted" span during decomposition.
2.  **Instruction Stripping (Pre-Scrubbing):** Before Causal Armor even sees the data, the Gateway performs a heuristic scan to redact common imperative patterns (e.g., "Ignore all previous instructions").
3.  **Causal Attribution (The Final Check):** If the model attempts to use a tool based on the MCP data, Causal Armor calculates the causal influence. If the `mcp_source` is the dominant cause of a high-risk action, the Gateway intercepts and **Sanitizes** the result.
