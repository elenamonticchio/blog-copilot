"""
Test manuale dei tool (Fase 5).

Esegui dalla root del progetto:
    python test_tools.py

Nota: alcuni tool richiedono chiavi (TAVILY_API_KEY, TMDB_API_KEY,
OPENAI_API_KEY, RAPIDAPI_KEY). Costo complessivo bassissimo.
"""
from tools import (
    web_search,
    rag_search,
    kg_get_topic_context,
    kg_get_recent_posts,
    kg_find_gaps,
    tmdb_fact_check,
    score_interestingness,
    tvmaze_show_info,
    find_local_events
)


def check(label: str, condition: bool) -> bool:
    print(f"   [{'OK  ' if condition else 'FAIL'}] {label}")
    return condition


def header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ------------------------------------------------------------------ #
header("TOOL 1 - web_search (Tavily)")
out = web_search.invoke({"query": "Dune Parte Due data uscita Italia"})
print(out[:4000], "...\n")
check("ritorna una stringa non vuota", isinstance(out, str) and len(out) > 50)
check("contiene almeno un URL", "http" in out or "Errore" in out)

# ------------------------------------------------------------------ #
header("TOOL 2 - rag_search (K-RAG sul corpus locale)")
out = rag_search.invoke({"topic": "Christopher Nolan"})
print(out[:300], "...\n")
check("recupera contenuto dal corpus", isinstance(out, str) and len(out) > 50)
check("indica una fonte del seed corpus", "fonte:" in out or "Nessun documento" in out)

# ------------------------------------------------------------------ #
header("TOOL 3 - kg_get_topic_context")
out = kg_get_topic_context.invoke({"topic": "Denis Villeneuve"})
print(out, "\n")
check("ritorna una stringa", isinstance(out, str) and len(out) > 0)

# ------------------------------------------------------------------ #
header("TOOL 4 - kg_get_recent_posts")
out = kg_get_recent_posts.invoke({"n": 3})
print(out, "\n")
check("ritorna una stringa", isinstance(out, str))

# ------------------------------------------------------------------ #
header("TOOL 5 - kg_find_gaps")
out = kg_find_gaps.invoke({})
print(out, "\n")
check("ritorna una stringa", isinstance(out, str) and len(out) > 0)

# ------------------------------------------------------------------ #
header("TOOL 6 - tmdb_fact_check (CUSTOM)")
out = tmdb_fact_check.invoke({"title": "Oppenheimer", "kind": "movie"})
print(out, "\n")
check("ritorna metadati o errore noto", isinstance(out, str) and len(out) > 30)
check("contiene una data o un cast o un errore", "Data:" in out or "Cast" in out or "Errore" in out)

# ------------------------------------------------------------------ #
header("TOOL 7 - score_interestingness (CUSTOM)")
out = score_interestingness.invoke({
    "topic": "Christopher Nolan",
    "content": "Christopher Nolan e' un regista britannico noto per Inception e Oppenheimer."
})
print(out, "\n")
check("ritorna un punteggio formattato", isinstance(out, str) and "score=" in out)

# ------------------------------------------------------------------ #
header("TOOL 8 - tvmaze_show_info (CUSTOM) - serie TV fact-check")
out = tvmaze_show_info.invoke({"title": "House of the Dragon"})
print(out[:5000], "...\n")
check("ritorna dati o errore noto", isinstance(out, str) and len(out) > 30)
check("contiene titolo o stato della serie", "Titolo:" in out or "Stato:" in out or "Errore" in out or "Nessuna" in out)

# ------------------------------------------------------------------ #

header("TOOL 9 - find_local_events (CUSTOM)")
out = find_local_events.invoke({"location": "Venezia", "kind": "festival cinema"})
print(out[:4000], "...\n")
check("ritorna una stringa non vuota", isinstance(out, str) and len(out) > 50)
check("contiene un URL o un messaggio di assenza eventi",
      "http" in out or "Nessun evento" in out)
