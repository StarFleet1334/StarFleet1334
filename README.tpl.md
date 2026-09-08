<!--
  ┌────────────────────────────────────────────────────────────────────────┐
  │  THIS IS THE SOURCE. README.md is generated from it — do not edit that │
  │  file, your change will be overwritten on the next run.                │
  │                                                                        │
  │  Prose here is yours to write. Everything between a LOG marker and its │
  │  closing pair is written by .github/build.py from the live API.        │
  │                                                                        │
  │      python .github/build.py            rebuild README.md now          │
  │      python .github/build.py --check    say whether it would change    │
  └────────────────────────────────────────────────────────────────────────┘
-->

<!--LOG:masthead-->
<!--/LOG:masthead-->

---

## ⌖ &nbsp;CURRENT HEADING

> **AETHER** — a desktop workspace with **no primary mouse**.
> A webcam watches your hands and your face; a headset mic listens; an agent
> sits at the other end of the desk. It ships with an **empty gesture
> vocabulary** and learns yours by watching how you actually move — so the
> dialect is *yours*, not a manual's.

<!--LOG:heading-->
<!--/LOG:heading-->

<sub>Also inside: a 2D alt-azimuth <b>Observatory</b> over 8,874 real catalogued stars ·
a <b>Codex</b> that reads a codebase into a force-directed constellation — one star per
module, one arc per import, the pulse travelling importer → imported ·
a <b>Chronosphere</b> that scrubs the whole board backwards through its own history.</sub>

---

## ✷ &nbsp;THE STAR CHART

<div align="center">

<!--LOG:starchart-->
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
<!--/LOG:systems-->

---

## ▦ &nbsp;THE HOLD

<!--LOG:hold-->
<!--/LOG:hold-->

<details>
<summary><b>⌁ &nbsp;NEW ARRIVALS</b> &nbsp;— on the dock, not yet stowed</summary>
<br>

<!--LOG:arrivals-->
<!--/LOG:arrivals-->

</details>

## ◉ &nbsp;SENSOR CONTACTS

<sub>Who has been on the deck. GitHub's traffic API remembers fourteen days and
then forgets, so <code>.github/views.py</code> keeps the ledger in
<code>views.json</code> and the totals below count from it. Nothing here comes
from a third party — the number is this repository's own traffic, read by this
repository.</sub>

<!--LOG:views-->
<!--/LOG:views-->

---

## ✕ &nbsp;THE BLACK BOX

<sub>This page rebuilds itself hourly, which means the one failure it cannot
otherwise show you is its own — an expired token, an API that started
refusing, a workflow disabled for inactivity all look exactly like a quiet
month. So the recorder keeps a fortnight of its own runs, one tick per closed
day, and reports by exception.</sub>

<!--LOG:blackbox-->
<!--/LOG:blackbox-->

---

## ⛬ &nbsp;WORKING NOTES

<table>
<tr>
<td width="30%"><b>Measured, not guessed</b></td>
<td>A number read off the machine beats a number I reasoned my way to. Anything about layout, timing or hit-testing gets checked in the real environment — not in a stub that agrees with me.</td>
</tr>
<tr>
<td><b>The failure should be a sentence</b></td>
<td>A thing that can't do the thing says which of the two reasons it is, in words. Stack traces are for me; sentences are for whoever is holding it.</td>
</tr>
<tr>
<td><b>Fail closed on the dangerous half</b></td>
<td>If the redactor throws, the file does not go into the archive. The right default is the one where the bad outcome is impossible, not the one where it's unlikely.</td>
</tr>
<tr>
<td><b>Rest, don't vanish</b></td>
<td>A control with nothing to act on stays visible and explains itself, dimmed. Something that disappears when idle can only ever be discovered by accident.</td>
</tr>
<tr>
<td><b>Ship the whole thought</b></td>
<td>The finding, the evidence and the fix are one thing in three parts. Three loose notes are three orphans.</td>
</tr>
</table>

---

<div align="center">
<pre>
──────────────────────────────────────────────────────
            E N D   O F   T R A N S M I S S I O N
──────────────────────────────────────────────────────
</pre>

<!--LOG:stamp-->
<!--/LOG:stamp-->

</div>
