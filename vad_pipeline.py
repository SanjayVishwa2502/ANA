import torch
import warnings
warnings.filterwarnings("ignore")

def run_vad(file_path):
    print("Loading Silero-VAD model...")
    # Load the model directly from the PyTorch Hub
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=False,
                                  trust_repo=True)
    
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    
    print(f"Reading '{file_path}'...")
    # Silero VAD processes audio best at a 16000 Hz sampling rate
    wav = read_audio(file_path, sampling_rate=16000)
    
    print("Analyzing audio for speech...")
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
    
    print("\n--- Speech Segments Detected ---")
    for segment in speech_timestamps:
        print(f"Speech found from sample {segment['start']} to {segment['end']}")
        
    if speech_timestamps:
        output_file = 'segmented_audio.wav'
        # Collects the chunks of speech and saves them into a new file
        save_audio(output_file, collect_chunks(speech_timestamps, wav), sampling_rate=16000)
        print(f"\nSuccess! Saved filtered speech to '{output_file}'")
    else:
        print("\nNo speech detected in the audio file.")

if __name__ == "__main__":
    # Ensure your recorded audio file matches this name
    run_vad("mock_audio.wav")