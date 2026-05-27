import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")   # carica le chiavi in os.environ

# --- LangSmith: le LANGSMITH_* vengono lette in automatico
#     da langchain/langgraph, qui garantiamo solo i default ---
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "blog-copilot-film-tv")

# --- parametri del modello ---
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# --- percorsi dei dati ---
DATA_DIR = ROOT / "data"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
KG_PATH = DATA_DIR / "knowledge_graph.json"   # allineato al kg_manager (JSON)
DATA_DIR.mkdir(exist_ok=True)


def get_llm(temperature: float = 0.3):
    """Restituisce il modello di chat configurato."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=LLM_MODEL, temperature=temperature)


def get_embeddings():
    """Restituisce il modello di embedding configurato."""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model=EMBED_MODEL)
