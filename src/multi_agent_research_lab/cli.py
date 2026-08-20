"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.utils.timer import elapsed_timer

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline end-to-end and report metrics."""

    _init()
    request = _parse_query(query)
    state = ResearchState(request=request)

    llm = LLMClient()
    search_client = SearchClient()

    with elapsed_timer() as timer:
        # Single-agent direct query answering with search retrieval
        sources = search_client.search(request.query, max_results=request.max_sources)
        state.sources = sources

        context_str = "\n\n".join(
            f"Source [{i + 1}] {s.title} ({s.url or 'N/A'}):\n{s.snippet}"
            for i, s in enumerate(sources)
        )
        system_prompt = (
            "You are a single-agent research assistant. Given the user query and retrieved context, "
            "provide a complete, comprehensive, and well-cited technical answer."
        )
        user_prompt = f"Query: {request.query}\n\nContext:\n{context_str}"

        response = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.final_answer = response.content
        latency = timer()

    cost_str = f"${response.cost_usd:.5f}" if response.cost_usd is not None else "N/A"
    in_tok = response.input_tokens or 0
    out_tok = response.output_tokens or 0

    state.add_trace_event(
        "baseline_execution",
        {
            "latency_seconds": latency,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": response.cost_usd,
        },
    )

    console.print(
        Panel.fit(state.final_answer, title=f"Single-Agent Baseline Response: {request.query}")
    )
    console.print(
        Panel.fit(
            f"[bold cyan]Latency:[/bold cyan] {latency:.3f}s | "
            f"[bold green]Input Tokens:[/bold green] {in_tok} | "
            f"[bold yellow]Output Tokens:[/bold yellow] {out_tok} | "
            f"[bold magenta]Estimated Cost:[/bold magenta] {cost_str}",
            title="Baseline Metrics",
            style="green",
        )
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=_parse_query(query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command("benchmark")
def benchmark_cmd(
    query: Annotated[
        str, typer.Option("--query", "-q", help="Research query")
    ] = "Research GraphRAG state-of-the-art",
    output_file: Annotated[
        str, typer.Option("--output", "-o", help="Report output file")
    ] = "reports/benchmark_report.md",
) -> None:
    """Run benchmark comparing single-agent baseline vs multi-agent workflow and generate report."""

    _init()
    from pathlib import Path

    from multi_agent_research_lab.evaluation.benchmark import (
        run_baseline_runner,
        run_benchmark,
        run_multi_agent_runner,
    )
    from multi_agent_research_lab.evaluation.report import render_markdown_report

    console.print(f"[bold green]Running Baseline on:[/bold green] {query}")
    _, baseline_metrics = run_benchmark("Baseline Single-Agent", query, run_baseline_runner)

    console.print(f"[bold green]Running Multi-Agent Workflow on:[/bold green] {query}")
    _, multi_metrics = run_benchmark("Multi-Agent Workflow", query, run_multi_agent_runner)

    metrics_list = [baseline_metrics, multi_metrics]
    report_md = render_markdown_report(metrics_list)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")

    console.print(Panel.fit(report_md, title="Benchmark Summary"))
    console.print(f"[bold cyan]Report saved to:[/bold cyan] {output_file}")


if __name__ == "__main__":
    app()
