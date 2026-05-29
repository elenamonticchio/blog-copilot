"""
Registro centrale dei tool del progetto.

Requisito PDF: 3 tool core + almeno 2 tool custom.
Stato attuale: 3 core + 4 custom (siamo abbondanti sui custom).

ALL_TOOLS viene passata a .bind_tools(...) nel nodo ReAct (Fase 6)
per abilitare la selezione DINAMICA dei tool.
"""
from tools.search_tool import web_search
from tools.rag_tool import rag_search
from tools.kg_tool import kg_get_topic_context, kg_get_recent_posts, kg_find_gaps
from tools.fact_check_tool import tmdb_fact_check
from tools.scorer_tool import score_interestingness
from tools.tvmaze_tool import tvmaze_show_info
from tools.utelly_tool import utelly_where_to_watch

# L'agente vede SOLO i tool di lettura del KG;
# la scrittura (kg.add_approved_post) resta gated nel nodo update_kg.
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
    utelly_where_to_watch,     # dove vedere un film/serie
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
    "utelly_where_to_watch",
]
