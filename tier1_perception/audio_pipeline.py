"""
Tier 1: Audio Processing Pipeline (Silero-VAD + Whisper ASR + Verbal Error Recovery)
Ambient Nursing Ally (ANA) Project
"""

import os
import sys
import re
import time
import warnings
from typing import Dict, List, Optional, Tuple, Any
from mrn_utils import extract_spoken_mrn, normalize_mrn, transcript_contains_mrn

# Windows console cp1252 UTF-8 safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

def run_vad(file_path: str, output_path: str = "segmented_audio.wav") -> Tuple[str, List[Dict[str, int]]]:
    """
    Applies Silero-VAD to segment active speech and filter ward background noise.
    Returns the path to the saved segmented audio and speech timestamps.
    """
    print(f"\n[Tier 1 Perception] 🎙️ Initializing Silero-VAD on '{file_path}'...")
    speech_timestamps: List[Dict[str, int]] = []
    
    if not os.path.exists(file_path):
        print(f"⚠️ Audio file not found at '{file_path}'. No speech segments produced.")
        return file_path, []

    try:
        import torch
        # Load Silero-VAD directly from PyTorch Hub
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True
        )
        (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
        
        # Silero VAD processes at 16,000 Hz
        wav = read_audio(file_path, sampling_rate=16000)
        speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
        
        print(f"   Detected {len(speech_timestamps)} active speech segments.")
        for idx, segment in enumerate(speech_timestamps[:3], 1):
            print(f"   - Segment {idx}: sample {segment['start']} to {segment['end']}")
            
        if speech_timestamps:
            save_audio(output_path, collect_chunks(speech_timestamps, wav), sampling_rate=16000)
            print(f"   ✅ Saved filtered speech to '{output_path}'.")
            return output_path, speech_timestamps
        else:
            print("   ⚠️ No speech detected; returning original file.")
            return file_path, []
    except Exception as e:
        print(f"   ⚠️ Silero-VAD hub load note ({e}). Returning direct audio stream.")
        return file_path, [{"start": 0, "end": 160000}]


def transcribe_audio(file_path: str, model_size: str = "base") -> str:
    """
    Transcribes segmented audio using OpenAI Whisper ASR.
    Returns only the transcript produced by Whisper; failures are not replaced
    with synthetic clinical content.
    """
    print(f"\n[Tier 1 Perception] 🔤 Transcribing '{file_path}' using Whisper '{model_size}'...")
    start_time = time.time()
    
    if not os.path.exists(file_path):
        print(f"   ⚠️ Audio file '{file_path}' unavailable. No transcript produced.")
        return ""

    try:
        import whisper
        model = whisper.load_model(model_size)
        result = model.transcribe(file_path, fp16=False)
        transcript = result.get("text", "").strip()
        elapsed = round(time.time() - start_time, 2)
        print(f"   ✅ ASR Transcription completed in {elapsed}s.")
        return transcript
    except Exception as e:
        print(f"   ⚠️ Whisper local inference failed ({e}). No transcript produced.")
        return ""


def verbal_error_recovery(transcript: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Verbal Error Recovery Node:
    Detects and rolls back mid-sentence nurse self-corrections
    (e.g., 'administer 10... wait, 0.4 milligrams' -> 'administer 0.4 milligrams').
    Matches clinical speech correction markers: 'wait,', 'scratch that,', 'correction:', 'I mean'.
    """
    corrections_logged: List[Dict[str, str]] = []
    
    correction_patterns = [
        # Pattern: "<incorrect> ... wait, <correct>"
        r"(\b[\w\.\d\s]+?)\s*\.{2,}\s*wait[,\s]+([\w\.\d]+(?:\s+milligrams|\s+mg|\s+units|\s+liters)?)",
        # Pattern: "<incorrect> scratch that <correct>"
        r"(\b[\w\.\d\s]+?)\s*scratch that[,\s]+([\w\.\d]+(?:\s+milligrams|\s+mg|\s+units|\s+liters)?)",
        # Pattern: "<incorrect> correction <correct>"
        r"(\b[\w\.\d\s]+?)\s*correction[,\s]+([\w\.\d]+(?:\s+milligrams|\s+mg|\s+units|\s+liters)?)"
    ]
    
    cleaned_transcript = transcript
    for pat in correction_patterns:
        matches = list(re.finditer(pat, cleaned_transcript, re.IGNORECASE))
        for m in matches:
            full_span = m.group(0)
            erroneous = m.group(1).strip()
            corrected = m.group(2).strip()
            corrections_logged.append({
                "original_slip": erroneous,
                "corrected_value": corrected,
                "pattern_matched": full_span
            })
            cleaned_transcript = cleaned_transcript.replace(full_span, corrected)
            
    if corrections_logged:
        print("\n[Tier 1 Perception] 🔄 Verbal Error Recovery Triggered:")
        for log in corrections_logged:
            print(f"   ⚠️ Self-Correction: Replaced '{log['original_slip']}' -> '{log['corrected_value']}'")
    else:
        print("\n[Tier 1 Perception] ✨ Verbal Error Recovery: No mid-sentence corrections detected.")
        
    return cleaned_transcript, corrections_logged


def verify_patient_context_anchoring(transcript: str, declared_mrn: Optional[str] = None) -> Dict[str, Any]:
    """
    Tier 1 Patient Context Anchoring Protocol (Methodology Redraft Section 2.1):
    Prevents acoustic cross-talk in multi-bed rooms.
    Verifies that the audio utterance contains an explicit patient identifier declaration
    (e.g., 'MRN48291' or digit-by-digit MRN speech). A scanner value can
    provide a second factor, but the same MRN must still occur in the transcript.
    If unanchored, the fail-safe flags cross-talk risk.
    """
    voice_mrn = extract_spoken_mrn(transcript)
    clean_declared = normalize_mrn(declared_mrn)
    if not voice_mrn and clean_declared and transcript_contains_mrn(transcript, clean_declared):
        voice_mrn = clean_declared
    
    if voice_mrn and clean_declared:
        if voice_mrn == clean_declared:
            return {
                "anchored": True,
                "anchored_mrn": voice_mrn,
                "source": "dual_verified (voice + bedside wristband)",
                "details": f"Patient Context fully verified: Voice MRN matches Bedside station ({voice_mrn})."
            }
        else:
            return {
                "anchored": False,
                "anchored_mrn": "UNKNOWN",
                "source": "mrn_mismatch",
                "details": f"MRN mismatch: transcript declares {voice_mrn}, but scanner supplied {clean_declared}. Audio quarantined."
            }
    elif voice_mrn:
        return {
            "anchored": True,
            "anchored_mrn": voice_mrn,
            "source": "voice_declared",
            "details": f"Patient Context anchored via verbal MRN declaration ({voice_mrn})."
        }
    elif clean_declared:
        return {
            "anchored": False,
            "anchored_mrn": "UNKNOWN",
            "source": "scanner_without_voice_mrn",
            "details": f"Scanner supplied {clean_declared}, but the MRN was not spoken in the transcript. Audio quarantined."
        }
    else:
        # Failsafe drop: No patient identifier detected in voice or bedside station
        return {
            "anchored": False,
            "anchored_mrn": "UNKNOWN",
            "source": "unanchored",
            "details": "🚨 PATIENT CONTEXT ANCHORING FAILED: Speak the MRN digit by digit or scan the wristband and also speak the same MRN. Audio quarantined."
        }


def run_perception_pipeline(audio_file_path: Optional[str] = None, declared_mrn: Optional[str] = None) -> Dict[str, object]:
    """
    Executes Tier 1 end-to-end:
    VAD segmentation -> Whisper ASR -> Verbal Rollback / Error Recovery -> Patient Context Anchoring
    """
    print("\n=======================================================")
    print("🎙️ TIER 1: MULTIMODAL PERCEPTION & ACOUSTIC INGESTION")
    print("=======================================================")
    
    target_audio = audio_file_path or ""
        
    # Step 1.1: VAD Segmentation
    segmented_path, timestamps = run_vad(target_audio, "datasets/segmented_audio.wav")
    
    # Step 1.2: Whisper Transcription
    raw_transcript = transcribe_audio(segmented_path)
    print(f"\n--- Raw ASR Transcription ---\n{raw_transcript}\n" + "-" * 30)
    
    # Step 1.3: Verbal Error Recovery
    cleaned_transcript, corrections = verbal_error_recovery(raw_transcript)
    
    # Step 1.4: Patient Context Anchoring (Section 2.1)
    context_anchor = verify_patient_context_anchoring(cleaned_transcript, declared_mrn)
    print(f"\n[Tier 1 Perception] 🏷️ Context Anchoring Status: {context_anchor['details']}")
    
    return {
        "raw_transcript": raw_transcript,
        "cleaned_transcript": cleaned_transcript,
        "corrections_logged": corrections,
        "audio_file": target_audio,
        "speech_timestamps": timestamps,
        "patient_context_anchor": context_anchor
    }

if __name__ == "__main__":
    result = run_perception_pipeline("mock_audio.mp3")
    print(f"\nCleaned Transcript Output:\n{result['cleaned_transcript']}")
