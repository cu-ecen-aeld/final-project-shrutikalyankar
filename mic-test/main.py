import threading
import queue
import time
import sys
import signal
from audio_capture import start_capture, audio_queue
from inference import get_top_detection

# --- Config ---
DRIVER_PATH = "/dev/birdclassifier"
CONFIDENCE_THRESHOLD = 0.70
INFERENCE_COOLDOWN = 3.0
USE_DRIVER = True  # Set True when kernel module is loaded

# --- Globals ---
_running = True
_last_detection_time = 0
_last_detection_species = None


def write_to_driver(result_string):
    """
    Writes detection result to kernel character driver.
    Falls back to stdout if driver not available.
    Format: "Common Raven:0.97"
    """
    if not USE_DRIVER:
        print(f"[DRIVER MOCK] Would write: '{result_string}'")
        return

    try:
        with open(DRIVER_PATH, "w") as f:
            f.write(result_string)
        print(f"[DRIVER] Written: '{result_string}'")
    except FileNotFoundError:
        print(f"[ERROR] {DRIVER_PATH} not found - is the kernel module loaded?")
        print(f"[DRIVER MOCK] Would write: '{result_string}'")
    except PermissionError:
        print(f"[ERROR] Permission denied on {DRIVER_PATH} - try sudo")


def inference_thread_fn():
    """
    Pulls audio windows from queue, runs inference,
    writes results to driver. Runs in its own thread.
    """
    global _last_detection_time, _last_detection_species

    print("[INFERENCE] Thread started.")

    while _running:
        try:
            window = audio_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        result = get_top_detection(window)

        if result is None:
            continue

        parts = result.split(":")
        if len(parts) != 2:
            continue

        species = parts[0]
        try:
            confidence = float(parts[1])
        except ValueError:
            continue

        if confidence < CONFIDENCE_THRESHOLD:
            continue

        now = time.time()
        same_species = (species == _last_detection_species)
        within_cooldown = (now - _last_detection_time) < INFERENCE_COOLDOWN

        if same_species and within_cooldown:
            print(f"[COOLDOWN] Suppressing repeat: {result}")
            continue

        _last_detection_time = now
        _last_detection_species = species
        print(f"[DETECTION] {result}")
        write_to_driver(result)

    print("[INFERENCE] Thread stopped.")


def signal_handler(sig, frame):
    global _running
    print("\n[MAIN] Shutting down...")
    _running = False


def main():
    global _running

    print("=" * 50)
    print("  AviAlert - Real-Time Bird Call Classifier")
    print("=" * 50)

    if not USE_DRIVER:
        print("[WARNING] Mock mode - driver writes disabled")
        print("[WARNING] Set USE_DRIVER=True when /dev/birdclassifier exists")

    signal.signal(signal.SIGINT, signal_handler)

    print("[MAIN] Starting audio capture...")
    stream = start_capture()
    if stream is None:
        print("[ERROR] Could not start audio capture. Exiting.")
        sys.exit(1)

    print("[MAIN] Starting inference thread...")
    inf_thread = threading.Thread(target=inference_thread_fn, daemon=True)
    inf_thread.start()

    print("[MAIN] Pipeline running. Press Ctrl+C to stop.")
    print("-" * 50)

    while _running:
        time.sleep(0.5)

    stream.stop()
    stream.close()
    inf_thread.join(timeout=3.0)
    print("[MAIN] Shutdown complete.")


if __name__ == "__main__":
    main()