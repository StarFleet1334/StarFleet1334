# Putting the log on the air

This folder is a complete profile repository. Everything in it belongs in
**`StarFleet1334/StarFleet1334`** — the repo whose README GitHub shows at the
top of your profile page. That repo already exists.

```
README.md            generated — do not edit
masthead.svg         generated — do not edit; the plate at the top of the page
heading.svg          generated — do not edit; CURRENT HEADING's signal path
systems.svg          generated — do not edit; the language shares, to scale
chart.svg            generated — do not edit; THE STAR CHART's plate
docs/index.html      the interactive chart. Hand-written; the build never touches it
docs/sky.json        generated — the star positions the page reads
PROCESS.md           the mechanism, end to end
README.tpl.md        the prose. Edit this.
manifest.json        numbers for the private project the API cannot see
decks.json           THE HOLD and the ignore list — data, hand- or tool-edited
.github/build.py     the generator
.github/manifest.py  measures a local project and rewrites manifest.json
.github/survey.py    analyses one repo, proposes a decks.json change
.github/apply.py     writes an approved proposal into decks.json
.github/roster.py    regenerates the survey dropdown from your repo list
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

## 2c · Optional — the PROFILE_TOKEN secret

Everything on the page builds without it. Two things still want it:

- **surveying a private repository** — `GITHUB_TOKEN` is scoped to this repo
  alone, so a private repo looks deleted to it;
- **keeping the survey dropdown current** — `GITHUB_TOKEN` is forbidden from
  pushing changes to any file under `.github/workflows/`, and the dropdown
  lives in one.

Create a PAT with read access to your repositories and permission to update
workflows, then **Settings → Secrets and variables → Actions → New repository
secret → `PROFILE_TOKEN`**. Without it the log run skips the roster step, says
so, and updates the page exactly as before.

## 2d · Turn on Pages, or the plate opens a 404

**Settings → Pages → Source: Deploy from a branch → `main` / `/docs` → Save.**

The plate in THE STAR CHART links to
`https://starfleet1334.github.io/StarFleet1334/`, which is `docs/index.html`
served by Pages. Until Pages is switched on that link 404s — the README is
correct and the site simply is not published yet.

Two things about this that are easy to get wrong:

- This repo is a **project** site, not a user site. A user site would have to
  be named `StarFleet1334.github.io`; this one is named `StarFleet1334`, so
  the URL carries the repo path. If you ever rename the repo, `PAGES` in
  `build.py` follows the name automatically but the old link dies.
- `docs/index.html` is **hand-written and the build never rewrites it**. Only
  `docs/sky.json` is generated. That split is on purpose: an hourly run
  produces a one-line diff in a data file rather than a regenerated
  application, and the page can be edited like the program it is.

## 3 · What updates on its own

Hourly at :17, on every push to the template, the data or the generator, and
whenever you press Run workflow or fire `repository_dispatch`:

| block | comes from |
|:--|:--|
| the masthead | `/users/…` — name, join date, repo count, followers, top languages, newest repo |
| THE STAR CHART | `chart.svg`, redrawn from the repo list and each repo's code bytes |
| the interactive chart | `docs/sky.json` — the same positions, as data |
| SYSTEMS ONLINE | `/languages` on every repo, one vote each, split by byte share, drawn to scale |
| THE HOLD | `decks.json`, minus any repo that no longer exists; each summary carries its own count |
| NEW ARRIVALS | every repo not yet filed into a deck |
| the stamp | the newest real push |

Everything else — the CURRENT HEADING prose, the working notes, the footer — is
yours and is never touched.

## 4 · The one design decision worth knowing

**Nothing in the build reads the clock.** The footer stamp is the date of your
newest actual push, not "generated on". So a run on a quiet day produces a
byte-identical file, `git diff --cached --quiet` finds nothing, and the job
exits without committing.

The history of this repo is therefore a record of when your work changed — not
a year of "chore: update README" from a cron.

There are no exceptions to this any more. The two blocks that read the clock
— SENSOR CONTACTS and THE BLACK BOX — have both been removed, so every value
on the page comes off the API and nothing can commit merely because time
passed. The profile repo itself is
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
- **The chart's magnitudes** — `MAG_BANDS` in `build.py`, in bytes of code.
  They are absolute rather than relative to the account on purpose: a band
  computed from the largest repo would re-magnitude every star the day one
  enormous repository arrived. Sizes and opacities are `MAG_R` / `MAG_O`.
- **The rover** — `ROVE_CYCLE` (seconds for one descent of the page),
  `ROVE_PLATES` and `ROVE_SHARE` in `build.py`. Each plate carries its own
  rover and crosses in its own slice of the cycle, so exactly one is on
  screen at a time. Delete the four `rover(...)` calls and it is gone; there
  is no other trace of it in the layout, because it walks a rule each plate
  already drew.
  <br>Note that `prefers-reduced-motion` is **not** honoured inside an
  `<img>`-embedded SVG — measured, in Chromium, in a file whose
  `prefers-color-scheme` query works. The query is written anyway, but a
  reader cannot switch the rover off, which is why it is small, slow, and
  alone on the page at any moment.
- **The private line.** `PRIVATE = {"AETHER"}` in `build.py` renders it without
  a link. Delete the row from `DECKS` if you would rather not mention it, or
  move it to a real link when the repo goes public.
- **The proficiency bars** are computed, not typed — if one reads wrong, the
  fix is in `LANG_ALIAS` / `LANG_SKIP`, not in the README.
- **Nothing on the page depends on a third-party service — now literally
  nothing.** The stat cards and the activity graph went first; the shields.io
  badge row went with the masthead, which carries the same counts and is drawn
  by this repo. Every pixel and every number on the page now comes from a file
  in it.
