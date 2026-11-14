"""
mission #6
title: asteroid alley
"""

import re


def preprocessing(puzzle_input: str):
    """Parse the puzzle input into a list of [x, y, vx, vy] asteroids."""
    numbers = list(map(int, re.findall(r'(-?\d+)', puzzle_input)))
    asteroids = [
        numbers[i:i+4]
        for i in range(0, len(numbers), 4)]
    return asteroids


def solver(asteroids: list[list[int]]):
    """Yield the collision count for no burn, then for the best burn."""
    collisions = [
        sum(
            (y - ((x + dx) / vx) * (vy - 1) == 0) and (x + dx) // vx < 10_000
            for x, y, vx, vy in asteroids
        )
        for dx in range(-10, 11)
    ]
    yield collisions[10]
    yield min(collisions)
