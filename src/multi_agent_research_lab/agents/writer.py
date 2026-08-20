"""Writer agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes with citations."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        sources_text = "\n".join(
            f"[{i + 1}] {s.title} ({s.url or 'N/A'})\nSnippet: {s.snippet}"
            for i, s in enumerate(state.sources)
        )

        system_prompt = (
            "You are a Principal Technical Writer. Synthesize a comprehensive, authoritative final report "
            "based on the research notes and analysis notes. Include explicit inline citations [1], [2], etc., "
            "and append a formal References section."
        )
        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Target Audience: {state.request.audience}\n\n"
            f"Research Notes:\n{state.research_notes or 'N/A'}\n\n"
            f"Analysis Notes:\n{state.analysis_notes or 'N/A'}\n\n"
            f"Available Sources:\n{sources_text}"
        )

        llm_resp = self.llm_client.complete(system_prompt, user_prompt)
        state.final_answer = llm_resp.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=llm_resp.content,
                metadata={
                    "input_tokens": llm_resp.input_tokens,
                    "output_tokens": llm_resp.output_tokens,
                    "cost_usd": llm_resp.cost_usd,
                },
            )
        )
        state.add_trace_event("writer_complete", {})
        return state
