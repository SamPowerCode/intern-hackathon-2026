#!/usr/bin/env python3
"""Generates Stage 1 seeds and lock codes for VAULT-9 hackathon.

The SEEDS are the three answers participants must find by reverse-engineering
the algorithm. The CODES are shown in the problem description.

Output (6 lines):
  seed_0   <- answer 1 (Code ALPHA)
  seed_1   <- answer 2 (Code BETA)
  seed_2   <- answer 3 (Code GAMMA)
  code_0   <- displayed in problem
  code_1   <- displayed in problem
  code_2   <- displayed in problem
"""

KEYLOG = "fjk39dls02pqzxcv8nm1"


def compute_code(seed: int, keylog: str, idx: int) -> int:
    acc = seed
    for j, ch in enumerate(keylog):
        acc = (acc * 31 + ord(ch) + idx * 17) & 0xFFFF
    return acc % 9000 + 1000


# Pre-compute which seeds have a unique solution in [1000, 9999] per code index.
# A seed is "unique" if no other seed in [1000, 9999] produces the same code.
def find_unique_seed_sets():
    unique_per_index = []
    for idx in range(3):
        code_to_seeds: dict[int, list[int]] = {}
        for s in range(1000, 10000):
            c = compute_code(s, KEYLOG, idx)
            code_to_seeds.setdefault(c, []).append(s)
        unique_per_index.append({
            seeds[0]: code
            for code, seeds in code_to_seeds.items()
            if len(seeds) == 1
        })
    return unique_per_index


unique_sets = find_unique_seed_sets()

# Pick seeds: one per third of the 1000–9999 range so they're spread out
# and don't look trivially guessable (no round numbers, no sequential values).
SEED_BANDS = [(3400, 4800), (5300, 6700), (7200, 8800)]

def pick_seeds(unique_sets):
    picked = []
    used_codes = set()
    for idx, (lo, hi) in enumerate(SEED_BANDS):
        us = unique_sets[idx]
        candidates = sorted(
            s for s in us
            if lo <= s <= hi
            and s % 100 != 0
            and s % 10 not in (0, 1, 5)
        )
        # Pick from the middle of each band so seeds don't cluster at boundaries
        mid = len(candidates) // 2
        for seed in candidates[mid:] + candidates[:mid]:
            code = us[seed]
            if code not in used_codes and seed not in picked:
                picked.append(seed)
                used_codes.add(code)
                break
    return picked


SEEDS = pick_seeds(unique_sets)
assert len(SEEDS) == 3, "Could not find 3 unique seeds"

CODES = [compute_code(s, KEYLOG, i) for i, s in enumerate(SEEDS)]

# Verify
for i in range(3):
    matches = [s for s in range(1000, 10000) if compute_code(s, KEYLOG, i) == CODES[i]]
    assert len(matches) == 1 and matches[0] == SEEDS[i], \
        f"Non-unique for index {i}: {matches}"

for seed in SEEDS:
    print(seed)
for code in CODES:
    print(code)
