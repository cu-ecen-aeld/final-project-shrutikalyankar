import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from feature_extract import extract_melspectrogram
from audio_capture import start_capture, audio_queue
from inference import get_top_detection
import queue
import threading
import time

# --- Config ---
N_MELS = 64
HISTORY_WINDOWS = 20       # how many windows to show at once
DETECTION_DISPLAY_TIME = 3  # seconds to show detection label

# --- Shared state ---
spec_history = np.zeros((N_MELS, HISTORY_WINDOWS))
current_detection = None
detection_timestamp = 0
_running = True


def inference_thread_fn():
    global current_detection, detection_timestamp

    while _running:
        try:
            window = audio_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        # Update spectrogram history
        mel = extract_melspectrogram(window)
        global spec_history
        spec_history = np.roll(spec_history, -1, axis=1)
        spec_history[:, -1] = mel.mean(axis=1)

        # Run inference
        result = get_top_detection(window)
        if result:
            current_detection = result
            detection_timestamp = time.time()
            print(f"[DETECTION] {result}")


def main():
    global _running

    # Start audio capture
    stream = start_capture()
    if stream is None:
        print("ERROR: Could not start capture")
        return

    # Start inference thread
    inf_thread = threading.Thread(target=inference_thread_fn, daemon=True)
    inf_thread.start()

    # Set up matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    img = ax.imshow(
        spec_history,
        aspect='auto',
        origin='lower',
        cmap='inferno',
        vmin=0,
        vmax=1,
        interpolation='nearest'
    )

    ax.set_xlabel('Time (windows)', color='white')
    ax.set_ylabel('Mel frequency bin', color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('white')

    detection_text = ax.text(
        0.5, 0.92, '',
        transform=ax.transAxes,
        ha='center', va='top',
        fontsize=16, fontweight='bold',
        color='#00ff88',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e', edgecolor='#00ff88')
    )

    title_text = ax.set_title(
        'AviAlert - Live Mel Spectrogram',
        color='white', fontsize=13
    )

    plt.tight_layout()

    def update(frame):
        img.set_data(spec_history)

        # Show detection label for DETECTION_DISPLAY_TIME seconds
        if current_detection and (time.time() - detection_timestamp) < DETECTION_DISPLAY_TIME:
            species, conf = current_detection.split(":")
            detection_text.set_text(f"{species}  {float(conf)*100:.0f}%")
        else:
            detection_text.set_text('')

        return [img, detection_text]

    ani = animation.FuncAnimation(
        fig, update,
        interval=500,        # update every 500ms
        blit=True,
        cache_frame_data=False
    )

    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        stream.stop()
        stream.close()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()