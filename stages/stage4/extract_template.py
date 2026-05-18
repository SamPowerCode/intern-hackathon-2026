#!/usr/bin/env python3
"""VAULT-9 Surveillance Override Extractor
The engineer's notes say: 'R channel, every Nth pixel, starting at pixel 0.'
Fill in the value of STEP below, then run this script.
"""
from PIL import Image

STEP = ???   # <-- fill this in from the problem description

img = Image.open("mittens_cam.png").convert("RGB")
pixels = list(img.getdata())

# Collect LSBs from the R channel at every STEP-th pixel
bits = [pixels[i][0] & 1 for i in range(0, len(pixels), STEP)]

# Decode bits into a string (8 bits per character, MSB first)
chars = []
for i in range(0, len(bits) - 7, 8):
    byte = 0
    for b in bits[i:i+8]:
        byte = (byte << 1) | b
    if byte == 0:
        break
    chars.append(chr(byte))

hidden = "".join(chars)
print("Hidden data:", hidden)

# The hidden data contains three comma-separated codes
codes = hidden.split(",")
print(f"Override code 1: {codes[0]}")
print(f"Override code 2: {codes[1]}")
print(f"Override code 3: {codes[2]}")
