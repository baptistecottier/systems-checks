#!/usr/bin/env python3

"""
Benchmark every mission against the known answers and write the scoreboard
into README.md.

Each mission runs in its own process with a timeout (5 minutes by default).
The measured time covers preprocessing and solving both parts, not
interpreter start-up or imports. Inputs are the personal ones cached by the
Puzzle Submitter extension; expected answers are the ones it recorded as
correct. A part with no recorded answer cannot be verified: it counts as
solved and is listed as unverified.

Example:
    python3 benchmark.py
"""

import argparse
import datetime
import importlib.util
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
MISSIONS = ROOT / "missions"
README = ROOT / "README.md"
INPUT_STORE = ROOT / ".puzzle-submitter" / "systemscheck.json"
EXTENSION = "baptistecottier.puzzle-submitter"
SITE = "https://systemscheck.dev/missions"
N_MISSIONS = 15
N_PARTS = 2
FAST = 10.0
START, END = "<!-- scoreboard:start -->", "<!-- scoreboard:end -->"


# Inputs and expected answers


def load_inputs() -> dict[int, str]:
    """Personal input of each mission, from Puzzle Submitter's store."""
    with open(INPUT_STORE, encoding="utf-8") as f:
        store = json.load(f).get("", {})
    return {
        int(mission): str(parts["1"]).rstrip("\n")
        for mission, parts in store.items()
        if "1" in parts
    }


def load_answers() -> dict[int, dict[str, str]]:
    """
    Answers recorded as correct by Puzzle Submitter for this folder, as
    {mission: {"1": answer, "2": answer}}. They live in the extension's
    workspace state, inside the VS Code workspace storage of this folder.
    """
    answers: dict[int, dict[str, str]] = {}
    storages = [
        Path.home() / "Library/Application Support" / app / "User"
        / "workspaceStorage"
        for app in ("Code", "Code - Insiders")
    ]
    for storage in storages:
        for workspace in storage.glob("*/workspace.json"):
            try:
                folder = json.loads(
                    workspace.read_text(encoding="utf-8")).get("folder", "")
            except (OSError, json.JSONDecodeError):
                continue
            if unquote(urlparse(folder).path).rstrip("/") != str(ROOT):
                continue
            database = workspace.with_name("state.vscdb").as_uri() + "?mode=ro"
            try:
                with closing(sqlite3.connect(database, uri=True)) as db:
                    row = db.execute(
                        "SELECT value FROM ItemTable WHERE key = ?",
                        (EXTENSION,)).fetchone()
            except sqlite3.Error:
                continue
            state: dict[str, Any] = json.loads(row[0]) if row else {}
            for key, recorded in state.items():
                match = re.fullmatch(
                    r"puzzleSubmitter\.progress\.systemscheck\.\.(\d+)", key)
                if match and isinstance(recorded, dict):
                    answers.setdefault(int(match[1]), {}).update(
                        {str(p): normalise(a) for p, a in recorded.items()})
    return answers


def normalise(answer: Any) -> str:
    """String form of an answer, as it would be submitted."""
    if isinstance(answer, float) and answer.is_integer():
        answer = int(answer)
    return str(answer).strip()


# Running a mission


