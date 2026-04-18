import os
import sys
import time

# Configuration based on your requirements
DEVICE_PATH = "/dev/birdclassifier"
CONFIDENCE_THRESHOLD = 0.80

def trigger_hardware(species, confidence):
    """
    Communicates with the AviAlert kernel driver.
    Format: 'species:confidence'
    """
    try:
        # Open the device node (Character Driver)
        with open(DEVICE_PATH, 'w') as bird_dev:
            # Create the payload (e.g., "robin:0.94")
            payload = f"{species}:{confidence:.2f}"
            
            # Write triggers the bird_write function in your C code
            bird_dev.write(payload)
            bird_dev.flush()  # Ensure data is sent immediately
            
        # Log to STDOUT as per DoD
        print(f"STDOUT: Detected {species} with {confidence:.2%}")
        print(f"[HW] Hardware pulse triggered for {species}")
        
    except FileNotFoundError:
        print(f"ERROR: {DEVICE_PATH} not found. Is the module loaded?")
    except PermissionError:
        print(f"ERROR: Permission denied. Run as root or update udev rules.")
    except Exception as e:
        print(f"ERROR: Failed to communicate with driver: {e}")

def main_pipeline_loop(inference_result):
    """
    Mock function representing where your ML model output is handled.
    inference_result: list of tuples (label, score)
    """
    for label, score in inference_result:
        # DoD requirement: Check confidence threshold
        if score >= CONFIDENCE_THRESHOLD:
            trigger_hardware(label, score)
        else:
            print(f"Inference: {label} ({score:.2f}) below threshold. No pulse.")

# --- Test Scenario ---
if __name__ == "__main__":
    # Simulate a detection of a Robin with 94% confidence
    test_results = [("robin", 0.94)]
    main_pipeline_loop(test_results)