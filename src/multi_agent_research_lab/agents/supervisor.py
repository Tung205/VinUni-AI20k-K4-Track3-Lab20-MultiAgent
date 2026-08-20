"""Supervisor / router implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, max_iterations: int | None = None) -> None:
        settings = get_settings()
        self.max_iterations = max_iterations or settings.max_iterations

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        if state.iteration >= self.max_iterations:
            next_route = "done"
        elif not state.sources or not state.research_notes:
            next_route = "researcher"
        elif not state.analysis_notes:
            next_route = "analyst"
        elif not state.final_answer:
            next_route = "writer"
        elif not any(r.agent == AgentName.CRITIC for r in state.agent_results):
            next_route = "critic"
        else:
            next_route = "done"

        state.record_route(next_route)
        state.add_trace_event(
            "supervisor_route",
            {
                "next_route": next_route,
                "iteration": state.iteration,
                "has_sources": bool(state.sources),
                "has_research_notes": bool(state.research_notes),
                "has_analysis_notes": bool(state.analysis_notes),
                "has_final_answer": bool(state.final_answer),
            },
        )
        return state
