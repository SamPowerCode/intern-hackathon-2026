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
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    balance      REAL NOT NULL,
    status       TEXT NOT NULL,
    emergency_code TEXT NOT NULL,
    deleted_at   TEXT
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
    ("V006", "Petty Cash",           50_000, "DELETED",  "3847", "2024-03-12 09:14:22"),
    ("V007", "Slush Fund",           12_000, "DELETED",  "9901", "2024-03-12 09:14:22"),
    ("V008", "Night Safe",            5_000, "LOCKED",   "9163", None),
]
c.executemany("INSERT INTO vaults VALUES (?,?,?,?,?,?)", vaults)

transactions = [
    ("V001", 500_000, "COMPLETED",  "2024-03-12 08:01:00"),
    ("V002", 120_000, "COMPLETED",  "2024-03-12 08:15:00"),
    ("V001",  12_500, "REVERSED",   "2024-03-12 09:14:23"),
    ("V003",   8_750, "REVERSED",   "2024-03-12 09:14:24"),
    ("V002",   9_000, "REVERSED",   "2024-03-12 09:14:24"),
    ("V004",   7_300, "REVERSED",   "2024-03-12 09:14:25"),
    ("V005",  10_200, "REVERSED",   "2024-03-12 09:14:25"),
    ("V003", 200_000, "COMPLETED",  "2024-03-12 08:45:00"),
    ("V004",  75_000, "PENDING",    "2024-03-12 09:00:00"),
    ("V005", 430_000, "COMPLETED",  "2024-03-12 07:30:00"),
]
c.executemany(
    "INSERT INTO transactions (vault_id, amount, status, created_at) VALUES (?,?,?,?)",
    transactions
)

access = [
    ("V001", "alice",    "VIEW_BALANCE",    "2024-03-12 08:00:01"),
    ("V002", "bob",      "VIEW_BALANCE",    "2024-03-12 08:12:44"),
    ("V003", "carol",    "TRANSFER",        "2024-03-12 08:44:11"),
    ("V005", "WHISKERS", "EMERGENCY_UNLOCK","2024-03-12 09:14:19"),
    ("V008", "MITTENS",  "EMERGENCY_UNLOCK","2024-03-12 09:14:22"),
    ("V001", "sysadmin", "AUDIT",           "2024-03-12 09:20:00"),
]
c.executemany(
    "INSERT INTO access_log (vault_id, username, action, timestamp) VALUES (?,?,?,?)",
    access
)

conn.commit()
conn.close()

conn2 = sqlite3.connect(OUT)
c2 = conn2.cursor()

q1 = c2.execute(
    "SELECT emergency_code FROM vaults WHERE id='V006' AND deleted_at IS NOT NULL"
).fetchone()[0]

q2 = c2.execute(
    "SELECT CAST(SUM(amount) AS INTEGER) FROM transactions WHERE status='REVERSED'"
).fetchone()[0]

q3 = c2.execute("""
    SELECT v.emergency_code
    FROM access_log a
    JOIN vaults v ON a.vault_id = v.id
    WHERE a.username = 'MITTENS'
""").fetchone()[0]

conn2.close()

print(q1)
print(q2)
print(q3)
