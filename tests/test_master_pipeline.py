"""
Integration Tests for Ambient Nursing Ally (ANA) Master Pipeline
"""

import unittest
from main.ana_master_pipeline import (
    build_ana_master_graph,
    run_ana_master_pipeline,
    ANAPipelineState
)
from langgraph.checkpoint.memory import MemorySaver

class TestMasterPipeline(unittest.TestCase):
    def test_end_to_end_success_pass(self):
        state = run_ana_master_pipeline(
            audio_file_path="datasets/mock_audio.mp3",
            simulate_rejection=False,
            force_low_confidence=False
        )
        self.assertEqual(state["pipeline_status"], "SUCCESS")
        self.assertTrue(state["hitl_approved"])
        self.assertIsNotNone(state["ledger_tx_id"])
        self.assertEqual(len(state["document_hash"]), 64)
        self.assertTrue(len(state["dart_note"]["data"]) > 0)
        self.assertTrue(len(state["dart_note"]["action"]) > 0)

    def test_cascading_error_isolation_checkpoint_rejection(self):
        state = run_ana_master_pipeline(
            audio_file_path="datasets/mock_audio.mp3",
            simulate_rejection=True,
            force_low_confidence=True
        )
        self.assertEqual(state["pipeline_status"], "ISOLATED_QUARANTINED")
        self.assertFalse(state["hitl_approved"])
        self.assertEqual(state["ledger_tx_id"], "")

if __name__ == "__main__":
    unittest.main()
