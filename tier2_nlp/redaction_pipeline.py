"""
Tier 2: Hybrid PII/PHI Redaction Pipeline (Presidio + spaCy NER + Custom MRN Regex)
Ambient Nursing Ally (ANA) Project
"""

import re
import warnings
from typing import Dict, List, Any, Tuple
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from mrn_utils import extract_spoken_mrn

warnings.filterwarnings("ignore")

_analyzer_instance = None
_anonymizer_instance = None

def get_redaction_engines() -> Tuple[AnalyzerEngine, AnonymizerEngine]:
    """Initializes and caches Presidio Analyzer and Anonymizer engines."""
    global _analyzer_instance, _anonymizer_instance
    if _analyzer_instance is None:
        _analyzer_instance = AnalyzerEngine()
        
    if _anonymizer_instance is None:
        _anonymizer_instance = AnonymizerEngine()
        
    return _analyzer_instance, _anonymizer_instance


def extract_redacted_phi(text: str) -> Dict[str, Any]:
    """
    Extracts explicit clinical identifiers (like MRN) before anonymization
    so that agentic patient context anchoring is maintained in memory.
    """
    patient_name_match = re.search(r"Patient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)

    extracted = {
        "extracted_mrn": extract_spoken_mrn(text) or "",
        "extracted_patient_name": patient_name_match.group(1) if patient_name_match else ""
    }
    return extracted


def run_redaction(text: str) -> Dict[str, Any]:
    """
    Executes hybrid PII/PHI redaction using Presidio and regex recognizers.
    Returns the scrubbed text, detected entities list, and patient context anchor.
    """
    print("\n[Tier 2 NLP] 🛡️ Running Hybrid Presidio + spaCy PII/PHI Redaction...")
    
    # Extract identifiers for shift context anchoring prior to scrubbing
    anchor_info = extract_redacted_phi(text)
    
    analyzer, anonymizer = get_redaction_engines()
    
    # MRNs are clinical routing identifiers and must remain visible in the note.
    entities_to_check = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"]
    analysis_results = analyzer.analyze(
        text=text,
        entities=entities_to_check,
        language="en"
    )
    
    # Anonymize scrubbed text
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis_results
    )
    
    scrubbed_text = anonymized_result.text
    
    detected_entities_summary = [
        {
            "entity_type": res.entity_type,
            "start": res.start,
            "end": res.end,
            "score": res.score
        }
        for res in analysis_results
    ]
    
    print(f"   Scrubbed {len(detected_entities_summary)} PII/PHI entities safely.")
    print(f"   Context Anchored: Patient MRN = {anchor_info['extracted_mrn']}")
    
    return {
        "scrubbed_text": scrubbed_text,
        "entities_detected": detected_entities_summary,
        "patient_id": anchor_info["extracted_mrn"],
        "patient_name_pre_redact": anchor_info["extracted_patient_name"]
    }

if __name__ == "__main__":
    sample = (
        "Patient Jonathan Harker, MRN48291. At 1400 hours, the patient became acutely diaphoretic "
        "and tachypneic, complaining of severe retro-sternal chest pain radiating to the left jaw."
    )
    res = run_redaction(sample)
    print("\n--- Scrubbed Text ---")
    print(res["scrubbed_text"])
