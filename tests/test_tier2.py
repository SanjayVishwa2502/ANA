"""
Unit Tests for Tier 2: NLP, Redaction & Schema-Constrained DART Extraction
"""

import unittest
from tier2_nlp.redaction_pipeline import run_redaction
from tier2_nlp.dart_pipeline import format_to_dart_schema, DARTNote
from tier2_nlp.chunking_pipeline import chunk_clinical_note

class TestTier2NLP(unittest.TestCase):
    def test_pii_redaction(self):
        text = "Patient Jonathan Harker, MRN48291 presented with acute diaphoresis."
        result = run_redaction(text)
        self.assertNotIn("MRN48291", result["scrubbed_text"])
        self.assertEqual(result["patient_id"], "MRN48291")
        self.assertIn("<MEDICAL_RECORD_NUMBER>", result["scrubbed_text"])

    def test_dart_schema_validation(self):
        sample = (
            "Patient <PERSON>, <MEDICAL_RECORD_NUMBER>. At 1400 hours, vitals were BP 165/95. "
            "Administered 0.4 mg nitroglycerin. Monitored post dose."
        )
        dart = format_to_dart_schema(sample)
        # Verify schema conformity via Pydantic
        validated = DARTNote(**dart)
        self.assertGreaterEqual(validated.confidence_score, 0.85)
        self.assertFalse(validated.requires_manual_flag)
        self.assertTrue(len(validated.data) > 0)
        self.assertTrue(len(validated.action) > 0)

    def test_clinical_chunking(self):
        sample = (
            "CHIEF COMPLAINT: Chest pain.\n"
            "VITAL SIGNS: BP 120/80, HR 72.\n"
            "MEDICATIONS: Aspirin 81 mg."
        )
        chunks = chunk_clinical_note(sample)
        self.assertEqual(len(chunks), 3)
        sections = [c["section"] for c in chunks]
        self.assertIn("CHIEF COMPLAINT", sections)
        self.assertIn("VITAL SIGNS", sections)

if __name__ == "__main__":
    unittest.main()
