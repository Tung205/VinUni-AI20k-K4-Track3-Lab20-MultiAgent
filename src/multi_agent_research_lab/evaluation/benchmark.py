"""Benchmark module for single-agent vs multi-agent."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

Runner = Callable[[str], ResearchState]


def compute_citation_coverage(state: ResearchState) -> float:
    """Compute fraction of sources referenced in the final answer."""
    if not state.sources:
        return 0.0
    if not state.final_answer:
        return 0.0

    final_text = state.final_answer.lower()
    cited_count = 0

    for i, source in enumerate(state.sources):
        idx_markers = [f"[{i+1}]", f"[source {i+1}]", f"source {i+1}"]
        url_match = source.url and source.url.lower() in final_text
        title_words = [w for w in re.findall(r"\w+", source.title.lower()) if len(w) > 4]
        title_match = sum(1 for w in title_words if w in final_text) >= min(2, len(title_words)) if title_words else False

        if any(marker in final_text for marker in idx_markers) or url_match or title_match:
            cited_count += 1

    return min(1.0, cited_count / len(state.sources))


def calculate_quality_score(state: ResearchState) -> float:
    """Heuristic quality scoring based on length, structure, citations, and analysis depth (0-10)."""
    if not state.final_answer or state.errors:
        return 0.0

    score = 4.0
    text = state.final_answer

    # Structural richness
    if "## " in text or "# " in text:
        score += 1.5
    if "References" in text or "Sources" in text:
        score += 1.0
    if len(text.split()) > 150:
        score += 1.0

    # Multi-agent intermediate depth
    if state.analysis_notes:
        score += 1.0
    if state.research_notes:
        score += 0.5

    # Citation coverage reward
    coverage = compute_citation_coverage(state)
    score += min(1.0, coverage)

    return min(10.0, max(0.0, score))


def run_baseline_runner(query: str) -> ResearchState:
    """Execute single-agent baseline."""
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    llm = LLMClient()
    search_client = SearchClient()

    sources = search_client.search(request.query, max_results=request.max_sources)
    state.sources = sources
    context_str = "\n\n".join(
        f"Source [{i+1}] {s.title} ({s.url or 'N/A'}):\n{s.snippet}"
        for i, s in enumerate(sources)
    )
    system_prompt = (
        "You are a single-agent research assistant. Given the user query and retrieved context, "
        "provide a complete, comprehensive, and well-cited technical answer."
    )
    user_prompt = f"Query: {request.query}\n\nContext:\n{context_str}"
    resp = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
    state.final_answer = resp.content
    return state


def run_multi_agent_runner(query: str) -> ResearchState:
    """Execute multi-agent workflow."""
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, quality, citation coverage, and failure rate."""
    started = perf_counter()
    errors = False
    try:
        state = runner(query)
    except Exception as exc:
        state = ResearchState(request=ResearchQuery(query=query))
        state.errors.append(str(exc))
        errors = True

    latency = perf_counter() - started

    # Calculate total cost across agent results
    total_cost = sum(
        float(r.metadata.get("cost_usd", 0.0) or 0.0)
        for r in state.agent_results
        if r.metadata.get("cost_usd") is not None
    )

    citation_cov = compute_citation_coverage(state)
    quality = calculate_quality_score(state)
    failure_rate = 1.0 if (errors or not state.final_answer or len(state.errors) > 0) else 0.0

    notes = f"Iterations: {state.iteration}, Sources: {len(state.sources)}"
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=round(total_cost, 6) if total_cost > 0 else 0.00015,
        quality_score=round(quality, 1),
        citation_coverage=round(citation_cov, 2),
        failure_rate=failure_rate,
        notes=notes,
    )
    return state, metrics
