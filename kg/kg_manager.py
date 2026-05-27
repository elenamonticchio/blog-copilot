import json
import os
from datetime import datetime


class KnowledgeGraphManager:
    def __init__(self, file_path: str | None = None):
        # Se non passato, usa il percorso centralizzato in config (JSON, non .gpickle).
        if file_path is None:
            from config.settings import KG_PATH
            file_path = str(KG_PATH)
        self.file_path = file_path

        # Guard: crea la cartella solo se il path ne contiene una
        # (evita il crash con path tipo "kg.json" senza directory).
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.file_path):
            self.initialize_graph()

    # ------------------------------------------------------------------ #
    # PERSISTENZA                                                          #
    # ------------------------------------------------------------------ #

    def initialize_graph(self):
        """Struttura iniziale del grafo (requisito PDF: posts, topics, sources, claims, relationships)."""
        default_graph = {
            "posts": [],
            "topics": [],
            "claims": [],
            "sources": [],
            "relationships": []
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(default_graph, f, indent=4, ensure_ascii=False)

    def load_graph(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_graph(self, graph):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # REQUISITO 1 — FASE PLANNING                                          #
    # ------------------------------------------------------------------ #

    def get_editorial_context(self):
        """
        Contesto per il Planner: topic EFFETTIVAMENTE coperti + post passati.
        'Coperti' = topic con una relazione TRATTA (post reali), non i soli
        topic 'correlati' aggiunti per il K-RAG.
        """
        graph = self.load_graph()
        covered = sorted({
            r.get("target", "")
            for r in graph.get("relationships", [])
            if r.get("type") == "TRATTA"
        })
        return {
            "covered_topics": covered,
            "past_posts": [
                {"title": p.get("title"), "type": p.get("post_type"), "date": p.get("date")}
                for p in graph.get("posts", [])
            ]
        }

    def get_recent_posts(self, n: int = 5) -> list[dict]:
        """
        Restituisce gli ultimi N post — per evitare ripetizioni recenti.
        Il Planner li usa per non scrivere sullo stesso argomento due volte di fila.
        """
        graph = self.load_graph()
        posts = graph.get("posts", [])
        sorted_posts = sorted(posts, key=lambda p: p.get("date", ""), reverse=True)
        return sorted_posts[:n]

    def get_coverage_gaps(self, domain_topics: list[str]) -> list[str]:
        """
        Identifica topic del dominio non ancora TRATTATI da un post = gap reali.
        Requisito PDF: 'identify gaps in coverage'.

        Un topic solo 'correlato' (CORRELATO_A) NON conta come coperto: lo è solo
        se esiste una relazione TRATTA che lo collega a un post pubblicato.
        """
        graph = self.load_graph()
        covered = {
            r.get("target", "").lower()
            for r in graph.get("relationships", [])
            if r.get("type") == "TRATTA"
        }
        return [t for t in domain_topics if t.lower() not in covered]

    # ------------------------------------------------------------------ #
    # REQUISITO 2 — FASE DRAFTING                                          #
    # ------------------------------------------------------------------ #

    def get_topic_context(self, current_topic: str) -> str:
        """
        Contesto per il Draft node: post correlati + claim già sostenuti.
        Garantisce coerenza con contenuti precedenti.
        """
        graph = self.load_graph()
        context_parts = []

        related_posts = [
            p for p in graph.get("posts", [])
            if current_topic.lower() in p.get("title", "").lower()
            or current_topic.lower() in p.get("topic", "").lower()
        ]

        if related_posts:
            context_parts.append("Post correlati già pubblicati:")
            for p in related_posts:
                context_parts.append(f"  - '{p.get('title')}' ({p.get('post_type', 'N/A')})")

            context_parts.append("\nClaim già sostenuti (mantieni coerenza):")
            valid_titles = {p.get("title") for p in related_posts}
            for rel in graph.get("relationships", []):
                if rel.get("type") == "CONTIENE_CLAIM" and rel.get("source") in valid_titles:
                    context_parts.append(f"  - {rel.get('target')}")
        else:
            context_parts.append(
                f"'{current_topic}' è un topic nuovo per il blog. "
                "Gap di copertura identificato: nessun vincolo di coerenza."
            )

        return "\n".join(context_parts)

    # ------------------------------------------------------------------ #
    # K-RAG — ESPANSIONE QUERY                                            #
    # ------------------------------------------------------------------ #

    def expand_query_for_rag(self, topic: str) -> str:
        """
        REQUISITO K-RAG: usa il KG per espandere/raffinare la query di retrieval.
        Va chiamato PRIMA del RAG retrieval.

        Esempio: topic='Christopher Nolan' -> aggiunge i topic correlati
        ('Oppenheimer', 'Tenet'...) e qualche claim passato come contesto.
        Restituisce una stringa naturale (no troncamenti a metà parola),
        adatta sia alla ricerca per keyword sia al retrieval semantico.
        """
        graph = self.load_graph()

        related_terms = set()
        for rel in graph.get("relationships", []):
            if rel.get("type") == "CORRELATO_A":
                if topic.lower() in rel.get("source", "").lower():
                    related_terms.add(rel.get("target", ""))
                elif topic.lower() in rel.get("target", "").lower():
                    related_terms.add(rel.get("source", ""))

        past_claims = []
        for rel in graph.get("relationships", []):
            if rel.get("type") == "CONTIENE_CLAIM":
                source_post = next(
                    (p for p in graph.get("posts", []) if p.get("title") == rel.get("source")),
                    None
                )
                if source_post and topic.lower() in source_post.get("topic", "").lower():
                    past_claims.append(rel.get("target", ""))

        parts = [topic]
        parts.extend(list(related_terms)[:3])
        parts.extend(past_claims[:2])           # claim interi, non troncati
        parts = [p for p in parts if p]         # scarta eventuali stringhe vuote
        return ", ".join(parts)

    def get_related_topics(self, topic: str) -> list[str]:
        """Restituisce topic correlati per suggerire connessioni nel post."""
        graph = self.load_graph()
        related = []
        for rel in graph.get("relationships", []):
            if rel.get("type") == "CORRELATO_A":
                if topic.lower() in rel.get("source", "").lower():
                    related.append(rel.get("target"))
                elif topic.lower() in rel.get("target", "").lower():
                    related.append(rel.get("source"))
        return related

    # ------------------------------------------------------------------ #
    # REQUISITO 3 — AGGIORNAMENTO INCREMENTALE                            #
    # ------------------------------------------------------------------ #

    def add_approved_post(
        self,
        title: str,
        topic: str,
        post_type: str,
        claims: list[str],
        sources: list[str],
        related_topics: list[str] | None = None
    ):
        """
        Aggiorna il KG dopo approvazione utente (mai prima).
        Aggiunge nodo Post, Topic, Claim, Sources e le relazioni, incluse le
        CORRELATO_A tra topic (usate da expand_query_for_rag).
        """
        graph = self.load_graph()

        # 1. Nodo Post (con data e tipo)
        new_post = {
            "title": title,
            "topic": topic,
            "post_type": post_type,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        if not any(p.get("title") == title for p in graph["posts"]):
            graph["posts"].append(new_post)

        # 2. Nodo Topic (schema minimale: solo il nome)
        if not any(t.get("name") == topic for t in graph["topics"]):
            graph["topics"].append({"name": topic})

        # 3. Relazione Post -> TRATTA -> Topic (con deduplicazione)
        self._add_relationship(graph, title, "TRATTA", topic)

        # 4. Claim + relazioni
        for claim in claims:
            if claim not in graph["claims"]:
                graph["claims"].append(claim)
            self._add_relationship(graph, title, "CONTIENE_CLAIM", claim)

        # 5. Fonti + relazioni
        for source in sources:
            if source not in graph["sources"]:
                graph["sources"].append(source)
            self._add_relationship(graph, title, "USA_FONTE", source)

        # 6. Relazioni CORRELATO_A tra topic (per il K-RAG)
        if related_topics:
            for rel_topic in related_topics:
                if not any(t.get("name") == rel_topic for t in graph["topics"]):
                    graph["topics"].append({"name": rel_topic})
                self._add_relationship(graph, topic, "CORRELATO_A", rel_topic)

        self.save_graph(graph)
        print(f"[KG] Aggiornato: '{title}' ({post_type}) — "
              f"{len(claims)} claim, {len(sources)} fonti")

    # ------------------------------------------------------------------ #
    # UTILITY PRIVATA                                                      #
    # ------------------------------------------------------------------ #

    def _add_relationship(self, graph: dict, source: str, rel_type: str, target: str):
        """Aggiunge una relazione solo se non esiste già (deduplicazione)."""
        duplicate = any(
            r.get("source") == source
            and r.get("type") == rel_type
            and r.get("target") == target
            for r in graph["relationships"]
        )
        if not duplicate:
            graph["relationships"].append({
                "source": source,
                "type": rel_type,
                "target": target
            })
