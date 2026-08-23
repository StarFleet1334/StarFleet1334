#!/usr/bin/env python3
"""Rebuild README.md from README.tpl.md and live GitHub data.

Stdlib only. Reads the public API, fills the <!--LOG:x--> blocks in the
template, writes README.md. Nothing here uses the wall clock: every value in
the output comes off the API, so the file changes only when the account
actually changed, and the workflow commits only when the file changes.

    python .github/build.py            # writes README.md
    python .github/build.py --check    # writes nothing, prints the diff-ability

env:  GITHUB_TOKEN   raises the rate limit to 5000/hr (the Action supplies it)
      PROFILE_USER   whose profile to build (default: StarFleet1334)
"""

from __future__ import annotations

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
TPL = ROOT / "README.tpl.md"
OUT = ROOT / "README.md"
MANIFEST = ROOT / "manifest.json"

API = "https://api.github.com"


# ─────────────────────────────────────────────────────────────────────────────
# THE HOLD — the only hand-edited data. File a new repo here and it moves out
# of NEW ARRIVALS on the next run. A row whose repos have all vanished is
# skipped, so a deleted repo never leaves a dead link behind.
# ─────────────────────────────────────────────────────────────────────────────

DECKS = [
    {
        "key": "engineering",
        "icon": "⚭",
        "title": "ENGINEERING DECK",
        "blurb": "distributed Java, events, contracts",
        "rows": [
            (["ecommerce-inventory-platform"], "the largest of them — inventory, end to end"),
            (["KafkaInMicroService"], "Kafka wired through a service boundary"),
            (["KafkaRatingService"], "ratings as an event stream"),
            (["CQRS"], "command/query separation, taken seriously"),
            (["MicroServicesGEureka"], "discovery with Eureka"),
            (["Spring-Boot-MicroService"], "the baseline the rest grew out of"),
            (["Tolerant-Streams"], "streams that survive bad input"),
            (["SCom", "2Com"], "service-to-service, the plumbing of it"),
        ],
    },
    {
        "key": "science",
        "icon": "⌖",
        "title": "SCIENCE DECK",
        "blurb": "proving it works before claiming it does",
        "rows": [
            (["WireMock-Demo", "WireMock-Api", "WireMock-Data"],
             "three angles on stubbing a dependency you don't own"),
            (["GatlingReport"], "load, measured rather than assumed"),
            (["newrelic-lighthouse-demo"], "observability meeting a front-end budget"),
            (["CarinaProject"], "UI automation"),
            (["Demo-TestService"], "the scaffold under all of it"),
        ],
    },
    {
        "key": "propulsion",
        "icon": "⚙",
        "title": "PROPULSION",
        "blurb": "Go, and things that had to be fast or small",
        "rows": [
            (["Channels-and-Routines-GoLang-"], "concurrency from first principles"),
            (["TransitionToGo"], "the crossing from JVM to Go, written down"),
            (["WebScrapper_Go", "FileFinder"], "small tools that do one thing"),
            (["GoUI", "Animated-Ball", "Clock"], "Go with a face on it"),
            (["Little-Game-in-GoLang", "cards"], "the fun ones"),
        ],
    },
    {
        "key": "bridge",
        "icon": "◈",
        "title": "THE BRIDGE",
        "blurb": "things people actually touch",
        "rows": [
            (["AETHER"], "gesture · face · voice workspace — {aether_lines} lines"),
            (["QuiziGeneratorWebExtension"], "turns the page you're reading into a quiz"),
            (["RepositoryAnalyzer"], "points a lens at a codebase and reports back"),
            (["GymCRM-System", "GymApplication"], "one real domain, modelled twice"),
            (["Chess", "steganography"], "rules, and hiding things inside pictures"),
            (["Chat-Sytem-", "Java-Chat-App"], "sockets, in two languages"),
        ],
    },
    {
        "key": "academy",
        "icon": "⌂",
        "title": "THE ACADEMY",
        "blurb": "repos written to be read by someone else",
        "rows": [
            (["Ocaml-For-Begginer-Students-Edition-"],
             "functional programming for people meeting it first"),
            (["Java-For-Students-Advanced-"], "the second pass, where it gets interesting"),
            (["duckietown-lx"], "autonomous driving exercises, on very small robots"),
        ],
    },
]

