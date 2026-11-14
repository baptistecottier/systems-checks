"""
mission #7
title: power struggle
"""

import re
from collections import defaultdict


def preprocessing(puzzle_input: str):
    """Parse the puzzle input into a list of (id, name, load, output)."""
    relays = [
        (int(a), b, int(c), int(d))
        for a, b, c, d in
        re.findall(r'(\d+)\|(\w+) (\d+) (\d+)', puzzle_input)
    ]
    return relays


def solver(relays: list[tuple[int, str, int, int]]):
    """Yield the total efficiency loss, then the top command's loss."""
    damaged_efficiency = 0
    types: dict[str, int] = defaultdict(int)
    for relay in relays:
        eff = efficiency(relay)
        if eff < 97:
            damaged_efficiency += eff
            for i in [0, 3, 6]:
                types[relay[1][i: i+3]] += eff
    yield damaged_efficiency
    yield max(types.values())


def efficiency(relay: tuple[int, str, int, int]):
    """Output as a percentage of load, for one relay."""
    return int(100 * relay[3] / relay[2])
