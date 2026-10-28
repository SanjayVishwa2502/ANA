import re
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# Standard clinical section headers commonly found in MIMIC-IV and EHR narratives
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

def chunk_clinical_note(text):
    """
    Splits a clinical note into semantic sections based on clinical headers.
    """
    # Compile combined regular expression pattern
    header_pattern = re.compile(f"({'|'.join(CLINICAL_HEADERS)})", re.IGNORECASE)
    
    # Split text while retaining the matched headers
    parts = header_pattern.split(text)
    
    chunks = []
    
    # Process header and body pairs
    if len(parts) > 1:
        # If text starts before any header, capture introductory chunk
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
        # Fallback if no explicit headers are matched
        chunks.append({"section": "GENERAL_NOTE", "content": text.strip()})
        
    return chunks

def run_semantic_chunking():
    print("Loading clinical dataset for Step 2.1 (Semantic Section Chunking)...")
    
    # Mock clinical text fallback if no external file is present
    sample_text = (
        "CHIEF COMPLAINT: Retro-sternal chest pain and shortness of breath.\n"
        "HISTORY OF PRESENT ILLNESS: Patient presented at 1400 hours with acute diaphoresis.\n"
        "VITAL SIGNS: Sinus tachycardia at 135 bpm, BP 165/95, SpO2 89% on room air.\n"
        "MEDICATIONS: Administered 0.4 mg sublingual nitroglycerin and 5000 unit Heparin bolus.\n"
        "LABORATORY RESULTS: Stat ECG shows ST-segment elevation in leads V2 through V4."
    )
    
    # Execute semantic section chunking
    chunks = chunk_clinical_note(sample_text)
    
    print("\n--- Semantic Chunks Extracted ---")
    for idx, chunk in enumerate(chunks, 1):
        print(f"\n[Chunk {idx}] Section: {chunk['section']}")
        print(f"Content: {chunk['content']}")
        print("-" * 50)
        
    print(f"\nSuccessfully created {len(chunks)} semantic section chunks!")

if __name__ == "__main__":
    run_semantic_chunking()