# Repos that exist but are private, so the API will never list them. Rendered
# without a link; counted nowhere.
PRIVATE = {"AETHER"}

# Repos that should never appear in NEW ARRIVALS (scratch, forks, coursework).
IGNORE = {"StarFleet1334", "partTwo", "Task2", "TT", "Test", "System", "Project-A"}

# One line per year of the log. A year with data but no line here gets its
# repos listed instead, so the timeline can never silently stop at 2026.
YEAR_NOTES = {
    2021: ["first commit pushed into the dark"],
    2022: ["java, properly", "data structures and the JVM's temper"],
    2023: ["services, queues, contracts"],
    2024: ["kafka, CQRS, eureka", "go's concurrency",
           "wiremock, gatling, new relic", "ocaml and java, written for students"],
    2025: ["an inventory platform", "a repository analyzer",
           "a quiz generator that lives in the browser"],
    2026: ["AETHER - hands, face, voice, and an agent at the desk"],
}

# Language byte counts are the truth, but a few names read better rolled up.
LANG_ALIAS = {"HTML": "HTML/CSS", "CSS": "HTML/CSS", "SCSS": "HTML/CSS"}
LANG_SKIP = {"Dockerfile", "Makefile", "Batchfile", "Shell", "Procfile"}

# What each language is actually for here. Missing → the bar renders bare.
LANG_NOTE = {
    "Java": "services, CQRS, Kafka, Eureka, chat, CRM",
    "Go": "goroutines, scrapers, a file finder, a UI, a clock",
    "Python": "AETHER's entire backend — FastAPI, MediaPipe, Whisper",
    "JavaScript": "vanilla, no framework, on purpose",
    "HTML/CSS": "hand-written, every rule of it",
    "Dart": "a chat system that had to run on a phone",
    "Kotlin": "an Android detour",
    "OCaml": "a teaching language, and a good one",
    "C": "when nothing else was close enough",
    "TypeScript": "where the types earned their keep",
}


# ─────────────────────────────────────────────────────────────────────────────
# the API, defensively
# ─────────────────────────────────────────────────────────────────────────────

def get(path: str):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-log",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r), r.headers


def paged(path: str) -> list:
    out, page = [], 1
    while page <= 10:
        sep = "&" if "?" in path else "?"
        body, _ = get(f"{path}{sep}per_page=100&page={page}")
        if not body:
            break
        out.extend(body)
        if len(body) < 100:
            break
        page += 1
    return out


def try_get(path, default=None):
    """A single failed call must never take the whole log down."""
    try:
        body, _ = get(path)
        return body
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"  ! {path}: {e}", file=sys.stderr)
        return default


# ─────────────────────────────────────────────────────────────────────────────
# blocks
# ─────────────────────────────────────────────────────────────────────────────

BOX_W = 58


def box(lines: list[str]) -> str:
    """A console box whose right edge cannot drift — every line is padded here
    rather than by hand. Keep the contents to width-1 characters: an ambiguous
    -width glyph is exactly what makes these boxes skew in someone's font."""
    out = ["╔" + "═" * BOX_W + "╗"]
    for s in lines:
        # a two-space gutter, kept by truncating rather than by trusting the
        # caller: a line that grows into the right wall reads as a rendering
        # bug even when the edge is still perfectly straight
        if len(s) > BOX_W - 2:
            s = s[:BOX_W - 3] + "…"
        out.append("║" + s.ljust(BOX_W) + "║")
    out.append("╚" + "═" * BOX_W + "╝")
    return "\n".join(out)


