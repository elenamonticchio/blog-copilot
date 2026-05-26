"""
Stato condiviso del grafo LangGraph — requisito MCP / State Management.

Mappa diretta sui campi richiesti dal PDF:
    user input        -> user_input
    reasoning trace   -> reasoning_trace
    tool outputs      -> tool_outputs
    KG summaries      -> kg_context
    planning info     -> editorial_plan, current_post_index, ...
"""
from typing import Annotated, Sequence, TypedDict
import operator

from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages

# Limite di sicurezza per i cicli di rigenerazione (human-in-the-loop)
MAX_ITERATIONS = 3


class PlannedPost(TypedDict):
    """Un singolo post nel piano editoriale, con giustificazione (requisito PDF)."""
    topic: str
    post_type: str        # "review" | "how-to" | "news" | "events"
    justification: str    # Perché questo topic ora (obbligatorio per il prof)
    priority: int         # Ordine nella sequenza


class AgentState(TypedDict):
    # ------------------------------------------------------------------ #
    # CONVERSAZIONE                                                        #
    # ------------------------------------------------------------------ #
    # Messaggi scambiati — add_messages evita sovrascritture
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Input testuale dell'utente (topic iniziale o feedback)
    user_input: str

    # ------------------------------------------------------------------ #
    # PIANIFICAZIONE (Planner node)                                        #
    # ------------------------------------------------------------------ #
    # Lista di post pianificati con giustificazione — NON solo stringhe
    editorial_plan: list[PlannedPost]

    # Indice del post su cui si lavora adesso nella sequenza
    current_post_index: int

    # Tipo del post corrente (derivato da editorial_plan[current_post_index])
    post_type: str   # "review" | "how-to" | "news" | "events"

    # Topic/titolo del post corrente (derivato da editorial_plan[current_post_index])
    current_topic: str

    # ------------------------------------------------------------------ #
    # RETRIEVAL E KNOWLEDGE (ReAct / K-RAG node)                          #
    # ------------------------------------------------------------------ #
    # Contesto strutturato dal Knowledge Graph (planning + drafting)
    kg_context: str

    # Documenti recuperati dal RAG — base per il grounding e le citazioni (K-RAG).
    # Lista normale (no reducer): il nodo la sovrascrive/azzera per ogni post.
    # Document porta con sé i metadati (url, fonte), utili a draft e KG update.
    retrieved_docs: list[Document]

    # Output grezzi dei tool (Search, RAG, custom tools)
    # Lista di dict: {"tool": nome, "output": testo, "source": url}
    tool_outputs: Annotated[list[dict], operator.add]

    # Trace ReAct: ogni elemento è {"thought": ..., "action": ..., "observation": ...}
    reasoning_trace: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------ #
    # GENERAZIONE BOZZA (Draft node)                                      #
    # ------------------------------------------------------------------ #
    # Testo completo della bozza generata
    current_draft: str

    # Citazioni estratte per il draft — il PDF richiede citazioni esplicite
    citations: list[dict]   # [{"title": ..., "url": ..., "source": ...}]

    # Claim chiave estratti dal contenuto — richiesti dal KG ("key claims extracted").
    # Estratti in fase di draft, riusati nella fase di update del Knowledge Graph.
    key_claims: list[str]

    # ------------------------------------------------------------------ #
    # HUMAN-IN-THE-LOOP (Human Review node)                               #
    # ------------------------------------------------------------------ #
    # Decisione utente: "approved" | "modified" | "rejected"
    user_status: str

    # Feedback testuale: testo modificato o commenti di revisione
    user_feedback: str

    # Bool pulito per gli edge condizionali LangGraph (derivato da user_status)
    approved: bool

    # Conta i cicli di rigenerazione — evita loop infiniti (cap = MAX_ITERATIONS)
    iteration_count: int