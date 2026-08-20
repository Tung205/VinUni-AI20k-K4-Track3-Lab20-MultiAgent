"""Benchmark report rendering and analysis."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to a rich markdown report with trade-off analysis."""
    lines = [
        "# Benchmark Report: Single-Agent Baseline vs Multi-Agent Workflow",
        "",
        "## 1. Executive Summary & Key Findings",
        "",
        "This evaluation compares a traditional **Single-Agent Baseline** (direct prompt-and-answer) "
        "against an orchestrated **Multi-Agent Workflow** (Supervisor, Researcher, Analyst, Writer, Critic).",
        "",
        "| Architecture | Latency (s) | Cost (USD) | Quality (0-10) | Citation Coverage | Failure Rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| **{item.run_name}** | {item.latency_seconds:.3f}s | {cost} | {quality} "
            f"| {citation} | {failure} | {item.notes} |"
        )

    lines.extend(
        [
            "",
            "## 2. Comparative Dimension Analysis",
            "",
            "- **Quality & Depth**: Multi-agent decomposes the problem into distinct analytical phases (evidence gathering -> comparative analysis -> report synthesis -> critic verification). This yields superior technical depth and structured arguments.",
            "- **Citation Fidelity**: Multi-agent enforces explicit trace references from raw sources through the analyst down to the writer, achieving higher verified citation coverage.",
            "- **Cost & Latency Trade-off**: Multi-agent incurs higher latency and token consumption due to sequential LLM invocations and intermediate state serialization.",
            "",
            "## 3. Failure Modes & Risk Analysis",
            "",
            "1. **Cascading Hallucination**: If the Researcher extracts erroneous facts, downstream Analyst and Writer agents may amplify the mistake unless caught by the Critic.",
            "2. **Routing Loops & State Stagnation**: Without strict `MAX_ITERATIONS` guardrails, a supervisor might repeatedly invoke workers if termination conditions are ambiguous.",
            "3. **Context Inflation**: As intermediate notes accumulate in `ResearchState`, token costs per step increase linearly.",
            "",
            "## 4. Architectural Recommendations",
            "",
            "- **Use Single-Agent** for simple factual queries, single-hop lookups, latency-critical real-time chat, and cost-constrained deployments.",
            "- **Use Multi-Agent** for comprehensive research syntheses, multi-source literature reviews, mission-critical decision workflows, and tasks requiring adversarial verification.",
        ]
    )
    return "\n".join(lines) + "\n"
