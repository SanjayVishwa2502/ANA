"""
Unit Tests for Tier 1: Multimodal Perception Layer
"""

import unittest
from tier1_perception.audio_pipeline import verbal_error_recovery, run_perception_pipeline

class TestTier1Perception(unittest.TestCase):
    def test_verbal_error_recovery_correction(self):
        text = "I immediately administered 10... wait, 0.4 milligrams of sublingual nitroglycerin"
        cleaned, corrections = verbal_error_recovery(text)
        self.assertIn("0.4 milligrams", cleaned)
        self.assertNotIn("10...", cleaned)
        self.assertEqual(len(corrections), 1)

    def test_verbal_error_recovery_clean_text(self):
        text = "Administered 0.4 mg nitroglycerin without complications."
        cleaned, corrections = verbal_error_recovery(text)
        self.assertEqual(cleaned, text)
        self.assertEqual(len(corrections), 0)

    def test_run_perception_pipeline(self):
        res = run_perception_pipeline()
        self.assertIn("cleaned_transcript", res)
        self.assertTrue(len(res["cleaned_transcript"]) > 0)

if __name__ == "__main__":
    unittest.main()
