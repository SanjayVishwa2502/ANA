from flask import Flask, jsonify, request

app = Flask(__name__)

# 1. Synthetic FHIR Patient Database 
SYNTHETIC_EHR = {
    "MRN48291": {
        "resourceType": "Patient",
        "id": "MRN48291",
        "name": [{"use": "official", "text": "Jonathan Harker"}],
        "clinicalStatus": "active",
        "active_medications": ["Nitroglycerin", "Heparin"],
        "allergies": ["Penicillin"],
        "recent_vitals": {
            "blood_pressure": "165/95",
            "heart_rate": 135,
            "spo2": "89%"
        }
    }
}

# 2. FHIR Endpoint: Lookup Patient History
@app.route('/fhir/Patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    print(f"\n[EHR Server] -> GET request received for Patient ID: {patient_id}")
    record = SYNTHETIC_EHR.get(patient_id)
    
    if record:
        return jsonify(record), 200
    return jsonify({"error": "Patient not found in Mock EHR"}), 404

# 3. FHIR Endpoint: Check Medication Interaction
@app.route('/fhir/MedicationInteraction', methods=['POST'])
def check_interaction():
    data = request.json
    medication = data.get("medication", "Unknown")
    print(f"\n[EHR Server] -> POST request received to check safety for: {medication}")
    
    # Mocking the interaction engine response
    return jsonify({
        "status": "Safety Verified",
        "details": f"No severe contraindications found for {medication}."
    }), 200

if __name__ == '__main__':
    print("===================================================")
    print("🏥 Starting Mock Smart-on-FHIR REST API...")
    print("🌐 Server running locally at: http://127.0.0.1:5000")
    print("===================================================")
    # Run the server on port 5000
    app.run(port=5001, debug=False)