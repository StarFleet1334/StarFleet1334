<div align="center">

<pre>
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        S T A R F L E E T  ·  1 3 3 4                     ║
║        open log / flight deck                            ║
║                                                          ║
║   ────────────────────────────────────────────────       ║
║                                                          ║
║   callsign      IDoctor                                  ║
║   on station    since 2021-07-04                         ║
║   manifest      54 public repositories                   ║
║   crewed by     Java  ·  Go  ·  Python  ·  JS            ║
║   heading       AETHER - a workspace you drive with      ║
║                 your hands, your face and your voice     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
</pre>

<sub>
<img src="https://img.shields.io/badge/repos-54-0d1117?style=flat-square&labelColor=0d1117&color=58a6ff" alt="repos" />
&nbsp;
<img src="https://img.shields.io/github/followers/StarFleet1334?style=flat-square&labelColor=0d1117&color=58a6ff&label=followers" alt="followers" />
&nbsp;
<img src="https://img.shields.io/badge/primary%20instrument-hands-0d1117?style=flat-square&labelColor=0d1117&color=f0883e" alt="primary instrument: hands" />
</sub>

</div>

---

## ⌖ &nbsp;CURRENT HEADING

> **AETHER** — a desktop workspace with **no primary mouse**.
> A webcam watches your hands and your face; a headset mic listens; an agent
> sits at the other end of the desk. It ships with an **empty gesture
> vocabulary** and learns yours by watching how you actually move — so the
> dialect is *yours*, not a manual's.

| | |
|---|---|
| **Surface** | 74 Python modules · 66 JS modules · ~81k lines |
| **Spine** | FastAPI over a websocket, vanilla JS, zero framework |
| **Eyes** | MediaPipe hand + face landmarks at frame rate |
| **Ears** | Vosk live preview, Whisper `medium.en` final — fully offline |
| **Rooms** | Canvas · Air Sketch (2D/3D) · Observatory · Codex · Palace · Watchtower · Console |
| **The trick** | A motion repeated ~6× gets *proposed back to you* to bind |

<sub>Also inside: a 2D alt-azimuth <b>Observatory</b> over 8,874 real catalogued stars ·
a <b>Codex</b> that reads a codebase into a force-directed constellation — one star per
module, one arc per import, the pulse travelling importer → imported ·
a <b>Chronosphere</b> that scrubs the whole board backwards through its own history.</sub>

---

## ✦ &nbsp;STAR CHART

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#0d1117","primaryTextColor":"#e6edf3","primaryBorderColor":"#30363d","lineColor":"#58a6ff","secondaryColor":"#161b22","tertiaryColor":"#161b22","fontFamily":"ui-monospace, SFMono-Regular, monospace","fontSize":"13px"}}}%%
flowchart LR
    ME(("◈"))

    ME --- A["distributed java"]
    ME --- B["go, close to the metal"]
    ME --- C["proving it works"]
    ME --- D["spatial + human input"]
    ME --- E["teaching it"]

    A --- A1["kafka services"]
    A --- A2["CQRS"]
    A --- A3["eureka microservices"]

    B --- B1["channels & routines"]
    B --- B2["scrapers, finders, UIs"]

    C --- C1["wiremock"]
    C --- C2["gatling + new relic"]
    C --- C3["carina"]

    D --- D1["AETHER"]
    D --- D2["codex constellations"]

    E --- E1["ocaml, beginners"]
    E --- E2["java, advanced"]

    classDef hub  fill:#0d1117,stroke:#58a6ff,stroke-width:2px,color:#58a6ff
    classDef limb fill:#161b22,stroke:#30363d,color:#e6edf3
    classDef leaf fill:#0d1117,stroke:#21262d,color:#8b949e
    class ME hub
    class A,B,C,D,E limb
    class A1,A2,A3,B1,B2,C1,C2,C3,D1,D2,E1,E2 leaf
```

---

## ⧗ &nbsp;SHIP'S LOG

```mermaid
timeline
    title trajectory
    2021 : first commit pushed into the dark
    2022 : java, properly : data structures and the JVM's temper
    2023 : services, queues, contracts
    2024 : kafka, CQRS, eureka : go's concurrency : wiremock, gatling, new relic : ocaml and java, written for students
    2025 : an inventory platform : a repository analyzer : a quiz generator that lives in the browser
    2026 : AETHER - hands, face, voice, and an agent at the desk
