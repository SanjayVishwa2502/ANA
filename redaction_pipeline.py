from tier2_nlp.redaction_pipeline import run_redaction

if __name__ == "__main__":
    transcript = "Patient Jonathan Harker, MRN48291. At 1400 hours, the patient became acutely diaphoretic and techipnic, complaining of severe retro-sternal chest pain radiating to theleft jaw. Vitals showed sinus tachycardia at 135 beats per minute, blood pressure 165 over 95, and SPO2 dropping to 89% on room air. I immediately administered 0.4 milligrams of sublingual nitroglycerin and started two liters of oxygen via nasal cannula, followed by a 5,000 unit heparin bolus. Stat ECG shows ST segment elevation in leads V2 through V4."
    
    result = run_redaction(transcript)
    print("\n--- De-identified Text (MRN preserved for routing) ---")
    print(result["scrubbed_text"])