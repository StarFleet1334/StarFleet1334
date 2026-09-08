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
.github/views.py     merges the last 14 days of traffic into views.json
views.json           the visit ledger — the API forgets, this does not
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

## 2c · The PROFILE_TOKEN secret

The page builds without it. Three things need it:

- **SENSOR CONTACTS** — the traffic API needs push-level access, and
  `traffic` is not among the permissions a workflow `GITHUB_TOKEN` can be
  granted at all. No `permissions:` block can buy it; only a PAT can;
- **surveying a private repository** — `GITHUB_TOKEN` is scoped to this repo
  alone, so a private repo looks deleted to it;
- **keeping the survey dropdown current** — `GITHUB_TOKEN` is forbidden from
  pushing changes to any file under `.github/workflows/`, and the dropdown
  lives in one.

Create the PAT, then **Settings → Secrets and variables → Actions → New
repository secret → `PROFILE_TOKEN`**.

| kind | what to tick |
|:--|:--|
| fine-grained | this repository → **Administration: Read**, **Contents:
Read and write**, **Workflows: Read and write**; plus **Metadata: Read** on
all repositories for the survey |
| classic | `repo` and `workflow` |

**Administration: Read is the one that is easy to miss.** Without it the
traffic call answers 403, `views.py` prints *that token cannot read traffic*
and leaves the ledger alone, and SENSOR CONTACTS sits there saying so. If
you already had a `PROFILE_TOKEN` before this section existed, it almost
certainly lacks that box — edit the token, do not make a second one.

Without the secret entirely the log run skips the roster and the traffic
steps, says so in the log, and updates the page exactly as before. Nothing
breaks.

Note that a public repository's Actions logs are world-readable, so surveying a
private repo publishes what the survey prints about it. The survey warns you at
the top of its own report.

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
| SENSOR CONTACTS | `views.json`, which `views.py` merges from `/traffic/views` |
| THE BLACK BOX | this workflow's own last fourteen days of runs |
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

Two blocks are deliberate exceptions, and both are bounded by the same rule
— **the day in progress is never written**, so neither can move more than
once a day. SENSOR CONTACTS moves on a day that had a visitor; THE BLACK BOX
on a day that was a different kind of day from the one rolling off its far
end. Everything else, THE STAR CHART included, still moves only when the
account does. See PROCESS.md § 3. The profile repo itself is
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

Unauthenticated you get 60 API calls an hour and the build needs about 62 —
THE BLACK BOX added six, paging this workflow's own runs — so a local build
now runs out before it finishes. It degrades rather than lying: a partial
language read is discarded in favour of coarse repo counts; THE BLACK BOX
prints a sentence saying it could not read its own runs *this build*, rather
than drawing fourteen dark ticks it has no evidence for; and if the API is
unreachable entirely the build exits non-zero and leaves `README.md` exactly
as it was. Set `GITHUB_TOKEN` to a personal access token with no scopes to
get 5000/hr locally — worth doing now that the budget is over sixty.

## 6 · Things you may want to change

- **Cadence** — the `cron` in `log.yml`. It commits only on real change, so a
  faster schedule costs nothing but Action minutes.
- **The chart's magnitudes** — `MAG_BANDS` in `build.py`, in bytes of code.
  They are absolute rather than relative to the account on purpose: a band
  computed from the largest repo would re-magnitude every star the day one
  enormous repository arrived. Sizes and opacities are `MAG_R` / `MAG_O`.
- **The recorder's horizon** — `FLIGHT_DAYS`, fourteen to match the traffic
  API's own reach. Lengthening it costs one more page of runs per week.
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
- **The visit counter is a real one, not a hit badge.** The usual profile
  counters are an `<img>` pointing at someone else's server, which counts a
  render rather than a visitor, is undercounted by GitHub's image proxy, hands
  a stranger your traffic, and shows nothing if that host goes away. This one
  is GitHub's own measurement of this repository, kept in a file you own. The
  honest trade is scope: it counts visits to **the repository page**, which is
  the only page-view number GitHub exposes at all — there is no API for views
  of the profile itself.
