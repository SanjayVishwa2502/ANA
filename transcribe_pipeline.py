import whisper
import time
import warnings
warnings.filterwarnings("ignore")

def transcribe_audio(file_path):
    print("Loading Whisper 'base' model for initial hardware test...")
    model = whisper.load_model("base") 
    
    print(f"Transcribing '{file_path}'...")
    start_time = time.time()
    
    # fp16=False prevents warnings if running on CPU; your GPU will still accelerate it
    result = model.transcribe(file_path, fp16=False) 
    end_time = time.time()
    
    print("\n--- Transcription Result ---")
    print(result["text"].strip())
    print(f"----------------------------")
    print(f"Time taken: {round(end_time - start_time, 2)} seconds")

if __name__ == "__main__":
    # We are now feeding the CLEANED audio from Step 1.1 into Whisper
    transcribe_audio("segmented_audio.mp3")