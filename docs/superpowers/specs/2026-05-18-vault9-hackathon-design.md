# VAULT-9 Hackathon — Design Spec
Date: 2026-05-18

## Overview

A 6-stage narrative hackathon for software engineering interns. Teams crack a series of bank vaults accidentally locked by Mittens, a 3-year-old tabby cat who walked across a live admin terminal. Each stage is a room in the bank, locked by a different security system. Teams solve each room sequentially, entering 3 answers to unlock the next stage.

The event runs across two sessions of 3–4 hours each. Stages 1–2 are self-contained (no downloads). Stages 3–6 require downloading files provided at the start of session 2.

## Narrative Premise

> At 09:14 on a Tuesday, Mittens Fluffington III — a 3-year-old tabby belonging to the Head of Security — walked across a live admin terminal and triggered an emergency lockdown across all 6 vault rooms. The source code is partially corrupted. The logs are a mess. You're the intern team on call. The bank opens at 9am tomorrow.

The cat's full registered name ("Mittens Fluffington III") is a plot point used as a passphrase in Stage 6. It must appear clearly in the Stage 6 narrative.

## Platform

Single-page `hackathon.html` built in the session prior to this spec. Stages 2–6 are AES-GCM encrypted in the source and only unlocked when the previous stage's answers are entered correctly. Each stage has 3 answer fields. Feedback shows "X out of 3 correct" without revealing which answers are wrong.

## Downloadable Files

Stages 3–6 require files. These are distributed as a single ZIP (`vault9-files.zip`) handed to teams at the start of session 2, or linked from within the stage description. Contents:

| File | Used in |
|------|---------|
| `vault_logs.txt` | Stage 3 |
| `mittens_cam.png` | Stage 4 |
| `vault_records.db` | Stage 5 |
| `final_lock.py` | Stage 6 |

## Stages

---

### Stage 1 — The Lobby
**Tool:** Python (self-contained)
**Estimated time:** 5–10 min

**Narrative:**
Mittens' first keystrokes triggered the emergency encoder. The VAULT-9 system captured the raw keystroke sequence and converted it into 3 emergency lock codes using its proprietary algorithm. Decode them.

**Challenge:**
Teams are given `lobby_decoder.py`. The script contains a hardcoded keylog string (`MITTENS_KEYLOG = "fjk39dls02pqzxcv8nm1"`) and a function that processes it through a chain of bitwise operations and modular arithmetic, printing 3 4-digit integers.

They run: `python lobby_decoder.py`

**Answers:** 3 × 4-digit integers, determined by running the script.

**AI resistance:** Low — intentionally. Stage 1 establishes the format and narrative. Real resistance builds from Stage 3.

---

### Stage 2 — The Keycard Room
**Tool:** Python (self-contained)
**Estimated time:** 20–35 min

**Narrative:**
Mittens sat on the laptop mid-rewrite and introduced exactly 3 bugs into the keycard authentication module. The script now crashes before printing the door codes. Find the bugs, fix them, run it.

**Challenge:**
Teams are given `keycard_auth.py` (~50 lines). It processes an embedded list of keycard records through an auth algorithm. Three bugs are present:
1. A `NameError` — one variable is misspelled in its definition vs. its usage
2. An off-by-one — a list slice uses the wrong index (`[1:6]` instead of `[0:6]`)
3. A wrong comparison operator — `>=` where `>` is needed (or vice versa) in the auth logic

All 3 bugs interact: fixing only 1 or 2 produces plausible-looking but incorrect output. The correct 3 door codes are only printed when all 3 bugs are fixed and the script runs to completion.

**Answers:** 3 integers output by the corrected script.

**AI resistance:** Medium. AI can find bugs but the output values require running the corrected computation. Subtle bug interactions mean partial fixes give wrong answers.

---

### Stage 3 — The Server Room
**Tool:** Bash / terminal
**File:** `vault_logs.txt` (~10,000 lines)
**Estimated time:** 25–40 min

**Narrative:**
VAULT-9 logs every event. Mittens' intrusion is buried in 10,000 lines of system logs. Three pieces of information are hidden in the file — extract them using command-line tools.

**Challenge:**
`vault_logs.txt` is a generated log file with consistent structure:
```
2024-03-12 09:13:47 [INFO]     VAULT-9: Heartbeat OK vault_id=V001 status=UNLOCKED
2024-03-12 09:14:22 [CRITICAL] VAULT-9: LOCKDOWN trigger=FELINE_INPUT session=SID-7429 vault_id=V001
```

Three questions:
1. How many `CRITICAL` lines contain `trigger=FELINE_INPUT`? (answered with `grep -c`)
2. What was the `session` ID of the lockdown? (answered with `grep` + `cut` or `awk`) — answer is the numeric part only, e.g. `7429`, not the full `SID-7429` prefix
3. Which `vault_id` was locked **last**? (answered with `grep` + `tail`)

**Answers:** 1 integer count, 1 integer session number (e.g. `7429`), 1 vault ID string (e.g. `V004`).

**AI resistance:** Strong. The file content is not available to AI. Teams must run bash commands against the actual file.

