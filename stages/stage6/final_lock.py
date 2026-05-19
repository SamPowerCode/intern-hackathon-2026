#!/usr/bin/env python3
"""VAULT-9 Final Lock Override Module v2.1
Obfuscated post-incident. Access restricted.
# Internal ref: auth key sourced from H.O.S. official vet registration
"""
import sys
# import hashlib


def _k(_p):
    return hashlib.sha256(_p.encode()).digest()


def _v(_s):
    return sum(ord(c) for c in _s) & 0xFF


def _x(_d, _key):
    return bytes(b ^ _key[(i + 1) % len(_key)] for i, b in enumerate(_d))


_a = bytes([0x21, 0x89, 0x10, 0x5e])
_b = bytes([0x5f, 0xea, 0x66, 0x27])
_c = bytes([0x2a, 0x96, 0x1b, 0x55])

if len(sys.argv) < 2:
    print("Usage: python3 final_lock.py <passphrase>")
    sys.exit(1)

_p = " ".join(sys.argv[1:])
_p = _p.strip().lower()  # normalise input
try:
    _key = _k(_p)
    _r1 = _x(_a, _key).decode("utf-8")
    _r2 = _x(_b, _key).decode("utf-8")
    _r3 = _x(_c, _key).decode("utf-8")
    if all(ch.isprintable() for ch in _r1 + _r2 + _r3) and len(_r1) > 0:
        print(f"FINAL CODE 1: {_r1}")
        print(f"FINAL CODE 2: {_r2}")
        print(f"FINAL CODE 3: {_r3}")
    else:
        print("ACCESS DENIED")
except Exception:
    print("ACCESS DENIED")
