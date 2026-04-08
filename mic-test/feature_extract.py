import numpy as np
import librosa

# --- Config ---
TARGET_RATE = 16000
N_MELS = 64            # number of mel frequency bins
N_FFT = 1024           # FFT window size
HOP_LENGTH = 512       # FFT hop size
F_MIN = 150            # min frequency (Hz) - bird calls rarely below this
F_MAX = 8000           # max frequency (Hz) - Nyquist limit for 16kHz
DURATION = 1.0         # seconds per window


def extract_melspectrogram(audio_window):
    """
    Takes a 1-second int16 audio window (16000 samples)
    Returns a normalized mel-spectrogram as a float32 numpy array
    Shape: (64, 32) — 64 mel bins x 32 time frames
    """
    # Convert int16 to float32 in range [-1.0, 1.0]
    audio_float = audio_window.astype(np.float32) / 32767.0

    # Compute mel-spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=audio_float,
        sr=TARGET_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        fmin=F_MIN,
        fmax=F_MAX
    )

    # Convert power to decibels (log scale)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Normalize to [0, 1]
    mel_min = mel_spec_db.min()
    mel_max = mel_spec_db.max()

    if mel_max - mel_min > 0:
        mel_spec_norm = (mel_spec_db - mel_min) / (mel_max - mel_min)
    else:
        mel_spec_norm = np.zeros_like(mel_spec_db)

    return mel_spec_norm.astype(np.float32)


def get_input_shape():
    """Returns the shape of the mel-spectrogram output."""
    dummy = np.zeros(TARGET_RATE, dtype=np.int16)
    result = extract_melspectrogram(dummy)
    return result.shape