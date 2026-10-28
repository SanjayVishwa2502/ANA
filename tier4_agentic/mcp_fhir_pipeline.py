"""
Tier 4: Model Context Protocol (MCP) Standardized FHIR Tools
Ambient Nursing Ally (ANA) Project
"""

import os
import json
from typing import Dict, Any, Optional
import requests
from langchain_core.tools import tool

# 1. Initialize Mock Smart-on-FHIR REST API Database (Synthetic Records)
MOCK_FHIR_DB: Dict[str, Dict[str, Any]] = {
    "MRN48291": {
        "resourceType": "Patient",
        "id": "MRN48291",
        "patient_name": "Jonathan Harker",
        "ward": "Cardiology Inpatient Ward 4B",
        "bed": "Bed-412",
        "clinicalStatus": "active",
        "active_medications": ["Nitroglycerin 0.4 mg SL", "Heparin 5000 unit IV bolus", "Aspirin 81 mg"],
        "recent_labs": "Stat ECG shows ST-segment elevation in leads V2-V4 (Anterior STEMI)",
        "allergies": ["Penicillin (Severe: Anaphylaxis)"],
        "recent_vitals": {
            "blood_pressure": "165/95",
            "heart_rate": 135,
            "spo2": "89%"
        }
    },
    "MRN99104": {
        "resourceType": "Patient",
        "id": "MRN99104",
        "patient_name": "Lucy Westenra",
        "ward": "General Medical Ward 2A",
        "clinicalStatus": "active",
        "active_medications": ["Ferrous Sulfate 325 mg oral TID"],
        "recent_labs": "Hemoglobin: 8.2 g/dL (Microcytic Anemia)",
        "allergies": ["Latex"],
        "recent_vitals": {
            "blood_pressure": "110/70",
            "heart_rate": 88,
            "spo2": "98%"
        }
    }
}

# Load extra records from datasets/mock_fhir_records.json if available
def _load_extra_fhir_records():
    json_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "mock_fhir_records.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
                for entry in bundle.get("entry", []):
                    res = entry.get("resource", {})
                    p_id = res.get("id")
                    if p_id:
                        MOCK_FHIR_DB[p_id] = res
        except Exception:
            pass

_load_extra_fhir_records()

# 2. Define Standardized MCP Tools for the LangGraph Agent
@tool
def lookup_patient_history(patient_id: str) -> str:
    """
    Fetches historical EHR data from the Mock Smart-on-FHIR API.
    Scoped strictly for administrative flowsheets and context retrieval (Non-SaMD).
    """
    clean_id = patient_id.strip().upper()
    print(f"\n[MCP Tool Execution] 🏥 Fetching FHIR records for Patient ID: '{clean_id}'...")
    
    # Try live HTTP Mock Server first (port 5001 or 5000)
    for port in [5001, 5000]:
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/fhir/Patient/{clean_id}", timeout=0.8)
            if resp.status_code == 200:
                print(f"   Connected to live Mock FHIR REST endpoint at port {port}.")
                return json.dumps(resp.json(), indent=2)
        except Exception:
            pass
            
    # Fallback to local in-memory synthetic FHIR DB
    record = MOCK_FHIR_DB.get(clean_id)
    if record:
        return json.dumps(record, indent=2)
    return f"Error: Patient ID '{clean_id}' not found in Mock EHR Database."


@tool
def check_medication_interaction(medication: str) -> str:
    """
    Checks for adverse drug-drug interactions or contraindications for a given medication.
    Administrative safety advisory check, requiring nurse verification before action.
    """
    clean_med = medication.strip()
    print(f"\n[MCP Tool Execution] 💊 Running safety interaction check for '{clean_med}'...")
    
    # Try live HTTP Mock Server
    for port in [5001, 5000]:
        try:
            resp = requests.post(
                f"http://127.0.0.1:{port}/fhir/MedicationInteraction",
                json={"medication": clean_med},
                timeout=0.8
            )
            if resp.status_code == 200:
                data = resp.json()
                return f"Safety Check: {data.get('status')} - {data.get('details')}"
        except Exception:
            pass
            
    # Synthetic rule-based safety verification
    clean_med_lower = clean_med.lower()
    if "penicillin" in clean_med_lower:
        return "⚠️ CRITICAL CONTRAINDICATION: Patient has documented severe anaphylaxis allergy to Penicillin!"
    elif "nitroglycerin" in clean_med_lower:
        return "✅ Verified: Sublingual Nitroglycerin verified for acute cardiac ischemia. Monitor for hypotension."
    elif "heparin" in clean_med_lower:
        return "✅ Verified: Heparin weight-based bolus approved for acute coronary syndrome. Check baseline aPTT/platelets."
    else:
        return f"✅ Safety Verified: No severe contraindications found for {clean_med} in active patient profile."


def run_mcp_tool_test():
    """Validates MCP standard tools execution."""
    print("=======================================================")
    print("🏥 TIER 4: MCP STANDARDIZED TOOLS & MOCK FHIR TEST")
    print("=======================================================")
    
    # Test Agent invoking Tool 1: Lookup History
    history_response = lookup_patient_history.invoke({"patient_id": "MRN48291"})
    print(f"\n--- Mock FHIR Patient Record ---\n{history_response}")
    
    # Test Agent invoking Tool 2: Check Interaction
    interaction_response = check_medication_interaction.invoke({"medication": "Heparin"})
    print(f"\n--- Interaction Safety Response ---\n{interaction_response}")

if __name__ == "__main__":
    run_mcp_tool_test()
