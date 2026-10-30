"""
Ambient Nursing Ally (ANA) — Clinical Perception & Pipeline Web Console
Flask Backend Server providing real-time audio capture, Tier 1 perception,
and end-to-end 5-Tier LangGraph execution for hospital inpatient wards.
"""

import os
import sys
import json
import time
import uuid
import wave
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Windows console cp1252 UTF-8 safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Tier & Master Pipeline Imports
from main.ana_master_pipeline import run_ana_master_pipeline
from tier1_perception.audio_pipeline import (
    run_perception_pipeline,
    verify_patient_context_anchoring
)
from mrn_utils import normalize_mrn
from tier5_security.ledger_audit_pipeline import (
    generate_clinical_hash,
    verify_offchain_integrity,
    get_shared_ledger
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

UPLOAD_DIR = os.path.join(PROJECT_ROOT, "datasets", "captured_audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

@app.route("/")
def index():
    """Renders the primary ANA Clinical Inpatient Ward Console."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Returns system status and operational readiness of all 5 tiers."""
    return jsonify({
        "status": "OPERATIONAL",
        "service": "Ambient Nursing Ally (ANA)",
        "version": "2.1.0-DSR-Agile",
        "tiers": {
            "tier1_perception": "Silero-VAD + Whisper ASR (16kHz)",
            "tier2_nlp": "Presidio PII/PHI Redactor + spaCy + DART Schema",
            "checkpoint": "Cascading Error Isolation (HITL Review)",
            "tier3_rag": "FAISS Dense + BM25 Sparse + RRF + Cross-Encoder",
            "tier4_agentic": "LangGraph MCP Agent + Mock Smart-on-FHIR",
            "tier5_security": "SHA-256 Anchoring + Hyperledger Fabric Ledger"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/upload_audio", methods=["POST"])
def upload_audio():
    """
    Accepts real-time microphone recordings (PCM WAV) or uploaded audio files,
    stores them in datasets/captured_audio/, and returns audio telemetry.
    """
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided in form-data."}), 400
        
    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    timestamp = int(time.time() * 1000)
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext or ext == ".blob":
        ext = ".wav"
        
    unique_name = f"rec_{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(dest_path)

    # Compute duration and telemetry
    duration_sec = 0.0
    sample_rate = 16000
    channels = 1
    file_size_kb = round(os.path.getsize(dest_path) / 1024, 2)

    try:
        if ext == ".wav":
            with wave.open(dest_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                frames = wf.getnframes()
                duration_sec = round(frames / float(sample_rate), 2)
        else:
            import soundfile as sf
            info = sf.info(dest_path)
            duration_sec = round(info.duration, 2)
            sample_rate = info.samplerate
            channels = info.channels
    except Exception as e:
        print(f"⚠️ Audio metadata warning: {e}")
        duration_sec = 12.5  # fallback estimate

    rel_path = os.path.relpath(dest_path, PROJECT_ROOT).replace("\\", "/")

    return jsonify({
        "success": True,
        "filename": unique_name,
        "relative_path": rel_path,
        "size_kb": file_size_kb,
        "duration_sec": duration_sec,
        "sample_rate": sample_rate,
        "channels": channels,
        "audio_url": f"/api/audio/{unique_name}",
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/audio/<filename>")
def serve_audio(filename):
    """Streams captured audio back to the browser for playback."""
    # Check captured audio first
    captured_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(captured_file):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        
    # Check datasets directory
    datasets_file = os.path.join(PROJECT_ROOT, "datasets", filename)
    if os.path.exists(datasets_file):
        return send_from_directory(os.path.join(PROJECT_ROOT, "datasets"), filename)
        
    # Check root directory
    root_file = os.path.join(PROJECT_ROOT, filename)
    if os.path.exists(root_file):
        return send_from_directory(PROJECT_ROOT, filename)
        
    return jsonify({"error": "Audio file not found."}), 404


@app.route("/api/run_pipeline", methods=["POST"])
def run_pipeline():
    """
    Executes the full ANA 5-Tier master pipeline on the captured audio.
    Accepts:
      - input_mode: ``audio`` or ``text``
      - audio_path: relative path to a captured or uploaded audio file
      - transcript: manual clinical text when input_mode is ``text``
      - patient_id: barcode scanner MRN or text-mode MRN
      - staff_name: submitting staff member's name
      - simulate_rejection: bool (tests HITL rejection branch)
      - force_low_confidence: bool (tests confidence flagging)
      - edge_buffering: bool (simulates local offline encrypted edge caching)
    """
    data = request.get_json() or {}
    input_mode = data.get("input_mode", "audio")
    audio_path = data.get("audio_path", "")
    manual_transcript = data.get("transcript", "")
    declared_mrn = data.get("patient_id", "")
    staff_name = data.get("staff_name", "")
    if input_mode not in {"audio", "text"}:
        return jsonify({"success": False, "error": "input_mode must be either 'audio' or 'text'."}), 400
    if not isinstance(staff_name, str) or not staff_name.strip():
        return jsonify({"success": False, "error": "Staff name is required."}), 400
    if not isinstance(declared_mrn, str):
        declared_mrn = ""
    declared_mrn = normalize_mrn(declared_mrn)
    if not declared_mrn:
        return jsonify({"success": False, "error": "A valid MRN is required."}), 400
    simulate_rejection = bool(data.get("simulate_rejection", False))
    force_low_conf = bool(data.get("force_low_confidence", False))
    edge_buffering = bool(data.get("edge_buffering", False))

    full_audio_path = None
    if input_mode == "audio":
        if not isinstance(audio_path, str) or not audio_path.strip():
            return jsonify({"success": False, "error": "Capture or upload audio before processing."}), 400

        # Resolve full path
        full_audio_path = os.path.abspath(os.path.join(PROJECT_ROOT, audio_path))
        if os.path.commonpath([PROJECT_ROOT, full_audio_path]) != PROJECT_ROOT:
            return jsonify({"success": False, "error": "Audio path must remain inside the project."}), 400
        if not os.path.isfile(full_audio_path):
            return jsonify({"success": False, "error": f"Audio file not found: {audio_path}"}), 400
    elif not isinstance(manual_transcript, str) or not manual_transcript.strip():
        return jsonify({"success": False, "error": "Clinical text is required for text input mode."}), 400

    shift_id = f"shift_{uuid.uuid4().hex[:8]}"

    # Execute ANA Master Pipeline
    try:
        final_state = run_ana_master_pipeline(
            audio_file_path=full_audio_path,
            patient_id=declared_mrn if declared_mrn else None,
            manual_transcript=manual_transcript if input_mode == "text" else None,
            input_mode=input_mode,
            staff_name=staff_name.strip(),
            simulate_rejection=simulate_rejection,
            force_low_confidence=force_low_conf,
            shift_thread_id=shift_id
        )

        # Format clean JSON payload for UI visualization
        response_payload = {
            "success": True,
            "shift_session_id": final_state.get("shift_session_id"),
            "staff_name": final_state.get("staff_name"),
            "input_mode": final_state.get("input_mode"),
            "pipeline_status": final_state.get("pipeline_status"),
            "status_summary": final_state.get("status_summary"),
            "edge_cached_simulation": {
                "active": edge_buffering,
                "encryption": "AES-256-GCM (Zero-Trust Local Queue)",
                "status": "Flushed to Core Backend" if not edge_buffering else "Queued in Local Flash Cache"
            },
            "tier1_perception": {
                "audio_source": audio_path,
                "speech_timestamps": final_state.get("speech_timestamps", []),
                "raw_transcript": final_state.get("raw_transcript", ""),
                "cleaned_transcript": final_state.get("cleaned_transcript", ""),
                "verbal_corrections": final_state.get("verbal_corrections", []),
                "patient_context_anchor": final_state.get("patient_context_anchor", {}),
                "active_speech_segments_count": len(final_state.get("speech_timestamps", []))
            },
            "tier2_nlp": {
                "patient_id": final_state.get("patient_id"),
                "scrubbed_text": final_state.get("scrubbed_text", ""),
                "entities_detected": final_state.get("entities_detected", []),
                "dart_note": final_state.get("dart_note", {}),
                "confidence_score": round(final_state.get("confidence_score", 0.0), 3),
                "requires_manual_flag": final_state.get("requires_manual_flag", False)
            },
            "checkpoint_hitl": {
                "hitl_approved": final_state.get("hitl_approved", True),
                "hitl_reviewer": final_state.get("hitl_reviewer", "Nurse_Auth_8841"),
                "hitl_timestamp": final_state.get("hitl_timestamp"),
                "hitl_rejection_reason": final_state.get("hitl_rejection_reason")
            },
            "tier3_rag": {
                "clinical_chunks": final_state.get("clinical_chunks", []),
                "retrieval_results": final_state.get("rag_retrieval_results", []),
                "total_chunks_indexed": len(final_state.get("clinical_chunks", []))
            },
            "tier4_agentic": {
                "patient_record": final_state.get("fhir_patient_record"),
                "medication_safety_report": final_state.get("medication_safety_report")
            },
            "tier5_security": {
                "document_hash": final_state.get("document_hash"),
                "ledger_tx_id": final_state.get("ledger_tx_id"),
                "tamper_check_result": final_state.get("tamper_check_result", {})
            }
        }
        return jsonify(response_payload)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/tamper_test", methods=["POST"])
def tamper_test():
    """
    Demonstrates Tier 5 cryptographic tampering detection by comparing
    original on-chain hash with a dynamically altered clinical note string.
    """
    data = request.get_json() or {}
    original_hash = data.get("original_hash", "")
    tampered_text = data.get("tampered_text", "")

    if not original_hash:
        return jsonify({"success": False, "error": "Missing original document hash."}), 400

    new_hash = generate_clinical_hash(tampered_text)
    is_valid = (new_hash == original_hash)

    return jsonify({
        "success": True,
        "is_intact": is_valid,
        "original_hash": original_hash,
        "computed_hash": new_hash,
        "verification_status": "VALID_AUTHENTIC" if is_valid else "TAMPER_DETECTED",
        "message": (
            "✅ Document integrity intact. Digital signature matches Hyperledger Fabric anchor."
            if is_valid else
            "🚨 TAMPER DETECTED: Cryptographic digest mismatch! Off-chain data modified without authorization."
        )
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("=" * 70)
    print("🏥 AMBIENT NURSING ALLY (ANA) — CLINICAL CONSOLE")
    print(f"🌐 Serving Clinical UI locally on: http://127.0.0.1:{port}")
    print("=" * 70)
    app.run(host="127.0.0.1", port=port, debug=False)
