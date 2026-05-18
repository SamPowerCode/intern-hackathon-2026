#!/usr/bin/env python3
"""VAULT-9 Emergency Lockdown Decoder v2.1
Authorised use only. Unauthorised access will be reported to Mittens.
"""

MITTENS_KEYLOG = "fjk39dls02pqzxcv8nm1"


def decode_lockdown(keylog):
    codes = []
    for i in range(3):
        acc = 0
        for j, ch in enumerate(keylog):
            acc = (acc * 31 + ord(ch) + i * 17) & 0xFFFF
        codes.append(acc % 9000 + 1000)
    return codes


if __name__ == "__main__":
    codes = decode_lockdown(MITTENS_KEYLOG)
    print(f"CODE ALPHA : {codes[0]}")
    print(f"CODE BETA  : {codes[1]}")
    print(f"CODE GAMMA : {codes[2]}")
