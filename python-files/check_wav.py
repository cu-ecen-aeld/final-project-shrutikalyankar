import wave

with wave.open("final_test.wav", "rb") as f:
    print("Channels    :", f.getnchannels())
    print("Sample rate :", f.getframerate(), "Hz")
    print("Bit depth   :", f.getsampwidth() * 8, "bit")
    print("Frames      :", f.getnframes())
    print("Duration    :", round(f.getnframes() / f.getframerate(), 2), "seconds")