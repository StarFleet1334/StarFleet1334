#!/usr/bin/env python3
"""Measure a private project and write manifest.json.

The Action can only see public repositories, so the numbers for AETHER would
otherwise be a figure someone typed once and never revisited. This walks the
real tree and writes what it finds, so the CURRENT HEADING table is measured
rather than remembered.

    python .github/manifest.py C:/Users/User/Desktop/secret/aether

Then commit manifest.json — the push triggers the workflow and the README
follows. Run it whenever the shape of the project has actually changed; it is
not something to schedule.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "manifest.json"

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules",
             "data", "backups", "dist", "build", ".mypy_cache", ".pytest_cache"}


def walk(root: pathlib.Path, suffix: str):
    for p in root.rglob(f"*{suffix}"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def count(root: pathlib.Path, sub: str, suffix: str) -> tuple[int, int]:
    base = root / sub
    if not base.is_dir():
        return 0, 0
    files = list(walk(base, suffix))
    lines = 0
    for f in files:
        try:
            lines += sum(1 for _ in f.open("r", encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return len(files), lines


def human(n: int) -> str:
    return f"~{round(n / 1000)}k" if n >= 1000 else str(n)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    root = pathlib.Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"! {root} is not a directory")
        return 1

    py_files, py_lines = count(root, "aether", ".py")
    js_files, js_lines = count(root, "ui/js", ".js")
    _css_files, css_lines = count(root, "ui/css", ".css")
    total = py_lines + js_lines + css_lines

    if not py_files and not js_files:
        print(f"! found nothing to measure under {root}")
        return 1

    existing = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            pass

    existing.update({
        "surface": (f"{py_files} Python modules · {js_files} JS modules "
                    f"· {human(total)} lines"),
        "aether_lines": human(total),
    })
    existing.setdefault("heading", "AETHER - hands, face and voice")
    existing.setdefault("spine", "FastAPI over a websocket, vanilla JS, zero framework")
    existing.setdefault("eyes", "MediaPipe hand + face landmarks at frame rate")
    existing.setdefault("ears", "Vosk live preview, Whisper `medium.en` final — fully offline")
    existing.setdefault("rooms", "Canvas · Air Sketch (2D/3D) · Observatory · Codex · "
                                 "Palace · Watchtower · Console")
    existing.setdefault("trick", "A motion repeated ~6× gets *proposed back to you* to bind")

    OUT.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"- {py_files} py / {js_files} js / {css_lines} css lines")
    print(f"- wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
