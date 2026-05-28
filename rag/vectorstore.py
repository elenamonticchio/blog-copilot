"""
Costruzione e caricamento del vectorstore (RAG).

Segue lo schema del tutorial LangGraph (loader -> splitter -> embeddings ->
vector store), ma con due adattamenti:
  - sorgente LOCALE (seed corpus in data/seed_corpus/*.md) invece del web
  - Chroma PERSISTENTE invece di InMemoryVectorStore: gli embedding si
    calcolano una sola volta e restano salvati su disco.

Uso:
  python -m rag.vectorstore      # costruisce l'indice (una tantum)
"""
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma

from config.settings import VECTORSTORE_DIR, get_embeddings

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed_corpus"
COLLECTION = "film_tv_blog"


def _load_seed_documents() -> list[Document]:
    """Carica ogni file .md del seed corpus come un Document con metadati."""
    documents = []
    for path in sorted(SEED_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(
            page_content=text,
            metadata={"source": path.name, "title": path.stem.replace("_", " ")},
        ))
    return documents


def build_index():
    """Carica il seed, fa chunking, calcola gli embedding e li salva su Chroma."""
    documents = _load_seed_documents()
    if not documents:
        raise RuntimeError(
            f"Nessun documento in {SEED_DIR}. Aggiungi file .md al seed corpus."
        )

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(documents)

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=COLLECTION,
        persist_directory=str(VECTORSTORE_DIR),
    )
    print(f"[RAG] Indicizzati {len(chunks)} chunk da {len(documents)} documenti "
          f"in {VECTORSTORE_DIR}")


def get_retriever(k: int = 4):
    """Carica il vectorstore persistito e restituisce un retriever."""
    vectorstore = Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(VECTORSTORE_DIR),
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    build_index()
