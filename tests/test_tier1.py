"""
Unit Tests for Tier 1: Multimodal Perception Layer
"""

import unittest
from tier1_perception.audio_pipeline import (
    run_perception_pipeline,
    transcribe_audio,
    verbal_error_recovery,
    verify_patient_context_anchoring,
)
from main.ana_master_pipeline import node_tier1_perception

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
        self.assertEqual(res["cleaned_transcript"], "")
        self.assertFalse(res["patient_context_anchor"]["anchored"])

    def test_spoken_mrn_is_required_and_supports_digit_words(self):
        result = verify_patient_context_anchoring(
            "Patient medical record number four eight two nine one has chest pain."
        )
        self.assertTrue(result["anchored"])
        self.assertEqual(result["anchored_mrn"], "MRN48291")

    def test_scanner_mrn_must_match_transcript(self):
        result = verify_patient_context_anchoring("HI.", declared_mrn="MRN48291")
        self.assertFalse(result["anchored"])
        self.assertEqual(result["source"], "scanner_without_voice_mrn")

    def test_scanner_mrn_accepts_bare_spoken_digit_sequence(self):
        result = verify_patient_context_anchoring(
            "Four eight two nine one, patient has chest pain.",
            declared_mrn="MRN48291",
        )
        self.assertTrue(result["anchored"])
        self.assertEqual(result["anchored_mrn"], "MRN48291")

    def test_missing_audio_does_not_create_clinical_transcript(self):
        self.assertEqual(transcribe_audio("missing-audio.wav"), "")

    def test_text_mode_skips_audio_transcription(self):
        result = node_tier1_perception({
            "input_mode": "text",
            "audio_path": "",
            "patient_id": "MRN48291",
            "manual_transcript": "Patient has chest pain.",
        })
        self.assertEqual(result["speech_timestamps"], [])
        self.assertIn("MRN48291", result["raw_transcript"])
        self.assertEqual(result["patient_context_anchor"]["anchored_mrn"], "MRN48291")

if __name__ == "__main__":
    unittest.main()
