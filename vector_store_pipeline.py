import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings("ignore")

# Input semantic chunks produced by Step 2.1
SEMANTIC_CHUNKS = [
    {"section": "CHIEF COMPLAINT", "content": "Retro-sternal chest pain and shortness of breath."},
    {"section": "HISTORY OF PRESENT ILLNESS", "content": "Patient presented at 1400 hours with acute diaphoresis."},
    {"section": "VITAL SIGNS", "content": "Sinus tachycardia at 135 bpm, BP 165/95, SpO2 89% on room air."},
    {"section": "MEDICATIONS", "content": "Administered 0.4 mg sublingual nitroglycerin and 5000 unit Heparin bolus."},
    {"section": "LABORATORY RESULTS", "content": "Stat ECG shows ST-segment elevation in leads V2 through V4."}
]

def build_vector_store():
    print("Loading bi-encoder embedding model ('all-MiniLM-L6-v2')...")
    # Bi-encoder model generating 384-dimensional dense vectors
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Format texts as "SECTION: Content" to preserve header metadata in embeddings
    texts_to_embed = [f"{c['section']}: {c['content']}" for c in SEMANTIC_CHUNKS]
    
    print("Generating dense vector embeddings...")
    embeddings = embedder.encode(texts_to_embed, convert_to_numpy=True)
    embeddings = np.array(embeddings).astype('float32')
    
    dimension = embeddings.shape[1]
    print(f"Generated {embeddings.shape[0]} embeddings of dimension {dimension}.")
    
    # Initialize local FAISS L2 (Euclidean distance) index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"FAISS index successfully built. Total vectors stored: {index.ntotal}\n")
    
    # Test Query: Search for cardiac symptoms and vital signs
    query = "What were the patient's vital signs and ECG findings?"
    print(f"Testing RAG Similarity Search with Query: '{query}'")
    
    query_vector = embedder.encode([query], convert_to_numpy=True).astype('float32')
    k = 2  # Retrieve top 2 most relevant chunks
    distances, indices = index.search(query_vector, k)
    
    print("\n--- Top Retrieved Clinical Chunks ---")
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
        retrieved_chunk = SEMANTIC_CHUNKS[idx]
        print(f"\n[Rank {rank}] Distance Score: {dist:.4f}")
        print(f"Section: {retrieved_chunk['section']}")
        print(f"Content: {retrieved_chunk['content']}")
        print("-" * 50)

if __name__ == "__main__":
    build_vector_store()