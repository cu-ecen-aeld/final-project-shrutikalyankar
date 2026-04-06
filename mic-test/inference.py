import numpy as np
import tempfile
import soundfile as sf
import os
from datetime import date
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# --- Config ---
TARGET_RATE = 16000
MIN_CONFIDENCE = 0.70       # only report detections above this
LOCATION_LAT = 40.0         # change to your actual location
LOCATION_LON = -105.0       # change to your actual location
RECORD_DATE = date.today()  # uses today's date for species filtering

# Load model once at startup — expensive operation, do NOT reload per window
print("Loading BirdNET model...")
_analyzer = Analyzer()
print("Model ready.")


def run_inference(audio_window):
    """
    Takes a 1-second int16 numpy array at 16kHz.
    Returns a list of (species_name, confidence) tuples above MIN_CONFIDENCE,
    or an empty list if nothing detected.
    """
    # BirdNET needs at least 3 seconds of audio — pad the 1s window to 3s
    padded = np.tile(audio_window, 3)  # repeat 3x → 48000 samples = 3s

    # Write to a temp wav file — birdnetlib works on files, not raw arrays
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        sf.write(tmp_path, padded.astype(np.float32) / 32767.0, TARGET_RATE)

        recording = Recording(
            _analyzer,
            tmp_path,
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            date=RECORD_DATE,
            min_conf=MIN_CONFIDENCE,
        )
        recording.analyze()

        results = [
            (d["common_name"], d["scientific_name"], d["confidence"])
            for d in recording.detections
        ]
        return results

    finally:
        os.unlink(tmp_path)  # always clean up temp file


def get_top_detection(audio_window):
    """
    Returns the single highest-confidence detection as a string
    formatted for writing to /dev/birdclassifier.
    Returns None if nothing detected above threshold.
    Format: "common_name:confidence"  e.g. "Common Raven:0.98"
    """
    results = run_inference(audio_window)

    if not results:
        return None

    # Sort by confidence, take the top result
    top = sorted(results, key=lambda x: x[2], reverse=True)[0]
    common_name, scientific_name, confidence = top

    return f"{common_name}:{confidence:.2f}"