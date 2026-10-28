"""
Tier 3: Historical Knowledge & Hybrid RAG Layer
Includes FAISS bi-encoder dense vector indexing, BM25 sparse lexical search,
Reciprocal Rank Fusion (RRF), Cross-Encoder re-ranking, and temporal decay scoring.
"""

from .vector_store_pipeline import build_vector_store, search_vector_store, SEMANTIC_CHUNKS_DEFAULT
from .hybrid_search_pipeline import run_hybrid_search

__all__ = [
    "build_vector_store",
    "search_vector_store",
    "run_hybrid_search",
    "SEMANTIC_CHUNKS_DEFAULT",
]
