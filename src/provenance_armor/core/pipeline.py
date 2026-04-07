"""ToolCallPipeline: the main orchestrator wiring all security components.

Every tool call flows through this pipeline:
1. Policy check   → is the tool allowed at all?
2. Risk assessment → classify risk level
3. Causal scoring  → LOO analysis (if causal_armor enabled + risk >= HIGH)
4. Sanitize loop   → if dominated, sanitize and retry (up to max_retries)
5. UI rendering    → display provenance, blast radius
6. Audit logging   → log the event
7. Decision        → allow / block / sanitize_and_retry / ask_user
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from provenance_armor.audit.logger import AuditLogger
from provenance_armor.core.analyzer import CausalAnalyzer
from provenance_armor.core.sanitizer import CausalSanitizer
from provenance_armor.core.scorer import LOOScorer
from provenance_armor.models.context import ContextWindow
from provenance_armor.models.policy import ViolationAction
from provenance_armor.models.scoring import CausalVerdict, DominanceResult
from provenance_armor.models.tool_call import RiskLevel, ToolCallRequest, ToolCallResult
from provenance_armor.policy.resolver import PolicyResolver

if TYPE_CHECKING:
    from provenance_armor.redaction.engine import RedactionEngine
    from provenance_armor.ui.renderer import ProvenanceRenderer

logger = logging.getLogger(__name__)


class ToolCallPipeline:
    """Main security pipeline orchestrator.

    Wires together policy resolution, causal scoring, sanitization,
    redaction, UI rendering, and audit logging into a single
    ``process()`` call.
    """

    def __init__(
        self,
        policy_resolver: PolicyResolver,
        scorer: LOOScorer,
        analyzer: CausalAnalyzer,
        sanitizer: CausalSanitizer,
        audit_logger: AuditLogger,
        redaction_engine: Optional["RedactionEngine"] = None,
        renderer: Optional["ProvenanceRenderer"] = None,
    ) -> None:
        self._policy = policy_resolver
        self._scorer = scorer
        self._analyzer = analyzer
        self._sanitizer = sanitizer
        self._audit = audit_logger
        self._redaction = redaction_engine
        self._renderer = renderer

    def process(
        self,
        context: ContextWindow,
        request: ToolCallRequest,
        prompt_id: Optional[str] = None,
    ) -> ToolCallResult:
        """Process a tool call through the full security pipeline."""

        # Step 1: Policy check
        policy = self._policy.resolve(request.function_name)
        if not policy.allowed:
            logger.info("Tool '%s' denied by policy", request.function_name)
            self._audit.log_tool_call(
                function_name=request.function_name,
                function_args=request.function_args,
                decision="block",
                success=False,
                prompt_id=prompt_id,
            )
            return ToolCallResult(request=request, decision="block")

        # Step 2: Risk assessment
        request.classify_risk()

        # Step 3: Causal scoring (if enabled and risk warrants it)
        dominance: Optional[DominanceResult] = None
        ca_config = policy.causal_armor

        if ca_config and ca_config.enabled and request.risk_level in (
            RiskLevel.CRITICAL,
            RiskLevel.HIGH,
        ):
            dominance = self._run_causal_analysis(
                context, request, ca_config.margin_tau
            )

            # Step 4: Handle dominance
            if dominance.verdict == CausalVerdict.DOMINATED:
                self._audit.log_causal_analysis(
                    verdict=dominance.verdict.value,
                    scores={
                        "p_full": dominance.scores.p_full,
                        "p_without_user": dominance.scores.p_without_user,
                        "p_without_untrusted": dominance.scores.p_without_untrusted,
                    },
                    dominant_spans=dominance.dominant_spans,
                    prompt_id=prompt_id,
                )

                decision = self._handle_dominance(
                    context, request, dominance, ca_config.on_violation,
                    ca_config.max_retries, ca_config.margin_tau, prompt_id,
                )
                if decision is not None:
                    return decision

        # Step 5: Redaction (on tool output if available)
        redacted_output = None
        if self._redaction and request.function_args.get("output"):
            from provenance_armor.redaction.engine import RedactionEngine
            result = self._redaction.scan(request.function_args["output"])
            if result.has_redactions:
                redacted_output = result.redacted_text

        # Step 6: Blast radius (for shell commands)
        blast_radius: Optional[dict[str, Any]] = None
        if request.raw_command:
            from provenance_armor._utils.shell_parser import parse_shell_command
            impact = parse_shell_command(request.raw_command)
            blast_radius = {
                "commands": impact.commands,
                "is_destructive": impact.is_destructive,
                "is_network": impact.is_network,
                "accesses_secrets": impact.accesses_secrets,
                "target_paths": impact.target_paths,
                "network_destinations": impact.network_destinations,
                "sensitive_paths": impact.sensitive_paths,
            }

        # Step 7: Render UI
        if self._renderer:
            self._renderer.render(request, dominance, blast_radius)

        # Step 8: Audit and return
        event = self._audit.log_tool_call(
            function_name=request.function_name,
            function_args=request.function_args,
            decision="allow",
            prompt_id=prompt_id,
        )

        return ToolCallResult(
            request=request,
            decision="allow",
            dominance_result=dominance,
            redacted_output=redacted_output,
            blast_radius=blast_radius,
            audit_event_id=event.event_id,
        )

    def _run_causal_analysis(
        self,
        context: ContextWindow,
        request: ToolCallRequest,
        margin_tau: float,
    ) -> DominanceResult:
        """Run LOO scoring and causal analysis."""
        scores = self._scorer.score(context, request)
        analyzer = CausalAnalyzer(margin_tau=margin_tau)
        return analyzer.analyze(scores, context)

    def _handle_dominance(
        self,
        context: ContextWindow,
        request: ToolCallRequest,
        dominance: DominanceResult,
        on_violation: ViolationAction,
        max_retries: int,
        margin_tau: float,
        prompt_id: Optional[str],
    ) -> Optional[ToolCallResult]:
        """Handle a dominated verdict according to the violation policy.

        Returns a ToolCallResult if the action should be blocked/ask_user,
        or None if sanitization succeeded and the pipeline should continue.
        """
        if on_violation == ViolationAction.BLOCK:
            self._audit.log_tool_call(
                function_name=request.function_name,
                function_args=request.function_args,
                decision="block",
                success=False,
                prompt_id=prompt_id,
            )
            return ToolCallResult(
                request=request,
                decision="block",
                dominance_result=dominance,
            )

        if on_violation == ViolationAction.ASK_USER:
            return ToolCallResult(
                request=request,
                decision="ask_user",
                dominance_result=dominance,
            )

        # SANITIZE_AND_RETRY
        for retry in range(max_retries):
            logger.info(
                "Sanitize-and-retry attempt %d/%d for %s",
                retry + 1, max_retries, request.function_name,
            )
            cleaned = self._sanitizer.sanitize(context, dominance)
            dominance = self._run_causal_analysis(cleaned, request, margin_tau)

            if dominance.verdict != CausalVerdict.DOMINATED:
                logger.info("Sanitization succeeded on attempt %d", retry + 1)
                return None  # Continue pipeline with clean context

        # Max retries exhausted — hard block
        logger.warning(
            "Sanitization failed after %d retries for %s — blocking",
            max_retries, request.function_name,
        )
        self._audit.log_tool_call(
            function_name=request.function_name,
            function_args=request.function_args,
            decision="block",
            success=False,
            prompt_id=prompt_id,
        )
        return ToolCallResult(
            request=request,
            decision="block",
            dominance_result=dominance,
        )
