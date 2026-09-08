#!/usr/bin/env python3
"""Rebuild README.md from README.tpl.md and live GitHub data.

Stdlib only. Reads the public API, fills the <!--LOG:x--> blocks in the
template, writes README.md. Almost nothing here uses the wall clock: every
value comes off the API, so the file changes only when the account actually
changed, and the workflow commits only when the file changes.

The one exception is deliberate and bounded. THE BLACK BOX is a statement
about *elapsed* time, so it cannot be written without a today — but it reads
the clock only to decide which days are closed, never for a value, and its
strip is one tick per closed UTC day. Time passing can therefore commit, and
never more than once a day.

    python .github/build.py            # writes README.md
    python .github/build.py --check    # writes nothing, prints the diff-ability

env:  GITHUB_TOKEN   raises the rate limit to 5000/hr (the Action supplies it)
      PROFILE_USER   whose profile to build (default: StarFleet1334)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import math
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
CHART = ROOT / "chart.svg"

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


def paged_soft(path, cap=3):
    """`paged`, but a refusal is *unknown* rather than *empty*.

    The strict pager raises, which is right for the repo list — a build with
    no repos should die. The recorder below must tell a quiet fortnight from
    a rate limit, and both look like an empty list unless the failure is kept
    distinct. Returns None when the first page could not be read.
    """
    out = []
    for page in range(1, cap + 1):
        sep = "&" if "?" in path else "?"
        body = try_get(f"{path}{sep}per_page=100&page={page}")
        if body is None:
            return out or None
        out.extend(body)
        if len(body) < 100:
            break
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


def unfiled(repos):
    """Every repo not in a deck and not ignored — NEW ARRIVALS' own set.

    Shared rather than recomputed so THE DOCK and NEW ARRIVALS can never
    disagree about what is filed; a repo that appears in one and not the other
    would read as a bug in whichever the reader looked at second.
    """
    filed = {n for d in DECKS for names, _ in d["rows"] for n in names}
    return [r for r in work(repos)
            if r["name"] not in filed and r["name"] not in IGNORE]


# ─────────────────────────────────────────────────────────────────────────────
# ✷ THE STAR CHART
#
# The account drawn the way an atlas draws a sky: one star per repository, the
# five decks traced over them as figures, and everything unfiled left as field
# stars belonging to no figure at all.
#
# THE HASH IS THE WHOLE DESIGN. A star's position comes from sha256 of its own
# name and from nothing else — not from a seed, not from a force-directed pass,
# not from its neighbours. That is what makes the plate committable: adding a
# repository adds a star and moves no other one, so the diff is the change.
# A relaxation pass would have looked better and would have redrawn every star
# in a region whenever one arrived, which on an hourly build is a chart that
# never settles.
#
# Two consequences of refusing relaxation, both accepted on purpose:
#
#   Stars can land close together. Real charts have doubles; a pair a pixel
#   apart reads as one bright star and costs nothing.
#
#   The figures DO change when a star arrives, because the figure is a minimum
#   spanning tree over the deck's stars and a new star genuinely changes it.
#   That is a real change and it should show.
#
# Python's hash() is salted per process — PYTHONHASHSEED — so it produces a
# different chart on every run and would commit hourly forever. It must be
# hashlib.
#
# Magnitude is apparent, not intrinsic: it is how large the repository is in
# code bytes, the way a star's magnitude is how bright it looks from here and
# not how much it matters. The bands are absolute rather than relative to the
# account, so one enormous new repository cannot re-band every star beside it.
# ─────────────────────────────────────────────────────────────────────────────

SKY_W, SKY_H = 920, 400
SKY_PAD = 34

SKY_GROUND = "#0a0e15"
SKY_EDGE = "#1b2431"
SKY_STAR = "#e9eef8"
SKY_FIGURE = "#31527f"
SKY_LABEL = "#5b8ede"
SKY_FIELD = "#8fa4c4"

# Absolute magnitude bands, in bytes of code. First match wins, brightest
# first. Absolute so a repo's magnitude depends only on that repo.
MAG_BANDS = [(1_000_000, 1), (400_000, 2), (150_000, 3),
             (50_000, 4), (15_000, 5), (0, 6)]
MAG_R = {1: 5.4, 2: 4.1, 3: 3.2, 4: 2.5, 5: 1.9, 6: 1.4}


# A monospace advance is a reliable 0.6em, which is the only reason a label's
# width can be known without a font engine. It has to be known: a repo name is
# up to 40 characters and the star it belongs to can sit anywhere on the plate.
LABEL_SIZE = 9.5
LABEL_ADV = 0.6
MAG_O = {1: 1.0, 2: 0.94, 3: 0.86, 4: 0.76, 5: 0.64, 6: 0.5}


def _hash(name, i):
    """A stable float in [0,1) from a name and a slot. hashlib, never hash()."""
    d = hashlib.sha256(f"{name}#{i}".encode("utf-8")).digest()
    return int.from_bytes(d[:6], "big") / (1 << 48)


def _regions(n):
    """One patch of sky per deck, laid out rather than typed.

    A hand-written table of five regions is a table that silently drops the
    sixth deck the day someone adds one to decks.json. These are computed from
    the count, so the plate simply gets busier.
    """
    if n <= 0:
        return []
    inner_w = SKY_W - 2 * SKY_PAD
    col = inner_w / n
    out = []
    for i in range(n):
        cx = SKY_PAD + col * (i + 0.5)
        # Alternating heights so neighbouring figures do not sit in a row and
        # read as one long chain.
        cy = SKY_H * (0.40 if i % 2 == 0 else 0.61)
        out.append((cx, cy, col * 0.40, SKY_H * 0.235))
    return out


def _place(name, region):
    """A point inside an ellipse, from the name alone.

    sqrt on the radius is what stops every figure being a dense knot with a
    bare rim: without it, uniform u concentrates points toward the centre.
    """
    cx, cy, rx, ry = region
    r = math.sqrt(_hash(name, 0))
    th = 2 * math.pi * _hash(name, 1)
    return (cx + rx * r * math.cos(th), cy + ry * r * math.sin(th))


def _mag(code_bytes):
    return next(m for lim, m in MAG_BANDS if code_bytes >= lim)


def _figure(stars):
    """A minimum spanning tree over a deck's stars — Prim, O(n²).

    A convex hull would trace the outline and a nearest-neighbour chain can
    double back on itself; the tree is what an atlas actually draws, and it is
    a function of the positions only, so it is as deterministic as they are.
    """
    if len(stars) < 2:
        return []
    todo = list(range(1, len(stars)))
    done = [0]
    edges = []
    while todo:
        best = min(((i, j) for j in todo for i in done),
                   key=lambda e: ((stars[e[0]][0] - stars[e[1]][0]) ** 2 +
                                  (stars[e[0]][1] - stars[e[1]][1]) ** 2))
        edges.append(best)
        done.append(best[1])
        todo.remove(best[1])
    return edges


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _sky(repos, sizes, manifest):
    """Where every star is. Draws nothing.

    Split out from the drawing because a deck's own plate has to put a star in
    the same place, relative to its neighbours, as the overview does — so the
    placement has to be computed once and handed to whatever is drawing.
    """
    by_name = {r["name"]: r for r in repos}
    regions = _regions(len(DECKS))

    figures = []
    for d, region in zip(DECKS, regions):
        stars = []
        for names, _ in d["rows"]:
            for n in names:
                if n in by_name:
                    stars.append((n, _place(n, region), _mag(sizes.get(n, 0)), False))
                elif n in PRIVATE:
                    # The API cannot measure a private repo, so its magnitude is
                    # asserted by manifest.json rather than read. The ring drawn
                    # round it is that distinction, made visible.
                    stars.append((n, _place(n, region),
                                  int(manifest.get("chart_magnitude", 1)), True))
        if stars:
            figures.append({"title": d["title"], "icon": d.get("icon", ""),
                            "blurb": d.get("blurb", ""), "region": region,
                            "stars": stars})

    whole = (SKY_W / 2, SKY_H / 2, (SKY_W - 2 * SKY_PAD) / 2,
             (SKY_H - 2 * SKY_PAD) / 2)
    field = []
    for r in sorted(unfiled(repos), key=lambda r: r["name"]):
        # Field stars get the whole plate, not a region — they belong to no
        # figure, which is the entire point of being unfiled. Sorted by name
        # because the repo list arrives sorted by pushed_at: without it the
        # identical picture is emitted in a different order every time
        # anything is pushed, and the plate commits for a change nobody
        # could see.
        n = r["name"]
        field.append((n, _place(n, whole), _mag(sizes.get(n, 0)), False))

    return {"figures": figures, "field": field}


def _stars_svg(out, stars, at, dim=False):
    for name, (x0, y0), mag, private in stars:
        x, y = at(x0, y0)
        r = MAG_R[mag] * (0.8 if dim else 1.0)
        o = MAG_O[mag] * (0.45 if dim else 1.0)
        fill = SKY_FIELD if dim else SKY_STAR
        if mag <= 2 and not dim:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{MAG_R[mag] * 2.6:.1f}" '
                       f'fill="{SKY_STAR}" fill-opacity="0.10"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                   f'fill="{fill}" fill-opacity="{o:.2f}"/>')
        if private:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{MAG_R[mag] + 4:.1f}" '
                       f'fill="none" stroke="{SKY_STAR}" stroke-width="0.8" '
                       f'stroke-opacity="0.45" stroke-dasharray="2 2"/>')


def _name_at(out, x, y, text, w, size=LABEL_SIZE, opacity=0.72):
    """Put a name beside a star on whichever side it fits.

    Which side is decided by whether the name *fits*, never by how far across
    the plate the star sits: a fraction-of-the-width rule put a 27-character
    name off the edge from a star only four fifths of the way over.
    """
    wide = len(text) * size * LABEL_ADV
    if x + 8 + wide <= w - SKY_PAD:
        anchor, dx = "start", 8
    else:
        anchor, dx = "end", -8
    out.append(f'<text x="{max(4, min(w - 4, x + dx)):.1f}" y="{y + 3.5:.1f}" '
               f'text-anchor="{anchor}" font-size="{size}" fill="{SKY_STAR}" '
               f'fill-opacity="{opacity}">{_esc(text)}</text>')


def _envelope(w, h):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img">',
            '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
            f'<rect width="{w}" height="{h}" fill="{SKY_GROUND}"/>',
            f'<rect x="6.5" y="6.5" width="{w - 13}" height="{h - 13}" '
            f'fill="none" stroke="{SKY_EDGE}" stroke-width="1"/>']


def _figure_path(out, stars, at):
    pts = [at(x, y) for _, (x, y), _, _ in stars]
    seg = "".join(f"M{pts[i][0]:.1f} {pts[i][1]:.1f}L{pts[j][0]:.1f} {pts[j][1]:.1f}"
                  for i, j in _figure(pts))
    if seg:
        out.append(f'<path d="{seg}" fill="none" stroke="{SKY_FIGURE}" '
                   f'stroke-width="1" stroke-opacity="0.55"/>')


def plate_sky(sky):
    """The whole account on one plate: figures, field stars, deck names."""
    figures, field = sky["figures"], sky["field"]
    at = lambda x, y: (x, y)
    out = _envelope(SKY_W, SKY_H)

    for f in figures:                       # figures first — never over a star
        _figure_path(out, f["stars"], at)
    _stars_svg(out, field, at, dim=True)

    for f in figures:
        _stars_svg(out, f["stars"], at)
        lead = min(f["stars"], key=lambda st: (st[2], st[0]))
        _name_at(out, lead[1][0], lead[1][1], lead[0], SKY_W)
        cx, cy, rx, ry = f["region"]
        out.append(f'<text x="{cx:.1f}" y="{cy + ry + 17:.1f}" text-anchor="middle" '
                   f'font-size="9" letter-spacing="2.2" fill="{SKY_LABEL}" '
                   f'fill-opacity="0.85">{_esc(f["title"])}</text>')

    counted = sum(len(f["stars"]) for f in figures)
    out.append(f'<text x="{SKY_PAD}" y="{SKY_H - 13}" font-size="8.5" '
               f'letter-spacing="1.6" fill="{SKY_LABEL}" fill-opacity="0.45">'
               f'{counted} CHARTED &#183; {len(field)} FIELD STARS &#183; '
               f'MAGNITUDE IS CODE BYTES</text>')
    out.append("</svg>")

    alt = ("A star chart of this account: " +
           " &#183; ".join(f"{f['title']} ({len(f['stars'])})" for f in figures) +
           f", and {len(field)} unfiled field stars belonging to no figure.")
    return "\n".join(out) + "\n", alt, (counted, len(field))


RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main"


# The plate plants its own anchor and links to it. A link that goes nowhere is
# the point: it is what stops GitHub supplying one that does.
PLATE_ANCHOR = "star-chart"


def _img(src, svg, width, alt):
    """An image that does NOT open a new tab when it is clicked.

    GitHub's renderer wraps every bare <img> — markdown or raw HTML, and even
    one inside a <summary> — in

        <a target="_blank" rel="noopener noreferrer nofollow" href="{the image}">

    which is why clicking the plate used to leave the page for a picture of
    it. It does *not* add that wrapper to an image the author has already put
    inside a link. Verified against GitHub's own renderer, not assumed: a bare
    img comes back carrying target="_blank", the same img inside a hand-written
    anchor comes back exactly as written.

    So the plate is wrapped in an anchor pointing at itself. Clicking it does
    nothing, which is the whole intention — a README cannot make a picture do
    anything, and the alternative is not "something better" but "a new tab
    onto the bare file".

    The href carries the content hash for the same reason the src does: GitHub
    caches README images hard, and a plate that changed can otherwise sit
    behind the old bytes.
    """
    stamp = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:8]
    return (f'<a name="{PLATE_ANCHOR}" href="#user-content-{PLATE_ANCHOR}">'
            f'<img src="{RAW}/{src}?v={stamp}" width="{width}" alt="{alt}" /></a>')


def block_starchart(sky):
    svg, alt, _ = plate_sky(sky)
    return _img("chart.svg", svg, 920, alt)


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


# ─────────────────────────────────────────────────────────────────────────────
# ✕ THE BLACK BOX
#
# The page reports on the account and never on itself, which means the one
# failure it cannot show you is its own. A token that expired, an API that
# started refusing, a workflow disabled after sixty days of inactivity: all
# three look exactly like a quiet month.
#
# One tick per **closed** UTC day, for a fortnight — the same rule and the same
# horizon as the traffic ledger next to it. The day in progress is never drawn,
# so the strip moves at most once a day; and when a quiet day rolls off the far
# end and a quiet day arrives at the near one, the string is unchanged and
# nothing is committed. It reports by exception, which is the only way a
# self-report is worth reading.
#
# A day is one of four things, and the fourth is the point:
#
#   ─  runs, none of which changed the page
#   ┼  the page changed — a commit by the bot lands that day
#   ╳  a run was refused
#   ·  no run at all. The recorder itself was off.
#
# Box-drawing glyphs rather than ✓/✗ on purpose: they are one cell wide in
# every monospace font, so the trace cannot skew, and a flat day genuinely
# draws as a flat line.
# ─────────────────────────────────────────────────────────────────────────────

FLIGHT_DAYS = 14
BOT = "github-actions[bot]"
WORKFLOW = "log.yml"
RUN_PAGES = 6                      # ~600 runs; a fortnight hourly is ~340

TICK_QUIET, TICK_MOVED, TICK_REFUSED, TICK_DARK = "─", "┼", "╳", "·"
BAD = {"failure", "timed_out", "startup_failure"}


def flight_recorder():
    """Read the last fortnight of this workflow's own runs.

    Returns None when the runs could not be read at all. That is not the same
    as a fortnight of silence, and the block must not draw fourteen dark ticks
    because a rate limiter said no — it would be reporting an outage that is
    entirely its own.
    """
    today = dt.datetime.now(dt.timezone.utc).date()
    first = today - dt.timedelta(days=FLIGHT_DAYS)
    since = first.isoformat()

    runs = []
    for page in range(1, RUN_PAGES + 1):
        body = try_get(f"/repos/{USER}/{USER}/actions/workflows/{WORKFLOW}/runs"
                       f"?created=%3E%3D{since}&per_page=100&page={page}")
        if body is None:
            if not runs:
                return None
            break
        batch = body.get("workflow_runs") or []
        runs.extend(batch)
        if len(batch) < 100:
            break

    # The bot's own commits are the record of which days the page actually
    # changed. Matching runs to commits by time would be a guess; the author
    # is a fact.
    commits = paged_soft(f"/repos/{USER}/{USER}/commits?since={since}T00:00:00Z") or []
    moved = {c["commit"]["author"]["date"][:10] for c in commits
             if (c.get("commit", {}).get("author", {}).get("name") == BOT)}

    ran, refused = set(), {}
    for r in runs:
        day = (r.get("run_started_at") or r.get("created_at") or "")[:10]
        if not day:
            continue
        ran.add(day)
        if r.get("conclusion") in BAD:
            refused.setdefault(day, r)

    days = []
    for i in range(FLIGHT_DAYS):
        day = (first + dt.timedelta(days=i)).isoformat()
        if day in refused:
            days.append((day, TICK_REFUSED))
        elif day in moved:
            days.append((day, TICK_MOVED))
        elif day in ran:
            days.append((day, TICK_QUIET))
        else:
            days.append((day, TICK_DARK))

    # The newest refusal in the window, and which step of it gave way. One
    # extra call, and only when there is something to explain.
    last = None
    if refused:
        day = max(refused)
        run = refused[day]
        jobs = try_get(f"/repos/{USER}/{USER}/actions/runs/{run['id']}/jobs") or {}
        step = next((st["name"] for j in jobs.get("jobs", [])
                     for st in j.get("steps", [])
                     if st.get("conclusion") in BAD), None)
        last = (day, step)

    return {"days": days, "refusal": last}


def block_blackbox(record) -> str:
    if record is None:
        return ("<sub>The recorder could not read its own runs this build — "
                "an unauthenticated build has no quota left for them, and a "
                "local <code>--check</code> will usually say this. It is a "
                "statement about this run, not about the workflow.</sub>")

    days = record["days"]
    trace = "".join(t for _, t in days)
    moved = trace.count(TICK_MOVED)
    refused = trace.count(TICK_REFUSED)
    dark = trace.count(TICK_DARK)

    tally = [f"{moved} changed the page"]
    if refused:
        tally.append(f"**{refused} refused**")
    if dark:
        tally.append(f"**{dark} with no run at all**")

    rows = [
        (f"Last {FLIGHT_DAYS} days", f"`{trace}` &nbsp;·&nbsp; " + " &nbsp;·&nbsp; ".join(tally)),
        ("Reading", f"`{TICK_QUIET}` ran, nothing moved &nbsp;·&nbsp; "
                    f"`{TICK_MOVED}` the page changed &nbsp;·&nbsp; "
                    f"`{TICK_REFUSED}` refused &nbsp;·&nbsp; "
                    f"`{TICK_DARK}` no run at all"),
    ]

    refusal = record["refusal"]
    if refusal:
        day, step = refusal
        where = f" &nbsp;·&nbsp; the *{step}* step" if step else ""
        rows.append(("Last refusal", f"`{day}`{where}"))
    else:
        rows.append(("Last refusal", f"none in {FLIGHT_DAYS} days"))

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
    fresh = sorted(unfiled(repos), key=lambda r: r.get("created_at", ""),
                   reverse=True)
    if not fresh:
        return ("<sub>Every repository is filed. The hold is in order.</sub>")
    rows = ["| repo | language | first commit |", "|:--|:--|:--|"]
    for r in fresh[:8]:
        lang = r.get("language") or "—"
        rows.append(f"| [`{r['name']}`](https://github.com/{USER}/{r['name']}) "
                    f"| {lang} | {(r.get('created_at') or '')[:10]} |")
    tail = ""
    if len(fresh) > 8:
        tail = f"\n\n<sub>…and {len(fresh) - 8} more not yet filed.</sub>"
    return "\n".join(rows) + tail


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


def languages(repos, code_bytes=None) -> list[tuple[str, float]]:
    """Each repo gets one vote, split between its languages by byte share.

    Raw bytes summed across the account is the obvious measure and it is
    wrong: one repo carrying a vendored CSS bundle put HTML/CSS at 8.3 MB
    against Java's 1.4 MB — which is true about the bytes and a lie about the
    work. Normalising inside each repo first caps what any single repository
    can contribute at 1.0, so the ranking reads as *how much of this account
    is written in X*, and still resolves finer than counting whole repos.

    `code_bytes`, when given, is filled with each repo's own total on the
    way past. THE STAR CHART needs it and the call has already been made;
    fetching /languages a second time to learn a number this loop is holding
    would double the most expensive part of the build.
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
        if code_bytes is not None:
            code_bytes[r["name"]] = total
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

    code_bytes = {}
    langs = languages(repos, code_bytes)
    print("- " + ", ".join(f"{n} {s:.1f}" for n, s in langs[:6]))

    index = {r["name"] for r in repos}

    sky = _sky(repos, code_bytes, manifest)
    svg, alt, tally = plate_sky(sky)
    print(f"- chart: {tally[0]} charted, {tally[1]} field stars")

    ledger = load_views()
    print(f"- ledger: {len(ledger['days'])} days, "
          f"{sum(d['views'] for d in ledger['days'].values())} views")

    record = flight_recorder()
    print("- recorder: " + ("unreadable this run" if record is None
                            else "".join(t for _, t in record["days"])))

    blocks = {
        "stardate": block_stardate(user, repos, langs, manifest),
        "surface":  block_surface(manifest),
        "badges":   block_badges(user, repos, ledger),
        "starchart": block_starchart(sky),
        "systems":  block_systems(langs),
        "views":    block_views(ledger),
        "blackbox": block_blackbox(record),
        "hold":     block_hold(index, manifest),
        "arrivals": block_arrivals(repos, index),
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

    want = {CHART: svg, OUT: text}
    moved = [f.name for f, body in want.items()
             if not (f.exists() and f.read_text(encoding="utf-8") == body)]

    if "--check" in sys.argv:
        print("- no change" if not moved else "- would change: " + ", ".join(moved))
        return 0

    # The chart is written before the page. The page names it by content hash,
    # so the one ordering that must never happen is a committed README
    # pointing at a chart that is not there yet.
    CHART.write_text(svg, encoding="utf-8", newline="\n")
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"- wrote {OUT.name} ({len(text)} bytes) and {CHART.name} "
          f"({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
