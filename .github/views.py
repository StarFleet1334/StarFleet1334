#!/usr/bin/env python3
"""Keep the traffic ledger the GitHub API only remembers for fourteen days.

GitHub exposes no counter for "how many people looked at my profile". The
closest real measurement it offers is the traffic API on the profile
repository itself — and it forgets: `/traffic/views` answers for the last 14
days and nothing before. So this script is the memory. Each run merges the
API's fourteen buckets into `views.json`, which is committed, and that file
is what the page counts from.

Two rules make the ledger trustworthy:

**Today is never recorded.** The bucket for the current UTC day is still
filling; writing it would move the number on every hourly run and turn the
repo history into a stream of "the counter went up by one". A day is written
only once it is closed, so the total moves at most once a day — and when it
moves, a whole day actually happened.

**A recorded day is never lowered.** The API is authoritative inside its
window, but a day read while it was still open (from an older ledger, or a
future change of heart about the rule above) must not be revised downward by
a later read that saw less. `max` is the merge.

    python .github/views.py            # merge today's answer into views.json
    python .github/views.py --check    # print what it would write, write nothing

env:  PROFILE_TOKEN  a PAT with **Administration: read** on this repository
                     (classic: `repo`). GITHUB_TOKEN is NOT enough — traffic
                     is not one of the permissions a workflow token can hold.
      PROFILE_USER   whose profile (default: StarFleet1334)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

USER = os.environ.get("PROFILE_USER", "StarFleet1334")
ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "views.json"

API = "https://api.github.com"
REPO = f"{USER}/{USER}"

# Top referrers are a 14-day rolling top-10 whose *counts* churn every hour.
# Only the names are kept: "they arrive from Google and LinkedIn" is the
# durable fact, and it changes about as often as anything else on the page.
REFERRERS_KEPT = 5


def get(path: str):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-log",
    })
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load() -> dict:
    """An unreadable ledger is left exactly where it is.

    Rewriting it from a fresh API read would silently discard every day older
    than the API's fourteen — which is the entire point of the file.
    """
    if not LEDGER.exists():
        return {"days": {}, "referrers": []}
    try:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"! views.json is not valid JSON ({e}); "
                         f"refusing to overwrite it")
    data.setdefault("days", {})
    data.setdefault("referrers", [])
    data.setdefault("state", "unknown")
    return data


def fetch_days() -> dict[str, dict] | None:
    body = get(f"/repos/{REPO}/traffic/views?per=day")
    out = {}
    for b in body.get("views", []):
        day = (b.get("timestamp") or "")[:10]
        if day:
            out[day] = {"views": int(b.get("count", 0)),
                        "uniques": int(b.get("uniques", 0))}
    return out


def fetch_referrers() -> list[str]:
    body = get(f"/repos/{REPO}/traffic/popular/referrers")
    return [r["referrer"] for r in body[:REFERRERS_KEPT] if r.get("referrer")]


def main() -> int:
    check = "--check" in sys.argv

    ledger = load()

    def settle(state, note=""):
        """Record WHY this run found what it found.

        An empty ledger has three completely different causes — no secret, a
        token that cannot read traffic, and a repository nobody has opened —
        and until now all three produced the same silent empty file and the
        same guessing sentence on the page. The state is stored WITHOUT a
        timestamp on purpose: it changes when the answer changes, so the file
        does not churn on a run that learned nothing new.
        """
        ledger["state"] = state
        if note:
            ledger["note"] = note
        elif "note" in ledger:
            del ledger["note"]

    if not (os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        print("- no token; the ledger stands as it is")
        settle("no-token")
        _save(ledger, check)
        return 0
    before = json.dumps(ledger, sort_keys=True)

    try:
        fresh = fetch_days()
    except urllib.error.HTTPError as e:
        # 403 here is almost always the one real setup mistake: a token
        # without Administration: read. Say which it is rather than dying.
        why = ("that token cannot read traffic — it needs Administration: read"
               if e.code in (403, 404) else str(e))
        print(f"! traffic for {REPO}: {why}; the ledger stands", file=sys.stderr)
        settle("denied" if e.code in (403, 404) else "error", why)
        _save(ledger, check)
        return 0
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"! traffic for {REPO}: {e}; the ledger stands", file=sys.stderr)
        settle("error", str(e))
        _save(ledger, check)
        return 0

    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    added = moved = 0
    for day, row in sorted(fresh.items()):
        if day >= today:
            continue                      # still filling; not a fact yet
        old = ledger["days"].get(day)
        merged = {"views": max(row["views"], (old or {}).get("views", 0)),
                  "uniques": max(row["uniques"], (old or {}).get("uniques", 0))}
        if old is None:
            added += 1
        elif merged != old:
            moved += 1
        ledger["days"][day] = merged

    try:
        refs = fetch_referrers()
        if refs:
            ledger["referrers"] = refs
    except (urllib.error.URLError, urllib.error.HTTPError,
            TimeoutError, ValueError) as e:
        print(f"  ! referrers: {e}; keeping the last set", file=sys.stderr)

    total = sum(d["views"] for d in ledger["days"].values())
    # The call worked. Whether it returned anything is a separate fact: the
    # traffic API omits days with no views, so a reachable repository nobody
    # has opened answers with an empty list, exactly like a refusal used to.
    settle("ok", "" if ledger["days"] else
           "the API answered, and no closed day has had a visit")
    print(f"- {len(ledger['days'])} days on the ledger, {total} views "
          f"({added} new, {moved} revised) — state {ledger['state']}")
    _save(ledger, check)
    return 0


def _save(ledger, check):
    text = json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    if check:
        same = LEDGER.exists() and LEDGER.read_text(encoding="utf-8") == text
        print("- no change" if same else "- views.json would change")
        return
    LEDGER.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
