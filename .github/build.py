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
# THE HOLD lives in decks.json, not here.
#
# It used to be a literal in this file, which was fine while a human was the
# only editor. The survey workflow writes to it too, and a program editing
# Python source to add a tuple is a class of bug this does not need: it is
# data, so it is stored as data.
# ─────────────────────────────────────────────────────────────────────────────

DECKSF = ROOT / "decks.json"


def load_decks():
    """Fail closed. An unreadable decks.json means THE HOLD would silently
    render as nothing at all — an empty page is a worse answer than no page."""
    if not DECKSF.exists():
        raise SystemExit(f"! {DECKSF.name} is missing; refusing to build a hollow page")
    try:
        data = json.loads(DECKSF.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"! {DECKSF.name} is not valid JSON ({e})")

    decks = [{**d, "rows": [(r["repos"], r["desc"]) for r in d["rows"]]}
             for d in data.get("decks", [])]
    if not decks:
        raise SystemExit(f"! {DECKSF.name} lists no decks")
    return decks, set(data.get("ignore", [])), set(data.get("private", []))


DECKS, IGNORE, PRIVATE = load_decks()

VIEWSF = ROOT / "views.json"


def load_views():
    """The traffic ledger, or nothing.

    Unlike decks.json this one may legitimately not exist yet — the first
    run of .github/views.py creates it — so a missing or unreadable file is
    an empty ledger and the block below says so in a sentence. Failing the
    build here would mean a token problem takes down the whole page.
    """
    if not VIEWSF.exists():
        return {"days": {}, "referrers": []}
    try:
        data = json.loads(VIEWSF.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"  ! views.json is not valid JSON ({e}); ignoring", file=sys.stderr)
        return {"days": {}, "referrers": []}
    return {"days": data.get("days") or {},
            "referrers": data.get("referrers") or []}


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


def block_badges(u, repos, ledger) -> str:
    def badge(label, value, color):
        lab = urllib.parse.quote(label)
        val = urllib.parse.quote(str(value))
        return (f'<img src="https://img.shields.io/badge/{lab}-{val}-0d1117'
                f'?style=flat-square&labelColor=0d1117&color={color}" alt="{label} {value}" />')

    row = [
        badge("repos", len(repos), "58a6ff"),
        badge("followers", u.get("followers", 0), "58a6ff"),
    ]
    seen = sum(d["views"] for d in (ledger.get("days") or {}).values())
    if seen:
        # Only once there is something to report. A badge reading "views 0" is
        # a claim about the account rather than about the ledger's age.
        row.append(badge("logged views", f"{seen:,}", "3fb950"))
    row.append(badge("primary instrument", "hands", "f0883e"))
    return "\n&nbsp;\n".join(row)


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



SPARK = "▁▂▃▄▅▆▇█"


def spark(values) -> str:
    """A fixed-height sparkline. An empty or flat run must not divide by zero,
    and a run of all-equal days deliberately draws as a flat middle rather
    than as a full bar — a wall of █ reads as a spike that never happened."""
    if not values:
        return ""
    hi, lo = max(values), min(values)
    if hi == lo:
        return ("▄" if hi else "▁") * len(values)
    span = len(SPARK) - 1
    return "".join(SPARK[round(span * (v - lo) / (hi - lo))] for v in values)


def block_views(ledger) -> str:
    """What the traffic ledger has, or the reason it has nothing.

    It rests rather than vanishing. There are two reasons for an empty
    ledger — it is younger than one closed day, or the token cannot read
    traffic — and the resting sentence names both, in order. A section that
    disappears when it has no data can only ever be found again by accident.
    """
    days = ledger.get("days") or {}
    if not days:
        return ("<sub>No closed day on the ledger yet. <code>.github/views.py</code> "
                "records a day only once it is over, so the first number appears "
                "after the first full UTC day. If it stays empty past that, the "
                "token cannot read traffic — it needs <b>Administration: read</b> "
                "on this repository.</sub>")

    order = sorted(days)
    total = sum(days[d]["views"] for d in order)
    uniq = sum(days[d]["uniques"] for d in order)
    recent = order[-14:]
    r_views = sum(days[d]["views"] for d in recent)
    r_uniq = sum(days[d]["uniques"] for d in recent)
    line = spark([days[d]["views"] for d in recent])
    busiest = max(order, key=lambda d: days[d]["views"])

    # Days *recorded*, not days elapsed. The ledger has a hole for any day the
    # workflow could not reach inside the API's fourteen, and counting the
    # calendar instead would claim a coverage the file does not have.
    rows = [
        ("Since", f"`{order[0]}` &nbsp;·&nbsp; {len(order)} days on the ledger"),
        ("All time", f"**{total:,}** views &nbsp;·&nbsp; {uniq:,} distinct"),
        ("Last 14 days", f"`{line}` &nbsp;·&nbsp; {r_views:,} views &nbsp;·&nbsp; {r_uniq:,} distinct"),
        ("Busiest day", f"`{busiest}` &nbsp;·&nbsp; {days[busiest]['views']:,} views"),
    ]
    refs = ledger.get("referrers") or []
    if refs:
        rows.append(("Arriving from", " · ".join(f"`{r}`" for r in refs)))

    out = ["| | |", "|---|---|"]
    out += [f"| **{k}** | {v} |" for k, v in rows]
    return "\n".join(out)


def cell(desc: str, aether_lines: str) -> str:
    """Render a deck row's description safely.

    Two things bite now that this text arrives from a web form rather than
    from a literal in this file:

    `str.format` was used for the one {aether_lines} placeholder, which means
    any other brace in the text is a format field. A perfectly reasonable note
    like "handles {json} payloads" raised KeyError and took the whole build
    down. A targeted replace has no such surface.

    And an unescaped pipe ends the table cell, so "small | fast" silently
    produced a row with a third column and a broken table.
    """
    return (desc.replace("{aether_lines}", aether_lines)
                .replace("|", r"\|"))


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
            rows.append(f"| {' · '.join(cells)} | {cell(desc, aether_lines)} |")
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

    ledger = load_views()
    print(f"- ledger: {len(ledger['days'])} days, "
          f"{sum(d['views'] for d in ledger['days'].values())} views")

    blocks = {
        "stardate": block_stardate(user, repos, langs, manifest),
        "surface":  block_surface(manifest),
        "badges":   block_badges(user, repos, ledger),
        "systems":  block_systems(langs),
        "views":    block_views(ledger),
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
