# Overview
### Goal
Create an embedded system that identifies specific bird calls in real-time and triggers hardware responses based on the detected species.

### Motivation
To demonstrate low-latency audio processing on an optimized, custom Linux distribution using Buildroot, combining kernel-space driver development with user-space ML inference on a resource-constrained ARM platform.

### Final Videos
[Watch Shruti's Video](https://drive.google.com/file/d/1HdYt9Z5GcIJgI08m132sGkWdAlbMQzLx/view?usp=drive_link)

[Watch Atharv's Video](https://drive.google.com/file/d/1GPHnHT2XEuXlE-AN1friiBOBo7CzuzT1/view?usp=sharing)  

### Project Description
A custom-built Linux distribution (Buildroot) that listens for bird calls using ALSA, extracts mel-spectrogram features, runs inference via a TFLite model (BirdNET), and triggers species-specific hardware alerts via a custom kernel character driver (/dev/birdclassifier).

### Challenges
Managing audio capture latency, optimizing mel-spectrogram and TFLite inference performance on an embedded ARM CPU, and ensuring precise synchronization between kernel-space hardware alerts and user-space audio processing.

### Block Diagram:
<img src="https://github.com/cu-ecen-aeld/final-project-shrutikalyankar/blob/main/Supporting_Files/Wiki/Block_Diagram.png" alt="Flowchart" width="500"/>

# Target Build System
**Buildroot**

# Hardware Platform
**Platform:** Raspberry Pi 4 (1 GB RAM minimum)  

**Buildroot Support:** The Raspberry Pi 4 is natively supported in Buildroot via the raspberrypi4_64_defconfig configuration targeting aarch64.  

### Hardware Requirements:
- Raspberry Pi 4 (borrowed from department — 1 unit)
- USB microphone module (capable of 16 kHz, 16-bit mono PCM capture via ALSA)
- LEDs and/or LCD for hardware alert output (connected via GPIO)
- MicroSD card (16 GB+) for the Buildroot image


# Open Source Projects Used
TBD: Mention any open source project content you intend to use with the project, beyond the base platform buildroot/yocto packages already used in assignments.

| **Project** | **Purpose** | **License** |
|-----------| ----- |-------------------|
| **[BirdNET-Analyzer (TFLite export)](https://github.com/birdnet-team/BirdNET-Lite.git)** | Pre-trained bird species classification model | MIT |
| **[TensorFlow Lite runtime](https://pypi.org/project/tflite-runtime/)** | On-device ML inference for ARM | Apache 2.0 |
| **[librosa (or KissFFT)](https://librosa.org/doc/main/index.html)** | Mel-spectrogram / MFCC feature extraction | ISC / BSD |
| **[ALSA (libasound)](https://github.com/alsa-project/alsa-lib)** | Audio capture from USB microphone | LGPL |
| **[Xeno-canto recordings](https://xeno-canto.org/)** | Test audio clips for accuracy evaluation | CC BY-SA |
| **[Buildroot](https://buildroot.org/)** | Automated tool for generating a custom Linux image | GPL-v2 |

# Previously Discussed Content
**We will be using a kernel character driver (aesdchar as a structural reference) adapted from prior course assignments. The driver (/dev/birdclassifier) will:**
- Accept write() calls from user space containing a species result string (e.g. "robin:0.94")
- Respond to the write by asserting a GPIO output (LED/buzzer) via gpiod_set_value()
- Support ioctl and/or wait_event so a separate monitor process can block on read() and be woken when a new classification result arrives
- Be registered via register_chrdev() and expose standard file_operations (open, read, write, ioctl, release)


# New Content
### Content discussed in class but not included in previous assignments:
- GPIO control from kernel space using the gpiod API (gpio_request, gpiod_set_value, gpio_free)
- Kernel wait_queue_head_t and wait_event_interruptible for blocking user-space reads

### Content not yet discussed in class:
- ALSA (Advanced Linux Sound Architecture): Linux kernel subsystem providing the PCM audio capture API used to stream microphone input. We will use libasound (user-space ALSA API) to open a PCM capture device, configure 16 kHz / 16-bit / mono parameters, and read audio frames into a ring buffer.
- Mel-spectrogram feature extraction: Converting raw PCM audio windows into a 2D frequency-vs-time representation using a filterbank of mel-scaled frequency bins. This is the input format expected by BirdNET and most pre-trained audio classifiers.
- TensorFlow Lite inference on ARM: Running a quantized .tflite model on the RPi 4 CPU using the TFLite C++ runtime, with the XNNPACK delegate enabled for 2–5× acceleration on ARM NEON SIMD units.
- Real-time audio pipeline architecture: Designing a multi-threaded capture-and-process pipeline with a lock-protected queue separating the ALSA capture thread from the inference thread, to prevent buffer underruns under inference load.


# Shared Material
N/A — No portions of this project are leveraged from other coursework or from previous semesters by ourselves or others, beyond the aesdchar kernel driver used as a structural reference (as noted under Previously Discussed Content).

# Source Code Organization
**Buildroot Repository:** https://github.com/cu-ecen-aeld/final-project-ZatharV  

**Application Repository:** https://github.com/cu-ecen-aeld/final-project-shrutikalyankar

We request 2 repositories total: one for the Buildroot fork and one for the application code above.

# Group Overview

## Team project members:

This project is being completed by a group of two members:

| **Team Member**       | **High-Level Role**       |
|------------------------|------------------------------------------------------------------------------------|
| **Atharv More**      | Kernel driver development, Buildroot image configuration, GPIO hardware integration, system bring-up |
| **Shruti kalyankar**   | Audio capture pipeline, mel-spectrogram feature extraction, TFLite inference integration, accuracy testing |

Both members share responsibility for end-to-end integration, latency tuning, and demo preparation.

**Contact**:  
Atharv More – *atharv.more@colorado.edu*  
Shruti kalyankar – *Shruti.Kalyankar@colorado.edu*

# Schedule Page
https://github.com/users/shrutikalyankar/projects/1/views/1
