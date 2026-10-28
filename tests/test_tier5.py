"""
Unit Tests for Tier 5: Cryptographic Hashing & Ledger Tamper Verification
"""

import unittest
from tier5_security.hash_pipeline import generate_clinical_hash
from tier5_security.ledger_audit_pipeline import (
    MockLedgerState,
    anchor_note_to_ledger,
    verify_offchain_integrity
)

class TestTier5Security(unittest.TestCase):
    def test_deterministic_hashing(self):
        note_1 = {"data": ["Vitals 120/80"], "action": ["Administered 0.4mg"]}
        note_2 = {"action": ["Administered 0.4mg"], "data": ["Vitals 120/80"]}  # Reordered keys
        hash1 = generate_clinical_hash(note_1)
        hash2 = generate_clinical_hash(note_2)
        # Deterministic sorting ensures identical hashes regardless of key insertion order
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # 256 bits in hex

    def test_tamper_detection(self):
        ledger = MockLedgerState()
        authentic_note = {"data": ["Vitals 120/80"], "action": ["0.4 mg nitroglycerin"]}
        tx_id, doc_hash = anchor_note_to_ledger(authentic_note, ledger=ledger)

        # 1. Unmodified note matches
        res_valid = verify_offchain_integrity(tx_id, authentic_note, ledger=ledger)
        self.assertTrue(res_valid["verified"])
        self.assertFalse(res_valid["tamper_detected"])

        # 2. Tampered note triggers alert
        tampered_note = {"data": ["Vitals 120/80"], "action": ["4.0 mg nitroglycerin"]}
        res_tampered = verify_offchain_integrity(tx_id, tampered_note, ledger=ledger)
        self.assertFalse(res_tampered["verified"])
        self.assertTrue(res_tampered["tamper_detected"])

if __name__ == "__main__":
    unittest.main()
