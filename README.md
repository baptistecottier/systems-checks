# Solutions for [Systems Check](https://systemscheck.dev) missions

<!-- scoreboard:start -->
## Scoreboard

| Missions | ★ |
| :-- | --: |
| `████ ` `     ` `     ` | 8/30 |

| # | Mission | ★ | Time |
| --: | :-- | :-: | --: |
| 1 | [critical capacity](https://systemscheck.dev/missions/1) | ★★ | 1 ms |
| 2 | [chaos in the cargo bay](https://systemscheck.dev/missions/2) | ★★ | 13 ms |
| 3 | [transmission trouble](https://systemscheck.dev/missions/3) | ★★ | 7 ms |
| 4 | [ghosts in the cleaning droids](https://systemscheck.dev/missions/4) | ★★ | 1 ms |

<sub>`█` solved in under 10 s &emsp; `▓` solved in under 5 min &emsp; `░` one part only &emsp; ` ` not solved<br>Python 3.15.2 · Apple M3 · 3 November 2026</sub>
<!-- scoreboard:end -->

## Benchmark

```bash
python3 benchmark.py
```

Each mission runs on the personal input in its own process with a 5 minute
timeout; the time covers preprocessing and solving both parts. Answers are
checked against the ones Puzzle Submitter recorded as correct; a part with no
recorded answer counts as solved but cannot be verified. `benchmark.py` then
rewrites the scoreboard above.
