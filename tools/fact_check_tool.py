"""
Fact-check tool su TMDb (CUSTOM 1 - requisito PDF: 'verify accuracy').

Per il dominio film/serie TV e' fondamentale validare date di uscita, titoli
ufficiali e cast prima di pubblicare. Le API di TMDb sono gratuite e affidabili.
"""
import os
import requests
from langchain_core.tools import tool

TMDB_BASE = "https://api.themoviedb.org/3"


@tool
def tmdb_fact_check(title: str, kind: str = "movie") -> str:
    """
    Verifica i metadati di un film o di una serie TV su TMDb.

    Args:
        title: titolo del film o della serie da verificare
        kind: 'movie' per un film, 'tv' per una serie

    Restituisce titolo ufficiale, data di uscita, voto medio, cast principale
    e trama. Usalo per verificare l'accuratezza prima di pubblicare un post.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return "Errore: TMDB_API_KEY non configurata in .env"
    if kind not in ("movie", "tv"):
        return "Errore: 'kind' deve essere 'movie' o 'tv'."

    try:
        r = requests.get(
            f"{TMDB_BASE}/search/{kind}",
            params={"api_key": api_key, "query": title, "language": "it-IT"},
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        return f"Errore TMDb (search): {e}"

    if not results:
        return f"Nessun risultato TMDb per '{title}' ({kind})."

    hit = results[0]
    item_id = hit["id"]
    name_key = "title" if kind == "movie" else "name"
    date_key = "release_date" if kind == "movie" else "first_air_date"

    cast = []
    try:
        r2 = requests.get(
            f"{TMDB_BASE}/{kind}/{item_id}/credits",
            params={"api_key": api_key, "language": "it-IT"},
            timeout=10,
        )
        if r2.ok:
            cast = [c["name"] for c in r2.json().get("cast", [])[:5]]
    except Exception:
        pass  # il fact-check funziona anche senza cast

    return (
        f"Titolo ufficiale: {hit.get(name_key)}\n"
        f"Data: {hit.get(date_key) or 'n/d'}\n"
        f"Voto medio: {hit.get('vote_average', 'n/d')} "
        f"({hit.get('vote_count', 0)} voti)\n"
        f"Cast principale: {', '.join(cast) if cast else 'n/d'}\n"
        f"Trama: {(hit.get('overview') or '')[:400]}"
    )
