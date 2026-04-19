import sounddevice as sd
import numpy as np
import queue
import threading

# --- Config ---
NATIVE_RATE = 48000       # mic's hardware rate
TARGET_RATE = 16000       # BirdNET expects 16kHz
DOWNSAMPLE_FACTOR = 3     # 48000 / 16000
WINDOW_SIZE = TARGET_RATE # 1 second of audio at 16kHz = 16000 samples
HOP_SIZE = WINDOW_SIZE // 2  # 50% overlap = 0.5s hop

# Thread-safe queue — capture thread puts windows, inference thread gets them
audio_queue = queue.Queue(maxsize=3)

# Internal buffer to accumulate samples before windowing
_buffer = np.array([], dtype=np.int16)
_buffer_lock = threading.Lock()

def _audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status)

    mono = indata[:, 0] if indata.ndim > 1 else indata[:, 0]
    mono_int16 = (mono * 32767).astype(np.int16)
    downsampled = mono_int16[::DOWNSAMPLE_FACTOR]

    global _buffer
    with _buffer_lock:
        _buffer = np.concatenate([_buffer, downsampled])

        while len(_buffer) >= WINDOW_SIZE:
            window = _buffer[:WINDOW_SIZE].copy()
            # Drop oldest if queue is full instead of blocking
            if audio_queue.full():
                try:
                    audio_queue.get_nowait()  # discard oldest
                except queue.Empty:
                    pass
            audio_queue.put_nowait(window)
            _buffer = _buffer[HOP_SIZE:]


def start_capture():
    """
    Opens the sounddevice input stream and starts capturing.
    Returns the stream object — keep a reference to it.
    """
    # Find the USB mic
    devices = sd.query_devices()
    mic_index = None
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0 and 'USB' in d['name']:
            mic_index = i
            break

    if mic_index is None:
        print("USB mic not found. Available devices:")
        print(sd.query_devices())
        return None

    print(f"Using device {mic_index}: {devices[mic_index]['name']}")
    print(f"Capturing at {NATIVE_RATE}Hz, downsampling to {TARGET_RATE}Hz")
    print(f"Window: {WINDOW_SIZE} samples (1s), Hop: {HOP_SIZE} samples (0.5s)")

    stream = sd.InputStream(
        device=mic_index,
        channels=1,
        samplerate=NATIVE_RATE,       # capture at 48kHz
        dtype='float32',              # sounddevice default
        blocksize=8192,               # chunk size per callback
        callback=_audio_callback
    )

    stream.start()
    return stream