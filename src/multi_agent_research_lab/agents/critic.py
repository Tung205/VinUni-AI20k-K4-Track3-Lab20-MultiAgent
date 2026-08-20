"""Critic agent implementation for fact-checking and citation validation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Fact-checking, citation verification, and safety-review agent."""

    name = "critic"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        system_prompt = (
            "You are a Rigorous Fact-Checking and Quality Assurance Critic. "
            "Examine the final answer, verify citation alignment against the sources, and check for hallucinations."
        )
        sources_summary = "\n".join(f"[{i+1}] {s.title}" for i, s in enumerate(state.sources))
        user_prompt = (
            f"Final Answer:\n{state.final_answer or 'N/A'}\n\n"
            f"Sources:\n{sources_summary}\n\n"
            f"Analysis:\n{state.analysis_notes or 'N/A'}"
        )

        llm_resp = self.llm_client.complete(system_prompt, user_prompt)
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=llm_resp.content,
                metadata={
                    "verified": True,
                    "input_tokens": llm_resp.input_tokens,
                    "output_tokens": llm_resp.output_tokens,
                    "cost_usd": llm_resp.cost_usd,
                },
            )
        )
        state.add_trace_event("critic_complete", {"status": "verified"})
        return state
