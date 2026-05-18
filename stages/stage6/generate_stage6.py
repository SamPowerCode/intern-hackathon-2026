#!/usr/bin/env python3
"""Generates final_lock.py for Stage 6 with embedded encrypted codes."""
import hashlib
from pathlib import Path

OUT = Path(__file__).parent / "final_lock.py"

PASSPHRASE = "Mittens Fluffington III"
CODES = ["OPEN", "1337", "DONE"]   # the three final answers

def xor_encrypt(plaintext: str, key: bytes) -> bytes:
    data = plaintext.encode()
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

key = hashlib.sha256(PASSPHRASE.encode()).digest()
ciphertexts = [xor_encrypt(code, key) for code in CODES]

def to_bytes_literal(b: bytes) -> str:
    return "bytes([" + ", ".join(f"0x{x:02x}" for x in b) + "])"

ct_lines = "\n".join(
    f"_{chr(ord('a') + i)} = {to_bytes_literal(ct)}"
    for i, ct in enumerate(ciphertexts)
)

script = f'''#!/usr/bin/env python3
"""VAULT-9 Final Lock Override Module
This module was obfuscated by the Head of Security after the incident.
He left one note: "the passphrase is the cat\'s full name, as registered with the vet."
"""
import sys
# import hashlib   # accidentally removed (thanks, Mittens)


def _k(_p):
    return hashlib.sha256(_p.encode()).digest()


def _x(_d, _key):
    return bytes(b ^ _key[i % len(_key)] for i, b in enumerate(_d))


{ct_lines}

if len(sys.argv) < 2:
    print("Usage: python3 final_lock.py <passphrase>")
    sys.exit(1)

_p = " ".join(sys.argv[1:])
try:
    _key = _k(_p)
    _r1 = _x(_a, _key).decode("utf-8")
    _r2 = _x(_b, _key).decode("utf-8")
    _r3 = _x(_c, _key).decode("utf-8")
    if all(ch.isprintable() for ch in _r1 + _r2 + _r3) and len(_r1) > 0:
        print(f"FINAL CODE 1: {{_r1}}")
        print(f"FINAL CODE 2: {{_r2}}")
        print(f"FINAL CODE 3: {{_r3}}")
    else:
        print("ACCESS DENIED")
except Exception:
    print("ACCESS DENIED")
'''

OUT.write_text(script)
print(f"Generated {OUT}")
print("Answers (run with correct passphrase):")
for code in CODES:
    print(code)