def block_surface(manifest) -> str:
    """The current project is private, so the API knows nothing about it.
    manifest.json is the one place the desk itself gets to speak; refresh it
    with .github/manifest.py and the numbers here follow the real tree."""
    m = manifest
    rows = [
        ("Surface", m.get("surface", "74 Python modules · 66 JS modules · ~81k lines")),
        ("Spine", m.get("spine", "FastAPI over a websocket, vanilla JS, zero framework")),
        ("Eyes", m.get("eyes", "MediaPipe hand + face landmarks at frame rate")),
        ("Ears", m.get("ears", "Vosk live preview, Whisper `medium.en` final — fully offline")),
        ("Rooms", m.get("rooms", "Canvas · Air Sketch (2D/3D) · Observatory · Codex · "
                                 "Palace · Watchtower · Console")),
        ("The trick", m.get("trick", "A motion repeated ~6× gets *proposed back to you* to bind")),
    ]
    out = ["| | |", "|---|---|"]
    out += [f"| **{k}** | {v} |" for k, v in rows]
    return "\n".join(out)


def work(repos):
    """Every repo except this one.

    The profile repo is pushed by the workflow itself, so leaving it in makes
    it permanently the newest thing on the account: the header would read
    "last seen in StarFleet1334" forever, and the stamp would move on every
    run — which quietly destroys the property the whole design rests on, that
    the file changes only when something actually happened.
    """
    return [r for r in repos
            if r["name"].lower() != USER.lower() and not r.get("fork")]


def block_stardate(u, repos, langs, manifest) -> str:
    since = (u.get("created_at") or "")[:10]
    crew = " · ".join(n for n, _ in langs[:4]) or "—"
    mine = work(repos)
    newest = mine[0]["name"] if mine else "—"
    heading = manifest.get("heading", "AETHER - hands, face and voice")

    rows = [
        "",
        "        S T A R F L E E T  ·  1 3 3 4",
        "        open log / flight deck",
        "",
        "   " + "─" * 48,
        "",
        f"   callsign      {u.get('name') or USER}",
        f"   on station    since {since}",
        f"   manifest      {len(repos)} public repositories",
        f"   crewed by     {crew}",
        f"   last seen in  {newest}",
        f"   heading       {heading}",
        "",
    ]
    return box(rows)


def block_badges(u, repos) -> str:
    def badge(label, value, color):
        lab = urllib.parse.quote(label)
        val = urllib.parse.quote(str(value))
        return (f'<img src="https://img.shields.io/badge/{lab}-{val}-0d1117'
                f'?style=flat-square&labelColor=0d1117&color={color}" alt="{label} {value}" />')

    return "\n&nbsp;\n".join([
        badge("repos", len(repos), "58a6ff"),
        badge("followers", u.get("followers", 0), "58a6ff"),
        badge("primary instrument", "hands", "f0883e"),
    ])


def block_systems(langs) -> str:
    if not langs:
        return "_language telemetry unavailable this run._"
    top = langs[:8]
    peak = top[0][1] or 1
    out = ["| | instrument | where it actually shows up |",
           "|:--|:--|:--|"]
    for name, size in top:
        filled = max(1, round(10 * size / peak))
        bar = "▰" * filled + "▱" * (10 - filled)
        note = LANG_NOTE.get(name, "")
        out.append(f"| `{bar}` | **{name}** | {note} |")
    return "\n".join(out)



def block_timeline(repos) -> str:
    by_year: dict[int, list] = {}
    for r in repos:
        y = int((r.get("created_at") or "0000")[:4] or 0)
        by_year.setdefault(y, []).append(r["name"])
    years = sorted(set(by_year) | set(YEAR_NOTES))
    lines = ["```mermaid", "timeline", "    title trajectory"]
    for y in years:
        if y < 2000:
            continue
        notes = YEAR_NOTES.get(y) or by_year.get(y, [])[:3]
        if not notes:
            continue
        safe = [n.replace(":", "-") for n in notes]
        lines.append(f"    {y} : " + " : ".join(safe))
    lines.append("```")
    return "\n".join(lines)


