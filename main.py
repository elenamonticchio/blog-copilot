"""
Entry point: costruisce lo stato iniziale, esegue il grafo e mostra l'esito.
"""
from langchain_core.messages import HumanMessage

from graph.builder import graph
import config.settings  # noqa: F401  (carica .env e attiva LangSmith)


def initial_state(user_input: str) -> dict:
    """Stato di partenza con tutti i campi inizializzati (evita KeyError nei nodi)."""
    return {
        "messages": [HumanMessage(content=user_input)],
        "user_input": user_input,
        "suggested_topics": [],
        "editorial_plan": [],
        "current_post_index": 0,
        "post_type": "",
        "current_topic": "",
        "kg_context": "",
        "retrieved_docs": [],
        "tool_outputs": [],
        "reasoning_trace": [],
        "current_draft": "",
        "citations": [],
        "key_claims": [],
        "user_status": "",
        "user_feedback": "",
        "approved": False,
        "iteration_count": 0,
    }


if __name__ == "__main__":
    state = initial_state("Voglio gestire il mio blog su film e serie TV")

    print("=== AVVIO GRAFO ===\n")
    final = graph.invoke(state)

    print("\n=== TOPIC SUGGERITI (dal KG) ===")
    for s in final["suggested_topics"]:
        print(f"  - [{s.get('post_type')}] {s.get('topic')} -> {s.get('reason')}")

    print("\n=== ESECUZIONE COMPLETATA ===")
    print("Post in piano  :", len(final["editorial_plan"]))
    print("Topic corrente :", final["current_topic"])
    print("Bozza          :", final["current_draft"])
    for i, step in enumerate(final["reasoning_trace"], 1):
        print(f"\n--- Step {i} ---")
        print("Thought     :", step.get("thought"))
        print("Action      :", step.get("action"))
        print("Observation :", step.get("observation"))
