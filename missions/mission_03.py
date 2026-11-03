"""
mission #3
title: transmission trouble
"""

import re
from collections import deque
from collections.abc import Iterator


def preprocessing(puzzle_input: str):
    """Parse relay coordinates and the message chunks."""
    _relays, _messages = puzzle_input.split("\n\n")
    relays = [
        (int(x), int(y))
        for _, x, y in re.findall(r'#(\S+) X(\d+) Y(\d+)', _relays)]
    messages = list(map(int, _messages.split(',')))
    return relays, messages


def solver(
        relays: list[tuple[int, int]],
        messages: list[int]) -> Iterator[int]:
    """Yield the answers to both parts."""
    yield count_paths(relays)
    yield forward_messages(relays, messages)


def count_paths(relays: list[tuple[int, int]]) -> int:
    """Count the paths from S to D that never visit a relay twice."""
    start = relays[0]
    end = relays[-1]

    queue = deque([(*start, frozenset({0}))])
    cnt = 0
    while queue:
        x, y, visited = queue.popleft()
        if (x, y) == end:
            cnt += 1
        else:
            for name, (nx, ny) in enumerate(relays):
                if name in visited:
                    continue
                if abs(nx - x) + abs(ny - y) <= 5:
                    queue.append((nx, ny, frozenset(visited | {name})))
    return cnt


def forward_messages(
        relays: list[tuple[int, int]],
        messages: list[int]) -> int:
    """Simulate the transmission and score the queue received by D."""
    neighbours = get_neighbours(relays)
    n_relays = len(relays)
    unmovable: set[int] = set()
    seen: list[set[int]] = [set() for _ in range(n_relays)]
    seen[0] = set(messages)

    queues: list[deque[int]] = [deque() for _ in range(n_relays)]
    queues[0] = deque(messages)

    while True:
        # Find the first non empty queue
        r = 0
        while not queues[r] or set(queues[r]) <= unmovable:
            r += 1
            if r == n_relays:
                return sum(list(queues[-1])[-5:]) * len(queues[-1])

        # Set distribution queue
        dests = [
            name
            for _, name in sorted(
                neighbours[r],
                key=lambda x: (x[0], len(queues[x[1]]), x[1]))
                ]

        # Forward chunk
        idx = 0
        unmoved = 0
        while len(queues[r]) > unmoved:
            movable = True
            message = queues[r].popleft()
            init_idx = idx
            while message in seen[dests[idx]]:
                idx = (idx + 1) % len(dests)
                if idx == init_idx:
                    unmoved += 1
                    queues[r].append(message)
                    unmovable.add(message)
                    movable = False
                    break

            if movable:
                queues[dests[idx]].append(message)
                seen[dests[idx]].add(message)
                if dests[idx] == (len(queues) - 1):
                    unmovable.add(message)
                idx = (idx + 1) % len(dests)


def get_neighbours(
        relays: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """For each relay, the (distance, relay) pairs in range, closest first."""
    neighbours: list[list[tuple[int, int]]] = []
    for r1, (x1, y1) in enumerate(relays):
        dists: list[tuple[int, int]] = []
        for r2, (x2, y2) in enumerate(relays):
            if r1 == r2:
                continue
            dist = abs(x2 - x1) + abs(y2 - y1)
            if dist <= 5:
                dists.append((dist, r2))
        neighbours.append(sorted(dists))
    return neighbours
