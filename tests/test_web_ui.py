"""Focused tests for web UI input-mode validation."""

import unittest
from unittest.mock import patch

from web_ui.app import app


class TestWebUI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_text_mode_requires_staff_mrn_and_text(self):
        response = self.client.post(
            "/api/run_pipeline",
            json={"input_mode": "text", "patient_id": "MRN48291"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Staff name is required", response.get_json()["error"])

    @patch("web_ui.app.run_ana_master_pipeline")
    def test_text_mode_passes_manual_input_without_audio(self, run_pipeline):
        run_pipeline.return_value = {
            "shift_session_id": "internal_thread",
            "staff_name": "Nurse Example",
            "input_mode": "text",
            "pipeline_status": "ISOLATED_QUARANTINED",
            "status_summary": "quarantined",
            "raw_transcript": "MRN48291. HI.",
            "cleaned_transcript": "MRN48291. HI.",
            "verbal_corrections": [],
            "speech_timestamps": [],
            "patient_context_anchor": {
                "anchored": False,
                "anchored_mrn": "UNKNOWN",
                "details": "manual test",
            },
            "patient_id": "MRN48291",
            "scrubbed_text": "MRN48291. HI.",
            "entities_detected": [],
            "dart_note": {},
            "confidence_score": 0.2,
            "requires_manual_flag": True,
            "hitl_approved": False,
            "hitl_reviewer": "Nurse_Auth_8841",
            "hitl_timestamp": "",
            "hitl_rejection_reason": "manual test",
            "clinical_chunks": [],
            "rag_retrieval_results": [],
            "fhir_patient_record": None,
            "medication_safety_report": None,
            "document_hash": "",
            "ledger_tx_id": "",
            "tamper_check_result": {},
        }

        response = self.client.post(
            "/api/run_pipeline",
            json={
                "input_mode": "text",
                "patient_id": "48291",
                "transcript": "HI.",
                "staff_name": "Nurse Example",
            },
        )

        self.assertEqual(response.status_code, 200)
        run_pipeline.assert_called_once()
        call = run_pipeline.call_args.kwargs
        self.assertIsNone(call["audio_file_path"])
        self.assertEqual(call["input_mode"], "text")
        self.assertEqual(call["manual_transcript"], "HI.")
        self.assertEqual(call["patient_id"], "MRN48291")
        self.assertEqual(response.get_json()["staff_name"], "Nurse Example")


if __name__ == "__main__":
    unittest.main()
