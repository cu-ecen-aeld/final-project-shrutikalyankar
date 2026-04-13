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


def run_inference(audio_window):
    min_samples = TARGET_RATE * 3
    if len(audio_window) < min_samples:
        repeats = int(np.ceil(min_samples / len(audio_window)))
        audio_window = np.tile(audio_window, repeats)[:min_samples]

    tmp_path = tempfile.mktemp(suffix=".wav")

    try:
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(TARGET_RATE)
            wf.writeframes(audio_window.astype(np.int16).tobytes())

        print(f"[DEBUG] max_amplitude={np.max(np.abs(audio_window))}, samples={len(audio_window)}")

        recording = Recording(
            _analyzer,
            tmp_path,
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            min_conf=MIN_CONFIDENCE,
        )
        recording.analyze()

        # DEBUG
        print(f"[DEBUG] detections={len(recording.detections)}")
        for d in recording.detections:
            print(f"[DEBUG] {d['common_name']}: {d['confidence']:.2f}")


        results = [
            (d["common_name"], d["scientific_name"], d["confidence"])
            for d in recording.detections
        ]
        return results

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_top_detection(audio_window):
    results = run_inference(audio_window)
    if not results:
        return None
    top = sorted(results, key=lambda x: x[2], reverse=True)[0]
    return f"{top[0]}:{top[2]:.2f}"