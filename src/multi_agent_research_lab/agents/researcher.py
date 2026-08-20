"""Researcher agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None, llm_client: LLMClient | None = None) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        query = state.request.query
        sources = self.search_client.search(query, max_results=state.request.max_sources)
        state.sources = sources

        context_str = "\n\n".join(
            f"Source [{i+1}] {s.title} ({s.url or 'N/A'}):\n{s.snippet}"
            for i, s in enumerate(sources)
        )

        system_prompt = (
            "You are a Senior Technical Researcher. Given the research query and retrieved sources, "
            "extract key empirical facts, architectural concepts, and cite each fact using [Source X] format."
        )
        user_prompt = f"Topic: {query}\n\nRetrieved Documents:\n{context_str}"

        llm_resp = self.llm_client.complete(system_prompt, user_prompt)
        state.research_notes = llm_resp.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=llm_resp.content,
                metadata={
                    "source_count": len(sources),
                    "input_tokens": llm_resp.input_tokens,
                    "output_tokens": llm_resp.output_tokens,
                    "cost_usd": llm_resp.cost_usd,
                },
            )
        )
        state.add_trace_event("researcher_complete", {"source_count": len(sources)})
        return state
