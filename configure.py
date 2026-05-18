#!/usr/bin/env python3
"""VAULT-9 Hackathon Configurator
Runs all stage scripts to capture correct answers, hashes them,
encrypts stage payloads, and patches hackathon.html in-place.
Run this after making any change to stage content or answers.
Requires: pip install cryptography
"""
import hashlib
import json
import base64
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).parent
PYTHON = sys.executable  # use same interpreter to find installed packages


# ── Crypto helpers ────────────────────────────────────────────────────────

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def normalize(answer) -> str:
    return str(answer).strip().lower()

def hash_answer(answer) -> str:
    return sha256_hex(normalize(answer))

def derive_key(stage_num: int, answers: list) -> bytes:
    combined = f"hackathon:stage{stage_num}:" + "|".join(normalize(a) for a in answers)
    return hashlib.sha256(combined.encode()).digest()

def encrypt_payload(payload: dict, key: bytes) -> str:
    iv = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(payload).encode()
    ciphertext = aesgcm.encrypt(iv, plaintext, None)
    return json.dumps({
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ciphertext).decode()
    })


# ── Run a stage script and return non-empty stdout lines ─────────────────

def run_script(rel_path: str, *args) -> list:
    result = subprocess.run(
        [PYTHON, str(ROOT / rel_path)] + list(args),
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        raise RuntimeError(f"{rel_path} failed:\n{result.stderr}")
    return [l for l in result.stdout.strip().split("\n") if l.strip()]


# ── Capture answers from each stage ──────────────────────────────────────

print("Running stage scripts...")

# Stage 1: lobby_decoder.py — output lines are "CODE X : NNNN"
s1_lines = run_script("stages/stage1/lobby_decoder.py")
s1_answers = [l.split(": ", 1)[1].strip() for l in s1_lines if ": " in l]
assert len(s1_answers) == 3, f"Stage 1: expected 3 answers, got {s1_answers}"
print(f"  Stage 1: {s1_answers}")

# Stage 2: keycard_auth_solution.py — output lines are "DOOR X CODE: NNNN"
s2_lines = run_script("stages/stage2/keycard_auth_solution.py")
s2_answers = [l.split(": ", 1)[1].strip() for l in s2_lines if ": " in l]
assert len(s2_answers) == 3, f"Stage 2: expected 3 answers, got {s2_answers}"
print(f"  Stage 2: {s2_answers}")

# Stage 3: generate_logs.py — last 3 non-empty lines are the answers
s3_lines = run_script("stages/stage3/generate_logs.py")
s3_answers = s3_lines[-3:]
assert len(s3_answers) == 3
print(f"  Stage 3: {s3_answers}")

# Stage 4: generate_image.py — last 3 non-empty lines
s4_lines = run_script("stages/stage4/generate_image.py")
s4_answers = s4_lines[-3:]
assert len(s4_answers) == 3
print(f"  Stage 4: {s4_answers}")

# Stage 5: generate_db.py — last 3 non-empty lines
s5_lines = run_script("stages/stage5/generate_db.py")
s5_answers = s5_lines[-3:]
assert len(s5_answers) == 3
print(f"  Stage 5: {s5_answers}")

# Stage 6: generate_stage6.py regenerates final_lock.py — last 3 non-empty lines
s6_lines = run_script("stages/stage6/generate_stage6.py")
s6_answers = s6_lines[-3:]
assert len(s6_answers) == 3
print(f"  Stage 6: {s6_answers}")


# ── Read problem HTML for each stage ─────────────────────────────────────

def read_html(rel: str) -> str:
    return (ROOT / rel).read_text().strip()

s2_html = read_html("stages/stage2/problem.html")
s3_html = read_html("stages/stage3/problem.html")
s4_html = read_html("stages/stage4/problem.html")
s5_html = read_html("stages/stage5/problem.html")
s6_html = read_html("stages/stage6/problem.html")


# ── Build encrypted payloads ──────────────────────────────────────────────

print("\nEncrypting stage payloads...")

s2_payload = {
    "title": "Stage 2 — The Keycard Room",
    "problem": s2_html,
    "answerHashes": [hash_answer(a) for a in s2_answers],
    "labels": ["Door A code", "Door B code", "Door C code"]
}
s2_blob = encrypt_payload(s2_payload, derive_key(1, s1_answers))

s3_payload = {
    "title": "Stage 3 — The Server Room",
    "problem": s3_html,
    "answerHashes": [hash_answer(a) for a in s3_answers],
    "labels": ["Number of CRITICAL events", "Session number", "Last vault locked"]
}
s3_blob = encrypt_payload(s3_payload, derive_key(2, s2_answers))

s4_payload = {
    "title": "Stage 4 — The Surveillance Room",
    "problem": s4_html,
    "answerHashes": [hash_answer(a) for a in s4_answers],
    "labels": ["Override code 1", "Override code 2", "Override code 3"]
}
s4_blob = encrypt_payload(s4_payload, derive_key(3, s3_answers))

s5_payload = {
    "title": "Stage 5 — The Records Room",
    "problem": s5_html,
    "answerHashes": [hash_answer(a) for a in s5_answers],
    "labels": ["V006 emergency code", "Sum of reversed transactions", "Mittens vault code"]
}
s5_blob = encrypt_payload(s5_payload, derive_key(4, s4_answers))

s6_payload = {
    "title": "Stage 6 — The Vault",
    "problem": s6_html,
    "answerHashes": [hash_answer(a) for a in s6_answers],
    "labels": ["Final code 1", "Final code 2", "Final code 3"]
}
s6_blob = encrypt_payload(s6_payload, derive_key(5, s5_answers))

print("  Done.")


# ── Patch hackathon.html ──────────────────────────────────────────────────

print("\nPatching hackathon.html...")

html_path = ROOT / "hackathon.html"
html = html_path.read_text()

# Replace Stage 1 answer hashes in STAGE_1_CONFIG
s1_hashes = [hash_answer(a) for a in s1_answers]

def replace_answer_hashes(html: str, hashes: list) -> str:
    pattern = r"(answerHashes:\s*\[)[^\]]*(\])"
    replacement = (
        "\\1\n            '"
        + "',\n            '".join(hashes)
        + "'\n        \\2"
    )
    return re.sub(pattern, replacement, html, count=1)

html = replace_answer_hashes(html, s1_hashes)

# Replace the entire ENCRYPTED_STAGES block to ensure clean replacement
blob_map = {2: s2_blob, 3: s3_blob, 4: s4_blob, 5: s5_blob, 6: s6_blob}
new_block = "    const ENCRYPTED_STAGES = {\n"
for stage_num, blob in blob_map.items():
    # Escape single quotes in blob (blob is JSON so should not have any, but be safe)
    escaped_blob = blob.replace("\\", "\\\\").replace("'", "\\'")
    new_block += f"        {stage_num}: '{escaped_blob}',\n"
new_block += "    };"

html = re.sub(
    r'const ENCRYPTED_STAGES = \{.*?\};',
    new_block,
    html,
    flags=re.DOTALL
)

html_path.write_text(html)
print("  hackathon.html patched.")


# ── Write ANSWERS.md ──────────────────────────────────────────────────────

answers_md = f"""# VAULT-9 Hackathon — Correct Answers

> **ORGANISER ONLY — do not share with participants**

Generated by configure.py. Re-run configure.py if you change any stage content.

## Stage 1 — The Lobby
| Field | Answer |
|-------|--------|
| Code ALPHA | `{s1_answers[0]}` |
| Code BETA  | `{s1_answers[1]}` |
| Code GAMMA | `{s1_answers[2]}` |

## Stage 2 — The Keycard Room
| Field | Answer |
|-------|--------|
| Door A code | `{s2_answers[0]}` |
| Door B code | `{s2_answers[1]}` |
| Door C code | `{s2_answers[2]}` |

**Bugs to fix:**
1. `highlevel` → `high_level` (NameError on variable name mismatch)
2. `[1:4]` → `[:3]` (slice off-by-one skipping highest card)
3. `i % 2 != 0` → `i % 2 == 0` (XOR wrong index parity)

## Stage 3 — The Server Room
| Field | Answer |
|-------|--------|
| CRITICAL event count | `{s3_answers[0]}` |
| Session number | `{s3_answers[1]}` |
| Last vault locked | `{s3_answers[2]}` |

## Stage 4 — The Surveillance Room
| Field | Answer |
|-------|--------|
| Override code 1 | `{s4_answers[0]}` |
| Override code 2 | `{s4_answers[1]}` |
| Override code 3 | `{s4_answers[2]}` |

**Extraction:** `STEP = 1`, LSB of R channel, every pixel from pixel 0.

## Stage 5 — The Records Room
| Field | Answer |
|-------|--------|
| V006 emergency code | `{s5_answers[0]}` |
| Sum of reversed transactions | `{s5_answers[1]}` |
| Mittens vault code | `{s5_answers[2]}` |

## Stage 6 — The Vault
| Field | Answer |
|-------|--------|
| Final code 1 | `{s6_answers[0]}` |
| Final code 2 | `{s6_answers[1]}` |
| Final code 3 | `{s6_answers[2]}` |

**Bug to fix:** uncomment `import hashlib` (line 2, currently commented out).
**Passphrase:** `Mittens Fluffington III`
"""

(ROOT / "ANSWERS.md").write_text(answers_md)
print("  ANSWERS.md written.")


# ── Build vault9-files.zip ────────────────────────────────────────────────

zip_files = [
    ("vault_logs.txt",       "stages/stage3/vault_logs.txt"),
    ("mittens_cam.png",      "stages/stage4/mittens_cam.png"),
    ("extract_template.py",  "stages/stage4/extract_template.py"),
    ("vault_records.db",     "stages/stage5/vault_records.db"),
    ("final_lock.py",        "stages/stage6/final_lock.py"),
]

zip_path = ROOT / "vault9-files.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for arcname, relpath in zip_files:
        full = ROOT / relpath
        if full.exists():
            zf.write(full, arcname)
            print(f"  Added {arcname}")
        else:
            print(f"  WARNING: {relpath} not found — skipping")

print(f"\nDone! vault9-files.zip ready for distribution.")
print(f"Open hackathon.html in a browser to test.")
