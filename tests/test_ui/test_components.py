"""Tests for UI components."""

from io import StringIO

from rich.console import Console

from provenance_armor.models.scoring import CausalVerdict, DominanceResult, LOOScoreSet
from provenance_armor.models.tool_call import RiskLevel, ToolCallRequest
from provenance_armor.ui.blast_radius import render_blast_radius
from provenance_armor.ui.causal_meter import render_causal_meter
from provenance_armor.ui.progressive import render_risk_badge, render_tool_header, should_checkpoint
from provenance_armor.ui.renderer import ProvenanceRenderer


def _safe_result() -> DominanceResult:
    return DominanceResult(
        scores=LOOScoreSet(p_full=-1.0, p_without_user=-5.0, p_without_untrusted=-1.5),
        verdict=CausalVerdict.SAFE,
        margin_tau=0.5,
        dominant_spans=[],
        explanation="Safe",
    )


def _dominated_result() -> DominanceResult:
    return DominanceResult(
        scores=LOOScoreSet(p_full=-1.0, p_without_user=-1.2, p_without_untrusted=-5.0),
        verdict=CausalVerdict.DOMINATED,
        margin_tau=0.5,
        dominant_spans=["span1"],
        explanation="Dominated",
    )


class TestCausalMeter:
    def test_safe_meter_renders(self):
        panel = render_causal_meter(_safe_result())
        assert panel.title is not None
        assert "SAFE" in panel.title

    def test_dominated_meter_renders(self):
        panel = render_causal_meter(_dominated_result())
        assert "DOMINATED" in panel.title


class TestBlastRadius:
    def test_destructive_command(self):
        panel = render_blast_radius(raw_command="rm -rf /tmp/data")
        assert panel.title is not None
        assert "DESTRUCTIVE" in panel.title

    def test_network_command(self):
        panel = render_blast_radius(raw_command="curl http://example.com/data")
        assert "NETWORK" in panel.title

    def test_safe_command(self):
        panel = render_blast_radius(raw_command="ls /tmp")
        assert "DESTRUCTIVE" not in panel.title


class TestProgressive:
    def test_risk_badge(self):
        badge = render_risk_badge(RiskLevel.CRITICAL)
        assert "CRITICAL" in badge.plain

    def test_checkpoint_required(self):
        assert should_checkpoint(RiskLevel.CRITICAL) is True
        assert should_checkpoint(RiskLevel.HIGH) is True
        assert should_checkpoint(RiskLevel.LOW) is False


class TestProvenanceRenderer:
    def test_render_does_not_crash(self, sample_context, sample_request):
        """Ensure rendering completes without errors."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        renderer = ProvenanceRenderer(console=console)

        sample_request.classify_risk()
        renderer.render(
            sample_request,
            dominance=_safe_result(),
            context=sample_context,
        )

        output = buf.getvalue()
        assert len(output) > 0
