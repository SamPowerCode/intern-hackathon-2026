# VAULT-9 Hackathon

A 6-stage narrative hackathon for software engineering interns. Teams crack a series of bank vaults accidentally locked by **Mittens Fluffington III**, a 3-year-old tabby who walked across a live admin terminal.

Each stage unlocks the next only when all three answers are correct. Stages 2–6 are AES-encrypted in the browser — participants can't read ahead by viewing source.

---

## Running the hackathon

### What participants need

- A laptop with Python 3 installed
- A browser (Chrome or Firefox)
- The `vault9-files.zip` for session 2 (see below)

### Session 1 (stages 1–2)

1. Open `hackathon.html` in a browser — no server needed, just double-click the file.
2. Stages 1 and 2 are self-contained. Participants copy code from the browser, save it locally, and run it.
3. No files to distribute for session 1.

### Session 2 (stages 3–6)

1. Distribute `vault9-files.zip` to each team at the start of the session (USB stick, shared drive, or download link).
2. Teams unzip it — they'll need the files for stages 3–6.
3. Stage 4 requires Pillow: `pip install Pillow`

Contents of `vault9-files.zip`:

| File | Used in |
|------|---------|
| `vault_logs.txt` | Stage 3 — bash/grep investigation |
| `mittens_cam.png` | Stage 4 — image steganography |
| `extract_template.py` | Stage 4 — partial extraction script |
| `vault_records.db` | Stage 5 — SQLite queries |
| `final_lock.py` | Stage 6 — obfuscated Python + bug fix |

---

## Correct answers

See `ANSWERS.md` — keep this file to yourself.

| Stage | Room | Answers |
|-------|------|---------|
| 1 | The Lobby | `9068`, `5884`, `2700` |
| 2 | The Keycard Room | `29703`, `48`, `8133` |
| 3 | The Server Room | `6`, `7429`, `V004` |
| 4 | The Surveillance Room | `4821`, `8803`, `5142` |
| 5 | The Records Room | `3847`, `47750`, `9163` |
| 6 | The Vault | `OPEN`, `1337`, `DONE` |

---

## Stage overview

| # | Room | Tool | Challenge |
|---|------|------|-----------|
| 1 | The Lobby | Python | Run a decoder script, read 3 output codes |
| 2 | The Keycard Room | Python | Fix 3 bugs in an auth script, run it |
| 3 | The Server Room | Bash | `grep`/`awk` a 11k-line log file |
| 4 | The Surveillance Room | Python + Pillow | Extract LSB steganography from a PNG |
| 5 | The Records Room | SQLite3 | Query a database with soft-deleted records |
| 6 | The Vault | Python | Fix a missing import, find the passphrase, run it |

---

## Modifying the hackathon

### Changing stage content

Each stage lives in `stages/stageN/`. The problem description HTML for stages 2–6 is in `stages/stageN/problem.html`. Stage 1's description is hardcoded in `hackathon.html` directly.

After any change, re-run the configurator to recompute hashes and re-encrypt everything:

```bash
python3 configure.py
```

This regenerates `ANSWERS.md`, `vault9-files.zip`, and patches `hackathon.html` in-place.

### Regenerating individual files

| File | How to regenerate |
|------|-------------------|
| `vault_logs.txt` | `python3 stages/stage3/generate_logs.py` |
| `mittens_cam.png` | `python3 stages/stage4/generate_image.py` |
| `vault_records.db` | `python3 stages/stage5/generate_db.py` |
| `final_lock.py` | `python3 stages/stage6/generate_stage6.py` |

Always run `configure.py` afterwards to keep `hackathon.html` in sync.

### Changing the number of stages

Update `const TOTAL_STAGES = 6;` in `hackathon.html` and the progress bar segment count, then update `configure.py` to add/remove stages.

---

## File structure

```
hackathon.html          ← participant-facing page (open in browser)
setup.html              ← organiser tool for manual hash/encrypt (optional)
configure.py            ← regenerates everything from source
requirements.txt        ← Pillow, cryptography
ANSWERS.md              ← correct answers (organiser only)
vault9-files.zip        ← distribute to teams at session 2 start

stages/
  stage1/lobby_decoder.py              ← self-contained Python script
  stage2/keycard_auth.py               ← buggy version (for participants)
  stage2/keycard_auth_solution.py      ← correct version (for configure.py)
  stage2/problem.html
  stage3/generate_logs.py              ← generates vault_logs.txt
  stage3/vault_logs.txt
  stage3/problem.html
  stage4/generate_image.py             ← generates mittens_cam.png
  stage4/extract_template.py           ← partial script (for participants)
  stage4/mittens_cam.png
  stage4/problem.html
  stage5/generate_db.py                ← generates vault_records.db
  stage5/vault_records.db
  stage5/problem.html
  stage6/generate_stage6.py            ← generates final_lock.py
  stage6/final_lock.py
  stage6/problem.html
```

---

## Security model

Stages 2–6 are AES-GCM encrypted. The correct answers to stage N are the decryption key for stage N+1. Even if a participant opens DevTools and reads the source, all they see for stages 2–6 are opaque base64 blobs — they can't read the next stage's content without solving the current one.

Stage 1's answer hashes are visible in source as SHA-256 digests. This is acceptable — brute-forcing 4-digit integers is trivial in theory, but doing so defeats the purpose of the exercise and won't help with stage 2 onward.
