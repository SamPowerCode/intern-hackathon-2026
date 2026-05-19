#!/usr/bin/env python3
"""VAULT-9 Stage 1 — organiser brute-force seed recovery.

Usage: python3 lobby_decoder.py <code_alpha> <code_beta> <code_gamma>

Given the three lock codes shown in the Stage 1 problem, this script
recovers the three hidden seeds (the participant answers).
"""
import sys

KEYLOG = "fjk39dls02pqzxcv8nm1"


def compute_code(seed: int, keylog: str, idx: int) -> int:
    acc = seed
    for j, ch in enumerate(keylog):
        acc = (acc * 31 + ord(ch) + idx * 17) & 0xFFFF
    return acc % 9000 + 1000


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 lobby_decoder.py <code_alpha> <code_beta> <code_gamma>")
        sys.exit(1)

    targets = [int(a) for a in sys.argv[1:]]
    for i, target in enumerate(targets):
        label = ["ALPHA", "BETA", "GAMMA"][i]
        for seed in range(1000, 10000):
            if compute_code(seed, KEYLOG, i) == target:
                print(f"SEED {label}: {seed}")
                break
        else:
            print(f"SEED {label}: NOT FOUND (code {target} has no solution in 1000-9999)")
