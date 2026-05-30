"""
Fact-check tool su TMDb (CUSTOM 1 - requisito PDF: 'verify accuracy').

Per il dominio film/serie TV è fondamentale validare:
- titoli ufficiali
- date di uscita
- cast
prima di pubblicare contenuti.

TMDb è una fonte affidabile per metadata cinematografici.
"""

import os
import requests
from langchain_core.tools import tool

TMDB_BASE = "https://api.themoviedb.org/3"


def _pick_best_match(results: list[dict], title: str) -> dict:
    """
    Prova a trovare la miglior corrispondenza per il titolo.
    Fallback: primo risultato.
    """
    if not results:
        return {}

    title_lower = title.strip().lower()

    for r in results:
        name = (r.get("title") or r.get("name") or "").strip().lower()
        if name == title_lower:
            return r

    return results[0]


def _fetch_overview_en(api_key: str, kind: str, item_id: int) -> str:
    """
    Fallback in inglese se l'overview italiana del hit della search e' vuota.
    (La search e' gia' fatta in it-IT, quindi l'overview IT arriva dal hit.)
    """
    try:
        r = requests.get(
            f"{TMDB_BASE}/{kind}/{item_id}",
            params={"api_key": api_key, "language": "en-US"},
            timeout=10,
        )
        if r.ok:
            return r.json().get("overview") or ""
    except Exception:
        pass
    return ""


@tool
def tmdb_fact_check(title: str, kind: str = "movie") -> str:
    """
    Verifica i metadati di un film o serie TV su TMDb.

    Args:
        title: titolo da verificare
        kind: 'movie' o 'tv'

    Restituisce:
    - titolo ufficiale
    - data di uscita
    - voto medio
    - cast principale
    - trama
    """
    api_key = os.getenv("TMDB_API_KEY")

    if not api_key:
        return "Errore: TMDB_API_KEY non configurata in .env"

    if kind not in ("movie", "tv"):
        return "Errore: 'kind' deve essere 'movie' o 'tv'."

    # ---------------- SEARCH (in it-IT: restituisce gia' l'overview IT) -- #
    try:
        r = requests.get(
            f"{TMDB_BASE}/search/{kind}",
            params={
                "api_key": api_key,
                "query": title,
                "language": "it-IT",
            },
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        return f"Errore TMDb (search): {e}"

    if not results:
        return f"Nessun risultato TMDb per '{title}' ({kind})."

    hit = _pick_best_match(results, title)

    item_id = hit.get("id")
    if not item_id:
        return f"Errore: ID mancante per '{title}'."

    name_key = "title" if kind == "movie" else "name"
    date_key = "release_date" if kind == "movie" else "first_air_date"

    # ---------------- CAST ---------------- #
    cast = []
    try:
        r2 = requests.get(
            f"{TMDB_BASE}/{kind}/{item_id}/credits",
            params={"api_key": api_key},
            timeout=10,
        )
        if r2.ok:
            cast = [
                c.get("name")
                for c in r2.json().get("cast", [])
                if c.get("name")
            ][:5]
    except Exception:
        cast = []

    # ---------------- OVERVIEW (prima dal hit IT, poi fallback EN) ----- #
    # Risparmia una chiamata HTTP: la search in it-IT include gia'
    # l'overview italiana. Chiamiamo TMDb di nuovo solo se e' vuota.
    overview = hit.get("overview") or ""
    if not overview:
        overview = _fetch_overview_en(api_key, kind, item_id)

    # ---------------- OUTPUT ---------------- #
    official_title = hit.get(name_key) or "n/d"
    date = hit.get(date_key) or "n/d"
    vote_avg = hit.get("vote_average")
    vote_count = hit.get("vote_count", 0)

    vote_str = (
        f"{vote_avg} ({vote_count} voti)"
        if vote_avg is not None
        else "n/d"
    )

    return (
        f"Titolo ufficiale: {official_title}\n"
        f"Data: {date}\n"
        f"Voto medio: {vote_str}\n"
        f"Cast principale: {', '.join(cast) if cast else 'n/d'}\n"
        f"Trama: {overview[:400] if overview else 'n/d'}"
    )