def child(path: str) -> None:
    """
    Run one mission on the input read from stdin, the way Puzzle Submitter
    does: preprocessing(text), then solver() on its result, unpacked when it
    is a tuple. Each answer is written to stdout as a JSON line as soon as it
    is known; everything the mission prints is discarded.
    """
    out = os.fdopen(os.dup(1), "w", encoding="utf-8")
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)

    def emit(**message: Any) -> None:
        out.write(json.dumps(message) + "\n")
        out.flush()

    data: Any = sys.stdin.read()
    try:
        spec = importlib.util.spec_from_file_location("mission", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        start = time.perf_counter()
        if hasattr(module, "preprocessing"):
            data = module.preprocessing(data)
        args = list(data) if isinstance(data, tuple) else [data]
        result = module.solver(*args)
        if result is None:
            result = ()
        elif isinstance(result, (str, bytes, dict)) or not isinstance(
                result, (Iterator, list, tuple)):
            result = (result,)
        for item in result:
            if item is not None:
                emit(answer=normalise(item), time=time.perf_counter() - start)
        emit(done=time.perf_counter() - start)
    except BaseException as exc:  # pylint: disable=broad-exception-caught
        emit(error=f"{type(exc).__name__}: {str(exc)[:200]}")
    out.close()
    os._exit(0)  # pylint: disable=protected-access


def run(path: Path, text: str, timeout: float) -> dict[str, Any]:
    """Run one mission in its own process and collect its answers."""
    command = [sys.executable, __file__, "--child", str(path)]
    try:
        proc = subprocess.run(
            command, input=text, capture_output=True, text=True,
            timeout=timeout, check=False, cwd=ROOT)
        lines, timed_out = proc.stdout.splitlines(), False
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or b""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        lines, timed_out = partial.splitlines(), True
    answers: list[str] = []
    total: float | None = None
    error: str | None = None
    for line in lines:
        message: dict[str, Any] = json.loads(line)
        if "answer" in message:
            answers.append(message["answer"])
        elif "done" in message:
            total = message["done"]
        elif "error" in message:
            error = message["error"]
    return {"answers": answers, "time": total, "timeout": timed_out,
            "error": error}


def grade(result: dict[str, Any], expected: dict[str, str]) -> list[str]:
    """State of each part: ok, unverified, wrong or missing."""
    states: list[str] = []
    for part in range(1, N_PARTS + 1):
        given = result["answers"][part - 1] \
            if part <= len(result["answers"]) else None
        known = expected.get(str(part))
        if given is None:
            states.append("missing")
        elif known is None:
            states.append("unverified")
        else:
            states.append("ok" if given == known else "wrong")
    return states


# Scoreboard


def title(path: Path) -> str:
    """Mission title, from the docstring of its file."""
    match = re.search(r"^title:\s*(.+)$", path.read_text(encoding="utf-8"),
                      re.MULTILINE)
    return match[1].strip() if match else ""


def symbol(states: list[str], elapsed: float | None) -> str:
    """One character per mission, as on the Advent of Code scoreboard."""
    solved = sum(s in ("ok", "unverified") for s in states)
    if solved == N_PARTS:
        return "█" if elapsed is not None and elapsed < FAST else "▓"
    return "░" if solved else " "


def render(board: dict[int, dict[str, Any]]) -> str:
    """Markdown of the scoreboard, between the README markers."""
    cells = "".join(board[m]["symbol"] for m in range(1, N_MISSIONS + 1))
    blocks = " ".join(f"`{cells[i:i + 5]}`" for i in range(0, len(cells), 5))
    stars = sum(entry["stars"] for entry in board.values())
    rows = [
        "## Scoreboard",
        "",
        "| Missions | ★ |",
        "| :-- | --: |",
        f"| {blocks} | {stars}/{N_MISSIONS * N_PARTS} |",
        "",
        "| # | Mission | ★ | Time |",
        "| --: | :-- | :-: | --: |",
    ]
    for mission in range(1, N_MISSIONS + 1):
        entry = board[mission]
        if not entry["stars"]:
            continue
        stars_cell = "★" * entry["stars"] + "☆" * (N_PARTS - entry["stars"])
        elapsed = entry["time"]
        time_cell = f"{elapsed * 1000:.0f} ms" if elapsed is not None else ""
        rows.append(
            f"| {mission} | [{entry['title']}]({SITE}/{mission}) "
            f"| {stars_cell} | {time_cell} |")
    today = datetime.date.today()
    rows += [
        "",
        f"<sub>`█` solved in under {FAST:.0f} s &emsp; "
        "`▓` solved in under 5 min &emsp; `░` one part only &emsp; "
        "` ` not solved<br>"
        f"Python {platform.python_version()} · {machine()} · "
        f"{today.day} {today:%B %Y}</sub>",
    ]
    return "\n".join([START, *rows, END])


def machine() -> str:
    """Name of the processor, e.g. Apple M3."""
    try:
        return subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
            text=True, check=True).stdout.strip() or platform.machine()
    except (OSError, subprocess.CalledProcessError):
        return platform.machine()


def write_readme(scoreboard: str) -> None:
    """Replace the scoreboard in README.md, or add it after the title."""
    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if START in text and END in text:
        before, rest = text.split(START, 1)
        text = before + scoreboard + rest.split(END, 1)[1]
    else:
        head, _, tail = text.partition("\n\n")
        text = f"{head}\n\n{scoreboard}\n\n{tail}".rstrip("\n") + "\n"
    README.write_text(text, encoding="utf-8")


# Command line


def main() -> None:
    """Benchmark every mission and rewrite the scoreboard."""
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    inputs, answers = load_inputs(), load_answers()
    board: dict[int, dict[str, Any]] = {}
    for mission in range(1, N_MISSIONS + 1):
        path = MISSIONS / f"mission_{mission:02d}.py"
        entry: dict[str, Any] = {
            "title": title(path) if path.exists() else "",
            "symbol": " ", "stars": 0, "time": None}
        if path.exists() and mission in inputs:
            result = run(path, inputs[mission], args.timeout)
            states = grade(result, answers.get(mission, {}))
            entry["symbol"] = symbol(states, result["time"])
            entry["stars"] = sum(s in ("ok", "unverified") for s in states)
            entry["time"] = result["time"]
            note = result["error"] or ("timeout" if result["timeout"] else "")
            print(f"mission {mission:2d}: {' '.join(states)} {note}".rstrip())
        board[mission] = entry
    write_readme(render(board))
    print(f"Scoreboard written to {README.name}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        main()
