"""
Interestingness scorer (CUSTOM 2 - requisito PDF: 'select based on quality
and interestingness').

Un LLM con output strutturato assegna a una risorsa testuale un punteggio
0-10 e una breve motivazione, considerando novita', autorevolezza, rilevanza
e originalita' rispetto al topic.
"""
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from config.settings import get_llm


class InterestScore(BaseModel):
    """Punteggio di interessantezza/qualita' di una risorsa per il blog."""
    score: float = Field(description="Punteggio da 0 (scarso) a 10 (eccellente)")
    reason: str = Field(description="Motivazione sintetica, max una frase")


SCORE_PROMPT = (
    "Valuta quanto questa risorsa e' interessante e di qualita' per un post "
    "di blog su film e serie TV, relativamente al topic '{topic}'.\n\n"
    "Risorsa:\n{content}\n\n"
    "Criteri: novita' informativa, autorevolezza della fonte, rilevanza al "
    "topic, originalita' del taglio. Punteggio da 0 a 10."
)


@tool
def score_interestingness(topic: str, content: str) -> str:
    """
    Assegna un punteggio di interessantezza/qualita' (0-10) a una risorsa
    testuale rispetto a un topic di blog, con una breve motivazione.
    Usalo per scegliere quali fonti tenere e quali scartare.
    """
    scorer = get_llm(temperature=0).with_structured_output(InterestScore)
    prompt = SCORE_PROMPT.format(topic=topic, content=content[:2000])
    out = scorer.invoke([{"role": "user", "content": prompt}])
    return f"score={out.score:.1f}/10  motivo: {out.reason}"
