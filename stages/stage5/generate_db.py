#!/usr/bin/env python3
"""Generates vault_records.db for Stage 5.
Prints the three query answers to stdout.
"""
import sqlite3
from pathlib import Path

OUT = Path(__file__).parent / "vault_records.db"
OUT.unlink(missing_ok=True)

conn = sqlite3.connect(OUT)
c = conn.cursor()

c.executescript("""
CREATE TABLE vaults (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    balance        REAL NOT NULL,
    status         TEXT NOT NULL,
    emergency_code TEXT NOT NULL,
    deleted_at     TEXT
);

CREATE TABLE transactions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    vault_id   TEXT NOT NULL,
    amount     REAL NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE access_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    vault_id   TEXT NOT NULL,
    username   TEXT NOT NULL,
    action     TEXT NOT NULL,
    timestamp  TEXT NOT NULL
);
""")

vaults = [
    ("V001", "Main Reserve",      9_500_000, "LOCKED",   "7741", None),
    ("V002", "Forex Holdings",    4_200_000, "LOCKED",   "2298", None),
    ("V003", "Bond Portfolio",    7_100_000, "LOCKED",   "6053", None),
    ("V004", "Cash Reserves",     2_800_000, "LOCKED",   "8814", None),
    ("V005", "Precious Metals",   6_300_000, "LOCKED",   "3391", None),
    # V006 deleted at lockdown moment — Q1 target
    ("V006", "Petty Cash",           50_000, "DELETED",  "3847", "2024-03-12 09:14:22"),
    # V007 archived the night before (routine, not incident-related)
    ("V007", "Slush Fund",           12_000, "ARCHIVED", "9901", "2024-03-11 17:30:00"),
    ("V008", "Night Safe",            5_000, "LOCKED",   "9163", None),
    ("V009", "Contingency Fund",    850_000, "LOCKED",   "4417", None),
    # V010 deleted one second after lockdown — red herring for Q1
    ("V010", "Overflow Reserve",     25_000, "DELETED",  "5572", "2024-03-12 09:14:23"),
]
c.executemany("INSERT INTO vaults VALUES (?,?,?,?,?,?)", vaults)

transactions = [
    # Normal completed transactions (noise)
    ("V001", 500_000, "COMPLETED",  "2024-03-12 08:01:00"),
    ("V002", 120_000, "COMPLETED",  "2024-03-12 08:15:00"),
    ("V003", 200_000, "COMPLETED",  "2024-03-12 08:45:00"),
    ("V004",  75_000, "PENDING",    "2024-03-12 09:00:00"),
    ("V005", 430_000, "COMPLETED",  "2024-03-12 07:30:00"),
    ("V009",  60_000, "COMPLETED",  "2024-03-12 07:55:00"),
    ("V002",  33_000, "CANCELLED",  "2024-03-12 09:10:00"),
    ("V001",  18_000, "PENDING",    "2024-03-12 09:12:00"),
    # Lockdown reversals — V005 has the largest single reversal (Q2 target)
    ("V001",   8_000, "REVERSED",   "2024-03-12 09:14:23"),
    ("V003",   8_750, "REVERSED",   "2024-03-12 09:14:24"),
    ("V002",   9_000, "REVERSED",   "2024-03-12 09:14:24"),
    ("V004",   7_300, "REVERSED",   "2024-03-12 09:14:25"),
    ("V005",  14_000, "REVERSED",   "2024-03-12 09:14:25"),
]
c.executemany(
    "INSERT INTO transactions (vault_id, amount, status, created_at) VALUES (?,?,?,?)",
    transactions
)

access = [
    # Normal daytime activity
    ("V001", "alice",    "VIEW_BALANCE",    "2024-03-12 08:00:01"),
    ("V002", "bob",      "VIEW_BALANCE",    "2024-03-12 08:12:44"),
    ("V003", "carol",    "TRANSFER",        "2024-03-12 08:44:11"),
    ("V009", "dave",     "VIEW_BALANCE",    "2024-03-12 09:05:33"),
    ("V004", "eve",      "TRANSFER",        "2024-03-12 09:09:17"),
    # Red herring: WHISKERS does EMERGENCY_UNLOCK 3 seconds before lockdown
    ("V003", "WHISKERS", "EMERGENCY_UNLOCK","2024-03-12 09:14:19"),
    # Noise at exact lockdown timestamp — multiple routine accesses
    ("V002", "alice",    "VIEW_BALANCE",    "2024-03-12 09:14:22"),
    ("V009", "dave",     "VIEW_BALANCE",    "2024-03-12 09:14:22"),
    # Q3 target: MITTENS at the exact lockdown timestamp
    ("V008", "MITTENS",  "EMERGENCY_UNLOCK","2024-03-12 09:14:22"),
    # Post-incident noise
    ("V001", "sysadmin", "AUDIT",           "2024-03-12 09:20:00"),
    ("V003", "sysadmin", "AUDIT",           "2024-03-12 09:20:01"),
]
c.executemany(
    "INSERT INTO access_log (vault_id, username, action, timestamp) VALUES (?,?,?,?)",
    access
)

conn.commit()
conn.close()

conn2 = sqlite3.connect(OUT)
c2 = conn2.cursor()

# Q1: vault deleted at the lockdown moment (V010 at :23 and V007 at night are red herrings)
q1 = c2.execute(
    "SELECT emergency_code FROM vaults WHERE deleted_at = '2024-03-12 09:14:22'"
).fetchone()[0]

# Q2: emergency code of the vault with the largest single REVERSED transaction
q2 = c2.execute("""
    SELECT v.emergency_code
    FROM transactions t
    JOIN vaults v ON t.vault_id = v.id
    WHERE t.status = 'REVERSED'
    ORDER BY t.amount DESC
    LIMIT 1
""").fetchone()[0]

# Q3: vault accessed at the exact lockdown timestamp with an unusual action
q3 = c2.execute("""
    SELECT v.emergency_code
    FROM access_log a
    JOIN vaults v ON a.vault_id = v.id
    WHERE a.timestamp = '2024-03-12 09:14:22'
      AND a.action = 'EMERGENCY_UNLOCK'
""").fetchone()[0]

conn2.close()

print(q1)
print(q2)
print(q3)
