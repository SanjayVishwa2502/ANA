import json
from langchain_core.tools import tool

# 1. Initialize Mock Smart-on-FHIR REST API Database (Synthetic Records)
MOCK_FHIR_DB = {
    "MRN48291": {
        "patient_name": "Jonathan Harker",
        "active_medications": ["Nitroglycerin", "Heparin"],
        "recent_labs": "Stat ECG shows ST-segment elevation",
        "allergies": ["Penicillin"]
    }
}

# 2. Define Standardized MCP Tools for the LangGraph Agent
@tool
def lookup_patient_history(patient_id: str) -> str:
    """Fetches historical EHR data from the Mock Smart-on-FHIR API."""
    print(f"\n[MCP Tool Execution]: Fetching FHIR records for Patient ID: {patient_id}...")
    record = MOCK_FHIR_DB.get(patient_id)
    if record:
        return json.dumps(record, indent=2)
    return "Error: Patient record not found in Mock EHR."

@tool
def check_medication_interaction(medication: str) -> str:
    """Checks for adverse interactions for a given medication."""
    print(f"\n[MCP Tool Execution]: Running safety check for '{medication}'...")
    # Mocking a safety check response
    return f"Safety Verified: No severe contraindications found for {medication}."

def run_mcp_tool_test():
    print("Initializing MCP Standardized Tools and Mock FHIR API...")
    
    # Test Agent invoking Tool 1: Lookup History
    history_response = lookup_patient_history.invoke({"patient_id": "MRN48291"})
    print(f"--- Mock FHIR API Response ---\n{history_response}")
    
    # Test Agent invoking Tool 2: Check Interaction
    interaction_response = check_medication_interaction.invoke({"medication": "Heparin"})
    print(f"\n--- Interaction Engine Response ---\n{interaction_response}")

if __name__ == "__main__":
    run_mcp_tool_test()