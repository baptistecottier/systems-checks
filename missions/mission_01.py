"""
mission #1
title: critical capacity
"""

from collections import defaultdict
from collections.abc import Iterator
import re

Notes = defaultdict[int, dict[bool, set[int]]]


def preprocessing(puzzle_input: str) -> Notes:
    """Group enabled/disabled ids by timestamp."""
    notes: Notes = defaultdict(lambda: {True: set(), False: set()})
    data = [(int(t), int(num_id), state.startswith('en'))
            for t, num_id, state
            in re.findall(r't=(\d+) #(\d+) (\w+)abled', puzzle_input)]
    for t, num_id, state in data:
        notes[t][True].discard(num_id)
        notes[t][state].add(num_id)
    return notes


def solver(notes: Notes) -> Iterator[int]:
    """Yield the answers to both parts."""
    disabled: set[int] = set()
    times_off: defaultdict[int, int] = defaultdict(int)
    ordered_times = sorted(notes.keys())
    lmd = 0
    time_lmd = 0
    max_time_off = 0
    last_time = 0
    for i, time in enumerate(ordered_times):
        for num_id in disabled:
            times_off[num_id] += time - last_time
        disabled.update(notes[time][False])

        for num_id in notes[time][True]:
            disabled.remove(num_id)
            max_time_off = max(max_time_off, times_off[num_id])
            times_off[num_id] = 0

        if len(disabled) > lmd:
            lmd = len(disabled)
            time_lmd = ordered_times[i + 1] - time
        last_time = time
    yield from (max_time_off, time_lmd)