def block_hold(index, manifest) -> str:
    aether_lines = manifest.get("aether_lines", "~81k")
    out = []
    for d in DECKS:
        rows = []
        for names, desc in d["rows"]:
            cells = []
            for n in names:
                if n in PRIVATE:
                    cells.append(f"**{n}** &nbsp;<sub>private, for now</sub>")
                elif n in index:
                    cells.append(f"[`{n}`](https://github.com/{USER}/{n})")
            if not cells:
                continue  # every repo in this row is gone; drop the dead links
            rows.append(f"| {' · '.join(cells)} | {desc.format(aether_lines=aether_lines)} |")
        if not rows:
            continue
        out.append("<details>")
        out.append(f"<summary><b>{d['icon']} &nbsp;{d['title']}</b> &nbsp;— {d['blurb']}</summary>")
        out.append("<br>\n")
        out.append("| repo | what it is |")
        out.append("|:--|:--|")
        out.extend(rows)
        out.append("\n</details>\n")
    return "\n".join(out)


def block_arrivals(repos, index) -> str:
    filed = {n for d in DECKS for names, _ in d["rows"] for n in names}
    unfiled = [r for r in work(repos)
               if r["name"] not in filed
               and r["name"] not in IGNORE]
    unfiled.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    if not unfiled:
        return ("<sub>Every repository is filed. The hold is in order.</sub>")
    rows = ["| repo | language | first commit |", "|:--|:--|:--|"]
    for r in unfiled[:8]:
        lang = r.get("language") or "—"
        rows.append(f"| [`{r['name']}`](https://github.com/{USER}/{r['name']}) "
                    f"| {lang} | {(r.get('created_at') or '')[:10]} |")
    tail = ""
    if len(unfiled) > 8:
        tail = f"\n\n<sub>…and {len(unfiled) - 8} more not yet filed.</sub>"
    return "\n".join(rows) + tail


def block_recent(repos) -> str:
    live = sorted(work(repos),
                  key=lambda r: r.get("pushed_at") or "", reverse=True)[:5]
    if not live:
        return "<sub>quiet.</sub>"
    rows = ["| | repo | last touched |", "|:--|:--|:--|"]
    for i, r in enumerate(live):
        mark = "▸" if i == 0 else "·"
        rows.append(f"| `{mark}` | [`{r['name']}`](https://github.com/{USER}/{r['name']}) "
                    f"| {(r.get('pushed_at') or '')[:10]} |")
    return "\n".join(rows)


def block_stamp(repos) -> str:
    """Deliberately not the wall clock — the stamp is the newest real push, so
    the README changes when something happened and not merely because a cron
    fired."""
    live = [r for r in work(repos) if r.get("pushed_at")]
    if not live:
        return "<sub>the desk is still on</sub>"
    newest = max(live, key=lambda r: r["pushed_at"])
    return (f"<sub>last log entry &nbsp;·&nbsp; {newest['pushed_at'][:10]} "
            f"&nbsp;·&nbsp; <code>{newest['name']}</code> &nbsp;·&nbsp; the desk is still on</sub>")


# ─────────────────────────────────────────────────────────────────────────────

def _fallback(repos, tally):
    for r in repos:
        lang = r.get("language")
        if lang and lang not in LANG_SKIP:
            key = LANG_ALIAS.get(lang, lang)
            tally[key] = tally.get(key, 0.0) + 1.0


