"""
mission #2
title: chaos in the cargo bay
"""

import heapq
from collections.abc import Iterator


def preprocessing(
        puzzle_input: str
        ) -> tuple[set[tuple[int, int]], int, int, tuple[int, int]]:
    """Parse the stationary suspensors, grid size and target."""
    lines = puzzle_input.splitlines()
    w = len(lines[0])
    h = len(lines)
    occupied: set[tuple[int, int]] = set()
    end: tuple[int, int] | None = None
    for y, line in enumerate(lines):
        for x, c in enumerate(line):
            if c == '#':
                occupied.add((x, y))
            if c == '*':
                end = (x, y)
    if not end:
        raise ValueError("No ending point found!")
    return occupied, w, h, end


def solver(
        occupied: set[tuple[int, int]], w: int, h: int,
        end: tuple[int, int]) -> Iterator[int]:
    """Yield the answers to both parts."""
    yield find_path(occupied, w, h, end)
    yield find_path(occupied, w, h, end, cheapest=True)


def find_path(
        occupied: set[tuple[int, int]], w: int, h: int,
        end: tuple[int, int], cheapest: bool = False) -> int:
    """Cost of the cheapest path from the top-left corner to end."""
    # pylint: disable=too-many-locals
    queue = [(0, 0, 0)]
    neighbours = {(-1, 0), (1, 0), (0, -1), (0, 1)}
    wide_neighbours = neighbours.union({(-1, -1), (1, -1), (-1, 1), (1, 1)})
    visited: set[tuple[int, int]] = set()
    while queue:
        length, x, y = heapq.heappop(queue)
        if (x, y) == end:
            return length
        for dx, dy in neighbours:
            nx = x + dx
            ny = y + dy
            if ((nx, ny) not in occupied and 0 <= nx < w and 0 <= ny < h
                    and (nx, ny) not in visited):
                if cheapest:
                    extra_cost = int(any(
                        (nx + tx, ny + ty) in occupied
                        for tx, ty in wide_neighbours))
                    heapq.heappush(queue, (length + 1 + extra_cost, nx, ny))
                else:
                    heapq.heappush(queue, (length + 1, nx, ny))
                visited.add((nx, ny))
    raise ValueError("No path found!")
