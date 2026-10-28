"""
Tier 4: Mock Smart-on-FHIR REST API Server (Flask)
Ambient Nursing Ally (ANA) Project
"""

import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# 1. Synthetic FHIR Patient Database 
SYNTHETIC_EHR = {
    "MRN48291": {
        "resourceType": "Patient",
        "id": "MRN48291",
        "name": [{"use": "official", "text": "Jonathan Harker"}],
        "gender": "male",
        "birthDate": "1978-04-12",
        "clinicalStatus": "active",
        "ward": "Cardiology Inpatient Ward 4B",
        "bed": "Bed-412",
        "active_medications": ["Nitroglycerin 0.4 mg SL", "Heparin 5000 units IV bolus", "Aspirin 81 mg"],
        "allergies": ["Penicillin (Severe: Anaphylaxis)"],
        "recent_vitals": {
            "blood_pressure": "165/95",
            "heart_rate": 135,
            "spo2": "89%"
        },
        "recent_labs": [
            "Stat ECG: ST-segment elevation in leads V2-V4 (Anterior STEMI)"
        ]
    },
    "MRN99104": {
        "resourceType": "Patient",
        "id": "MRN99104",
        "name": [{"use": "official", "text": "Lucy Westenra"}],
        "gender": "female",
        "clinicalStatus": "active",
        "ward": "General Medical Ward 2A",
        "active_medications": ["Ferrous Sulfate 325 mg oral TID"],
        "allergies": ["Latex"],
        "recent_vitals": {
            "blood_pressure": "110/70",
            "heart_rate": 88,
            "spo2": "98%"
        }
    }
}

# 2. FHIR Endpoint: Lookup Patient History
@app.route('/fhir/Patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    clean_id = patient_id.strip().upper()
    print(f"\n[Mock FHIR Server] -> GET /fhir/Patient/{clean_id}")
    record = SYNTHETIC_EHR.get(clean_id)
    if record:
        return jsonify(record), 200
    return jsonify({"error": f"Patient '{clean_id}' not found in Mock EHR"}), 404

# 3. FHIR Endpoint: Check Medication Interaction
@app.route('/fhir/MedicationInteraction', methods=['POST'])
def check_interaction():
    data = request.get_json(force=True, silent=True) or {}
    medication = data.get("medication", "Unknown")
    print(f"\n[Mock FHIR Server] -> POST /fhir/MedicationInteraction for '{medication}'")
    
    med_lower = medication.lower()
    if "penicillin" in med_lower:
        return jsonify({
            "status": "Contraindication Alert",
            "details": "Severe documented allergy: Penicillin triggers anaphylactic shock."
        }), 200
        
    return jsonify({
        "status": "Safety Verified",
        "details": f"No adverse contraindications found for {medication} in active EHR record."
    }), 200

def start_server(port: int = 5001):
    print("===================================================")
    print("🏥 Starting Mock Smart-on-FHIR REST API Server...")
    print(f"🌐 Server running locally at: http://127.0.0.1:{port}")
    print("===================================================")
    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    start_server(5001)
