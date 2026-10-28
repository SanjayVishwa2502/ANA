import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import warnings
warnings.filterwarnings("ignore")

# Input semantic chunks from Step 2.1
SEMANTIC_CHUNKS = [
    {"section": "CHIEF COMPLAINT", "content": "Retro-sternal chest pain and shortness of breath."},
    {"section": "HISTORY OF PRESENT ILLNESS", "content": "Patient presented at 1400 hours with acute diaphoresis."},
    {"section": "VITAL SIGNS", "content": "Sinus tachycardia at 135 bpm, BP 165/95, SpO2 89% on room air."},
    {"section": "MEDICATIONS", "content": "Administered 0.4 mg sublingual nitroglycerin and 5000 unit Heparin bolus."},
    {"section": "LABORATORY RESULTS", "content": "Stat ECG shows ST-segment elevation in leads V2 through V4."}
]

def run_hybrid_search():
    print("Initializing Hybrid RAG Pipeline (BM25 + FAISS + Cross-Encoder)...")
    
    # Prepare documents as "SECTION: Content"
    documents = [f"{c['section']}: {c['content']}" for c in SEMANTIC_CHUNKS]
    
    # 1. Sparse BM25 Indexing
    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    
    # 2. Dense FAISS Vector Indexing
    print("Loading bi-encoder ('all-MiniLM-L6-v2') for dense vectors...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    doc_embeddings = embedder.encode(documents, convert_to_numpy=True).astype('float32')
    
    dimension = doc_embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(doc_embeddings)
    
    # Query Execution
    query = "What were the patient's vital signs and ECG findings?"
    print(f"\nTarget Query: '{query}'")
    
    # Execute BM25 Sparse Search
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_ranked_indices = np.argsort(bm25_scores)[::-1]
    
    # Execute FAISS Dense Search
    query_vector = embedder.encode([query], convert_to_numpy=True).astype('float32')
    k_dense = len(SEMANTIC_CHUNKS)
    _, faiss_indices = faiss_index.search(query_vector, k_dense)
    dense_ranked_indices = faiss_indices[0]
    
    # 3. Reciprocal Rank Fusion (RRF) with k=60
    rrf_k = 60
    rrf_scores = {}
    
    for rank, idx in enumerate(bm25_ranked_indices):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    for rank, idx in enumerate(dense_ranked_indices):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    fused_candidate_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_candidates = fused_candidate_indices[:3]  # Candidate pool for cross-encoder
    
    print("\n--- RRF Top Candidates ---")
    for idx in top_candidates:
        print(f"[{SEMANTIC_CHUNKS[idx]['section']}] RRF Score: {rrf_scores[idx]:.5f}")
        
    # 4. Cross-Encoder Re-Ranking
    print("\nLoading Cross-Encoder ('cross-encoder/ms-marco-MiniLM-L-6-v2')...")
    cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    pairs = [[query, documents[idx]] for idx in top_candidates]
    cross_scores = cross_encoder.predict(pairs)
    
    ranked_results = sorted(zip(top_candidates, cross_scores), key=lambda x: x[1], reverse=True)
    
    print("\n--- Final Re-Ranked RAG Context Payload ---")
    for rank, (doc_idx, score) in enumerate(ranked_results, 1):
        chunk = SEMANTIC_CHUNKS[doc_idx]
        print(f"\n[Rank {rank}] Re-Rank Score: {score:.4f}")
        print(f"Section: {chunk['section']}")
        print(f"Content: {chunk['content']}")
        print("-" * 50)

if __name__ == "__main__":
    run_hybrid_search()