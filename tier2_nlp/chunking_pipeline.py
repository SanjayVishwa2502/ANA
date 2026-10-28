"""
Tier 2 / Tier 3: Semantic Clinical Section Chunking Pipeline
Ambient Nursing Ally (ANA) Project
"""

import re
import warnings
from typing import List, Dict, Any

warnings.filterwarnings("ignore")

CLINICAL_HEADERS = [
    r"CHIEF COMPLAINT:",
    r"HISTORY OF PRESENT ILLNESS:",
    r"PAST MEDICAL HISTORY:",
    r"VITAL SIGNS:",
    r"PHYSICAL EXAMINATION:",
    r"LABORATORY RESULTS:",
    r"MEDICATIONS:",
    r"ASSESSMENT AND PLAN:",
    r"DISCHARGE DIAGNOSIS:"
]

def chunk_clinical_note(text: str) -> List[Dict[str, str]]:
    """
    Splits clinical narrative text into semantic sections based on clinical headers.
    Returns list of dicts: [{"section": header_name, "content": text_body}]
    """
    header_pattern = re.compile(f"({'|'.join(CLINICAL_HEADERS)})", re.IGNORECASE)
    parts = header_pattern.split(text)
    chunks: List[Dict[str, str]] = []
    
    if len(parts) > 1:
        if parts[0].strip():
            chunks.append({"section": "HEADER_INFO", "content": parts[0].strip()})
            
        for i in range(1, len(parts), 2):
            header_name = parts[i].replace(":", "").strip().upper()
            content_body = parts[i+1].strip() if (i + 1) < len(parts) else ""
            if content_body:
                chunks.append({
                    "section": header_name,
                    "content": content_body
                })
    else:
        # Fallback if text does not use standard EHR headers
        chunks.append({"section": "GENERAL_NOTE", "content": text.strip()})
        
    return chunks

def run_semantic_chunking(sample_text: str = None) -> List[Dict[str, str]]:
    """Runs semantic section chunking on sample or provided clinical text."""
    print("\n[Tier 2 NLP] 📑 Running Semantic Clinical Section Chunking...")
    
    if not sample_text:
        sample_text = (
            "CHIEF COMPLAINT: Retro-sternal chest pain and shortness of breath.\n"
            "HISTORY OF PRESENT ILLNESS: Patient presented at 1400 hours with acute diaphoresis.\n"
            "VITAL SIGNS: Sinus tachycardia at 135 bpm, BP 165/95, SpO2 89% on room air.\n"
            "MEDICATIONS: Administered 0.4 mg sublingual nitroglycerin and 5000 unit Heparin bolus.\n"
            "LABORATORY RESULTS: Stat ECG shows ST-segment elevation in leads V2 through V4."
        )
        
    chunks = chunk_clinical_note(sample_text)
    print(f"   Successfully extracted {len(chunks)} semantic section chunks.")
    return chunks

if __name__ == "__main__":
    res = run_semantic_chunking()
    for c in res:
        print(f"[{c['section']}]: {c['content']}")