```

---

## ⚙ &nbsp;SYSTEMS ONLINE

| | instrument | where it actually shows up |
|:--|:--|:--|
| `▰▰▰▰▰▰▰▰▰▱` | **Java / Spring** | 26 repos — services, CQRS, Kafka, Eureka, chat, CRM |
| `▰▰▰▰▰▰▰▱▱▱` | **Go** | 11 repos — goroutines, scrapers, a file finder, a UI, a clock |
| `▰▰▰▰▰▰▰▱▱▱` | **Python** | AETHER's entire backend — FastAPI, MediaPipe, Whisper |
| `▰▰▰▰▰▰▱▱▱▱` | **Vanilla JS** | 37k lines of it, no framework, on purpose |
| `▰▰▰▰▰▰▱▱▱▱` | **Kafka · CQRS · microservices** | event-driven Java, the boring-on-purpose kind |
| `▰▰▰▰▰▱▱▱▱▱` | **Testing & perf** | WireMock, Gatling, Carina, New Relic + Lighthouse |
| `▰▰▰▰▱▱▱▱▱▱` | **Three.js / WebGL** | 3D canvas, holographic sketch, star fields |
| `▰▰▰▱▱▱▱▱▱▱` | **Dart · Kotlin · OCaml** | a chat system, an Android detour, a teaching language |

---

## ▦ &nbsp;THE HOLD

<details>
<summary><b>⚭ &nbsp;ENGINEERING DECK</b> &nbsp;— distributed Java, events, contracts</summary>
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

</details>

<details>
<summary><b>⌖ &nbsp;SCIENCE DECK</b> &nbsp;— proving it works before claiming it does</summary>
<br>

| repo | what it is |
|:--|:--|
| [`WireMock-Demo`](https://github.com/StarFleet1334/WireMock-Demo) · [`-Api`](https://github.com/StarFleet1334/WireMock-Api) · [`-Data`](https://github.com/StarFleet1334/WireMock-Data) | three angles on stubbing a dependency you don't own |
| [`GatlingReport`](https://github.com/StarFleet1334/GatlingReport) | load, measured rather than assumed |
| [`newrelic-lighthouse-demo`](https://github.com/StarFleet1334/newrelic-lighthouse-demo) | observability meeting a front-end budget |
| [`CarinaProject`](https://github.com/StarFleet1334/CarinaProject) | UI automation |
| [`Demo-TestService`](https://github.com/StarFleet1334/Demo-TestService) | the scaffold under all of it |

</details>

<details>
<summary><b>⚙ &nbsp;PROPULSION</b> &nbsp;— Go, and things that had to be fast or small</summary>
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
<summary><b>◈ &nbsp;THE BRIDGE</b> &nbsp;— things people actually touch</summary>
<br>

| repo | what it is |
|:--|:--|
| **AETHER** &nbsp;<sub>private, for now</sub> | gesture · face · voice workspace, ~81k lines |
| [`QuiziGeneratorWebExtension`](https://github.com/StarFleet1334/QuiziGeneratorWebExtension) | turns the page you're reading into a quiz |
| [`RepositoryAnalyzer`](https://github.com/StarFleet1334/RepositoryAnalyzer) | points a lens at a codebase and reports back |
| [`GymCRM-System`](https://github.com/StarFleet1334/GymCRM-System) · [`GymApplication`](https://github.com/StarFleet1334/GymApplication) | one real domain, modelled twice |
| [`Chess`](https://github.com/StarFleet1334/Chess) · [`steganography`](https://github.com/StarFleet1334/steganography) | rules, and hiding things inside pictures |
| [`Chat-Sytem-`](https://github.com/StarFleet1334/Chat-Sytem-) · [`Java-Chat-App`](https://github.com/StarFleet1334/Java-Chat-App) | sockets, in two languages |

</details>

<details>
<summary><b>⌂ &nbsp;THE ACADEMY</b> &nbsp;— repos written to be read by someone else</summary>
<br>

| repo | what it is |
|:--|:--|
| [`Ocaml-For-Begginer-Students-Edition-`](https://github.com/StarFleet1334/Ocaml-For-Begginer-Students-Edition-) | functional programming for people meeting it first |
| [`Java-For-Students-Advanced-`](https://github.com/StarFleet1334/Java-For-Students-Advanced-) | the second pass, where it gets interesting |
| [`duckietown-lx`](https://github.com/StarFleet1334/duckietown-lx) | autonomous driving exercises, on very small robots |

</details>

---

## ◉ &nbsp;TELEMETRY

<div align="center">

<img height="165" alt="stats" src="https://github-readme-stats.vercel.app/api?username=StarFleet1334&show_icons=true&hide_border=true&include_all_commits=true&count_private=true&theme=transparent&title_color=58a6ff&text_color=8b949e&icon_color=f0883e&ring_color=58a6ff" />
<img height="165" alt="languages" src="https://github-readme-stats.vercel.app/api/top-langs/?username=StarFleet1334&layout=compact&hide_border=true&langs_count=8&theme=transparent&title_color=58a6ff&text_color=8b949e" />

<br><br>

<img width="88%" alt="flight path" src="https://github-readme-activity-graph.vercel.app/graph?username=StarFleet1334&bg_color=00000000&color=58a6ff&line=58a6ff&point=f0883e&area=true&area_color=58a6ff&hide_border=true&custom_title=flight%20path" />

</div>

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

<details>
<summary><sub>⌁ &nbsp;raw sensor feed</sub></summary>
<br>

<pre>
       ·        ✦                    ·               ✧
   ✧                    ·                                    ·
             ·                  ✦          ·
    ·                                              ✦
                 ✦        ·               ·                ✧
       ·                          ·

   8,874 catalogued stars sit in a file on my desk.
   Not one of them is synthetic. That is the whole point.
</pre>

</details>

---

<div align="center">
<pre>
──────────────────────────────────────────────────────
            E N D   O F   T R A N S M I S S I O N
──────────────────────────────────────────────────────
</pre>
<sub>the desk is still on</sub>
</div>
