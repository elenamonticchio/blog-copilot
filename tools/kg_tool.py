"""
Knowledge Graph tool (CORE - requisito PDF).

Scelta di design: l'agente ReAct vede SOLO i tool di lettura del KG.
L'operazione di update (kg.add_approved_post) NON e' esposta come tool
selezionabile: viene chiamata direttamente dal nodo `update_kg` DOPO
l'approvazione umana, per rispettare il vincolo del PDF
'KG aggiornato solo dopo approvazione'.

Il requisito 'querying AND updating' del PDF resta soddisfatto:
  - querying  -> @tool qui sotto (per la selezione dinamica)
  - updating  -> kg.add_approved_post chiamato dal nodo gated
"""
from langchain_core.tools import tool

from kg.kg_manager import KnowledgeGraphManager
from config.domain import DOMAIN_TOPICS


@tool
def kg_get_topic_context(topic: str) -> str:
    """
    Restituisce il contesto del Knowledge Graph per un topic:
    post correlati gia' pubblicati e claim sostenuti in passato.
    Usalo PRIMA di scrivere per garantire coerenza editoriale.
    """
    return KnowledgeGraphManager().get_topic_context(topic)


@tool
def kg_get_recent_posts(n: int = 5) -> str:
    """
    Elenca gli ultimi N post pubblicati sul blog (titolo, tipo, data).
    Utile per evitare ripetizioni recenti.
    """
    posts = KnowledgeGraphManager().get_recent_posts(n)
    if not posts:
        return "Nessun post ancora pubblicato."
    return "\n".join(
        f"- {p.get('title')}  ({p.get('post_type', 'N/A')}, {p.get('date', '?')})"
        for p in posts
    )


@tool
def kg_find_gaps() -> str:
    """
    Identifica i topic del dominio del blog non ancora trattati
    (gap di copertura). Usalo per proporre nuovi argomenti.
    """
    gaps = KnowledgeGraphManager().get_coverage_gaps(DOMAIN_TOPICS)
    if not gaps:
        return "Nessun gap: tutti i topic del dominio sono stati trattati almeno una volta."
    return ", ".join(gaps)
