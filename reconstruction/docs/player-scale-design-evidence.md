# W0-P #90: player-scale game design — evidence, prioritization and gates

**Researched:** 14 November 2026. **Status:** competitor/popularity evidence
and proposed clean-room design; **not recovered ROB RUN mechanics, not
shipped gameplay, not evidence of causal feature effects.**
Maintains the master [waterfall blueprint](full-game-waterfall.md).
A numeric target below is a *test hypothesis* until real pilot cohorts exist.

## What can and cannot be inferred from successful player bases

**Never compare unlike denominators as if interchangeable:** Steam *peak
concurrent* (one instant), units *sold* (cumulative), Roblox *daily active
users* (a day) and Fortnite *hours* (a year) measure different behaviors.
Peak concurrency signals potential demand, not loyalty, D7 retention or
profit. A game's popularity does not identify which individual mechanic
made it popular. Benchmarks below are independent market signals used to
choose **small experiments** for this original crime sandbox.

| Observed game/platform evidence | Measure, date and authority | Candidate lesson / inference, NOT proven causal |
| --- | --- | --- |
| **ROB RUN**: free-to-play, role-based open-world crime sandbox | **418,021 Steam all-time peak concurrent** on 14 Nov 2026; SteamDB review snapshot ~**53% positive** (mixed) at research time. [SteamDB chart](https://steamdb.info/app/4262460/charts/), [official Steam listing](https://store.steampowered.com/app/4262460/ROB_RUN/) | Strong immediate market interest; mixed reception makes fairness, player ramp, anti-cheat and quality at least as important as spectacle. Do not mistake a peak for retained players. |
| **ARC Raiders**: extraction with improvised co-op/PvP outcomes | Publisher Nexon reported **12.4 million units** sold and **960,000 concurrent players across platforms** in Jan 2026, 10 weeks after launch. [Nexon announcement](https://www.nexon.co.jp/en/news/detail/?id=20260113-9bbd7e90) | Test legible high-stakes extraction, non-scripted player encounters and recoverable loss; do not copy proprietary content. |
| **Schedule I**: open-world crime-business simulation | SteamDB reports **459,075 all-time Steam peak concurrent**, 6 Apr 2025; [SteamDB chart](https://steamdb.info/app/3164500/charts/) | Try satisfying small-business, logistics, cashflow and property ownership alongside shooting, with an actual playable economics loop. |
| **Rust**: social survival, factions and player-built bases | **262,284 Steam all-time peak concurrent**, 2 Jan 2025; longitudinal concurrent activity remains sizable in 2026. [SteamDB chart](https://steamdb.info/app/252490/charts/) | Test defendable ownership, meaningful alliances and cyclical territory conflict but protect late joiners and casuals from helpless gear gaps. |
| **R.E.P.O.**: small-team physics heist/horror comedy | **271,571 Steam all-time peak concurrent**, 23 Mar 2025. [SteamDB chart](https://steamdb.info/app/3241660/charts/) | Prototype surprising team interaction and comedic failure/recovery that players might *choose* to share. Clip-worthiness is a hypothesis. |
| **HELLDIVERS II**: cooperative mission-level shared objectives | Publisher Sony documented **12 million+ units sold by 5 May 2024** on PC/PS5. [Sony investor materials](https://www.sony.com/en/SonyInfo/IR/library/presen/business_segment_meeting/pdf/2024/presen_E.pdf) | Trial short team missions and faction contribution, but keep the one-mission loop excellent before a global-war simulation. |
| **Minecraft**: personal creative expression and building | **350 million lifetime units** by the April 2025 benchmark. [Guinness record citing Mojang](https://www.guinnessworldrecords.com/world-records/best-selling-video-game) | Prototype player-authored base identity and useful blueprints; do not infer that a full block-editing engine is justified. |
| **Roblox**: social identity, creation and discovery | SEC-filed Q3 2026 letter: **138 million DAU**, nearly **34 billion hours engaged** in Q3. [Company filing](https://www.sec.gov/Archives/edgar/data/1315098/000162828026068235/ex991-q32026earningsshar.htm) | Social re-entry and lightweight community-authored goals may help longevity; these metrics do not imply an unmoderated game platform is viable for a small project. |
| **Fortnite creator experiences** | Epic reported **5.23 billion creator-island hours** in 2024, **36.5%** of Fortnite playtime; creator-made roleplay and noncombat content increased. [Epic 2024 creator review](https://www.fortnite.com/news/fortnite-ecosystem-2024-year-in-review-celebrating-creators-and-looking-ahead) | Support varied noncombat social roles and bounded custom contracts *after* core mechanics, moderation and discovery work. |

**Early weak-signal negatives (NOT representative survey data):** In
[14 Nov 2026 ROB RUN solo-play discussion](https://www.reddit.com/r/robrun/comments/1xvyw5v/not_for_solos/),
players described highly time-consuming recovery for solos. In
[cycle-pacing discussion](https://www.reddit.com/r/robrun/comments/1xw60r9/1_week_wipes_are_a_problem/),
players disagreed about weekly resets and late-entry fairness; in
[griefing and progression discussion](https://www.reddit.com/r/robrun/comments/1xwgbs9/rob_runs_biggest_issues/),
users reported cheating, griefing and early endgame, with counterclaims
from others. Small self-selected threads **do not measure prevalence**.
They provide *failure scenarios to test*, not license to assert all
players demand the same changes.

## Chosen experience pillars, in dependency order

The matrix here is a decision contract for the corresponding
[master blueprint](full-game-waterfall.md#player-scale-experience-pillars--evidence-backed-design-priorities-w0-p-90).
Every mechanic is **PROPOSED** unless separately verified in the
source [evidence ledger](evidence.md). The gameplay ownership remains
W2→W7; this doc and issue #90 do not bypass pending W1-AH #87 / W1-AI #89.

| Priority, player value | Minimal first implementation | Experiment or acceptance signal | Dependency and guardrail |
| --- | --- | --- | --- |
| **P0: first fun in one short session** | Safe optional guided cargo delivery or single-room robbery with clear payout/deposit and next-role preview; replayable solo, co-op optional | Closed-playtest median time-to-meaningful-choice, time-to-secured-payout, tutorial opt-out, interrupted-run recovery, D1/D7 per solo/crew cohorts. **5-minute first payout is a hypothesis, not a sourced rule.** | W2 journey and economy; W3 deterministic playable; W7 playtest. No forced purchase, party, registration maze or time-locked tutorial. |
| **P0: trust and counterplay in high stakes** | Transparent stake/loss warning; server-correct payouts and inventory; spawn protection, reconnect and loss receipts; rapid report/block path | No dupe in deterministic tests; falsified client actions rejected; recorded failed reconnect inventory restoration; verified false-positive rate and unfair-death reports | W2 threat model, W4 authority/security, W7 real adversarial sessions. Do not promise cheat-free service or turn high stakes into grief. |
| **P1: emergent, asymmetric team stories** | One compact robbery with stealth/loud path, driver/lookout/infiltrator roles, live police opposition, easy code invite and ping wheel | Distinct successful approaches, team-join completion, solo mission viability, fair cops-vs-criminals counterplay, repeat cooperative sessions | W3 local scenarios before W4 replicated parties, W6 social affordances. No requirement to use voice chat. |
| **P1: creative ownership and economy** | One defensible but bounded hideout, vehicle customization, small production route and player-visible settlement contribution | First meaningful owned space, cash/item ledger conservation, repeat property use, late-cycle solo progress vs clan | W2 resource and wipe invariants; W3 production/build; W4 persistence. No transferable pay-to-win advantages. |
| **P1: social proof without manipulation** | Opt-in local 15–30 s recap of an unexpected escape/betrayal, manual review then private share; post-run crew invite | Consent rates, manually shared stories, share-to-party join; monitor report/block and privacy deletion rates | W6/W7 after reliable replay capture and privacy design; no auto-posting, voice capture, public identifiers without informed consent. |
| **P2: living creator/community events** | First one constrained, moderated job/route contract template; optional server-event rotation and end-cycle non-power legacy card | Unique creators **and** completers, meaningful task variety, content abuse review load, season re-entry without power advantage | Only after W4 authority and W6 moderation. No unrestricted scripting, creator marketplace, infinite live-ops promises or full Minecraft/Roblox tooling. |

## Stage-specific delivery gates and instrumentation

**W2 design gate:** A tested journey map for first-time solo, party,
late-cycle entrant and returning player; explicit role choice, recovery,
transaction invariants, privacy/voice consent, spawn/camping counterplay,
authority and wipe reset semantics. All numbers labeled PROPOSED and
versioned. Define source-controlled `economy_quote`, `job_result`,
`loss_receipt` and `season_legacy` contracts only when needed by a
real playable slice; do not overengineer services.

**W3 single-player gate:** One satisfying 10–20 minute representative
loop composed of entry, clear choice, risk, cash-out and meaningful
upgrade/base action; replay same content via two routes or roles. Test
that a new solo player can recover from death and return, rather than
requiring a clan. A test duration is a trial design assumption, not
a known original mission requirement.

**W4 multiplayer gate:** Shared server authority for money, items,
movement, damage and property; join/reconnect; cooperative roles
without voice; adversarial money duplication and spawn-camp tests;
latency/performance budgets set after actual load tests. This is the
quality prerequisite for high-player-count social discovery.

**W5/W6 content and social gate:** Distinct authored objectives,
opt-in localized replay review and deletion, moderated typed contracts,
friend discovery and seasonal non-power legacy. Ship a small content
set that changes decisions, not a large list of unfinished modes.

**W7 launch gate:** Actual Unity 6000.3 Editor/Play Mode/Windows EXE,
manual solo/crew sessions, real reconnect/dupe/grief tests, accessible
UI/controls, privacy review, client FPS/server tick under measured load.
Headless CI cannot substitute for these tests.

**Metrics and interpretation contract:**

- Primary north star: **successful meaningful sessions per active
  player**, partitioned by solo/crew, novice/veteran and cycle age.
  Define an event only after player action plus one resolved
  cash-out/mission/build/defense consequence; not simply a login.
- Funnel: game launch → playable state → first meaningful choice →
  first objective attempt → first secured reward → second session.
  Record opt-out and explicit abandon causes; avoid measuring
  only players who completed tutorial (survivorship bias).
- Retention: D1/D7 by **new-account cohorts**, plus re-entry after
  server resets; report sample size and confidence intervals. Never
  market peak CCU as proof of D7 health.
- Trust: crash/softlock and loss rate, anti-cheat false positives,
  player reports, victim response time, server-authoritative
  economy conservation, time-to-progress parity and solo late-entry
  disadvantage. Watch for worse outcomes after adding PvP.
- Growth: voluntary friend joins, creator contracts *completed*,
  opt-in clip-to-invite conversion, with abuse/privacy rates as
  simultaneous non-negotiable guardrails; do not optimize forced
  invite volume or extract every possible social graph edge.
- Player experiments: closed-playtest two versions of first session,
  calibrated risk, alternate wipe cadence **only if population and
  cohort quality permit**; review new/solo vs veteran/clan separately.
  Record sample limits. No arbitrary guaranteed lift or fake KPI target.

## Explicit rejections / defer list

Do **not** reproduce competitor IP or original ROB RUN media without
rights. Do not introduce coercive streaks, excessive time gating,
manipulative FOMO, pay-to-win advantages, guaranteed virality,
unbounded clan dominance, public-by-default clips, unsolicited
chat/invites, personal voice replay without consent, or full arbitrary
user scripting/editors as launch prerequisites. High risk is only
enjoyable with clear stakes, readable counterplay, and viable comeback.
The original reference game's published seven-day Federal Raid is
OFFICIAL **for that game**; other cadence experiments are PROPOSED
**for our independent game**. No features in this document should
be represented as already implemented in current GitHub source.

## Evidence-to-implementation trace

- **W0-P #90:** This analysis and the player-scale master-section
  (documentation-only; no source scan or gameplay code affected).
- **W1 #87 / #89 and control #32:** Independent, fail-closed binary
  extraction and source coverage. Do not bypass or combine concerns.
- **W2:** convert highest-value P0/P1 journeys into formal
  authoritative contracts and a small playable acceptance scope.
- **W3/W4:** prove single-player and then multiplayer quality before
  expanding creator events or cosmetic breadth.
- **W5/W6/W7:** deliver content, consent-gated social loops and
  actual Editor/EXE/user testing after earlier gates.

**Do not conflate research, backlog, source-code implementation and
released features.** The repository's truthful completion ledger remains
the source of record.
