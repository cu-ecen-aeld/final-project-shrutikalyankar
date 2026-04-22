import numpy as np
import tempfile
import os
import wave
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# --- Config ---
TARGET_RATE = 16000   
MIN_CONFIDENCE = 0.25
LOCATION_LAT = 40.0
LOCATION_LON = -105.0

print("Loading BirdNET model...")
_analyzer = Analyzer()
print("Model ready.")

#takes a 1 second audio window(16k samples) from the audio queue
def run_inference(audio_window):
    min_samples = TARGET_RATE * 3           #BirdNet needs 3sec audio min
    if len(audio_window) < min_samples:
        repeats = int(np.ceil(min_samples / len(audio_window)))
        audio_window = np.tile(audio_window, repeats)[:min_samples]  #np.tile repeats the array. 
                                            #so 1 sec call gets repeated thrice
    tmp_path = tempfile.mktemp(suffix=".wav")

    #upsample from 16kHz to 48kHz by repeating samples 3 times
    try:
        audio_48k = np.repeat(audio_window, 3)
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(audio_48k.astype(np.int16).tobytes())

        print(f"[DEBUG] max_amplitude={np.max(np.abs(audio_window))}, samples={len(audio_window)}")
        #sets location so sets up inference coordinates
        recording = Recording(
            _analyzer,
            tmp_path,
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            min_conf=MIN_CONFIDENCE,
        )
        recording.analyze()  #now run the birdNet inference. 
        #TFLite model runs acceleration pack here. 
        #internally, birdnetlib reads the file, splits it into 3 sec chunks, extracts spectrograms
        #and runs them through the neural network

        # DEBUG
        print(f"[DEBUG] detections={len(recording.detections)}")
        for d in recording.detections:
            print(f"[DEBUG] {d['common_name']}: {d['confidence']:.2f}")


        results = [
            (d["common_name"], d["scientific_name"], d["confidence"])
            for d in recording.detections
        ]
        return results

    finally:  #delete temp wav files
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_top_detection(audio_window):
    results = run_inference(audio_window)
    if not results:
        return None
    top = sorted(results, key=lambda x: x[2], reverse=True)[0]
    return f"{top[0]}:{top[2]:.2f}"