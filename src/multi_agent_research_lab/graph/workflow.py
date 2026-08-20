"""LangGraph workflow implementation."""

from typing import Any

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.supervisor = SupervisorAgent(max_iterations=self.settings.max_iterations)
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    def build(self) -> Any:
        """Create and compile a LangGraph graph."""
        graph = StateGraph(ResearchState)

        # Register nodes
        graph.add_node("supervisor", self.supervisor.run)
        graph.add_node("researcher", self.researcher.run)
        graph.add_node("analyst", self.analyst.run)
        graph.add_node("writer", self.writer.run)
        graph.add_node("critic", self.critic.run)

        # Set entry point
        graph.set_entry_point("supervisor")

        # Routing function based on latest supervisor decision
        def route_condition(state: ResearchState) -> str:
            if not state.route_history:
                return "done"
            decision = state.route_history[-1]
            if decision in ["researcher", "analyst", "writer", "critic"]:
                return decision
            return "done"

        # Conditional edges from supervisor
        graph.add_conditional_edges(
            "supervisor",
            route_condition,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "done": END,
            },
        )

        # Workers always return control to supervisor
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        graph.add_edge("critic", "supervisor")

        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        app = self.build()
        result = app.invoke(state)
        if isinstance(result, ResearchState):
            return result
        return ResearchState.model_validate(result)