---

### Stage 4 — The Surveillance Room
**Tool:** Python + Pillow
**File:** `mittens_cam.png`
**Estimated time:** 30–45 min

**Narrative:**
The security camera caught Mittens in the act. The paranoid lead engineer always embedded backup override codes into surveillance images. His notes read: *"R channel, every 10th pixel, starting at pixel 0."*

**Challenge:**
Teams download `mittens_cam.png` — a greyscale security camera-style image with Mittens visible. The stage provides a partial extraction script with one blank to fill in (`STEP = ???`). The problem description states the step is 10. They complete the script and run it; it reads the R channel value of pixels at indices 0, 10, 20... and decodes 3 integers from those values.

**Answers:** 3 integers decoded from pixel R-channel values.

**AI resistance:** Very strong. The image is not available to AI. The partial script requires understanding the extraction logic, not just copy-pasting.

---

### Stage 5 — The Records Room
**Tool:** SQLite3 (CLI or Python `sqlite3` module)
**File:** `vault_records.db`
**Estimated time:** 35–50 min

**Narrative:**
The vault management database holds the master override codes. Mittens walked on the delete key. The records are marked deleted — but SQLite doesn't forget.

**Challenge:**
`vault_records.db` has 3 tables: `vaults`, `transactions`, `access_log`. Three questions, each requiring a different SQL technique:

1. **Soft-deleted rows** — Query `vaults WHERE deleted_at IS NOT NULL`. One column in those rows contains a code.
2. **Aggregation** — `SUM` of `amount` for `transactions WHERE status = 'REVERSED'`. Mittens triggered a batch of reversals.
3. **Join + filter** — Find the `access_log` entry where `user = 'MITTENS'`, join to `vaults`, retrieve `emergency_code`.

**Answers:** A short string from deleted vault row, an integer sum, a short string from the join.

**AI resistance:** Very strong. Database content is not available to AI. Teams must write and run queries against the actual file.

---

### Stage 6 — The Vault
**Tool:** Python
**File:** `final_lock.py`
**Estimated time:** 40–55 min

**Narrative:**
The final lock runs on a script the lead engineer obfuscated "for security" and never documented. He left one clue in the comments: *"the passphrase is the cat's full name, as registered with the vet."*

**Challenge:**
`final_lock.py` is ~60 lines of Python with obfuscated variable names (`x1`, `x2`, `_k`, etc.) but readable logic. Two obstacles:
1. A missing `import hashlib` at the top (one final Mittens bug) — the script won't run until this is added
2. The script takes one CLI argument (the passphrase). With a wrong passphrase it prints `ACCESS DENIED`. With `"Mittens Fluffington III"` it decrypts 3 embedded ciphertexts and prints the final codes

The passphrase is established in the stage narrative (not hidden in the script) — teams must read carefully.

**Answers:** 3 decrypted strings/codes printed by the script when run with the correct passphrase.

**AI resistance:** Strong. The file is not available to AI. Even if pasted in, the passphrase is only findable by reading the stage narrative, not the script. The missing import adds satisfying friction.

---

## Difficulty Curve

```
Easy                                                    Hard
  |----1----|--------2--------|---3---|---4---|---5---|---------6---------|
  0        10                35     45      55      70                  90 min
```

All teams are expected to complete all 6 stages within the two sessions (6–8 hours total). Stages 1–3 in session 1, stages 4–6 in session 2.

## Answer Format Notes

- All answers are normalised to lowercase + trimmed before hashing, so validation is case-insensitive
- Numeric answers should be plain integers (no commas, no currency symbols, no prefixes)
- Stage 3 answer 2 is the numeric session number only (e.g. `7429`), not the full `SID-7429` token — the problem description must make this explicit
- Stage 3 answer 3 is the vault ID as it appears in the log (e.g. `v004` after lowercasing — keep vault IDs lowercase in the log file to avoid ambiguity)
- Each stage's 3 answer hashes are baked into the encrypted payload for that stage (except Stage 1, which is in plaintext config in `hackathon.html`)

## Files To Build

| File | Description |
|------|-------------|
| `hackathon.html` | Main participant page (already built) |
| `setup.html` | Organiser encryption tool (already built) |
| `lobby_decoder.py` | Stage 1 script |
| `keycard_auth.py` | Stage 2 buggy script |
| `generate_logs.py` | Script to generate `vault_logs.txt` |
| `vault_logs.txt` | Generated log file for Stage 3 |
| `generate_image.py` | Script to generate `mittens_cam.png` with hidden data |
| `mittens_cam.png` | Surveillance image for Stage 4 |
| `generate_db.py` | Script to generate `vault_records.db` |
| `vault_records.db` | SQLite database for Stage 5 |
| `final_lock.py` | Obfuscated Python script for Stage 6 |
| `vault9-files.zip` | ZIP of all downloadable files for session 2 |
| `ANSWERS.md` | Organiser reference — all correct answers per stage |

Generator scripts (`generate_*.py`) are kept so the organiser can regenerate assets if needed and verify answers.
