"""
Tier 3: FAISS Dense Vector Store Pipeline
Ambient Nursing Ally (ANA) Project
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import warnings
from typing import List, Dict, Tuple, Any

warnings.filterwarnings("ignore")

SEMANTIC_CHUNKS_DEFAULT = [
    {"section": "CHIEF COMPLAINT", "content": "Retro-sternal chest pain and shortness of breath.", "hours_ago": 2.0},
    {"section": "HISTORY OF PRESENT ILLNESS", "content": "Patient presented at 1400 hours with acute diaphoresis.", "hours_ago": 2.0},
    {"section": "VITAL SIGNS", "content": "Sinus tachycardia at 135 bpm, BP 165/95, SpO2 89% on room air.", "hours_ago": 1.5},
    {"section": "MEDICATIONS", "content": "Administered 0.4 mg sublingual nitroglycerin and 5000 unit Heparin bolus.", "hours_ago": 1.0},
    {"section": "LABORATORY RESULTS", "content": "Stat ECG shows ST-segment elevation in leads V2 through V4.", "hours_ago": 0.5}
]

_embedder_model = None

def get_sentence_embedder(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Caches and returns bi-encoder embedding model."""
    global _embedder_model
    if _embedder_model is None:
        _embedder_model = SentenceTransformer(model_name)
    return _embedder_model


def build_vector_store(chunks: List[Dict[str, Any]] = None) -> Tuple[faiss.IndexFlatL2, SentenceTransformer, List[str], List[Dict[str, Any]]]:
    """
    Builds a local FAISS dense vector index from clinical chunks.
    Returns (faiss_index, embedder, texts_embedded, original_chunks).
    """
    if not chunks:
        chunks = SEMANTIC_CHUNKS_DEFAULT
        
    print(f"\n[Tier 3 RAG] 🧠 Building FAISS Dense Vector Store with {len(chunks)} chunks...")
    embedder = get_sentence_embedder()
    
    # Format texts as "SECTION: Content" to preserve header metadata
    texts_to_embed = [f"{c.get('section', 'CLINICAL')}: {c.get('content', '')}" for c in chunks]
    
    embeddings = embedder.encode(texts_to_embed, convert_to_numpy=True).astype("float32")
    dimension = embeddings.shape[1]
    
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"   ✅ Indexed {index.ntotal} vectors (dimension {dimension}).")
    return index, embedder, texts_to_embed, chunks


def search_vector_store(query: str, index: faiss.IndexFlatL2, embedder: SentenceTransformer, chunks: List[Dict[str, Any]], k: int = 2) -> List[Dict[str, Any]]:
    """Executes dense vector similarity search against the FAISS index."""
    query_vector = embedder.encode([query], convert_to_numpy=True).astype("float32")
    k = min(k, len(chunks))
    distances, indices = index.search(query_vector, k)
    
    retrieved = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(chunks):
            retrieved.append({
                "chunk": chunks[idx],
                "distance": float(dist),
                "similarity_score": float(1.0 / (1.0 + dist))
            })
    return retrieved

if __name__ == "__main__":
    idx, emb, texts, chks = build_vector_store()
    res = search_vector_store("vital signs and ecg", idx, emb, chks)
    for r in res:
        print(f"[{r['chunk']['section']}] Dist: {r['distance']:.4f}")
