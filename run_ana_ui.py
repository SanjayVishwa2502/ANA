"""
Ambient Nursing Ally (ANA) — Web UI & Acoustic Console Launcher
Starts the Clinical Inpatient Ward Console for live voice recording,
Silero-VAD acoustic isolation, Whisper ASR, and 5-tier pipeline orchestration.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Windows console cp1252 UTF-8 safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from web_ui.app import app

def main():
    port = int(os.environ.get("PORT", 8080))
    print("\n" + "=" * 76)
    print("🏥  AMBIENT NURSING ALLY (ANA) — CLINICAL CONSOLE & ACOUSTIC INGESTION")
    print("=" * 76)
    print("🎙️  Tier 1 Sound Capture: Live Browser Mic (16kHz PCM WAV) & Audio File Upload")
    print("🧠  Acoustic Perception: Silero-VAD Speech Isolation + Whisper ASR")
    print("🛡️  Clinical NLP & DART : Presidio Hybrid Redactor + DART Note Extraction")
    print("⏸️  HITL Checkpoint     : Cascading Error Isolation (Nurse Single-Click Review)")
    print("🔍  Tier 3 Knowledge    : Hybrid RAG (BM25 + FAISS + RRF + Cross-Encoder)")
    print("🏥  Tier 4 Orchestration: LangGraph MCP Tools + Mock Smart-on-FHIR REST API")
    print("⛓️  Tier 5 Cryptography : SHA-256 Anchoring + Hyperledger Fabric Ledger")
    print("-" * 76)
    print(f"🌐  Open your browser at: http://127.0.0.1:{port}")
    print("=" * 76 + "\n")
    
    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    main()

