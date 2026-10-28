from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
import warnings
warnings.filterwarnings("ignore")

def run_redaction(text):
    print("Loading Hybrid Redaction Engine with Custom Regex...")
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    
    # Custom Regex Recognizer for Medical Record Numbers (MRN)
    mrn_pattern = Pattern(name="mrn_regex", regex=r"MRN\d+", score=0.9)
    mrn_recognizer = PatternRecognizer(supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern])
    analyzer.registry.add_recognizer(mrn_recognizer)
    
    # Analyze text for both built-in PERSON entities and our custom MRN entity
    results = analyzer.analyze(text=text, entities=["PERSON", "MEDICAL_RECORD_NUMBER"], language='en')
    
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    
    print("\n--- Fully Redacted Text ---")
    print(anonymized_result.text)
    print("---------------------------")

if __name__ == "__main__":
    transcript = "Patient Jonathan Harker, MRN48291. At 1400 hours, the patient became acutely diaphoretic and techipnic, complaining of severe retro-sternal chest pain radiating to theleft jaw. Vitals showed sinus tachycardia at 135 beats per minute, blood pressure 165 over 95, and SPO2 dropping to 89% on room air. I immediately administered 0.4 milligrams of sublingual nitroglycerin and started two liters of oxygen via nasal cannula, followed by a 5,000 unit heparin bolus. Stat ECG shows ST segment elevation in leads V2 through V4."
    
    run_redaction(transcript)