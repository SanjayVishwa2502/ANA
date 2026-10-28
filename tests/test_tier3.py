"""
Unit Tests for Tier 3: Historical Knowledge & Hybrid RAG Layer
"""

import unittest
from tier3_rag.vector_store_pipeline import build_vector_store, search_vector_store
from tier3_rag.hybrid_search_pipeline import run_hybrid_search, calculate_temporal_decay

class TestTier3RAG(unittest.TestCase):
    def test_temporal_decay(self):
        decay_recent = calculate_temporal_decay(0.5, half_life_hours=6.0)
        decay_older = calculate_temporal_decay(10.0, half_life_hours=6.0)
        self.assertGreater(decay_recent, decay_older)
        self.assertLessEqual(decay_recent, 1.0)
        self.assertGreaterEqual(decay_older, 0.2)

    def test_vector_store_build_and_search(self):
        idx, emb, texts, chks = build_vector_store()
        self.assertEqual(idx.ntotal, len(chks))
        results = search_vector_store("vital signs and ecg findings", idx, emb, chks, k=2)
        self.assertEqual(len(results), 2)
        self.assertIn("chunk", results[0])

    def test_hybrid_search(self):
        out = run_hybrid_search("nitroglycerin and heparin medications", top_k=2)
        self.assertIn("results", out)
        self.assertTrue(len(out["results"]) > 0)
        top = out["results"][0]
        self.assertIn("section", top)
        self.assertIn("rrf_score", top)

if __name__ == "__main__":
    unittest.main()
