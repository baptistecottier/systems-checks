"""
mission #5
title: nanofab frustration
"""

import heapq
import re
from collections.abc import Iterator
from math import inf

from shapely import MultiPolygon, Polygon, union_all


def preprocessing(puzzle_input: str):
    """Parse each line as the rectangle given by its four vertices."""
    coords = [
        (int(a), int(b))
        for a, b in re.findall(r'(\d+),(\d+)', puzzle_input)]

    rectangles = [
        Polygon(coords[i:i+4]) for i in range(0, len(coords), 4)
    ]
    return rectangles


def solver(data: list[Polygon]) -> Iterator[int]:
    """Yield the answers to both parts."""
    shape = union_all(data)
    assert isinstance(shape, MultiPolygon)
    perimeter = int(shape.length)
    yield perimeter

    tl_corners = [top_left_coord(poly) for poly in shape.geoms]
    states: dict[tuple[int, int], int] = {
        (i, 1 << i): manhattan((0, 0), corner)
        for i, corner in enumerate(tl_corners)
    }
    distances = [
        [manhattan(a, b) for b in tl_corners] for a in tl_corners]
    queue = [(d, i, mask) for (i, mask), d in states.items()]
    heapq.heapify(queue)
    target = 2 ** len(tl_corners) - 1
    while queue:
        d, i, visited = heapq.heappop(queue)
        if states.get((i, visited), inf) < d:
            continue
        if i == -1:
            yield d + perimeter
            return
        if visited == target:
            heapq.heappush(
                queue, (d + manhattan(tl_corners[i], (0, 0)), -1, visited))
        for ni in range(len(tl_corners)):
            if visited >> ni & 1:
                continue
            nv = visited | (1 << ni)
            nd = d + distances[i][ni]
            if states.get((ni, nv), inf) <= nd:
                continue
            heapq.heappush(queue, (nd, ni, nv))
            states[(ni, nv)] = nd


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Distance between two points moving only along the axes."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def top_left_coord(poly: Polygon) -> tuple[int, int]:
    """Vertex with the smallest y, then the smallest x."""
    coords = sorted(poly.exterior.coords, key=lambda x: (x[1], x[0]))
    return (int(coords[0][0]), int(coords[0][1]))
