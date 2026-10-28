"""
Tier 3: Hybrid RAG Pipeline (BM25 + FAISS + RRF + Cross-Encoder + Temporal Decay)
Ambient Nursing Ally (ANA) Project
"""

import math
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import warnings
from typing import List, Dict, Any, Optional

from .vector_store_pipeline import build_vector_store, SEMANTIC_CHUNKS_DEFAULT

warnings.filterwarnings("ignore")

_cross_encoder_model = None

def get_cross_encoder(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> CrossEncoder:
    """Caches and returns cross-encoder re-ranking model."""
    global _cross_encoder_model
    if _cross_encoder_model is None:
        _cross_encoder_model = CrossEncoder(model_name)
    return _cross_encoder_model


def calculate_temporal_decay(hours_ago: float, half_life_hours: float = 6.0) -> float:
    """
    Computes exponential time-decay weight for clinical shift notes.
    Ensures recent nursing observations during a 12-hour shift are scored higher than older notes.
    Score = exp(-ln(2) * hours_ago / half_life_hours)
    """
    if hours_ago <= 0:
        return 1.0
    decay = math.exp(-0.69315 * (hours_ago / half_life_hours))
    return max(0.2, min(1.0, decay))


def run_hybrid_search(
    query: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    top_k: int = 3,
    use_cross_encoder: bool = True,
    apply_temporal_decay: bool = True
) -> Dict[str, Any]:
    """
    Executes multi-stage Hybrid Retrieval:
    1. Sparse BM25 Lexical Search
    2. Dense FAISS Vector Search
    3. Reciprocal Rank Fusion (RRF, k=60)
    4. Temporal Time-Decay Re-Weighting
    5. Cross-Encoder Full Attention Re-Ranking
    """
    if not chunks:
        chunks = SEMANTIC_CHUNKS_DEFAULT
        
    print(f"\n[Tier 3 RAG] 🔍 Executing Hybrid Search (BM25 + FAISS + RRF + Cross-Encoder)...")
    print(f"   Query: '{query}' across {len(chunks)} clinical note chunks.")
    
    # Format documents
    documents = [f"{c.get('section', 'CLINICAL')}: {c.get('content', '')}" for c in chunks]
    
    # 1. Sparse BM25 Indexing & Search
    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_ranked_indices = np.argsort(bm25_scores)[::-1]
    
    # 2. Dense FAISS Indexing & Search
    faiss_index, embedder, _, _ = build_vector_store(chunks)
    query_vector = embedder.encode([query], convert_to_numpy=True).astype("float32")
    k_dense = len(chunks)
    _, faiss_indices = faiss_index.search(query_vector, k_dense)
    dense_ranked_indices = faiss_indices[0]
    
    # 3. Reciprocal Rank Fusion (RRF with k=60)
    rrf_k = 60
    rrf_scores = {}
    
    for rank, idx in enumerate(bm25_ranked_indices):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    for rank, idx in enumerate(dense_ranked_indices):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    # Apply Temporal Context Decay if chunk has time metadata
    if apply_temporal_decay:
        for idx in rrf_scores:
            hours_ago = float(chunks[idx].get("hours_ago", 1.0))
            decay_factor = calculate_temporal_decay(hours_ago)
            rrf_scores[idx] = rrf_scores[idx] * (0.8 + 0.2 * decay_factor)
            
    fused_candidate_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_candidates = fused_candidate_indices[:min(top_k + 2, len(chunks))]
    
    print(f"   RRF fused {len(top_candidates)} top candidate sections for re-ranking.")
    
    # 4. Cross-Encoder Re-Ranking
    ranked_results: List[Dict[str, Any]] = []
    
    if use_cross_encoder:
        try:
            cross_encoder = get_cross_encoder()
            pairs = [[query, documents[idx]] for idx in top_candidates]
            cross_scores = cross_encoder.predict(pairs)
            
            scored_candidates = sorted(
                zip(top_candidates, cross_scores),
                key=lambda x: x[1],
                reverse=True
            )
            
            for rank, (doc_idx, score) in enumerate(scored_candidates[:top_k], 1):
                chunk = chunks[doc_idx]
                ranked_results.append({
                    "rank": rank,
                    "section": chunk.get("section", "CLINICAL"),
                    "content": chunk.get("content", ""),
                    "hours_ago": chunk.get("hours_ago", 1.0),
                    "cross_encoder_score": float(score),
                    "rrf_score": float(rrf_scores[doc_idx])
                })
        except Exception as e:
            print(f"   ⚠️ Cross-encoder note ({e}). Using RRF ranking.")
            ranked_results = []
            
    if not ranked_results:
        # Fallback to pure RRF ranking if cross-encoder was skipped
        for rank, doc_idx in enumerate(top_candidates[:top_k], 1):
            chunk = chunks[doc_idx]
            ranked_results.append({
                "rank": rank,
                "section": chunk.get("section", "CLINICAL"),
                "content": chunk.get("content", ""),
                "hours_ago": chunk.get("hours_ago", 1.0),
                "cross_encoder_score": 0.0,
                "rrf_score": float(rrf_scores[doc_idx])
            })
            
    print(f"   ✅ Top match: [{ranked_results[0]['section']}] - '{ranked_results[0]['content'][:60]}...'")
    
    return {
        "query": query,
        "results": ranked_results,
        "total_indexed": len(chunks)
    }

if __name__ == "__main__":
    out = run_hybrid_search("vital signs and ecg findings")
    for r in out["results"]:
        print(f"Rank {r['rank']} [{r['section']}] Score: {r['cross_encoder_score']:.4f}")
