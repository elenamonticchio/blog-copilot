"""
Registro centrale dei tool del progetto.

Requisito PDF:
  - 3 categorie core: Search, RAG retrieval, Knowledge Graph
  - 2 tool custom progettati dal team (qui ne abbiamo 4)

ALL_TOOLS sara' passata a .bind_tools(...) nel nodo ReAct di Fase 6,
abilitando la selezione DINAMICA dei tool richiesta dal PDF.
"""
from tools.search_tool import web_search
from tools.rag_tool import rag_search
from tools.kg_tool import kg_get_topic_context, kg_get_recent_posts, kg_find_gaps
from tools.fact_check_tool import tmdb_fact_check
from tools.scorer_tool import score_interestingness
from tools.tvmaze_tool import tvmaze_show_info
from tools.events_tool import find_local_events

# Tutti i tool esposti al ReAct agent.
# Nota: l'update del KG NON e' esposto come tool: viene chiamato direttamente
# dal nodo update_kg DOPO l'approvazione umana (vincolo PDF).
ALL_TOOLS = [
    # --- CORE (3 categorie) ---
    web_search,                # search esterno (Tavily)
    rag_search,                # RAG sul corpus locale (K-RAG)
    kg_get_topic_context,      # KG: contesto su un topic
    kg_get_recent_posts,       # KG: ultimi post
    kg_find_gaps,              # KG: gap di copertura
    # --- CUSTOM (4) ---
    tmdb_fact_check,           # verifica metadati film/serie su TMDb
    score_interestingness,     # score di qualita'/interessantezza (LLM)
    tvmaze_show_info,          # calendario e dettagli serie TV
    find_local_events,         # eventi cinema/TV nell'area geografica
]

__all__ = [
    "ALL_TOOLS",
    "web_search",
    "rag_search",
    "kg_get_topic_context",
    "kg_get_recent_posts",
    "kg_find_gaps",
    "tmdb_fact_check",
    "score_interestingness",
    "tvmaze_show_info",
    "find_local_events",
]
