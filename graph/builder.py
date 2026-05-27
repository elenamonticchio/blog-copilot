"""
Costruzione e cablaggio del grafo LangGraph.
La logica dei nodi vive in agents/nodes.py — qui c'è solo il wiring.
"""
from langgraph.graph import StateGraph, START, END

from graph.state import AgentState
from agents.nodes import (
    suggest_topics,
    planner,
    research,
    verify_and_select,
    draft,
    human_review,
    update_kg,
    route_after_review,
)


def build_graph():
    builder = StateGraph(AgentState)

    # registra i nodi
    builder.add_node("suggest_topics", suggest_topics)
    builder.add_node("planner", planner)
    builder.add_node("research", research)
    builder.add_node("verify_and_select", verify_and_select)
    builder.add_node("draft", draft)
    builder.add_node("human_review", human_review)
    builder.add_node("update_kg", update_kg)

    # flusso lineare principale
    builder.add_edge(START, "suggest_topics")
    builder.add_edge("suggest_topics", "planner")
    builder.add_edge("planner", "research")
    builder.add_edge("research", "verify_and_select")
    builder.add_edge("verify_and_select", "draft")
    builder.add_edge("draft", "human_review")

    # edge condizionale: cuore dell'human-in-the-loop
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "update_kg": "update_kg",
            "draft": "draft",     # rigetto -> rigenera
            "end": END,
        },
    )

    builder.add_edge("update_kg", END)

    # NOTA Fase 7: per l'interrupt servira un checkpointer:
    #   from langgraph.checkpoint.memory import MemorySaver
    #   return builder.compile(checkpointer=MemorySaver())
    return builder.compile()


graph = build_graph()
