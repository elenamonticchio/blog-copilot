"""
Nodi del grafo (architettura modulare — separati dal cablaggio in graph/builder.py).

Stato attuale:
  - suggest_topics  -> REALE: interroga il KG (gap + post recenti) e genera idee con l'LLM
  - planner         -> SEMI-REALE: trasforma i suggerimenti in un piano editoriale
  - research        -> STUB (Fase 4/6: K-RAG con tool e ReAct)
  - verify_and_select -> STUB (Fase 6)
  - draft           -> STUB (Fase 6)
  - human_review    -> STUB (Fase 7: interrupt reale)
  - update_kg       -> STUB (Fase 6/7: scrive nel KG dopo approvazione)
"""
import json
import re

from graph.state import AgentState, PlannedPost, MAX_ITERATIONS
from config.settings import get_llm
from config.domain import DOMAIN_TOPICS
from kg.kg_manager import KnowledgeGraphManager


def _extract_json_array(text: str):
    """Estrae il primo array JSON da una risposta LLM, tollerando backtick/testo extra."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("Nessun array JSON nella risposta")
    return json.loads(match.group(0))


# ====================================================================== #
# 1. SUGGEST TOPICS  (REALE)                                             #
# ====================================================================== #

def suggest_topics(state: AgentState) -> dict:
    """
    Interroga il KG per i gap di copertura e i post recenti, poi usa l'LLM
    per proporre idee di post concrete. Requisiti PDF: 'suggest topics',
    'avoid repetition', 'identify gaps in coverage'.
    """
    print("→ [suggest_topics] interrogo il KG: gap di copertura + post recenti")
    kg = KnowledgeGraphManager()

    gaps = kg.get_coverage_gaps(DOMAIN_TOPICS)
    recent_titles = [p.get("title") for p in kg.get_recent_posts(5)]

    # Se il blog ha già coperto tutto il dominio, riparti dall'intero universo.
    candidate_topics = gaps if gaps else DOMAIN_TOPICS

    prompt = (
        "Sei l'assistente editoriale di un blog su film e serie TV.\n"
        f"Topic del dominio NON ancora trattati (gap di copertura): {candidate_topics}\n"
        f"Post pubblicati di recente, da NON ripetere: {recent_titles}\n\n"
        "Proponi 3 idee di post concrete e interessanti che colmino i gap.\n"
        "Per ciascuna indica: topic, post_type (uno tra: review, how-to, news, events), "
        "reason (perché vale la pena scriverne ora).\n"
        "Rispondi SOLO con un array JSON, senza testo extra né backtick. Esempio:\n"
        '[{"topic": "...", "post_type": "review", "reason": "..."}]'
    )

    response = get_llm(temperature=0.5).invoke(prompt)

    try:
        suggestions = _extract_json_array(response.content)
    except (ValueError, json.JSONDecodeError):
        # Fallback robusto: usa i primi gap come suggerimenti grezzi
        suggestions = [
            {"topic": t, "post_type": "news", "reason": "gap di copertura nel KG"}
            for t in candidate_topics[:3]
        ]

    print(f"   trovati {len(gaps)} gap → {len(suggestions)} topic proposti")
    return {
        "suggested_topics": suggestions,
        "messages": [response],
        "reasoning_trace": [{
            "thought": "Quali topic del dominio non ho ancora trattato di recente?",
            "action": "kg.get_coverage_gaps + kg.get_recent_posts + llm_ideation",
            "observation": f"{len(suggestions)} topic proposti dai gap",
        }],
    }


# ====================================================================== #
# 2. PLANNER  (SEMI-REALE)                                               #
# ====================================================================== #

def planner(state: AgentState) -> dict:
    """
    Trasforma i topic suggeriti in un piano editoriale ordinato.
    Per ora l'ordine segue le proposte; l'ordinamento/giustificazione via LLM
    (requisito Planning completo) arriverà nella Fase 8.
    """
    print("→ [planner] costruisco il piano editoriale dai suggerimenti")
    suggestions = state.get("suggested_topics", [])

    plan: list[PlannedPost] = [
        {
            "topic": s.get("topic", ""),
            "post_type": s.get("post_type", "news"),
            "justification": s.get("reason", ""),
            "priority": i + 1,
        }
        for i, s in enumerate(suggestions)
    ]

    if not plan:  # fallback se suggest_topics non ha prodotto nulla
        plan = [{
            "topic": "Topic di esempio",
            "post_type": "review",
            "justification": "fallback: nessun suggerimento disponibile",
            "priority": 1,
        }]

    return {
        "editorial_plan": plan,
        "current_post_index": 0,
        "current_topic": plan[0]["topic"],
        "post_type": plan[0]["post_type"],
        "reasoning_trace": [{
            "thought": "Ordino i candidati in una sequenza editoriale",
            "action": "build_plan",
            "observation": f"{len(plan)} post pianificati; parto da '{plan[0]['topic']}'",
        }],
    }


# ====================================================================== #
# 3-7. NODI ANCORA STUB                                                  #
# ====================================================================== #

def research(state: AgentState) -> dict:
    """STUB — Fase 4/6: K-RAG (Search + RAG espansi col KG) in stile ReAct."""
    print(f"→ [research] (stub) K-RAG sul topic: {state['current_topic']}")
    return {
        "kg_context": "stub: contesto dal Knowledge Graph",
        "retrieved_docs": [],
        "tool_outputs": [{"tool": "search", "output": "stub", "source": "stub-url"}],
        "reasoning_trace": [{
            "thought": "Espando la query col KG, poi recupero documenti",
            "action": "search + rag_retrieve",
            "observation": "stub: documenti recuperati",
        }],
    }


def verify_and_select(state: AgentState) -> dict:
    """STUB — Fase 6: verifica accuratezza + selezione per qualità/interessantezza."""
    print("→ [verify_and_select] (stub) verifico i fatti e filtro le fonti")
    return {
        "reasoning_trace": [{
            "thought": "Date/cast coerenti? Fonti autorevoli?",
            "action": "fact_check + quality_filter",
            "observation": "stub: fonti validate",
        }],
    }


def draft(state: AgentState) -> dict:
    """STUB — Fase 6: bozza ancorata ai documenti, con citazioni e key claims."""
    print("→ [draft] (stub) genero la bozza del post")
    return {
        "current_draft": f"[BOZZA STUB] Post '{state['post_type']}' su: {state['current_topic']}",
        "citations": [{"title": "stub", "url": "stub-url", "source": "stub"}],
        "key_claims": ["stub: affermazione chiave estratta dal testo"],
        "reasoning_trace": [{
            "thought": "Scrivo in coerenza col KG e cito le fonti",
            "action": "generate_draft",
            "observation": "stub: bozza pronta",
        }],
    }


def human_review(state: AgentState) -> dict:
    """STUB — Fase 7: qui ci sarà l'interrupt reale (approva/modifica/rigetta)."""
    print("→ [human_review] (stub) auto-approvo")
    return {
        "user_status": "approved",
        "approved": True,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def update_kg(state: AgentState) -> dict:
    """STUB — Fase 6/7: scriverà nel KG (add_approved_post) SOLO dopo approvazione."""
    print("→ [update_kg] (stub) aggiorno il KG")
    return {
        "reasoning_trace": [{
            "thought": "Post approvato: lo registro nel KG con le sue relazioni",
            "action": "kg.add_approved_post",
            "observation": "stub: KG aggiornato",
        }],
    }


# ====================================================================== #
# ROUTING CONDIZIONALE (dopo la revisione umana)                         #
# ====================================================================== #

def route_after_review(state: AgentState) -> str:
    """approvato -> update_kg ; rigettato -> draft ; troppi tentativi -> end."""
    if state.get("approved"):
        return "update_kg"
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        print("   (raggiunto MAX_ITERATIONS: mi fermo)")
        return "end"
    return "draft"
