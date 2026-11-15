"""
mission #8
title: rubbish race
"""

import heapq
import re
from collections import defaultdict
from collections.abc import Iterator

Networks = defaultdict[str, dict[str, int]]
Garbages = dict[str, int]


def preprocessing(puzzle_input: str) -> tuple[Networks, Garbages]:
    """Parse the puzzle input into the tunnel network and rubbish levels."""
    networks: Networks = defaultdict(dict)
    tunnels = re.findall(r'(\w{3})-\[(\d+)\]>(\w{3})', puzzle_input)
    for tunnel_in, tunnel_len, tunnel_out in tunnels:
        networks[tunnel_in][tunnel_out] = int(tunnel_len)

    garbages: Garbages = {
        n: int(v) for (n, v) in re.findall(r'(\w{3}) (\d+)', puzzle_input)}
    return networks, garbages


def solver(networks: Networks, garbages: Garbages) -> Iterator[int | None]:
    """Yield the fastest beacon time, then the same with rubbish."""
    yield fastest_beacon_time(networks)
    yield fastest_beacon_time(networks, garbages)


def fastest_beacon_time(
        networks: Networks, garbages: Garbages | None = None) -> int | None:
    """Seconds until the first beacon reaches the incinerator."""
    if garbages is None:
        garbages = defaultdict(int)

    chutes = set(networks.keys()).difference(
        {vv for v in networks.values() for vv in v})

    queue = [(0, node) for node in chutes]
    while queue:
        time, pos = heapq.heappop(queue)

        # Count droids occurences
        cnt = 1
        while (droid := heapq.heappop(queue)) == (time, pos):
            cnt += 1
        heapq.heappush(queue, droid)

        time += -(-garbages[pos] // cnt)
        garbages[pos] = 0

        if pos not in networks:
            return time

        for direction in networks[pos]:
            heapq.heappush(queue, (time + networks[pos][direction], direction))

    return None
