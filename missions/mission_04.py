"""
mission #4
title: ghosts in the cleaning droids
"""

import re
from collections import defaultdict


def preprocessing(puzzle_input: str):
    """Parse each log as (droid id, zone id, message, checksum)."""
    return [
        (int(x[0]), int(x[1]), x[2], int(x[3]))
        for x in re.findall(r'(\d+):(\d+)\|(\w+)\|(\d+)', puzzle_input)]


def solver(logs: list[tuple[int, int, str, int]]):
    """Yield the answers to both parts."""
    wrong_cs = 0
    commands: dict[str, int] = defaultdict(int)
    for droid_id, zone_id, message, cs in logs:
        real_cs = checksum(droid_id, zone_id, message)
        if real_cs != cs:
            for i in range(0, len(message) - 1, 2):
                commands[message[i:i+2]] += 1
            wrong_cs += cs
    yield wrong_cs
    commands_frequencies = sorted(commands.values(), reverse=True)
    yield commands_frequencies[0] * commands_frequencies[1]


def checksum(d_id: int, z_id: int, m: str):
    """XOR of the character codes of the formatted log line."""
    cs = 0
    for c in list(f"{d_id}:{z_id}|{m}|"):
        cs ^= ord(c)
    return cs
