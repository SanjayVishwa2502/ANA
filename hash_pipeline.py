import hashlib
import json

def generate_clinical_hash(dart_note: dict) -> str:
    """Generates a deterministic SHA-256 hash for a clinical DART note."""
    print("Serializing DART note deterministically...")
    # Sort keys to ensure the exact same JSON structure always produces the identical hash
    serialized_note = json.dumps(dart_note, sort_keys=True, separators=(',', ':'))
    
    print("Computing SHA-256 cryptographic hash...")
    sha256_hash = hashlib.sha256(serialized_note.encode('utf-8')).hexdigest()
    return sha256_hash

def run_hash_test():
    print("Initializing Tier 5 Cryptographic Hash Generator...")
    
    # Sample DART note output from Step 1.4
    sample_dart_note = {
        "data": ["Acutely diaphoretic and tachypneic", "Vitals: Sinus tachycardia at 135 bpm"],
        "action": ["Administered 0.4 mg sublingual nitroglycerin", "Started 2 L oxygen"],
        "response": ["Initial evaluation logged"],
        "teaching": ["Patient advised to remain still"],
        "confidence_score": 0.96,
        "requires_manual_flag": False
    }
    
    document_hash = generate_clinical_hash(sample_dart_note)
    
    print("\n--- Cryptographic Audit Trail Metadata ---")
    print(f"Actor ID: Nurse_Auth_8841")
    print(f"Action Type: DART_NOTE_GENERATED")
    print(f"Off-Chain Payload Size: {len(json.dumps(sample_dart_note))} bytes")
    print(f"SHA-256 Hash (For Ledger): {document_hash}")
    print("------------------------------------------")

if __name__ == "__main__":
    run_hash_test()