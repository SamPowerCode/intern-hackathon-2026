#!/usr/bin/env python3
"""Generates vault_logs.txt for Stage 3.
Prints the three answers to stdout after generation.
"""
import random
import re
from pathlib import Path

random.seed(42)

OUT = Path(__file__).parent / "vault_logs.txt"

VAULTS = ["V001", "V002", "V003", "V004", "V005"]
USERS  = ["alice", "bob", "carol", "dave", "eve", "sysadmin"]
INFO_MSGS = [
    "Heartbeat OK",
    "Backup snapshot complete",
    "Access granted",
    "Token refreshed",
    "Config reloaded",
    "Audit log flushed",
    "Connection established",
    "Session started",
    "Balance reconciled",
]
WARN_MSGS = [
    "Slow query detected latency={}ms",
    "Disk usage at {}%",
    "Retry attempt {} of 3",
    "Rate limit approaching threshold={}",
]
ERROR_MSGS = [
    "Connection timeout after {}ms",
    "Invalid token for user={}",
    "DB write failed retries={}",
]

# Lockdown sequence: vaults locked in this order (last one is the answer)
LOCKDOWN_ORDER = ["V002", "V005", "V003", "V001", "V004"]
SESSION_ID = 7429        # answer 2
FELINE_CRITICAL_COUNT = 6  # answer 1 (one per lockdown + one spurious alert)

lines = []

def ts(hour, minute, second, ms=0):
    return f"2024-03-12 {hour:02d}:{minute:02d}:{second:02d}.{ms:03d}"


def info(t, msg, vault=None, user=None):
    extra = ""
    if vault:
        extra += f" vault_id={vault}"
    if user:
        extra += f" user={user}"
    return f"{t} [INFO    ] VAULT-9: {msg}{extra}"


def warning(t, msg):
    return f"{t} [WARNING ] VAULT-9: {msg}"


def error(t, msg):
    return f"{t} [ERROR   ] VAULT-9: {msg}"


def critical(t, msg):
    return f"{t} [CRITICAL] VAULT-9: {msg}"


# Generate background lines from 06:00 to 09:13
for hour in range(6, 10):
    for minute in range(60):
        if hour == 9 and minute >= 14:
            break
        for second in range(60):
            v = random.choice(VAULTS)
            u = random.choice(USERS)
            r = random.random()
            t = ts(hour, minute, second, random.randint(0, 999))
            if r < 0.78:
                lines.append(info(t, random.choice(INFO_MSGS), vault=v, user=u))
            elif r < 0.90:
                lines.append(warning(t, random.choice(WARN_MSGS).format(
                    random.randint(50, 999))))
            elif r < 0.97:
                lines.append(error(t, random.choice(ERROR_MSGS).format(
                    random.randint(1, 9))))
            else:
                lines.append(info(t, "Scheduled maintenance ping", vault=v))

# 09:14 - The Incident

# INFO-level feline sensor events scattered through the morning — distractors for Q1
lines.append(info(
    ts(7, 23, 41, 502),
    "Feline motion detected zone=BREAK_ROOM trigger=FELINE_INPUT status=DISMISSED"
))
lines.append(info(
    ts(8,  5, 17,  83),
    "Acoustic anomaly registered trigger=FELINE_INPUT sensor_id=ASN-11 zone=CORRIDOR_A status=ROUTINE"
))
lines.append(info(
    ts(8, 47, 33, 791),
    "Proximity sensor ping trigger=FELINE_INPUT zone=STAIRWELL status=MONITORING"
))

# Unrelated CRITICAL events before the feline lockdown (red herrings with different session IDs)
lines.append(critical(
    ts(9, 13, 11, 221),
    "System integrity check failed component=AUTH_MODULE error=CRC_MISMATCH"
))
lines.append(critical(
    ts(9, 13, 47, 889),
    f"Failsafe sensor triggered sensor_id=FSM-9 vault_id=V003 session=SID-0031"
))
lines.append(critical(
    ts(9, 14,  1, 112),
    f"Intrusion alert motion_zone=LOBBY session=SID-4422 status=FALSE_POSITIVE"
))

# INFO-level feline sensor events in the lead-up — NOT critical, must NOT be counted for Q1
lines.append(info(
    ts(9, 14,  8, 332),
    f"Feline proximity sensor triggered trigger=FELINE_INPUT zone=TERMINAL_ROOM"
))
lines.append(info(
    ts(9, 14, 15, 118),
    f"Motion anomaly detected trigger=FELINE_INPUT vault_id=V001 status=MONITORING"
))

# CRITICAL lockdown-adjacent event with a different SID — distractor for Q2
lines.append(critical(
    ts(9, 14, 20, 339),
    f"LOCKDOWN PROTOCOL ACTIVE alert_level=ELEVATED session=SID-4422 reason=PERIMETER_BREACH"
))

# Spurious CRITICAL before lockdowns (counts toward FELINE_CRITICAL_COUNT)
lines.append(critical(
    ts(9, 14, 22, 441),
    f"Unauthorised keystroke sequence detected — possible feline input "
    f"trigger=FELINE_INPUT session=SID-{SESSION_ID}"
))

# Lock each vault in order
lock_second = 23
for vault in LOCKDOWN_ORDER:
    lines.append(critical(
        ts(9, 14, lock_second, random.randint(0, 999)),
        f"LOCKDOWN INITIATED trigger=FELINE_INPUT session=SID-{SESSION_ID} vault_id={vault}"
    ))
    lock_second += 3

# Post-incident noise — also mentions vault_ids so simple vault_id greps add noise
for i, vault in enumerate(LOCKDOWN_ORDER):
    lines.append(info(
        ts(9, 14, 40 + i * 2, random.randint(0, 999)),
        f"Lock status verified vault_id={vault} status=SECURED"
    ))

for second in range(50, 60):
    t = ts(9, 14, second, random.randint(0, 999))
    lines.append(info(t, "LOCKDOWN CONFIRMED all vaults secured"))

for second in range(0, 60):
    t = ts(9, 15, second, random.randint(0, 999))
    lines.append(info(t, "Security team notified awaiting override"))

OUT.write_text("\n".join(lines) + "\n")

# Print answers
content = OUT.read_text()

# Q1: CRITICAL lines that contain FELINE_INPUT
count = sum(1 for l in content.splitlines() if "FELINE_INPUT" in l and "[CRITICAL]" in l)

# Q3: seconds value from the timestamp of the last LOCKDOWN INITIATED event
last_lock_second = None
for line in content.splitlines():
    if "LOCKDOWN INITIATED" in line:
        m = re.search(r'\d{2}:\d{2}:(\d{2})\.\d+', line)
        if m:
            last_lock_second = int(m.group(1))

print(count)
print(SESSION_ID)
print(last_lock_second)