def languages(repos) -> list[tuple[str, float]]:
    """Each repo gets one vote, split between its languages by byte share.

    Raw bytes summed across the account is the obvious measure and it is
    wrong: one repo carrying a vendored CSS bundle put HTML/CSS at 8.3 MB
    against Java's 1.4 MB — which is true about the bytes and a lie about the
    work. Normalising inside each repo first caps what any single repository
    can contribute at 1.0, so the ranking reads as *how much of this account
    is written in X*, and still resolves finer than counting whole repos.
    """
    tally: dict[str, float] = {}
    wanted = [r for r in repos if not r.get("fork")]
    ok = 0
    for r in wanted:
        body = try_get(f"/repos/{r['full_name']}/languages", None)
        if body is None:
            continue
        ok += 1
        sizes: dict[str, int] = {}
        for name, size in body.items():
            if name in LANG_SKIP:
                continue
            sizes[LANG_ALIAS.get(name, name)] = sizes.get(LANG_ALIAS.get(name, name), 0) + size
        total = sum(sizes.values())
        if not total:
            continue
        for name, size in sizes.items():
            tally[name] = tally.get(name, 0.0) + size / total

    # A partial answer is worse than a coarse one: forty repos measured and
    # fourteen missing would silently rank the account by whichever half the
    # rate limiter happened to let through.
    if wanted and ok < 0.9 * len(wanted):
        print(f"  ! only {ok}/{len(wanted)} repos measured — "
              f"falling back to repo counts", file=sys.stderr)
        tally = {}
        _fallback(repos, tally)

    return sorted(tally.items(), key=lambda kv: -kv[1])


def main() -> int:
    print(f"- building the log for {USER}")
    user = try_get(f"/users/{USER}")
    if not user:
        print("! cannot reach the API; leaving README.md untouched", file=sys.stderr)
        return 1

    repos = paged(f"/users/{USER}/repos?type=owner&sort=pushed")
    repos = [r for r in repos if not r.get("private")]
    print(f"- {len(repos)} public repositories")

    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            print(f"- manifest.json: {', '.join(manifest)}")
        except ValueError as e:
            print(f"  ! manifest.json is not valid JSON ({e}); ignoring", file=sys.stderr)

    langs = languages(repos)
    print("- " + ", ".join(f"{n} {s:.1f}" for n, s in langs[:6]))

    index = {r["name"] for r in repos}

    blocks = {
        "stardate": block_stardate(user, repos, langs, manifest),
        "surface":  block_surface(manifest),
        "badges":   block_badges(user, repos),
        "systems":  block_systems(langs),
        "timeline": block_timeline(repos),
        "hold":     block_hold(index, manifest),
        "arrivals": block_arrivals(repos, index),
        "recent":   block_recent(repos),
        "stamp":    block_stamp(repos),
    }

    text = TPL.read_text(encoding="utf-8")

    # The template opens with a note addressed to whoever edits it. That note
    # is wrong in the generated file — it says "this is the source" — so it is
    # swapped for one addressed to whoever lands on README.md by mistake.
    banner = ("<!--\n"
              "  GENERATED FILE — do not edit.\n"
              "  Written by .github/build.py from README.tpl.md and the GitHub API.\n"
              "  Edit the template, or the deck data in build.py, and push.\n"
              "-->\n")
    text = re.sub(r"\A<!--.*?-->\n", banner, text, count=1, flags=re.S)

    missing = []
    for key, value in blocks.items():
        pat = re.compile(
            rf"(<!--LOG:{key}-->)(.*?)(<!--/LOG:{key}-->)", re.S)
        if not pat.search(text):
            missing.append(key)
            continue
        text = pat.sub(lambda m: m.group(1) + "\n" + value + "\n" + m.group(3), text)
    if missing:
        print(f"  ! template has no slot for: {', '.join(missing)}", file=sys.stderr)

    left = re.findall(r"<!--LOG:(\w+)-->", text)
    unknown = [k for k in left if k not in blocks]
    if unknown:
        print(f"  ! template asks for unknown blocks: {', '.join(unknown)}", file=sys.stderr)

    if "--check" in sys.argv:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("- no change" if same else "- README.md would change")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"- wrote {OUT.name} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
