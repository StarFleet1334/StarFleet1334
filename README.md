<!--
  GENERATED FILE — do not edit.
  Written by .github/build.py from README.tpl.md and the GitHub API.
  Edit the template, or the deck data in build.py, and push.
-->

<!--LOG:masthead-->
<a name="log" href="#user-content-log"><img src="https://raw.githubusercontent.com/StarFleet1334/StarFleet1334/main/masthead.svg?v=752d98af" width="920" alt="STARFLEET 1334 — open log / flight deck. The account’s callsign, join date, repository count and current heading." /></a>
<!--/LOG:masthead-->

---

## ⌖ &nbsp;CURRENT HEADING

> **AETHER** — a desktop workspace with **no primary mouse**.
> A webcam watches your hands and your face; a headset mic listens; an agent
> sits at the other end of the desk. It ships with an **empty gesture
> vocabulary** and learns yours by watching how you actually move — so the
> dialect is *yours*, not a manual's.

<!--LOG:heading-->
<a name="heading" href="#user-content-heading"><img src="https://raw.githubusercontent.com/StarFleet1334/StarFleet1334/main/heading.svg?v=a64e4ebd" width="920" alt="AETHER's signal path: a webcam at frame rate and a fully offline headset mic feed three channels — hands, face and voice — into the desk (FastAPI over a websocket, vanilla JS, zero framework), with an agent at the other end, opening onto Canvas · Air Sketch (2D/3D) · Observatory · Codex · Palace · Watchtower · Console. 74 Python modules · 66 JS modules · ~82k lines. A motion repeated ~6× gets proposed back to you to bind." /></a>
<!--/LOG:heading-->

<sub>Also inside: a 2D alt-azimuth <b>Observatory</b> over 8,874 real catalogued stars ·
a <b>Codex</b> that reads a codebase into a force-directed constellation — one star per
module, one arc per import, the pulse travelling importer → imported ·
a <b>Chronosphere</b> that scrubs the whole board backwards through its own history.</sub>

---

## ✷ &nbsp;THE STAR CHART

<div align="center">

<!--LOG:starchart-->
<a href="https://starfleet1334.github.io/StarFleet1334/"><img src="https://raw.githubusercontent.com/StarFleet1334/StarFleet1334/main/chart.svg?v=742b48bb" width="920" alt="A star chart of this account: ENGINEERING DECK (9) &#183; SCIENCE DECK (7) &#183; PROPULSION (9) &#183; THE BRIDGE (9) &#183; THE ACADEMY (3), and 12 unfiled field stars belonging to no figure." /></a>
<!--/LOG:starchart-->

</div>

<sub><b>Click the plate.</b> It is a picture, and a README cannot make one
interactive — GitHub strips <code>&lt;script&gt;</code>, inline
<code>&lt;svg&gt;</code>, <code>&lt;style&gt;</code> and even
<code>&lt;map&gt;</code>, and an SVG loaded through <code>&lt;img&gt;</code> is
painted in the browser's secure mode, where no click and no hover reach inside
it. So the plate is a door rather than a control: it opens
<a href="https://starfleet1334.github.io/StarFleet1334/">the chart</a> in the
<b>same tab</b>, where every star can be clicked for its catalogue entry,
hovered for its magnitude, dragged, zoomed, and filtered down to one deck. Same
sky, same positions — the page reads the coordinates this plate was drawn
from.</sub>

<sub>One star per repository. Each deck of THE HOLD is a figure traced over its
own patch of sky; everything not yet filed into a deck is a field star,
belonging to no figure — which is what being unfiled looks like. <b>Magnitude
is apparent, not intrinsic</b>: it is how much code the repository holds, the
way a star's magnitude is how bright it looks from here and not how much it
matters. A star ringed with a dashed circle is private, so the API cannot
measure it and the page is taking <code>manifest.json</code>'s word.<br>
Every position is <code>sha256</code> of the repository's own name and nothing
else — no seed, no force-directed pass, no dependence on its neighbours — so a
new repository adds a star and moves no other one. The figures are minimum
spanning trees, so they do change when a star arrives, which is a real change
and should show.</sub>

---

## ⚙ &nbsp;SYSTEMS ONLINE

<sub>Every repository gets one vote, split between its languages by byte share — so no single vendored bundle can outrank a language that was actually written.</sub>

<!--LOG:systems-->
<a name="systems" href="#user-content-systems"><img src="https://raw.githubusercontent.com/StarFleet1334/StarFleet1334/main/systems.svg?v=682674cf" width="920" alt="Share of the account by language, one vote per repository split by byte share: Java 51%, Go 23%, HTML/CSS 7%, JavaScript 7%, Python 5%, Kotlin 2%, Dart 2%, OCaml 2%." /></a>
<!--/LOG:systems-->

---

## ▦ &nbsp;THE HOLD

<!--LOG:hold-->
<details>
<summary><b>⚭ &nbsp;ENGINEERING DECK</b> &nbsp;— distributed Java, events, contracts &nbsp;·&nbsp; <code>9 repositories</code></summary>
<br>

