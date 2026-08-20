"""Analyst agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        notes = state.research_notes or "No raw notes available."
        sources_summary = "\n".join(
            f"- [{i + 1}] {s.title} (Relevance: {s.metadata.get('relevance', 'N/A')})"
            for i, s in enumerate(state.sources)
        )

        system_prompt = (
            "You are a Critical Systems Analyst. Analyze the research notes, compare differing perspectives, "
            "evaluate evidence reliability, identify technical bottlenecks/limitations, and suggest architectural trade-offs."
        )
        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Sources Summary:\n{sources_summary}\n\n"
            f"Research Notes:\n{notes}"
        )

        llm_resp = self.llm_client.complete(system_prompt, user_prompt)
        state.analysis_notes = llm_resp.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=llm_resp.content,
                metadata={
                    "input_tokens": llm_resp.input_tokens,
                    "output_tokens": llm_resp.output_tokens,
                    "cost_usd": llm_resp.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst_complete", {})
        return state
