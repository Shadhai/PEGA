# ============================================================
# src/rag/retriever.py
# CINT-70 Enhanced RAG Retriever
#
# Searches:
#   1. NASA structured datasets
#   2. NASA PDF chunks
#   3. Past execution experiences
#   4. Known failure patterns
# ============================================================

import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer


class Retriever:
    def __init__(self):
        print("  Loading RAG engine...")

        self.model = SentenceTransformer(
            "./models/minilm"
        )

        self.documents: List[Dict[str, Any]] = []
        self.embeddings = None

        # Load NASA knowledge, including extracted PDF chunks.
        self._load_documents()

        # Lazy-load experience memory so the RAG engine can still
        # initialize even when experience storage is unavailable.
        self._memory = None

        print(
            f"  RAG ready! Loaded {len(self.documents)} documents."
        )

    # ============================================================
    # EXPERIENCE MEMORY
    # ============================================================

    @property
    def memory(self):
        if self._memory is None:
            from src.memory.experience import ExperienceMemory

            self._memory = ExperienceMemory()

        return self._memory

    # ============================================================
    # DOCUMENT LOADING
    # ============================================================

    def _load_documents(self):
        """
        Load NASA knowledge from structured JSON datasets and
        extracted NASA PDF chunks.

        Sources:
            data/raw/tool_specifications.json
            data/raw/thermal_constraints.json
            data/raw/failure_reports.json
            data/extracted/pdf_chunks.json
        """

        docs: List[Dict[str, Any]] = []

        # --------------------------------------------------------
        # Tool specifications
        # --------------------------------------------------------

        try:
            with open(
                "data/raw/tool_specifications.json",
                "r",
                encoding="utf-8",
            ) as f:
                tool_data = json.load(f)

            for tool in tool_data:
                docs.append(
                    {
                        "text": (
                            f"Tool: {tool['tool_name']}. "
                            f"Weight: {tool['weight_kg']}kg. "
                            f"Max force: "
                            f"{tool['max_contact_force_n']}N. "
                            f"Holster: {tool['holster_id']}, "
                            f"Backup: "
                            f"{tool['backup_holster']}"
                        ),
                        "source": "tool_specifications",
                        "type": "nasa_doc",
                    }
                )

        except FileNotFoundError:
            print(
                "  RAG note: tool_specifications.json "
                "not found"
            )
        except Exception as e:
            print(
                f"  RAG tool specification load error: {e}"
            )

        # --------------------------------------------------------
        # Thermal constraints
        # --------------------------------------------------------

        try:
            with open(
                "data/raw/thermal_constraints.json",
                "r",
                encoding="utf-8",
            ) as f:
                thermal_data = json.load(f)

            for mat in thermal_data:
                docs.append(
                    {
                        "text": (
                            f"Material: {mat['material']}. "
                            f"Range: "
                            f"{mat['min_temp_c']}C to "
                            f"{mat['max_temp_c']}C."
                        ),
                        "source": "thermal_constraints",
                        "type": "nasa_doc",
                    }
                )

        except FileNotFoundError:
            print(
                "  RAG note: thermal_constraints.json "
                "not found"
            )
        except Exception as e:
            print(
                f"  RAG thermal constraint load error: {e}"
            )

        # --------------------------------------------------------
        # Failure reports
        # --------------------------------------------------------

        try:
            with open(
                "data/raw/failure_reports.json",
                "r",
                encoding="utf-8",
            ) as f:
                failure_data = json.load(f)

            for fail in failure_data:
                recovery_steps = fail.get(
                    "recovery_steps",
                    []
                )

                docs.append(
                    {
                        "text": (
                            f"Failure: {fail['title']}. "
                            f"Recovery: "
                            f"{' '.join(recovery_steps[:2])}"
                        ),
                        "source": "failure_reports",
                        "type": "nasa_doc",
                    }
                )

        except FileNotFoundError:
            print(
                "  RAG note: failure_reports.json "
                "not found"
            )
        except Exception as e:
            print(
                f"  RAG failure report load error: {e}"
            )

        # --------------------------------------------------------
        # NASA PDF chunks
        #
        # These are produced by the PDF extraction pipeline:
        #
        # data/extracted/pdf_chunks.json
        #
        # Expected format:
        #
        # [
        #     {
        #         "text": "...",
        #         "source": "some_nasa_document.pdf"
        #     },
        #     ...
        # ]
        # --------------------------------------------------------

        pdf_chunks_file = Path(
            "data/extracted/pdf_chunks.json"
        )

        if pdf_chunks_file.exists():

            try:
                with open(
                    pdf_chunks_file,
                    "r",
                    encoding="utf-8",
                ) as f:
                    pdf_chunks = json.load(f)

                pdf_count = 0

                # Support the expected list format.
                if isinstance(pdf_chunks, list):

                    for chunk in pdf_chunks:

                        if not isinstance(chunk, dict):
                            continue

                        text = chunk.get("text")
                        source = chunk.get(
                            "source",
                            "nasa_pdf"
                        )

                        if not text:
                            continue

                        docs.append(
                            {
                                "text": str(text),
                                "source": str(source),
                                "type": "nasa_pdf",
                            }
                        )

                        pdf_count += 1

                # Also tolerate:
                # {"chunks": [...]}
                elif isinstance(pdf_chunks, dict):

                    chunks = pdf_chunks.get(
                        "chunks",
                        []
                    )

                    for chunk in chunks:

                        if not isinstance(chunk, dict):
                            continue

                        text = chunk.get("text")
                        source = chunk.get(
                            "source",
                            "nasa_pdf"
                        )

                        if not text:
                            continue

                        docs.append(
                            {
                                "text": str(text),
                                "source": str(source),
                                "type": "nasa_pdf",
                            }
                        )

                        pdf_count += 1

                print(
                    f"  Loaded {pdf_count} NASA PDF chunks"
                )

            except json.JSONDecodeError as e:
                print(
                    f"  PDF chunk JSON error: {e}"
                )

            except Exception as e:
                print(
                    f"  PDF chunk load error: {e}"
                )

        else:
            print(
                "  RAG note: pdf_chunks.json not found; "
                "continuing without PDF knowledge"
            )

        # --------------------------------------------------------
        # Build document store
        # --------------------------------------------------------

        self.documents = docs

        # --------------------------------------------------------
        # Build embeddings for ALL NASA documents.
        #
        # This automatically includes:
        #   - structured NASA JSON
        #   - NASA PDF chunks
        # --------------------------------------------------------

        if docs:

            texts = [
                d["text"]
                for d in docs
            ]

            self.embeddings = self.model.encode(
                texts,
                convert_to_numpy=True
            )

            # Normalize embeddings so dot product behaves like
            # cosine similarity.
            norms = np.linalg.norm(
                self.embeddings,
                axis=1,
                keepdims=True
            )

            norms[norms == 0] = 1.0

            self.embeddings = (
                self.embeddings / norms
            )

        else:
            self.embeddings = np.empty(
                (0, 0),
                dtype=np.float32
            )

        print(
            f"  NASA knowledge indexed: "
            f"{len(self.documents)} documents"
        )

    # ============================================================
    # SEARCH
    # ============================================================

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search NASA documents/PDF chunks and past experiences.

        Returns a combined ranking of:
            - NASA structured knowledge
            - NASA PDF knowledge
            - past successful/failed experiences
        """

        results: List[Dict[str, Any]] = []

        # --------------------------------------------------------
        # Search NASA documents + PDF chunks
        # --------------------------------------------------------

        if (
            self.embeddings is not None
            and len(self.embeddings) > 0
        ):

            query_emb = self.model.encode(
                [query],
                convert_to_numpy=True
            )

            # Normalize query embedding to match document vectors.
            query_norm = np.linalg.norm(
                query_emb,
                axis=1,
                keepdims=True
            )

            query_norm[query_norm == 0] = 1.0

            query_emb = (
                query_emb / query_norm
            )

            similarities = np.dot(
                self.embeddings,
                query_emb.T
            ).flatten()

            count = min(
                top_k,
                len(similarities)
            )

            top_indices = np.argsort(
                similarities
            )[-count:][::-1]

            for idx in top_indices:

                score = float(
                    similarities[idx]
                )

                if score > 0.1:

                    document = self.documents[idx]

                    results.append(
                        {
                            "document": document,
                            "score": score,
                            "source": "nasa_knowledge",
                        }
                    )

        # --------------------------------------------------------
        # Search past experiences
        # --------------------------------------------------------

        try:
            experiences = (
                self.memory.get_similar_experiences(
                    query,
                    top_k=3
                )
            )

            for exp in experiences:

                exp_text = (
                    "PAST EXPERIENCE: "
                    f"Task: "
                    f"{exp.get('command', '')[:80]}... "
                    f"Outcome: "
                    f"{exp.get('outcome', 'UNKNOWN')}. "
                    f"Trust: "
                    f"{float(exp.get('trust_score', 0.0)):.1%}. "
                )

                if exp.get("safe_coordinates"):
                    exp_text += (
                        "Safe coords: "
                        f"{exp['safe_coordinates']}. "
                    )

                if exp.get("recovery_count", 0) > 0:
                    exp_text += (
                        "Required "
                        f"{exp['recovery_count']} "
                        "recovery attempts."
                    )

                results.append(
                    {
                        "document": {
                            "text": exp_text,
                            "source": "experience",
                            "type": "past_experience",
                        },
                        "score": float(
                            exp.get(
                                "similarity",
                                0.0
                            )
                        ),
                        "source": "experience_memory",
                    }
                )

        except Exception as e:
            # Experience memory is optional. NASA RAG should
            # continue working even if memory is unavailable.
            print(
                f"  Experience search skipped: {e}"
            )

        # --------------------------------------------------------
        # Sort combined NASA + experience results
        # --------------------------------------------------------

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return results[:top_k + 3]

    # ============================================================
    # FAILURE WARNINGS
    # ============================================================

    def get_failure_warnings(self) -> str:
        """
        Get known failure patterns from experience memory.

        These warnings can be injected into the planner prompt
        so that known problematic strategies are avoided.
        """

        try:
            patterns = (
                self.memory.get_failure_patterns()
            )

            if not patterns:
                return ""

            warnings = (
                "KNOWN FAILURE PATTERNS "
                "(avoid these):\n"
            )

            for pattern in patterns[:5]:

                obstacle = pattern.get(
                    "obstacle",
                    "unknown"
                )

                frequency = pattern.get(
                    "frequency",
                    0
                )

                warnings += (
                    f"- Obstacle '{obstacle}' "
                    f"caused {frequency} failures. "
                )

                safe_alternatives = pattern.get(
                    "safe_alternatives"
                )

                if safe_alternatives:
                    warnings += (
                        "Safe alternative: "
                        f"{safe_alternatives}\n"
                    )
                else:
                    warnings += "\n"

            return warnings

        except Exception as e:
            print(
                f"  Failure warning lookup skipped: {e}"
            )
            return ""