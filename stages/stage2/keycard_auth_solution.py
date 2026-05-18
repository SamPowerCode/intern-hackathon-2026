#!/usr/bin/env python3
"""VAULT-9 Keycard Authentication Module — REFERENCE VERSION (not for participants)"""

KEYCARD_DATA = [
    ("KC-001", 3, 8421),
    ("KC-002", 1, 2934),
    ("KC-003", 5, 7156),
    ("KC-004", 2, 4823),
    ("KC-005", 4, 9012),
    ("KC-006", 3, 6347),
    ("KC-007", 2, 1895),
    ("KC-008", 5, 5631),
    ("KC-009", 1, 3278),
    ("KC-010", 4, 7904),
]


def compute_door_codes(keycards):
    sorted_cards = sorted(keycards, key=lambda c: (-c[1], c[2]))

    # Door A: sum of values for cards with level >= 4
    high_level = [c for c in sorted_cards if c[1] >= 4]
    door_a = sum(c[2] for c in high_level)

    # Door B: product of access levels for the top 3 cards by value
    top3 = sorted(keycards, key=lambda c: c[2], reverse=True)[:3]
    door_b = 1
    for c in top3:
        door_b *= c[1]

    # Door C: XOR of values at even indices in the sorted list
    door_c = 0
    for i, c in enumerate(sorted_cards):
        if i % 2 == 0:
            door_c ^= c[2]

    return door_a, door_b, door_c


if __name__ == "__main__":
    door_a, door_b, door_c = compute_door_codes(KEYCARD_DATA)
    print(f"DOOR A CODE: {door_a}")
    print(f"DOOR B CODE: {door_b}")
    print(f"DOOR C CODE: {door_c}")
