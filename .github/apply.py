#!/usr/bin/env python3
"""Apply an approved proposal to decks.json.

Runs only after a human approved the survey. It edits data, never source, and
never touches README.md — the build does that afterwards from the new data.

    python .github/apply.py proposal.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECKSF = ROOT / "decks.json"


def main() -> int:
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "proposal.json")
    if not src.exists():
        print(f"! no proposal at {src}")
        return 1

    p = json.loads(src.read_text(encoding="utf-8"))
    data = json.loads(DECKSF.read_text(encoding="utf-8"))
    repo, action = p["repo"], p["action"]

    if action == "ignore":
        if repo in data.get("ignore", []):
            print(f"- {repo} is already ignored; nothing to do")
            return 0
        data.setdefault("ignore", []).append(repo)
        data["ignore"] = sorted(set(data["ignore"]))
        print(f"- ignore += {repo}")
    else:
        # Refuse to file the same repo twice. The survey warns about it; this
        # is the half that cannot be clicked past.
        for d in data["decks"]:
            for row in d["rows"]:
                if repo in row["repos"]:
                    print(f"! {repo} is already on the {d['key']} deck — "
                          f"edit decks.json by hand to change its wording")
                    return 1

        deck = next((d for d in data["decks"] if d["key"] == p["deck"]), None)
        if deck is None:
            print(f"! no deck called {p['deck']!r}; "
                  f"have {[d['key'] for d in data['decks']]}")
            return 1
        deck["rows"].append({"repos": [repo], "desc": p["desc"]})
        print(f"- {p['deck']} += {repo}: {p['desc']}")

    DECKSF.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(f"- wrote {DECKSF.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
