import numpy as np

# --- Config ---
TARGET_RATE = 16000
N_MELS = 64
N_FFT = 1024
HOP_LENGTH = 512
F_MIN = 150
F_MAX = 8000


def extract_melspectrogram(audio_window):
    """
    Takes a 1-second int16 audio window (16000 samples)
    Returns a normalized mel-spectrogram as a float32 numpy array
    Shape: (64, 32)
    Uses numpy only — no librosa dependency
    """
    audio_float = audio_window.astype(np.float32) / 32767.0

    # STFT using numpy
    frames = []
    for i in range(0, len(audio_float) - N_FFT, HOP_LENGTH):
        frame = audio_float[i:i + N_FFT] * np.hanning(N_FFT)
        frames.append(np.abs(np.fft.rfft(frame)) ** 2)

    if not frames:
        return np.zeros((N_MELS, 32), dtype=np.float32)

    power_spec = np.array(frames).T

    # Mel filterbank
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / TARGET_RATE)
    mel_min = 2595 * np.log10(1 + F_MIN / 700)
    mel_max = 2595 * np.log10(1 + F_MAX / 700)
    mel_points = np.linspace(mel_min, mel_max, N_MELS + 2)
    hz_points = 700 * (10 ** (mel_points / 2595) - 1)

    filterbank = np.zeros((N_MELS, len(freqs)))
    for m in range(1, N_MELS + 1):
        f_left = hz_points[m - 1]
        f_center = hz_points[m]
        f_right = hz_points[m + 1]
        for k, f in enumerate(freqs):
            if f_left <= f <= f_center:
                filterbank[m - 1, k] = (f - f_left) / (f_center - f_left)
            elif f_center < f <= f_right:
                filterbank[m - 1, k] = (f_right - f) / (f_right - f_center)

    mel_spec = np.dot(filterbank, power_spec)
    mel_spec_db = 10 * np.log10(mel_spec + 1e-10)

    # Normalize to [0, 1]
    mel_min_val = mel_spec_db.min()
    mel_max_val = mel_spec_db.max()
    if mel_max_val - mel_min_val > 0:
        mel_spec_norm = (mel_spec_db - mel_min_val) / (mel_max_val - mel_min_val)
    else:
        mel_spec_norm = np.zeros_like(mel_spec_db)

    # Resize to (64, 32)
    target_frames = 32
    if mel_spec_norm.shape[1] >= target_frames:
        mel_spec_norm = mel_spec_norm[:, :target_frames]
    else:
        pad = target_frames - mel_spec_norm.shape[1]
        mel_spec_norm = np.pad(mel_spec_norm, ((0, 0), (0, pad)))

    return mel_spec_norm.astype(np.float32)


def get_input_shape():
    dummy = np.zeros(TARGET_RATE, dtype=np.int16)
    result = extract_melspectrogram(dummy)
    return result.shape