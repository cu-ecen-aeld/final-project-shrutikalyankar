import pyaudio
import wave
import numpy as np

RECORD_RATE = 48000        # mic's native rate — keep this
TARGET_RATE = 16000        # what BirdNET needs
DOWNSAMPLE_FACTOR = 3      # 48000 / 16000 = 3
CHUNK = 8192
FORMAT = pyaudio.paInt16
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "test_16k.wav"

audio = pyaudio.PyAudio()

def get_mic():
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            return i, int(info['maxInputChannels'])
    return None, None

device_index, channels = get_mic()

if device_index is None:
    print("Mic not found.")
    exit()

# Stream at 48000 — what the mic actually supports
stream = audio.open(format=FORMAT,
                    channels=channels,
                    rate=RECORD_RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK)

print(f"Recording at {RECORD_RATE}Hz for {RECORD_SECONDS}s... make some noise!")
frames = []

for _ in range(0, int(RECORD_RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    frames.append(data)

print("Done recording. Downsampling to 16000Hz...")

stream.stop_stream()
stream.close()
audio.terminate()

# Convert to numpy, mix to mono if needed, downsample
raw = np.frombuffer(b''.join(frames), dtype=np.int16)
if channels > 1:
    raw = raw.reshape(-1, channels)
    raw = raw.mean(axis=1).astype(np.int16)   # average channels → mono

downsampled = raw[::DOWNSAMPLE_FACTOR]         # every 3rd sample = 16kHz

with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(TARGET_RATE)
    wf.writeframes(downsampled.tobytes())

print(f"Saved as {WAVE_OUTPUT_FILENAME}")
print(f"Copy to Windows and run: python check_wav.py")