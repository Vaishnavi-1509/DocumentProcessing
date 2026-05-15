from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from app.workflow.state import ClaimState
from app.workflow.nodes.segregator import segregator_node
from app.workflow.nodes.id_agent import id_agent_node
from app.workflow.nodes.discharge_agent import discharge_agent_node
from app.workflow.nodes.bill_agent import bill_agent_node
from app.workflow.nodes.aggregator import aggregator_node


def route_to_extractors(state: ClaimState) -> list[Send]:
    return [
        Send("id_agent", state),
        Send("discharge_agent", state),
        Send("bill_agent", state),
    ]


graph = StateGraph(ClaimState)
graph.add_node("segregator", segregator_node)
graph.add_node("id_agent", id_agent_node)
graph.add_node("discharge_agent", discharge_agent_node)
graph.add_node("bill_agent", bill_agent_node)
graph.add_node("aggregator", aggregator_node)

graph.add_edge(START, "segregator")
graph.add_conditional_edges("segregator", route_to_extractors)
graph.add_edge("id_agent", "aggregator")
graph.add_edge("discharge_agent", "aggregator")
graph.add_edge("bill_agent", "aggregator")
graph.add_edge("aggregator", END)

claim_graph = graph.compile()