| repo | what it is |
|:--|:--|
| [`ecommerce-inventory-platform`](https://github.com/StarFleet1334/ecommerce-inventory-platform) | the largest of them — inventory, end to end |
| [`KafkaInMicroService`](https://github.com/StarFleet1334/KafkaInMicroService) | Kafka wired through a service boundary |
| [`KafkaRatingService`](https://github.com/StarFleet1334/KafkaRatingService) | ratings as an event stream |
| [`CQRS`](https://github.com/StarFleet1334/CQRS) | command/query separation, taken seriously |
| [`MicroServicesGEureka`](https://github.com/StarFleet1334/MicroServicesGEureka) | discovery with Eureka |
| [`Spring-Boot-MicroService`](https://github.com/StarFleet1334/Spring-Boot-MicroService) | the baseline the rest grew out of |
| [`Tolerant-Streams`](https://github.com/StarFleet1334/Tolerant-Streams) | streams that survive bad input |
| [`SCom`](https://github.com/StarFleet1334/SCom) · [`2Com`](https://github.com/StarFleet1334/2Com) | service-to-service, the plumbing of it |

</details>

<details>
<summary><b>⌖ &nbsp;SCIENCE DECK</b> &nbsp;— proving it works before claiming it does &nbsp;·&nbsp; <code>7 repositories</code></summary>
<br>

| repo | what it is |
|:--|:--|
| [`WireMock-Demo`](https://github.com/StarFleet1334/WireMock-Demo) · [`WireMock-Api`](https://github.com/StarFleet1334/WireMock-Api) · [`WireMock-Data`](https://github.com/StarFleet1334/WireMock-Data) | three angles on stubbing a dependency you don't own |
| [`GatlingReport`](https://github.com/StarFleet1334/GatlingReport) | load, measured rather than assumed |
| [`newrelic-lighthouse-demo`](https://github.com/StarFleet1334/newrelic-lighthouse-demo) | observability meeting a front-end budget |
| [`CarinaProject`](https://github.com/StarFleet1334/CarinaProject) | UI automation |
| [`Demo-TestService`](https://github.com/StarFleet1334/Demo-TestService) | the scaffold under all of it |

</details>

<details>
<summary><b>⚙ &nbsp;PROPULSION</b> &nbsp;— Go, and things that had to be fast or small &nbsp;·&nbsp; <code>9 repositories</code></summary>
<br>

| repo | what it is |
|:--|:--|
| [`Channels-and-Routines-GoLang-`](https://github.com/StarFleet1334/Channels-and-Routines-GoLang-) | concurrency from first principles |
| [`TransitionToGo`](https://github.com/StarFleet1334/TransitionToGo) | the crossing from JVM to Go, written down |
| [`WebScrapper_Go`](https://github.com/StarFleet1334/WebScrapper_Go) · [`FileFinder`](https://github.com/StarFleet1334/FileFinder) | small tools that do one thing |
| [`GoUI`](https://github.com/StarFleet1334/GoUI) · [`Animated-Ball`](https://github.com/StarFleet1334/Animated-Ball) · [`Clock`](https://github.com/StarFleet1334/Clock) | Go with a face on it |
| [`Little-Game-in-GoLang`](https://github.com/StarFleet1334/Little-Game-in-GoLang) · [`cards`](https://github.com/StarFleet1334/cards) | the fun ones |

</details>

<details>
<summary><b>◈ &nbsp;THE BRIDGE</b> &nbsp;— things people actually touch &nbsp;·&nbsp; <code>9 repositories</code></summary>
<br>

| repo | what it is |
|:--|:--|
| **AETHER** &nbsp;<sub>private, for now</sub> | gesture · face · voice workspace — ~82k lines |
| [`QuiziGeneratorWebExtension`](https://github.com/StarFleet1334/QuiziGeneratorWebExtension) | turns the page you're reading into a quiz |
| [`RepositoryAnalyzer`](https://github.com/StarFleet1334/RepositoryAnalyzer) | points a lens at a codebase and reports back |
| [`GymCRM-System`](https://github.com/StarFleet1334/GymCRM-System) · [`GymApplication`](https://github.com/StarFleet1334/GymApplication) | one real domain, modelled twice |
| [`Chess`](https://github.com/StarFleet1334/Chess) · [`steganography`](https://github.com/StarFleet1334/steganography) | rules, and hiding things inside pictures |
| [`Chat-Sytem-`](https://github.com/StarFleet1334/Chat-Sytem-) · [`Java-Chat-App`](https://github.com/StarFleet1334/Java-Chat-App) | sockets, in two languages |

</details>

<details>
<summary><b>⌂ &nbsp;THE ACADEMY</b> &nbsp;— repos written to be read by someone else &nbsp;·&nbsp; <code>3 repositories</code></summary>
<br>

| repo | what it is |
|:--|:--|
| [`Ocaml-For-Begginer-Students-Edition-`](https://github.com/StarFleet1334/Ocaml-For-Begginer-Students-Edition-) | functional programming for people meeting it first |
| [`Java-For-Students-Advanced-`](https://github.com/StarFleet1334/Java-For-Students-Advanced-) | the second pass, where it gets interesting |
| [`duckietown-lx`](https://github.com/StarFleet1334/duckietown-lx) | autonomous driving exercises, on very small robots |

</details>

<!--/LOG:hold-->

<details>
<summary><b>⌁ &nbsp;NEW ARRIVALS</b> &nbsp;— on the dock, not yet stowed</summary>
<br>

<!--LOG:arrivals-->
| repo | language | first commit |
|:--|:--|:--|
| [`Shelves`](https://github.com/StarFleet1334/Shelves) | JavaScript | 2026-08-21 |
| [`social-media-app-Task-`](https://github.com/StarFleet1334/social-media-app-Task-) | Java | 2024-11-14 |
| [`SimD`](https://github.com/StarFleet1334/SimD) | Java | 2024-08-12 |
| [`SimpleAuthenticationAp`](https://github.com/StarFleet1334/SimpleAuthenticationAp) | Java | 2024-06-03 |
| [`CMDGeneration`](https://github.com/StarFleet1334/CMDGeneration) | Java | 2024-04-18 |
| [`Demo_API`](https://github.com/StarFleet1334/Demo_API) | Go | 2024-03-23 |
| [`SpamMaker`](https://github.com/StarFleet1334/SpamMaker) | Go | 2024-02-24 |
| [`network_cm`](https://github.com/StarFleet1334/network_cm) | Java | 2023-12-09 |

<sub>…and 4 more not yet filed.</sub>
<!--/LOG:arrivals-->

</details>

## ◉ &nbsp;SENSOR CONTACTS

<sub>Who has been on the deck. GitHub's traffic API remembers fourteen days and
then forgets, so <code>.github/views.py</code> keeps the ledger in
<code>views.json</code> and the totals below count from it. Nothing here comes
from a third party — the number is this repository's own traffic, read by this
repository.</sub>

<!--LOG:views-->
<sub>No closed day on the ledger yet. <code>.github/views.py</code> records a day only once it is over, so the first number appears after the first full UTC day. If it stays empty past that, the token cannot read traffic — it needs <b>Administration: read</b> on this repository.</sub>
<!--/LOG:views-->

---

## ✕ &nbsp;THE BLACK BOX

<sub>This page rebuilds itself hourly, which means the one failure it cannot
otherwise show you is its own — an expired token, an API that started
refusing, a workflow disabled for inactivity all look exactly like a quiet
month. So the recorder keeps a fortnight of its own runs, one tick per closed
day, and reports by exception.</sub>

<!--LOG:blackbox-->
| | |
|---|---|
| **Last 14 days** | `─╳┼─────┼─────` &nbsp;·&nbsp; 2 changed the page &nbsp;·&nbsp; **1 refused** |
| **Reading** | `─` ran, nothing moved &nbsp;·&nbsp; `┼` the page changed &nbsp;·&nbsp; `╳` refused &nbsp;·&nbsp; `·` no run at all |
| **Last refusal** | `2026-09-08` &nbsp;·&nbsp; the *rebuild the log* step |
<!--/LOG:blackbox-->

---

## ⛬ &nbsp;WORKING NOTES

<sub>Five things this desk keeps being right about.</sub>

<dl>

<dt><b>01 &nbsp;·&nbsp; Measured, not guessed</b></dt>
<dd>A number read off the machine beats a number I reasoned my way to. Anything about layout, timing or hit-testing gets checked in the real environment — not in a stub that agrees with me.</dd>

<dt><b>02 &nbsp;·&nbsp; The failure should be a sentence</b></dt>
<dd>A thing that can't do the thing says which of the two reasons it is, in words. Stack traces are for me; sentences are for whoever is holding it.</dd>

<dt><b>03 &nbsp;·&nbsp; Fail closed on the dangerous half</b></dt>
<dd>If the redactor throws, the file does not go into the archive. The right default is the one where the bad outcome is impossible, not the one where it's unlikely.</dd>

<dt><b>04 &nbsp;·&nbsp; Rest, don't vanish</b></dt>
<dd>A control with nothing to act on stays visible and explains itself, dimmed. Something that disappears when idle can only ever be discovered by accident.</dd>

<dt><b>05 &nbsp;·&nbsp; Ship the whole thought</b></dt>
<dd>The finding, the evidence and the fix are one thing in three parts. Three loose notes are three orphans.</dd>

</dl>

---

<div align="center">
<pre>
──────────────────────────────────────────────────────
            E N D   O F   T R A N S M I S S I O N
──────────────────────────────────────────────────────
</pre>

<!--LOG:stamp-->
<sub>last log entry &nbsp;·&nbsp; 2026-08-28 &nbsp;·&nbsp; <code>Shelves</code> &nbsp;·&nbsp; the desk is still on</sub>
<!--/LOG:stamp-->

</div>
