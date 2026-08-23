#!/usr/bin/env python3
"""Survey one repository and propose what the profile should do about it.

Reads a repo through the public API, prints an insight report to the Actions
job summary, and writes proposal.json — the exact change it would make to
decks.json. It never edits anything: .github/apply.py does that, and only
after a human has approved the run.

    python .github/survey.py --repo RepositoryAnalyzer
    python .github/survey.py --repo Chess --deck bridge --note "rules, drawn out"
    python .github/survey.py --repo Task2 --action ignore

The verdict is a heuristic and says so. Every signal it weighed is printed
with its weight, so the reviewer is approving a visible argument rather than
a number that appeared from nowhere.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER = os.environ.get("PROFILE_USER", "StarFleet1334")
ROOT = pathlib.Path(__file__).resolve().parent.parent
DECKSF = ROOT / "decks.json"
API = "https://api.github.com"

SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")
OUTPUT = os.environ.get("GITHUB_OUTPUT")

# A name that has only ever meant "I was trying something".
SCRATCH = re.compile(
    r"^(test|tests|demo|sample|temp|tmp|untitled|new|foo|bar|scratch|playground|"
    r"task\d*|part\w*|tt|try|todo|hello[-_]?world)\b", re.I)

# key -> what pushes a repo onto that deck. First match wins, in this order.
DECK_RULES = [
    ("science", re.compile(
        r"wiremock|gatling|carina|newrelic|lighthouse|selenium|junit|cypress|"
        r"playwright|jmeter|\btest(ing)?\b|\bqa\b|benchmark|load[-_]?test", re.I)),
    ("engineering", re.compile(
        r"kafka|cqrs|eureka|micro[-_]?service|spring|grpc|rabbit|stream|saga|"
        r"event[-_]?driven|inventory|\bapi\b|backend|service", re.I)),
    ("academy", re.compile(
        r"student|tutorial|course|lecture|beginner|advanced|teaching|exercise|"
        r"workshop|duckietown|\blx\b|edition", re.I)),
]

LANG_DECK = {"Go": "propulsion", "OCaml": "academy"}

lines: list[str] = []


def say(s: str = "") -> None:
    lines.append(s)
    print(s)


def get(path: str):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-survey",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def soft(path, default=None):
    """A missing sub-resource is information, not a crash: a repo with no
    README returns 404 and that absence is one of the signals."""
    try:
        return get(path)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return default


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.0f}"


def days_between(a: str, b: str) -> int:
    """Dates only, no clock: two ISO stamps in, whole days out."""
    def ord_(s):
        y, m, d = int(s[:4]), int(s[5:7]), int(s[8:10])
        return (367 * y - 7 * (y + (m + 9) // 12) // 4 + 275 * m // 9 + d)
    return ord_(b) - ord_(a)


# ─────────────────────────────────────────────────────────────────────────────

def gather(repo: str) -> dict:
    # Not soft(): the first call must say WHICH failure this is. Swallowing it
    # reported a rate limit as "does not exist", which sends the reader off to
    # check a repository name that was right all along.
    try:
        meta = get(f"/repos/{USER}/{repo}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SystemExit(f"! {USER}/{repo} does not exist, or is not public")
        if e.code in (403, 429):
            left = e.headers.get("X-RateLimit-Remaining")
            if left == "0":
                raise SystemExit(
                    "! the GitHub API rate limit is spent. Unauthenticated it is "
                    "60/hour; set GITHUB_TOKEN for 5000. Nothing was surveyed.")
            raise SystemExit(f"! {USER}/{repo} refused the request: {e}")
        raise SystemExit(f"! could not read {USER}/{repo}: {e}")
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise SystemExit(f"! could not reach the GitHub API: {e}")

    langs = soft(f"/repos/{USER}/{repo}/languages", {}) or {}
    commits = soft(f"/repos/{USER}/{repo}/commits?per_page=100", []) or []
    contributors = soft(f"/repos/{USER}/{repo}/contributors?per_page=100", []) or []
    releases = soft(f"/repos/{USER}/{repo}/releases?per_page=10", []) or []
    readme = soft(f"/repos/{USER}/{repo}/readme")
    contents = soft(f"/repos/{USER}/{repo}/contents/", []) or []

    readme_text = ""
    if readme and readme.get("content"):
        try:
            readme_text = base64.b64decode(readme["content"]).decode("utf-8", "replace")
        except (ValueError, TypeError):
            readme_text = ""

    dates = [c["commit"]["author"]["date"][:10]
             for c in commits if c.get("commit", {}).get("author", {}).get("date")]

    return {
        "meta": meta, "langs": langs, "commits": commits, "contributors": contributors,
        "releases": releases, "readme": readme, "readme_text": readme_text,
        "contents": [c["name"] for c in contents if isinstance(c, dict)],
        "first_commit": min(dates) if dates else None,
        "last_commit": max(dates) if dates else None,
    }


def judge(repo: str, g: dict) -> tuple[int, list[tuple[bool, int, str]]]:
    m, s = g["meta"], []

    def sig(ok, weight, text):
        s.append((bool(ok), weight, text))

    created, pushed = m["created_at"][:10], (m.get("pushed_at") or m["created_at"])[:10]
    lifespan = days_between(created, pushed)
    ncommits = len(g["commits"])
    readme_len = len(g["readme_text"])
    build_files = {"pom.xml", "build.gradle", "build.gradle.kts", "go.mod",
                   "requirements.txt", "pyproject.toml", "package.json",
                   "Dockerfile", "docker-compose.yml", "Makefile", "Cargo.toml"}
    has_build = sorted(build_files & set(g["contents"]))

    sig(m.get("description"), 2, "has a description")
    sig(readme_len >= 400, 2, f"README is {readme_len} bytes (≥ 400)")
    sig(ncommits >= 10, 2, f"{ncommits}{'+' if ncommits == 100 else ''} commits (≥ 10)")
    sig(has_build, 1, f"a real build file: {', '.join(has_build) or 'none'}")
    sig(lifespan >= 14, 2, f"worked on across {lifespan} days (≥ 14)")
    sig(m.get("size", 0) >= 100, 1, f"{m.get('size', 0)} KB on disk (≥ 100)")
    sig(m.get("stargazers_count", 0) >= 1, 1,
        f"{m.get('stargazers_count', 0)} stars")
    sig(g["releases"], 1, f"{len(g['releases'])} releases")

    sig(not m.get("archived"), 0, "not archived")
    sig(not m.get("fork"), 0, "not a fork")
    if m.get("archived"):
        s.append((False, -3, "ARCHIVED"))
    if m.get("fork"):
        s.append((False, -4, "a fork — someone else's work"))
    if SCRATCH.match(repo):
        s.append((False, -4, f"the name '{repo}' reads as scratch work"))
    if ncommits < 3:
        s.append((False, -3, f"only {ncommits} commits"))
    if not readme_len:
        s.append((False, -2, "no README at all"))

    score = sum(w for ok, w, _ in s if (ok and w > 0) or (not ok and w < 0))
    return score, s


def suggest_deck(repo: str, g: dict) -> tuple[str, str]:
    m = g["meta"]
    hay = " ".join([repo, m.get("description") or "",
                    " ".join(m.get("topics") or []), " ".join(g["contents"])])
    for key, rx in DECK_RULES:
        hit = rx.search(hay)
        if hit:
            return key, f"matched /{hit.group(0)}/"
    top = max(g["langs"], key=g["langs"].get) if g["langs"] else None
    if top in LANG_DECK:
        return LANG_DECK[top], f"written in {top}"
    return "bridge", "nothing more specific matched"


def suggest_note(repo: str, g: dict) -> str:
    desc = (g["meta"].get("description") or "").strip().rstrip(".")
    if desc:
        return desc[0].lower() + desc[1:] if desc[:1].isupper() and desc[:2] != desc[:2].upper() else desc
    top = max(g["langs"], key=g["langs"].get) if g["langs"] else "code"
    return f"{top}, and not yet described — write one clause here"


# ─────────────────────────────────────────────────────────────────────────────

def report(repo: str, g: dict, score: int, signals, deck: str, why: str,
           note: str, verdict: str, action: str, already: str | None) -> None:
    m = g["meta"]
    say(f"## ⌖ Survey — `{repo}`")
    say()
    if already:
        say(f"> **Already filed** on the *{already}* deck. Approving will add a "
            f"second row, which is almost never what you want — edit "
            f"`decks.json` directly instead.")
        say()

    say("| | |")
    say("|:--|:--|")
    say(f"| description | {m.get('description') or '_none_'} |")
    say(f"| created | {m['created_at'][:10]} |")
    say(f"| last push | {(m.get('pushed_at') or '')[:10]} |")
    say(f"| commits seen | {len(g['commits'])}"
        f"{' (API caps the page at 100)' if len(g['commits']) == 100 else ''} |")
    if g["first_commit"]:
        say(f"| commit span | {g['first_commit']} → {g['last_commit']} |")
    say(f"| size | {m.get('size', 0)} KB |")
    say(f"| stars / forks / watchers | {m.get('stargazers_count', 0)} / "
        f"{m.get('forks_count', 0)} / {m.get('subscribers_count', 0)} |")
    say(f"| open issues | {m.get('open_issues_count', 0)} |")
    say(f"| licence | {(m.get('license') or {}).get('spdx_id') or '_none_'} |")
    say(f"| topics | {', '.join(m.get('topics') or []) or '_none_'} |")
    say(f"| releases | {len(g['releases'])} |")
    say(f"| README | {len(g['readme_text'])} bytes |")
    say(f"| contributors | {len(g['contributors'])} |")
    say(f"| archived / fork | {m.get('archived')} / {m.get('fork')} |")
    say()

    if g["langs"]:
        total = sum(g["langs"].values()) or 1
        say("**Languages**")
        say()
        say("| language | bytes | share |")
        say("|:--|--:|--:|")
        for name, size in sorted(g["langs"].items(), key=lambda kv: -kv[1]):
            say(f"| {name} | {human_bytes(size)} | {100 * size / total:.0f}% |")
        say()

    if g["contents"]:
        say(f"**Top level** — `{'`, `'.join(sorted(g['contents'])[:18])}`")
        say()

    head = [ln for ln in g["readme_text"].splitlines() if ln.strip()][:3]
    if head:
        say("**README opens with**")
        say()
        for ln in head:
            say("> " + ln.strip()[:160])
        say()

    say("### Signals")
    say()
    say("| | weight | signal |")
    say("|:--:|--:|:--|")
    for ok, w, text in signals:
        if w == 0:
            continue
        fired = (ok and w > 0) or (not ok and w < 0)
        say(f"| {'✓' if fired else '·'} | {w:+d} | {text} |")
    say(f"| | **{score:+d}** | **total** |")
    say()

    badge = {"list": "✦ WORTH LISTING", "borderline": "◈ BORDERLINE",
             "ignore": "· NOT WORTH LISTING"}[verdict]
    say(f"### Verdict — {badge}  (score {score}, list ≥ 4, ignore < 2)")
    say()
    say("This is a heuristic over the signals above, not a judgement. "
        "The approval gate exists because you may disagree with it, and you "
        "are the one who is right.")
    say()

    say("### Proposed change to `decks.json`")
    say()
    if action == "ignore":
        say("Add to the **ignore** list — it will stop appearing under NEW ARRIVALS:")
        say()
        say("```json")
        say(f'  "{repo}"')
        say("```")
    else:
        say(f"Append to the **{deck}** deck _({why})_:")
        say()
        say("```json")
        say(json.dumps({"repos": [repo], "desc": note}, indent=2, ensure_ascii=False))
        say("```")
    say()
    say("Approve the **apply** job to write it, run the build and push. "
        "Reject, and nothing at all is changed.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--deck", default="auto")
    ap.add_argument("--note", default="")
    ap.add_argument("--action", default="file", choices=("file", "ignore"))
    ap.add_argument("--out", default="proposal.json")
    a = ap.parse_args()

    repo = a.repo.strip().strip("/").split("/")[-1]
    g = gather(repo)

    score, signals = judge(repo, g)
    verdict = "list" if score >= 4 else ("borderline" if score >= 2 else "ignore")

    auto_deck, why = suggest_deck(repo, g)
    deck = auto_deck if a.deck in ("", "auto") else a.deck
    if a.deck not in ("", "auto"):
        why = "you chose it"
    note = a.note.strip() or suggest_note(repo, g)

    already = None
    if DECKSF.exists():
        data = json.loads(DECKSF.read_text(encoding="utf-8"))
        for d in data.get("decks", []):
            for row in d["rows"]:
                if repo in row["repos"]:
                    already = d["key"]
        if repo in data.get("ignore", []):
            already = "ignore"

    report(repo, g, score, signals, deck, why, note, verdict, a.action, already)

    proposal = {"repo": repo, "action": a.action, "deck": deck, "desc": note,
                "verdict": verdict, "score": score, "already": already}
    pathlib.Path(a.out).write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")

    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    if OUTPUT:
        with open(OUTPUT, "a", encoding="utf-8") as f:
            f.write(f"verdict={verdict}\nscore={score}\ndeck={deck}\n"
                    f"repo={repo}\naction={a.action}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
