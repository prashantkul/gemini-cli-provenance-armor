#!/usr/bin/env python3
"""Gemini CLI BeforeTool hook for Provenance Armor.

This hook intercepts tool calls from Gemini CLI, runs causal analysis
to detect Indirect Prompt Injection, and returns allow/deny decisions.

Install by adding to your .gemini/settings.json:

{
  "hooks": {
    "BeforeTool": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "name": "provenance-armor",
            "type": "command",
            "command": "python3 /path/to/hooks/provenance_armor_hook.py",
            "timeout": 10000
          }
        ]
      }
    ]
  }
}
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add src/ to path so we can import provenance_armor
HOOK_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# Common dev commands that are safe even though they're MEDIUM risk
_SAFE_DEV_COMMANDS = frozenset({
    "npm", "npx", "yarn", "pnpm", "bun",
    "pip", "uv", "poetry", "pdm",
    "make", "cmake", "cargo", "go", "tsc", "node",
    "pytest", "jest", "vitest", "mocha",
    "eslint", "prettier", "ruff", "mypy", "black",
    "git", "gh",
    "docker", "docker-compose",
    "cat", "echo", "pwd", "whoami", "date", "which", "type",
    "mkdir", "touch", "cp", "mv", "ls", "find", "wc",
    "head", "tail", "sort", "uniq", "diff",
    "python", "python3", "ruby", "java", "javac",
})


def log(msg: str) -> None:
    """Debug logging to stderr (never stdout — that's for JSON responses)."""
    print(f"[provenance-armor] {msg}", file=sys.stderr)


def build_context_from_transcript(transcript_path: str | None) -> list[dict]:
    """Read the conversation transcript to build context for causal analysis."""
    if not transcript_path or not Path(transcript_path).exists():
        return []

    try:
        data = json.loads(Path(transcript_path).read_text())
        messages = []
        for entry in data if isinstance(data, list) else data.get("messages", []):
            role = entry.get("role", "")
            parts = entry.get("parts", [])
            content = ""
            for part in parts:
                if isinstance(part, str):
                    content += part
                elif isinstance(part, dict):
                    content += part.get("text", "")
            if content:
                messages.append({"role": role, "content": content})
        return messages
    except Exception as e:
        log(f"Could not read transcript: {e}")
        return []


def scan_workspace_for_untrusted(cwd: str) -> list[tuple[str, str]]:
    """Scan common files in the workspace that could contain injections."""
    untrusted: list[tuple[str, str]] = []
    suspect_files = [
        "README.md", "README.rst", "README.txt", "README",
        "CONTRIBUTING.md", "SETUP.md", "INSTALL.md",
        ".github/ISSUE_TEMPLATE.md", ".github/pull_request_template.md",
        "package.json", "pyproject.toml", "Makefile",
    ]

    for filename in suspect_files:
        filepath = Path(cwd) / filename
        if filepath.exists():
            try:
                content = filepath.read_text(errors="replace")[:5000]
                untrusted.append((str(filepath), content))
            except Exception:
                pass

    return untrusted


def analyze_tool_call(hook_input: dict) -> dict:
    """Run Provenance Armor causal analysis on the tool call.

    Returns a hook response dict with decision and reasoning.
    """
    from provenance_armor.core.analyzer import CausalAnalyzer
    from provenance_armor.core.decomposer import ContextDecomposer
    from provenance_armor.core.sanitizer import CausalSanitizer
    from provenance_armor.core.scorer import LOOScorer
    from provenance_armor.models.scoring import CausalVerdict
    from provenance_armor.models.tool_call import RiskLevel, ToolCallRequest
    from provenance_armor.providers.heuristic import HeuristicProvider
    from provenance_armor._utils.shell_parser import parse_shell_command

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    cwd = hook_input.get("cwd", os.getcwd())
    transcript_path = hook_input.get("transcript_path")

    # Build the tool call request
    raw_command = None
    if tool_name in ("run_shell_command", "shell"):
        raw_command = tool_input.get("command", tool_input.get("cmd", ""))

    request = ToolCallRequest(
        function_name=tool_name,
        function_args=tool_input,
        raw_command=raw_command,
    )
    request.classify_risk()

    # Low-risk tools pass through without analysis
    if request.risk_level == RiskLevel.LOW:
        return {
            "decision": "allow",
            "message": f"[provenance-armor] Low-risk tool '{tool_name}' — skipping analysis",
        }

    # Safe common dev commands pass through (no pipe, no network, no secrets)
    if raw_command:
        impact = parse_shell_command(raw_command)
        is_safe_dev_cmd = (
            not impact.is_network
            and not impact.accesses_secrets
            and not impact.piped
            and all(
                cmd in _SAFE_DEV_COMMANDS for cmd in impact.commands
            )
        )
        if is_safe_dev_cmd:
            return {
                "decision": "allow",
                "message": f"[provenance-armor] Safe dev command — {' '.join(impact.commands)}",
            }

    # Build context from transcript + workspace files
    decomposer = ContextDecomposer()

    # Try to extract user request from transcript
    messages = build_context_from_transcript(transcript_path)
    user_request = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_request = msg["content"]
            break

    if not user_request:
        user_request = f"(user instruction not available — tool call: {tool_name})"

    # Scan workspace for untrusted content
    untrusted_data = scan_workspace_for_untrusted(cwd)

    # If there's a shell command, also treat it as context
    if raw_command:
        impact = parse_shell_command(raw_command)

        # Quick blast radius check — flag obviously dangerous combos
        if impact.is_network and impact.is_destructive:
            log(f"CRITICAL: Command is both destructive and network-accessing: {raw_command}")
            return {
                "decision": "deny",
                "reason": (
                    f"[provenance-armor] BLOCKED: Command combines destructive "
                    f"and network operations — {', '.join(impact.commands)}"
                ),
            }

    context = decomposer.from_explicit(
        user_request=user_request,
        untrusted_data=untrusted_data,
        history=[msg["content"] for msg in messages if msg.get("role") != "user"][:5],
    )

    # Run LOO scoring with heuristic provider
    provider = HeuristicProvider()
    scorer = LOOScorer(provider)
    analyzer = CausalAnalyzer(margin_tau=0.5)

    scores = scorer.score(context, request)
    result = analyzer.analyze(scores, context)

    log(f"Tool: {tool_name} | Risk: {request.risk_level.value} | "
        f"Verdict: {result.verdict.value} | Margin: {scores.dominance_margin:+.2f}")

    if result.verdict == CausalVerdict.DOMINATED:
        # Identify the source of the injection
        sources = []
        for span_id in result.dominant_spans:
            span = context.span_by_id(span_id)
            if span and span.provenance:
                sources.append(span.provenance.display())

        source_str = ", ".join(sources) if sources else "unknown"

        return {
            "decision": "deny",
            "reason": (
                f"[provenance-armor] BLOCKED — Indirect Prompt Injection detected.\n"
                f"  Verdict: {result.verdict.value.upper()}\n"
                f"  Untrusted data influence: {scores.untrusted_influence:.2f} "
                f"(vs user: {scores.user_influence:.2f})\n"
                f"  Dominant source: {source_str}\n"
                f"  {result.explanation}"
            ),
        }

    if result.verdict == CausalVerdict.SUSPICIOUS:
        return {
            "decision": "allow",
            "message": (
                f"[provenance-armor] WARNING — Suspicious causal pattern.\n"
                f"  Margin: {scores.dominance_margin:+.2f} (threshold: {result.margin_tau})\n"
                f"  Proceeding with caution."
            ),
        }

    return {
        "decision": "allow",
        "message": f"[provenance-armor] OK — {result.verdict.value} (margin: {scores.dominance_margin:+.2f})",
    }


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            log("No input received on stdin")
            print(json.dumps({"decision": "allow", "message": "[provenance-armor] No input — passthrough"}))
            sys.exit(0)

        hook_input = json.loads(raw_input)
        tool_name = hook_input.get("tool_name", "unknown")
        log(f"Intercepted: {tool_name}")

        response = analyze_tool_call(hook_input)

        print(json.dumps(response))
        sys.stdout.flush()
        sys.exit(0)

    except Exception as e:
        log(f"Error: {e}")
        # Non-zero exit (not 2) = warning, tool proceeds
        print(json.dumps({"decision": "allow", "message": f"[provenance-armor] Hook error: {e}"}))
        sys.stdout.flush()
        sys.exit(0)


if __name__ == "__main__":
    main()
