"""
Logica di recupero K-RAG.

- krag_retrieve: espande la query con il Knowledge Graph (requisito K-RAG:
  'use the KG to expand or refine retrieval queries'), recupera dal vectorstore
  e, opzionalmente, filtra i documenti non rilevanti in stile self-RAG.
- format_citations: estrae le citazioni dai metadati dei documenti recuperati.
"""
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from config.settings import get_llm
from kg.kg_manager import KnowledgeGraphManager
from rag.vectorstore import get_retriever


class GradeDocuments(BaseModel):
    """Valutazione binaria di rilevanza di un documento (self-RAG)."""
    binary_score: str = Field(description="'yes' se rilevante, 'no' altrimenti")


GRADE_PROMPT = (
    "Sei un valutatore della rilevanza di un documento rispetto a un argomento.\n\n"
    "Documento:\n{context}\n\n"
    "Argomento: {topic}\n\n"
    "Se il documento contiene informazioni pertinenti all'argomento, rispondi 'yes', "
    "altrimenti 'no'."
)


def krag_retrieve(topic: str, k: int = 4, grade: bool = True) -> list[Document]:
    """
    1) Espande la query usando il KG (topic correlati + claim passati).
    2) Recupera i documenti dal vectorstore.
    3) (opzionale) Scarta i documenti non rilevanti con un grader LLM.

    Nota: il grading fa una chiamata LLM per documento. Per risparmiare credito
    durante i test puoi passare grade=False.
    """
    kg = KnowledgeGraphManager()
    expanded_query = kg.expand_query_for_rag(topic)
    print(f"   [K-RAG] query espansa: {expanded_query}")

    docs = get_retriever(k=k).invoke(expanded_query)

    if not grade or not docs:
        return docs

    grader = get_llm(temperature=0).with_structured_output(GradeDocuments)
    relevant: list[Document] = []
    for doc in docs:
        prompt = GRADE_PROMPT.format(context=doc.page_content[:1500], topic=topic)
        verdict = grader.invoke([{"role": "user", "content": prompt}])
        if verdict.binary_score.strip().lower() == "yes":
            relevant.append(doc)

    # Se il grading scarta tutto, restituisci comunque i documenti grezzi (fallback)
    return relevant or docs


def format_citations(docs: list[Document]) -> list[dict]:
    """Estrae citazioni uniche dai metadati dei documenti recuperati."""
    seen, citations = set(), []
    for doc in docs:
        source = doc.metadata.get("source", "sconosciuta")
        if source not in seen:
            seen.add(source)
            citations.append({
                "title": doc.metadata.get("title", source),
                "url": doc.metadata.get("url", ""),
                "source": source,
            })
    return citations
