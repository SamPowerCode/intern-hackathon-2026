#!/usr/bin/env python3
"""Generates mittens_cam.png for Stage 4.
Hides three codes in the LSB of the R channel at every STEP-th pixel.
Prints the three hidden codes to stdout.
"""
import random
from pathlib import Path
from PIL import Image

random.seed(99)

OUT  = Path(__file__).parent / "mittens_cam.png"
SIZE = (400, 300)   # width x height
STEP = 1            # every pixel

CODES = [4821, 8803, 5142]   # the three hidden answers
MESSAGE = ",".join(str(c) for c in CODES) + "\x00"  # null-terminated
BITS = []
for ch in MESSAGE:
    byte = ord(ch)
    for bit_pos in range(7, -1, -1):
        BITS.append((byte >> bit_pos) & 1)

# Build base image: dark grey security-camera look
pixels = []
for y in range(SIZE[1]):
    for x in range(SIZE[0]):
        cx = abs(x - SIZE[0] // 2) / (SIZE[0] // 2)
        cy = abs(y - SIZE[1] // 2) / (SIZE[1] // 2)
        vignette = max(0, 1 - (cx**2 + cy**2) * 0.6)
        base = int(random.gauss(80, 12) * vignette)
        base = max(0, min(255, base))
        pixels.append((base, base, base))

# Embed bits into LSB of R channel at every STEP-th pixel
flat_indices = list(range(0, SIZE[0] * SIZE[1], STEP))
assert len(BITS) <= len(flat_indices), "Image too small for message"

pixel_list = list(pixels)
for i, bit in enumerate(BITS):
    idx = flat_indices[i]
    r, g, b = pixel_list[idx]
    r = (r & 0xFE) | bit   # set LSB
    pixel_list[idx] = (r, g, b)

# Add timestamp overlay FIRST, then embed bits so overlay doesn't clobber them
img = Image.new("RGB", SIZE)
img.putdata(pixel_list)

try:
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SIZE[0], 16], fill=(0, 0, 0))
    draw.text((4, 2), "CAM-1  VAULT-9 SECURITY  2024-03-12 09:14:22", fill=(0, 200, 0))
    draw.rectangle([0, SIZE[1]-16, SIZE[0], SIZE[1]], fill=(0, 0, 0))
    draw.text((4, SIZE[1]-14), "REC  ●  MOTION DETECTED", fill=(200, 0, 0))
except Exception:
    pass  # overlay is cosmetic only

# Re-embed bits AFTER overlay so draw operations don't overwrite the hidden data
pixel_list = list(img.getdata())
for i, bit in enumerate(BITS):
    idx = flat_indices[i]
    r, g, b = pixel_list[idx]
    r = (r & 0xFE) | bit   # set LSB
    pixel_list[idx] = (r, g, b)
img.putdata(pixel_list)

img.save(OUT)
print(CODES[0])
print(CODES[1])
print(CODES[2])
