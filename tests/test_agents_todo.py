"""Unit tests for agents, supervisor routing, and multi-agent workflow."""

from multi_agent_research_lab.agents import AnalystAgent, CriticAgent, ResearcherAgent, SupervisorAgent, WriterAgent
from multi_agent_research_lab.core.schemas import AgentName, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_supervisor_routing_order() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain GraphRAG architecture"))
    supervisor = SupervisorAgent(max_iterations=6)

    # Step 1: No sources -> researcher
    state = supervisor.run(state)
    assert state.route_history[-1] == "researcher"

    # Researcher executes
    researcher = ResearcherAgent()
    state = researcher.run(state)
    assert len(state.sources) > 0
    assert state.research_notes is not None

    # Step 2: Has sources & notes, no analysis -> analyst
    state = supervisor.run(state)
    assert state.route_history[-1] == "analyst"

    # Analyst executes
    analyst = AnalystAgent()
    state = analyst.run(state)
    assert state.analysis_notes is not None

    # Step 3: Has analysis, no final answer -> writer
    state = supervisor.run(state)
    assert state.route_history[-1] == "writer"

    # Writer executes
    writer = WriterAgent()
    state = writer.run(state)
    assert state.final_answer is not None

    # Step 4: Has final answer, no critic -> critic
    state = supervisor.run(state)
    assert state.route_history[-1] == "critic"

    # Critic executes
    critic = CriticAgent()
    state = critic.run(state)
    assert any(r.agent == AgentName.CRITIC for r in state.agent_results)

    # Step 5: Everything complete -> done
    state = supervisor.run(state)
    assert state.route_history[-1] == "done"


def test_workflow_end_to_end() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    workflow = MultiAgentWorkflow()
    final_state = workflow.run(state)

    assert final_state.final_answer is not None
    assert len(final_state.sources) > 0
    assert final_state.research_notes is not None
    assert final_state.analysis_notes is not None
    assert "done" in final_state.route_history
    assert len(final_state.agent_results) >= 4
