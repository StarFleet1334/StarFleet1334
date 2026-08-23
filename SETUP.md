# Putting the log on the air

This folder is a complete profile repository. Everything in it belongs in
**`StarFleet1334/StarFleet1334`** — the repo whose README GitHub shows at the
top of your profile page. That repo already exists.

```
README.md            generated — do not edit
PROCESS.md           the mechanism, end to end
README.tpl.md        the prose. Edit this.
manifest.json        numbers for the private project the API cannot see
decks.json           THE HOLD and the ignore list — data, hand- or tool-edited
.github/build.py     the generator
.github/manifest.py  measures a local project and rewrites manifest.json
.github/survey.py    analyses one repo, proposes a decks.json change
.github/apply.py     writes an approved proposal into decks.json
.github/workflows/log.yml      hourly rebuild
.github/workflows/survey.yml   analyse → approve → file
```

## 1 · Push it

```bash
git clone https://github.com/StarFleet1334/StarFleet1334.git
cd StarFleet1334
# copy the contents of this folder in, over the existing README.md
git add -A
git commit -m "log: the desk goes on the air"
git push
```

## 2 · Let the Action write

**Settings → Actions → General → Workflow permissions → Read and write.**

Without it the build runs, produces the right file, and fails at `git push`.
That is the one setup step that is not in the repo, and the only failure mode
that looks like the workflow is broken when it is not.

Then **Actions → log → Run workflow** to prove it end to end.

## 2b · Create the approval gate

**Settings → Environments → New environment → `readme` → Required reviewers →
add yourself → Save.**

The `survey` workflow's apply job names this environment. A job naming an
environment that has no protection rules runs **immediately** — so without this
step the survey would analyse and apply in one go, and it would look like it
worked. Free on public repositories.

## 3 · What updates on its own

Hourly at :17, on every push to the template, the data or the generator, and
whenever you press Run workflow or fire `repository_dispatch`:

| block | comes from |
|:--|:--|
| the console box | `/users/…` — name, join date, repo count, top languages, newest repo |
| the badges | live repo and follower counts |
| SYSTEMS ONLINE | `/languages` on every repo, one vote each, split by byte share |
| SHIP'S LOG | repo creation dates, with your prose per year |
| THE HOLD | `DECKS`, minus any repo that no longer exists |
| NEW ARRIVALS | every repo not yet filed into a deck |
| RECENTLY ON THE BENCH | the five most recently pushed repos |
| the stamp | the newest real push |

Everything else — the CURRENT HEADING prose, the working notes, the footer — is
yours and is never touched.

## 4 · The one design decision worth knowing

**Nothing in the build reads the clock.** The footer stamp is the date of your
newest actual push, not "generated on". So a run on a quiet day produces a
byte-identical file, `git diff --cached --quiet` finds nothing, and the job
exits without committing.

The history of this repo is therefore a record of when your work changed — not
a year of "chore: update README" from a cron. The profile repo itself is
excluded from every "newest" calculation for the same reason: the Action pushes
to it, so counting it would make the bot's own commit the news.

## 5 · Day-to-day

**A new repo appears.** It shows up under NEW ARRIVALS within the hour, by
itself. To decide what it is worth, run **Actions → survey** with its name: you
get an insight report, and an approval gate that files it into a deck (or into
the ignore list) only if you say so. See PROCESS.md § 6.

To skip the ceremony, edit `decks.json` by hand and push:

```json
{ "repos": ["my-new-thing"], "desc": "what it is, in one clause" }
```

**A repo is deleted.** Nothing to do — the next hourly run drops it from every
count, and any deck row that pointed at it disappears rather than leaving a
dead link.

**A new year starts.** Add a line to `YEAR_NOTES`. If you forget, the timeline
lists that year's repos instead — it cannot silently stop.

**AETHER's numbers change.** From anywhere:

```bash
python .github/manifest.py C:/Users/User/Desktop/secret/aether
git commit -am "log: remeasure" && git push
```

It walks the real tree — skipping `.venv`, `data`, `__pycache__` — and writes
the module and line counts into `manifest.json`. The API cannot see a private
repo, so this is the only path by which a real measurement of it reaches the
page.

**Preview before pushing.**

```bash
python .github/build.py --check    # says whether README.md would change
python .github/build.py            # writes it
```

Unauthenticated you get 60 API calls an hour and the build needs about 56, so
a second local run inside the hour will hit the limit. It degrades rather than
lying: a partial language read is discarded in favour of coarse repo counts,
and if the API is unreachable entirely the build exits non-zero and leaves
`README.md` exactly as it was. Set `GITHUB_TOKEN` to a personal access token
with no scopes to get 5000/hr locally.

## 6 · Things you may want to change

- **Cadence** — the `cron` in `log.yml`. It commits only on real change, so a
  faster schedule costs nothing but Action minutes.
- **The private line.** `PRIVATE = {"AETHER"}` in `build.py` renders it without
  a link. Delete the row from `DECKS` if you would rather not mention it, or
  move it to a real link when the repo goes public.
- **The proficiency bars** are computed, not typed — if one reads wrong, the
  fix is in `LANG_ALIAS` / `LANG_SKIP`, not in the README.
- **Nothing on the page depends on a third-party service.** The stat cards and
  the activity graph were removed; every number now comes from a GitHub API
  call this repo makes itself. The only image left is the shields.io badge row,
  and it degrades to alt text if that host is down.
