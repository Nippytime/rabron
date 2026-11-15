# MASTER PLAN — RABRON
**Canonical production charter and acceptance contract | Version 1.0 | 14 November 2026**

> Status: PLAN, NOT A SHIPPED GAME. A complete, original, polished Windows-first multiplayer crime sandbox is the destination. The repository contains a prototype, evidence extraction tooling and design documentation; no full game, production multiplayer service or release build has been verified. Every milestone below needs its own evidence before it can be marked complete.

## 0. How to use this document

This is the production-facing master plan for Nippytime/rabron. It defines **what must be made**, **the player experience it must deliver**, **the order of execution**, **the measurable quality gates**, **who decides**, and **what evidence proves completion**. It is intentionally ambitious in product quality and conservative in unvalidated scope.

Source-of-truth precedence:
1. **Actual GitHub code, open Issues/PRs, latest commit and Actions jobs** determine the *current implementation and CI truth*.
2. **reconstruction/data/extraction_coverage.json** and linked original-byte artifacts determine *source inventory coverage*.
3. **reconstruction/docs/full-game-waterfall.md** defines detailed prior W0–W8 system scope and historical milestones; this master plan adds a production operating system rather than erasing it.
4. **reconstruction/docs/player-scale-design-evidence.md** preserves market comparisons and their statistical limitations.
5. Approved specifications, tests, playtest results and decision records determine subsequent design choices. Draft assumptions never become source-verified facts.

If a measured status changes, update the relevant ledger, acceptance record and this snapshot through a reviewable PR; do not silently replace old historical evidence. **Branching rule: one independently deliverable Issue → work/<number>-<slug> from dev → one PR into dev → all nonempty required checks green → merge → verify postmerge → update control Issue #32.** main remains the production line.

### 0.1 Factual snapshot at plan creation

| Area | Verified integration dev | In-flight, NOT integrated into dev |
| --- | --- | --- |
| Integration head | e65566979896ca8f97a235c102bf04be6c6e24a6 | W1-AI issue #89, PR #92, branch work/89-sectorcenter-common-lfs at 3169404d88d16d3b03f2b82f640efc81d9fede55 |
| Original tracked UnityFS sources | 322 of 330 documented; 8 still unscanned | PR #92 proposed measured 324 of 330; 6 still unscanned; no merge assumed |
| Numeric completeness | 44 unresolved older numeric field caps | PR #92 introduces two additional bounded caps (46 total outstanding on its branch) |
| Other evidence gap | One separately unparsed oversized Wwise MonoBehaviour; no recovered original server-authoritative method formulas | Unchanged; a passing bounded scanner does not prove numeric completeness |
| Original code/rights | Original IL2CPP method bodies and server logic not recovered; no third-party art/audio reuse rights presumed | Nothing in PR #92 changes this |
| Gameplay | Basic portable heist/cash/laundering/bank rule simulation and rudimentary Unity 3D prototype exist | Most full-game mechanics, authoritative multiplayer and content are not built |
| Release acceptance | Python/.NET/synthetic test evidence exists | **Actual Unity 6000.3 Editor import, Play Mode execution, Windows EXE and human gameplay test remain NOT RUN** |
| Other open delivery | Issue #3 extraction and #9 playable Unity acceptance; #32 control | Issue #93 canonical master production plan |

At the time of issue #93 creation, W1-AI current-head original-source recheck and 182/182 PR-head check runs had reported success, but **PR #92 remained open**. The authoritative dev values above must not be replaced by proposed branch values until a verified merge and postmerge CI. No new extraction or gameplay is claimed by this plan.

## 1. Product charter: what a player actually gets

### 1.1 Identity and positioning
- **Genre:** original third-person, systemic open-world crime/social sandbox with high-stakes jobs, vehicle-based escape, asymmetric police/criminal roles, logistics, property, territorial conflict and persistent identity.
- **Initial platform:** Windows PC/Steam, keyboard/mouse first and complete controller coverage before release. Additional platforms are not commitments.
- **Experience:** legible, tactile, fast to start, fair in loss, deep over repeat sessions. A solo player has a meaningful career; crews create memorable emergent stories; police provide counterplay rather than one-sided punishment.
- **Originality:** invent original world, characters, layout, UI, names, art, sound and server rules. Recovered client metadata can inform understanding only with documented provenance; it does not authorize reuse or prove reference-game server mechanics.
- **Business:** a complete, fairly priced game is the baseline. Live events/social loops are optional layers, never a substitute for the core game; no pay-to-win, predatory streaks or forced social sharing.

### 1.2 The non-negotiable north-star loop
**Observe the world → choose a lawful or unlawful opportunity → acquire/prepare → execute with skill and risk → react to guards, players and police → extract/surrender/fail → sell, secure or lose goods → invest in vehicles, property and abilities → encounter new opportunities and consequences.**

Every major feature must strengthen at least one link, create a meaningful player choice, or improve trust, legibility and feel. Features that do not pass this test are postponed.

### 1.3 The quality bar
AAA *discipline* here means vertical-slice proof, consistent craft direction, specialist signoff, repeatable asset pipelines, actual-device profiling, automated and hands-on testing, secure state handling, honest release gates and live operational readiness. It does **not** mean a giant team, cinematic budget, hundreds of systems or unconstrained world size. Start with a small city block that feels finished, then reproduce that standard.

Experience pillars, in priority order:
1. **P0: Instant comprehension and satisfying movement.** Readable objective, polished third-person input, camera, collision, animation and interaction.
2. **P0: Accessible first reward and fair high stakes.** A first paid task without unfair spawn-camping; damage, money, loss and arrest outcomes explainable.
3. **P0: Trustworthy systems.** Deterministic economy and server authority before public multiplayer, validated inventories and saves, no silent lost transactions.
4. **P1: Emergent role-based stories.** Heists with stealth/loud paths, civilian/logistics alternatives, police response, solo and co-op.
5. **P1: Expressive ownership and re-entry.** Vehicles, bases, factions and layered progression; cycles that respect new and occasional players.
6. **P2: Optional replay, social contracts and events.** Only if moderation, privacy, operating cost and core retention justify expansion.

**Kill criteria:** Do not greenlight a complex extension when the representative end-to-end loop has recurring crashes, broken economy invariants, unfair loss, confusing controls, poor performance or no demonstrated player enjoyment.

## 2. Player promises and user journeys

### 2.1 First five minutes: measurable design hypothesis, not a fabricated fact
1. **Spawn safely:** visible orientation, one objective, controllable player in an intelligible environment; no surprise lethal encounter while learning controls.
2. **Choose:** a safe cargo delivery or small-risk stealth theft; legal path is a full alternative, not a decorative tutorial.
3. **Act:** responsive third-person walking, driving/interacting where appropriate, clear feedback, no confusing modal chains.
4. **Receive consequence:** earned payout or comprehensible failure; currency source and secured/at-risk status shown.
5. **Preview agency:** a next lawful, criminal or co-op goal and an optional guided route; all tutorials revisitable/skippable.

**Validation:** blinded first-time users without developer coaching; collect first-input time, time to first earned/secured payout, stuck locations, abandon reasons, route completion, satisfaction and accessibility observations. **Five-minute payout is a testable target** to revise from sessions, not a verified design rule.

### 2.2 Session types
- **5–15 min:** secure quick job, purchase/sell, recover from loss, modify gear, small robbery, police patrol.
- **15–45 min:** planned heist, longer freight run, pursuit, property work order, faction skirmish.
- **Long sessions:** compound operations, coordinated settlement defense, strategy and community stories.
- **Solo:** every required economy phase has solo-viable options and recovery after failure.
- **Crew:** teamwork saves time or opens strategy, not a hard paywall on meaningful progression.

These are initial design ranges to playtest, not promised production analytics.

### 2.3 Representative end-to-end acceptance scenario
A brand-new player enters the town, understands the UI, accepts a small cargo job, loads a vehicle, drives through readable roads, earns a server/accounted payout, banks it, explores a criminal job, scouts and steals, triggers plausible alarm/AI escalation, escapes or is arrested, understands the value lost or kept, returns safely and can buy one meaningful upgrade. No developer intervention, unstated debug commands, missing content or fake transaction success. Then repeat in a co-op server with hostile and friendly players, disconnects and rejoin.

## 3. Production method: disciplined, staged and evidence-driven

### 3.1 Studio-scale production practices adapted to this project
Use professional **discovery/preproduction → prototype → representative vertical slice → production → alpha → beta → gold/release → operations**. Ubisoft's published methodology distinguishes production, alpha (all experience paths present), beta (polished game for balancing/bug fixing), master and operations; adapt these as **proof points**, not elapsed dates. [Primary reference](https://www.ubisoft.com/en-us/company/how-we-make-games/creative-process).

- **Preproduction:** pillar definitions, player journeys, technical risk register, authority design, art/audio guide, one-page feature briefs, resource and quality budget.
- **Prototype:** test that movement, a risky heist, police interaction and currency consequences are fun. Disposable greybox is allowed; gameplay code and data contracts tested.
- **Vertical slice:** one small geographically coherent location, *fully finished* from art/audio/UI/input/gameplay/AI/performance/QA through playable Windows binary. This is the model for scaling every content unit.
- **Production:** manufacture remaining content via approved reusable archetypes and verified build pipeline; prioritize breadth only after slice quality.
- **Alpha:** all promised launch features and player journeys accessible end-to-end with representative content, even if rough. Full game playable; nothing critical exists only in a design document.
- **Content lock:** every planned launch asset/mission/system enumerated and integrated; new scope only for a blocking defect.
- **Beta:** no blocker regressions, sustained real-player testing, balancing, optimization, accessibility and localization checks; default focus on repair, not features.
- **Release candidate:** reproducible signed/releasable build with rollback, servers, dashboards, incident process and support tested. Release only after exit checks.
- **Operations:** disciplined hotfixes, telemetry-informed live tuning and player support.

### 3.2 Cadence and decisions
- Weekly small **playable build** from integration; nightly automated tests for relevant supported platforms; scope-specific performance captures at milestones.
- Short written feature brief before work: player problem, in/out scope, state diagram, UX, art/audio needs, authority boundary, asset cost, test cases, metrics, risks, exit criteria.
- One narrow Issue/PR per independently verified change; no duplicate epics disguised as deliverable PRs.
- Daily triage of blockers and red CI; weekly scenario playtest and burn-down review; milestone **Go / Repair / Cut** decision.
- Every proposal enters **backlog → specified → implemented → CI verified → integrated → playable verified → accepted**. The last states are distinct.
- Reserve explicit capacity for fixes, rework, technical debt, QA and optimization; never plan at 100% feature throughput.
- Decision records contain: choice, alternatives, measured reasons, date, owner and reversal trigger. Approval of one gate does not imply approval of future scope.

## 4. Waterfall gates and playable milestones

| Gate | Exit deliverable and required evidence | Blocking conditions |
| --- | --- | --- |
| **W0 / Product brief** | This charter, game pillars, user journeys, original-IP policy, scope tiers, ownership, KPIs and major-risk list accepted | Unknown target audience, no solo role, unresolved rights assumptions |
| **W1 / E1 extraction disposition** | 330/330 original bundle paths accounted for; every remaining source disposition logged; exact SHA provenance and capped/unparsed inventory; authoritative vs client/proposed field classification | Missing sources miscounted as success; pointer counted as original file; unknown numerics called authentic |
| **W2 / Design contract** | Data schemas, state transitions, economy proofs, threat model, networking authority, scene/world topology, cinematic/visual/audio bible, playtest plan, build/test matrix; reviewed test vectors | No money conservation, unclear irreversible loss, undefined authority, circular gameplay |
| **W3 / Solo first playable** | Complete playable offline slice with movement, heist/guards/alarm/loot/escape, payout/bank and alternate safe path; repeatable tests, Unity Editor/Play Mode and Windows build evidence | UI-only demo, mocks presented as live, can only play with developer guidance, missing build |
| **W3 / Representative polished vertical slice** | One contiguous district at near-shipping fidelity with one legal job, heist (two approaches), police outcome, working car/AI/HUD/audio, save/restart and accessible controls, frame captures | Core feel/polish fails player test, pipeline can't reproduce district, frame hitching is unmeasured |
| **W4 / Multiplayer proof** | Dedicated authoritative session; 2+ clients plus bots/test actors; reconnect, economy atomicity, secure input validation, movement/interaction, combat/cargo/state synchronization under simulated network faults | Client can mint currency, dupe, forge hits, own arbitrary state; disconnect loses money |
| **W5 / Alpha + content completion** | Launch-scope game paths, NPC archetypes, world and mission catalog, home/bases/progression/wipe simulator, menus, audio and content pass complete | Placeholder content promised as final, unreachable systems, missing player roles |
| **W6 / Social/live acceptance** | Only accepted optional party, crew, moderation, consent capture, bounded events and safe communications; moderation/ops workload demonstrated | Consent default-on, unmoderated public creator tools, features that undermine solo or economy |
| **W7 / Beta and release candidate** | All required checks and actual Unity/Windows tests; measured hardware/perf/network/load/security; accessibility, privacy, localization, QA, telemetry, server drills, store approval and release bundle | Zero/missing/skipped/red checks, P0/P1 crashes/exploits, failed save recovery, untested executable |
| **W8 / Live operation** | Observability, incident response, hotfix+rollback, config governance, analytics and ethical iteration; credible player-facing communication | Unsafe balance pushes, no incident owner, no recovery from corrupted or abandoned games |

**Non-negotiable sequencing:** Documentation and isolated reusable tests may be written early, but W2 authoritative contract must precede a production W4 backend; W3 prove-the-fun before content expansion; W7 real executable verification is not replaced by Python CI. *No gate claims a timeframe or an implementation completion merely because the document exists.*

## 5. Complete launch-system inventory (traceable to Issues)

Use the table as an acceptance catalog. Each row needs a design brief, owner, versioned config, tests, player scenario, performance and accessibility checks. **All are planned unless explicitly supported by executable test evidence.**

| Domain | Required player-facing scope / finish test | Earliest owner gate |
| --- | --- | --- |
| **Player and camera** | Walk, sprint, crouch, jump, contextual traversal; predictable acceleration/stop, camera collision and obstruction recovery, aiming, remappable controls, gamepad; validate tight interiors/vehicles | W2 contracts, W3 |
| **Interaction and inventory** | Look/focus prompts, doors, pickups, containers, carry/drop, equipment/stash/storage, weight and item states; no double-interact duplication | W3, authoritative W4 |
| **Combat and injury** | Readable recoil/ammo/reload, health/armor/hit reaction, death/down/surrender, clear reason for loss; ballistic/hit rules are PROPOSED until proven; server validation later | W3, W4 |
| **Crime/heists** | Scout, approach, security, entry, alarms, guards, objectives, extraction, failure, earned loot; one heist allows quiet and loud viable paths | W3, W5 |
| **Police/legal** | Civilian safety, alert/heat, escalating response, pursuit, arrest/jail/release, police player jobs, confiscation, warrants and anti-grief constraints | W3, W4 |
| **AI** | Pedestrian/guard/police behavior state machines, sight/hearing, patrol, alert propagation, navigation, search, chase and fallback for blocked paths; debug overlays and deterministic seeds | W3, W5 |
| **Vehicles/logistics** | Enter/exit, driving/handling/camera, vehicle durability, storage, pickups/deliveries, road hazards, recovery and cargo accounting | W3, W4, W5 |
| **Economy** | Loot origin, fence, dirty/clean cash, laundering, ATM/bank, transactions, shops, prices, taxes, sink/faucet tracking; no mint-on-retry | W2 invariants, W3, W4 |
| **Property/building** | Rent/own plot, snap/rotate/preview, permissions, crafting/storage, production timers, raids, durable updates and collision validity | W3, W4, W5 |
| **Factions/territory** | Settlement/district ownership, tax/treasury, contest/defense, clan roles/permissions and anti-monopoly/new-player recovery | W3, W4, W6 |
| **Persistence/progression** | Reliable saves, account/player identity, inventory history, skill/gear choices, migration, seasonal power-reset vs durable legacy; opt-out of forced grind | W2, W4 |
| **World/level design** | Original walkable city district, roads, interiors, desert/prison/settlement as budgeted, readable landmarks, points of interest, nav/physics/traffic and streaming | W3, W5 |
| **UI/UX** | Title, onboarding, HUD, map, task log, inventory, trade/confirmation, social, settings, loading, errors, death/reconnect, accessible focus/navigation | W3–W7 |
| **Social/co-op** | Join/invite, explicit party roles, non-voice pings, reporting/block/mute, safe trade, moderation; never gate core career on party membership | W4, W6 |
| **Audio/feel** | Footsteps/foley, weapons, engine, music direction, world ambience, spatial cues, mix priorities and visual/haptic alternatives | W3, W5 |
| **Replay/community** | Optional user-reviewed highlight/replay and templated community contracts, only after privacy and moderation proof | W6, optional |
| **Operations** | Telemetry, logs, incident process, admin tools, rollout/rollback and support response; no debug admin commands exposed to players | W4–W8 |

### 5.1 Action/reaction chains: quality definition
For every pivotal action require **intent → anticipation → execution → physical/visual/audio response → world consequence → recoverable next action**. Examples:
- Open door: reachable prompt, animation, collision/nav update, latch sound, alert propagation, remembered state.
- Fire weapon: intentional input, visible muzzle event, synchronized reload/ammo, traceable impact, reaction, clear damage feedback and server verdict.
- Steal item: physically readable transfer, inventory authoritative mutation, alarm/heat possibility, clear sale value and correct state after disconnect.
- Drive: distinct vehicle inertia, enter/exit, collision/audio feedback, responsive camera, believable damage and cargo consequences.
- Arrest: fair cause and reasonable warning, transition effects, inventory confiscation journal and clear recovery route.
UI notification alone is insufficient proof of gameplay completion.

### 5.2 Rules, roles and replay value
- Player roles: civilian (legal freight/commercial), thief (stealth/high risk), police (response/containment), builder/trader (base/economy), crew/faction member (optional collective play).
- Conflict should be **earned and legible**, with reversible recovery, safe onboarding, event logs and sensible penalties for targeting helpless users.
- Economy needs understandable **risk–reward–time** decisions; no endless exploit-farming, unavoidable zero-sum progression or arbitrary loss without explanation.
- Wipe/cycle duration is a **design experiment**, not fixed to the reference game's seven-day example; preserve user identity, settings and non-power records when a cycle ends. Test late joiners and casual players explicitly.
- Win states are multiple: earn and secure wealth, successful crime, just policing, grow property, win a territory event, achieve solo career milestones; don't reduce enjoyment to grind rank.

## 6. Core data, simulation and network architecture

### 6.1 Foundational technical choices
- Keep the proven project basis: **Unity 6000.3.18f1 evidence/build reference, C#/.NET gameplay logic**. Verify the actual target editor environment, render pipeline and packages before committing to a new networking/rendering stack.
- One **pure rule/domain** implementation for item IDs, transactions, contracts, timers and state transitions; Unity scene components adapt input, animation, physics and presentation. Avoid dual client/server business rules.
- Use well-named feature modules (Player, Interaction, Inventory, Economy, Crime, Police, Vehicle, Property, World, Social) with tests and narrow dependencies. Shared abstractions only where a real boundary exists.
- ScriptableObjects or versioned serializable data define tuning; domain rules validate inputs. Keep one stable schema/ID registry and migration tests; do not scatter values in prefabs.
- Treat the simulation clock, random seed, unit conventions, currency arithmetic and authority rules as explicit contracts. Money represented in integer minor units with checked bounds. Avoid float-based financial balances.
- Stable content IDs; separate user-facing localization keys from gameplay identifiers; save format version and forward/backward migration policy from W2.
- Source evidence tags **OFFICIAL / BUILD / EXTRACTED / OBSERVED / PROPOSED** on every externally copied or calibrated mechanic. The plan is not authorization to copy game media.

### 6.2 Entity and event boundaries
Define structured events for job accepted/completed, item created/consumed/transferred, inventory snapshot, loot picked, police response, currency debited/credited, property built/removed, faction permission changed, player arrested/released and cycle reset. Each has unique ID, actor, context, server time, validated preconditions, result and reconciliation tests.

**Transaction invariant:** a credited currency/item unit has a traceable authorized source; transfers net to zero except an explicit named faucet/sink; retried requests produce exactly one business effect. Prevent inconsistent states across account, bag, safe, car, bank, trade and settlement.

**Save invariant:** crash or disconnect cannot restore spent goods or erase a successful debit without compensating audit record. Provide repair/reconcile tooling, backup/restore test and versioned migrations before live exposure.

### 6.3 Authoritative multiplayer
Only after W2/W3:
1. Choose network transport/library from a proof-of-concept matrix: server hosting and operating cost, tick stability, client prediction support, spatial interest management, ecosystem/LTS, licensing, tooling and reproducible CI.
2. **Server owns** currency, items, damage, ownership, crafting timers, vehicle cargo, faction permissions, arrest, spawn, mission rewards and economic side effects.
3. Client sends bounded **intents**, never unsigned ledger or arbitrary world mutations. Validate identity, distance, rate, item ownership, sequence IDs, chronology and collision plausibility.
4. Use prediction/interpolation for feel with **server reconciliation** and lag-compensation policy for validated interactions/combat; define accepted RTT/jitter/loss tests before tuning.
5. Reconnect uses session identity, replay-safe state resume and explicit temporary ownership/disconnect policies; crashes do not create free duplicate claims.
6. World/entity replication uses relevance/interest filtering, prioritization and low-cost delta updates only when tests show need. A distributed multi-region architecture is **not** day-one default.
7. Hostile tests cover forged amounts/hits, rapid duplicate RPCs, race conditions, reordering, packet loss, simultaneous trades, stale sessions, abuse of physics, movement speed and destructive resource claims.
8. Maintain minimum admin audit controls and security monitoring that do not expose players' private communication by default.

**Concurrency and rates are hypotheses:** determine authoritative tick, active players/server, interpolation buffer, lag tolerance, geographic regions and hosting size from realistic vertical-slice load runs, not copied market figures.

### 6.4 Layered project structure / runtime
- **Client presentation:** input, third-person camera, effects, UI, audio, streaming, prediction and accessibility.
- **Shared domain:** explicit data contracts, deterministic economic rules, state transitions, authorization-independent validation.
- **Server:** account/session checks, authoritative simulation and transactions, permissions, persistence, anti-abuse checks and instrumentation.
- **Content:** versioned IDs/configs, addressable/scene catalog, localization, asset validation and authored scenario definitions.
- **Tools/QA:** test harnesses, bots, profiling scenes, seedable economy simulation, Unity smoke/Play Mode/Windows build and release packaging.

No service mesh, feature-store, microservice fleet, bespoke engine, generalized visual scripting system or full UGC runtime without a demonstrated need. Apply DRY, KISS, YAGNI and SOLID pragmatically; small readable tests and explicit transitions over speculative frameworks.

## 7. Art direction, world building and the content factory

### 7.1 Visual identity and world bible (approve before bulk production)
Establish a unique named world and **one-page** art bible: silhouette language, color/value palette, realism/stylization ratio, scale, architecture/material family, character shape, camera/FOV, UI typography, VFX, lighting and weather. The player must distinguish civilians, guards, police, loot, objectives and vehicle classes at playing distance. Aim for a consistent, ownable style rather than a legally risky near-clone.

**World-blockout order:** city street block + one heist interior + legal cargo point + police/pursuit route + storage/bank → representative complete district → adjacent district via modular kit → remote biome/settlement only if production budget and streaming tests allow. Density of decisions beats empty map kilometers.

### 7.2 Content production pipeline (one asset from concept to shipped)
**Brief → reference/rights check → concept/silhouette → greybox gameplay metric → model/rig/animation → materials/textures → physics/collision/nav/LOD → lighting/VFX/audio hooks → prefab/IDs/addressable bundle → automated validation → scene integration → CPU/GPU/memory profile → player playtest → signoff.**

Every item has an owner, naming convention, scale/unit, pivot, collision layer, LOD policy, texture and material budget, atlas/reuse policy, animation states, VFX/audio hooks, memory/performance class, authoring license, source file and target prefab/scene. Store source DCC files in the approved large-asset repository workflow, not unmanaged git blobs.

**Representative content dossiers:**
- **Character:** functional skeleton; player, police, guard and civilian silhouettes; coherent locomotion, turns, interaction, enter/exit, combat, hit, surrender and death. Include facial/emote system only where camera proximity demonstrates value.
- **Weapon:** distinct aim/readability, recoil feel, muzzle/smoke/impact audio, first/third-person coherency, ammo/reload, collision/effects scalability, server hit confirmation.
- **Vehicle:** model, wheels/seat/camera positions, audio banks, physics parameters, cargo volume, damage and occlusion/culling behavior.
- **Building/heist:** approach routes, visibility, AI graph/nav, doors, cameras/alarms/safes, exit strategies, stealth/noise, art kit, streaming bounds and objective markers.
- **Property:** snap grid/constraints, cost/weight, recipe, ownership and permission UI, visual construction stages, authoritative storage and demolition recovery.
- **Mission:** one-page brief, required roles, legal/illegal path, trigger/precondition table, objectives, alternative completion/failure, rewards, telemetry and replayable seed variation.

### 7.3 Production leverage without generic content
- Build reusable road/interior/prop kits, cover spaces, placement validators, mission archetypes and sound variations, but retain hand-authored landmark moments.
- Local design iterations start in blockout, not high-fidelity art. Lock traversal and metrics before final mesh/lighting; preserve navigation/line-of-sight tests when dressing.
- Use quality tiers and content taxonomy; content expansion only when creation-to-accepted time, defect rate and performance cost can be forecast.
- Do not use placeholder/copyright-protected reference assets in public builds. Maintain a release-asset provenance register and open-source license audit.

## 8. Animation, audio, lighting and tactile polish

A polished sandbox needs **coherent cause and effect**:
- **Animation:** locomotion blends, acceleration/braking, smooth camera-relative turning, grounded foot planting, interaction alignment, weapon reload, entering vehicles, reaction/knockback and interruptions; stable transitions when network corrections occur.
- **Audio:** authored transient/loop layers for movement, clothing, vehicles, weapons, loot, doors, alarms, police, interiors/weather and key UI actions. Mix with ducking and priority; audio conveys distance, line-of-sight and danger without relying only on audio.
- **VFX:** readable impact type, alarm state, hit effects, environmental dust/weather; protect players from visibility-obscuring excess and photosensitivity.
- **Lighting:** consistent material response, indoor/outdoor transitions, narrative focal points and readable enemy/loot silhouettes; time-of-day/weather only if gameplay and performance validate them.
- **Camera:** collision, wall occlusion, cinematic but user-controllable framing, adjustable shake/FOV/sensitivity, invert settings, aiming and vehicle rigs.
- **Haptics/feedback:** optional, configurable and never the only communication channel.
- **Polish capture:** short gameplay clip, input-to-feedback measurement, frame-time capture, audio mix review and accessibility pass for every signature interaction.

## 9. UX, accessibility, localization and trust

**Minimum complete UI journeys:** launch → settings → enter game → understand tasks/map → accept job → use items → receive consequences → purchase/trade confirm → reconnect/fail → report/block/help → safely quit/reopen. No hidden critical information, dead-end screen or silent failed action.

Accessibility from W2 rather than end-of-project remediation:
- Full remapping, controller navigation/focus, keyboard-only alternatives, UI scale, readable typography/contrast, reduced motion/shake, subtitles/captions/speaker cues and non-color-only indicators.
- Alternative visual/audio/haptic cues, aim/input options as appropriate for fairness, time-to-act considerations, tutorials revisit/skip, readable map/routes, consistent errors and confirmation.
- Online social UI accessibility: mute/block/report and settings must be navigable without requiring voice.
- Record audit by selected Xbox Accessibility Guidelines topics; the XAGs are industry best practices, not an automatic certification claim. [Microsoft XAG](https://learn.microsoft.com/en-us/xbox/accessibility/guidelines).
- Localize data, UI and dynamic currency/date presentation from the start; initial language scope is a production decision, not an automatic commitment to all languages. Verify truncation, fonts, culturally safe content, subtitles and narration availability.

**Respectful systems:** privacy-safe opt-in analytics, no mandatory social posting, transparent cash loss, clear live-service resets, no abusive chat defaults, moderation review and appeal, accessible support route and deletion/data-retention policy.

## 10. Performance and hardware acceptance

The release hardware matrix is **not yet measured**. Establish target CPU/GPU/RAM/SSD combinations in W2 after surveying realistic PC players; label every proposed performance number as an *initial engineering hypothesis* until reproducible captures exist.

| Proposed acceptance target | How to verify / where it can change |
| --- | --- |
| **60 FPS target on selected recommended Windows hardware** during regular city gameplay | Player build with profiler markers and scene/stress cases; frame-time distribution p50/p95/p99, not editor FPS |
| **Frame pacing and responsiveness** in heist/crowd/vehicle/lighting heavy scenes | Record camera/input-to-response, CPU main thread/render thread/GPU, GC allocations and stutters |
| **Playable minimum-spec baseline** | Choose a documented lower hardware profile from measurements; publish actual settings and stable behavior, not a guessed spec |
| **Server tick, region load, latency and packet loss budgets** | Synthetic clients plus real machines; repeated load/soak, peak heist/crowd, reconnect and combat correction |
| **Memory, load times, streaming stalls and asset size** | Cold/warm Windows build, iterative streaming traversal, memory leak/fragmentation tracking, disk and network profiles |
| **Build determinism and stability** | Archived hashes, symbols, crash IDs, known asset manifest, reproducible smoke, rollback package |

Optimization workflow: reproduce → profile CPU/GPU/memory/audio/network → identify dominant cost → make smallest high-confidence fix → rerun representative scene and regression cases. Do not blindly add Jobs/Burst/DOTS, occlusion or async systems without measured need. Reuse LOD, streaming, culling, shader variants, batching and sensible scene segmentation when real profiles justify them.

Primary engine references: [Unity Profiler 6000.3](https://docs.unity.com/en-us/engine/6000.3/manual/analysis/profiler/introduction), [Unity rendering/profile](https://docs.unity.com/en-us/engine/6000.3/manual/analysis/graphics-performance-profiling), [Unity measure before optimizing](https://docs.unity.com/en-us/engine/6000.3/manual/analysis/graphics-performance-profiling/optimizing-graphics-performance).

## 11. QA, testing strategy and acceptance evidence

### 11.1 Testing pyramid
- **Unit/domain:** inventory, prices, item invariants, credits/debits, jobs, statuses, cooldowns, state machine transition permutations, random seed replay, save migrations; fast headless .NET CI.
- **Contract/schema:** serialization, item/mission IDs, config limits, client/server protocol compatibility, source provenance and reconciliation invariants.
- **Unity Edit Mode:** editor import, script compilation, prefab/scene dependencies, object setup, asset checks, basic nav/physics/collision and pipeline validation.
- **Unity Play Mode:** movement/camera, target prompts, collisions, heist/guards/alerts, loot/Bank UI flow, entry/exit and scene change; actual test runner evidence.
- **Windows EXE smoke:** clean machine launch, initial menu, load level, input, playable loop, save/restart, exit and crash dumps. No editor-only green substitutes.
- **Multiplayer integration:** bots and multiple clients, headless server, lag/loss/jitter, reconnect, concurrent trades, disputes, ownership checks, denial-of-service bounds, migrations, soak and shutdown recovery.
- **Manual/UX:** blind onboarding, feel review, accessibility checks, audio/visual craft, localization/culture, edge-case exploratory play and abusive player scenarios.
- **Release:** clean-install build hash, platform and license audit, security, save restore, server upgrade/rollback and store listing consistency.

### 11.2 Severity taxonomy
- **P0 blocker:** money/item duplication, security/privacy breach, save corruption, widespread crash, unlaunchable build, unavailable core progress.
- **P1 critical:** unfair unavoidable loss, major disconnect exploit, repeatable unplayable story path, broken camera/input, major performance failure or inaccessible required UI.
- **P2:** noticeable but recoverable content/polish defect with reproducible workaround.
- **P3:** minor cosmetic or enhancement only.
At beta/gold, P0/P1 = **zero open**; any accepted P2 needs owner, documented impact, ship decision and postrelease target. Never hide severity by relabeling to unblock CI.

### 11.3 Evidence contract
A milestone evidence packet contains exact commit SHA, dependency versions, test list/number executed, nonempty check statuses, CI URLs, real OS/Unity/build identifiers, reproducible scenario steps, performance files and defect reports. **Missing, skipped, canceled, red, queued or zero required checks cannot be interpreted as passed.** A passed synthetic test does not say that Unity Player/Editor tests ran.

## 12. Security, privacy, economy integrity and moderation

- Threat model human cheats, injected inputs, movement spoofing, inventory/credit forgery, duplicates, stolen accounts, compromised sessions, toxic interaction, griefing, DDoS/abuse and operator error.
- **Server authoritative** and idempotent ledger operations; immutable transaction IDs, anti-replay, bounded rate, trusted server clock, safe concurrent writes, immutable balances or guarded updates, audit/rollback and sandbox exploit harnesses.
- All player/admin actions authorized and logged with proportional privacy; privileges least-permission, credential rotation, no secrets in repo/CI logs, audited server config changes and emergency remote suspend.
- Avoid exposing player IP, chat/private voice or detailed account identifiers through optional replay/social tools. Clip and telemetry consent is granular and revocable, with reasonable retention.
- Moderation: in-game mute/block/report, fair investigation, repeat-abuse handling, escalation, appeals, community guidance, and staffing/cost budget before public social features.
- No remote arbitrary-code player contracts or unmoderated asset uploads in V1. Event payouts from typed approved templates with caps, not client-authorized scripts.

## 13. Analytics, user research and business validation

Every metric needs definition, cohort, unit, event taxonomy, consent basis and owner. Use anonymized aggregate analytics by default and honor privacy opt-outs.

**Core experience:** time to control, first meaningful choice, first secured payout, completed jobs, recoverable fail states, solo vs crew objective completion, invalid input, user-rated clarity/fun and drop-offs.

**Fairness/economy:** wealth generation and sinks, loss cause, gear disparity, unfair-death reports, arrest fairness, median recovery after wipe, newcomer earnings, exploit/rollback incidence and settlement concentration.

**Quality/operations:** crash-free sessions, launch success, load/framerate distribution by hardware tier, sync errors, RTT/loss, unauthorized mutations, server cost per concurrent/active user, moderation queue and support resolution.

**Retention/acquisition:** D1/D7 return for well-defined cohorts (not equivalent to sales or DAU), player referral joins and optional shared clips; no claim of causal feature success from another title's Steam peak or total copies.

Use **structured playtests** at milestone exits: hypothesis → instrument → recruit representative solo/co-op/novice/accessibility users → observer notes + anonymous metrics → severity/impact review → fix/cut/accept decision. Pair quantitative measures with interviews and recorded behavior; do not optimize only for apparent retention or vanity metrics.

## 14. People, ownership, capacity and production control

The team size is **not established**. Map roles even if one person owns several; do not invent personnel or payroll.

| Function / accountable owner | Deliverables and decision right |
| --- | --- |
| **Game director / product owner** | Pillars, launch scope, player promise, budget and milestone Go/No-Go |
| **Producer / technical PM** | Risks/dependencies, capacity, scope cuts, Issue/PR cadence, cross-discipline evidence and release checklist |
| **Technical director** | Architecture, Unity version/packages, profiling, determinism, security and CI; approves risky changes |
| **Gameplay/AI/physics engineers** | Player feel, heists, police, vehicles, inventory, rule tests and systemic debugging |
| **Backend/network/security engineers** | Authority, persistence, sessions, rate limits, simulations, deployment, runbooks |
| **Design/level/economy** | Play loops, missions, district blockouts, pacing, balance data, exploit models and test vectors |
| **Art/technical art/animation/VFX** | Style guide, production-ready asset kits, import validation, optimization and feedback quality |
| **Audio composer/sound designer** | Unique sound identity, spatial/mix/cue implementation and loudness/accessibility coverage |
| **UI/UX/accessibility** | Journeys, interface, input/navigation, localization and usability tests |
| **QA/release/ops/community** | Automated and manual verification, defects, release acceptance, incident/feedback/moderation readiness |

**Staffing principle:** one accountable owner per deliverable, even when responsibilities are combined; do not schedule full-time specialists that do not exist. Estimate feature effort from a completed vertical slice and real content throughput, not optimistic AAA comparisons.

**Budget principle:** track burn and committed runway; measure person-days, art throughput and server spend after prototypes. Each feature has implementation + asset + integration + regression + localization + moderation + maintenance cost. If unsustainable, cut the feature before quality or safety.

### 14.1 Definition of Ready / Done
**Ready:** small scope, user outcome, source tag, data/state contract, dependencies, design constraints, test scenarios, assets and ownership clear; no avoidable open decision.

**Code Done:** focused branch, tests and static validation, reviewed diffs, no introduced secrets, traceable instrumentation, config/migration review, security/performance impacts declared, docs and regression tests updated, all current-head nonempty CI green.

**Feature Done:** Code Done **plus** a real integrated player scenario with actual Unity/EXE evidence, user comprehension, art/audio/camera polish, performance class, no P0/P1 defects, accessibility and telemetry review. *Tests passing in GitHub is not equal to Feature Done.*

**Milestone Done:** every required feature done, measured quality packet, approved exceptions, explicit Go/No-Go decision. No implied success from branch labels, plans or placeholders.

## 15. Release management and Steam production

### 15.1 Platform readiness
Prepare original name/branding, trademark review, public screenshots of actual gameplay, authentic trailer, rated content disclosure, hardware specs based on testing, support/legal/privacy documents, store metadata and truthful feature list. No concept art presented as playable screenshots.

**Store page:** Steamworks Coming Soon requires listing/review preparation, and the public page must be live at least two weeks before release; check the latest official eligibility requirements before scheduling. [Steamworks Coming Soon](https://partner.steamgames.com/doc/store/coming_soon).

**Playtest:** use controlled private keys or Steam Playtest *before* any paid public release; gather behavioral, networking, operational and onboarding evidence, not just hype. [Steamworks Playtest](https://partner.steamgames.com/doc/features/playtest).

**Early Access:** only if current build is *already enjoyable and worth its price*, with stated present limitations, a credible support cadence and no reliance on hypothetical future purchases to finish development. Never use Early Access as a funding substitute for an unplayable tech demo. [Steamworks Early Access](https://partner.steamgames.com/doc/store/earlyaccess).

**Release:** Steam store presence and build review/approval; app setup, platform compatibility, launch checks and explicit release controls. Allow review lead time, verify actual Valve status; no date promise before approval. [Steamworks Release Process](https://partner.steamgames.com/doc/store/releasing), [Review Process](https://partner.steamgames.com/doc/store/review_process).

### 15.2 Gold checklist
- Stable exact release commit/build ID, clean signed/offline test build, original-asset rights list, all promised content reachable.
- No open P0/P1; real Unity import, tests, Windows EXE and online scenario pass on documented machines.
- Economy and account recovery/backup restored in disaster drill; region/server budget, scaling and admin permissions validated.
- Performance and crash-free targets met on published minimum/recommended hardware; accessibility and input matrix tested.
- Store page accurately lists only shipped features; support portal, moderation incident owners, privacy and patch notes ready.
- Explicit human acceptance required for financial spend, legal/licensing, final art direction, Windows playtest and public launch.

### 15.3 Live operations (W8)
- Canary deployment → health monitoring → staged rollout → rollback criteria; reversible economy config changes with versioned audit.
- Hotfix triage priority: security/corruption, crash/blockers, unfair gameplay, balance, polish. Publish incident status and corrections.
- Scheduled content only when actual active population and operations capacity justify it. No automatic week-long wipe mandate.
- Capture behavioral feedback without surveillance, stop harmful mechanics and publish material changes in player language.

## 16. Milestone-sized backlog and dependency map

The following are **planning packages**, not new GitHub Issues to create en masse. Break each approved package into independent Issues at implementation time and check for existing work first.

| Order | Deliverable package | Dependency and required handoff |
| --- | --- | --- |
| **Now: W1-AI #89 / PR #92** | Verify original sector-center and common sources, all current-head checks and postmerge; close #89 and update #32 | Existing active source work, independent of this documentation issue |
| **W1-AJ+** | Account for remaining six proposed original LFS paths after #92; classify numeric caps and separate Wwise unparsed; capture permanent source-disposition E1 report | Exact latest dev ledger, source pointer availability/rights |
| **W2-A** | Full economy/inventory/auth authority specification, data schema, deterministic test vectors, migration/threat model | W1 status explicitly accepted as complete or blocked with documented unknowns |
| **W2-B** | Player feel, first-five-minute UX, heist/AI/police/vehicle scenario briefs; original world and art/audio/UX direction | W2-A boundaries and resource capacity |
| **W3-A** | Upgrade existing #9 vertical slice: stable player/camera/interaction, legal delivery + heist + AI/alert + money/loss cycle; real Unity+Windows evidence | W2 specs, asset kits, performance baseline |
| **W3-B** | Polished representative district and repeatable production-quality content pipeline | W3-A actual feel/player acceptance, not UI mocks |
| **W3-C/D** | Offline systemic completeness for vehicles, police, property, production, faction/wipe and full player journeys with headless invariants | W3-A/B, economy rules and scope budgeting |
| **W4-A** | Dedicated server, authoritative accounts/inventory/economy, persistence, reconnect, secure protocols | W2 threat/economy model and verified W3 loop |
| **W4-B** | Real multi-client simulation, prediction/lag, PvP/AI validation, exploit load and server soak | W4-A, measurable network/hardware envelope |
| **W5-A/B** | Accepted world expansion, distinct content archetypes and full launch mission/progression matrix; alpha and content lock | W3 slice quality and W4 authority budget |
| **W6-A/B** | Optional party/crew/territory events, privacy-safe highlights and bounded templates only where core proof supports them | Multiplayer safety, moderation capacity and measured usefulness |
| **W7-A/B** | Unity/Windows full QA, perf, accessibility/localization, security/ops, Steam test, beta → RC → human gold decision | Content complete, actual CI and manual test proof |
| **W8** | Supported release, monitored hotfixes and responsibly scoped new content | Gold decision, sustainable live operations |

The **critical path** is: finish source disposition → validate domain/authority design → make one superb solo slice → prove it in real Unity/Windows → validate server trust → manufacture a complete compact world → harden/release. A giant social backend, open-world map or cosmetic catalog does not outrank this path.

## 17. Risk register and explicit stop/go rules

| Risk | Early signal | Mitigation / stop condition |
| --- | --- | --- |
| Evidence mistaken for source authority | Claim of real formula from serialized client field | Keep source tags, block promotion without observation/source proof; externalize proposed tuning |
| Rights/IP infringement | Non-owned model/audio/logo/scene in release pipeline | Asset provenance approval, replace with original work, no media export by default |
| Scope explosion | Many unfinished systems, no polished representative slice | Freeze a single complete district/loop, cut or defer P2 and nonessential breadth |
| Unfair PvP/economy exploits | Unexplained losses, dupe/rollback test failure, spawn grief | Halt online launch, authoritative transaction/anti-abuse repairs and loss attribution |
| Unity reality gap | CI green but Editor/EXE never run | Do not mark playable/release gates passed until real executable tests exist |
| Performance collapse | Dramatic frame-time spikes with content density/network actors | Profiling budgets, modular asset cost, cap concurrency and reduce world scope |
| Persistent-state corruption | Reconnect duplicates/spends wrong, migration fails | Idempotency and ledger tests, snapshot restores, staged rollouts and audit |
| Art/content debt | Assets inconsistent, costly to build and unoptimized | Approve style bible and vertical-slice production pipeline before mass output |
| Operational unsustainability | Moderation/server expenses exceed capacity | Cut high-cost social/UGC, bound worlds and events, no unstaffed live features |
| Weak first session | New users fail safe reward, dislike controls or don't understand risk | Fix onboarding and core feel before introducing more features |
| Market mismatch | Engagement guesses from competitor peaks | Independent playtests and player feedback; no invented sales/retention conversion |

## 18. End-state definition: a genuinely complete game

The project can be called **Complete** only after: a finished original content set supports all marketed launch career loops; solo and online progression work; role/heist/police/economy/vehicle/property systems interact coherently; the art/audio/UI/animation style is consistent; normal failures are safe and understandable; accounts, authority, security and economy have passed adversarial tests; supported Windows hardware meets measured performance; accessibility and localization scope is delivered; Unity Edit/Play Mode and packaged EXE tests are verified; store listing and legal/licensing pass; release/rollback/support/moderation operations are ready; all required PR/CI gates have actual nonempty green results; no blocker issues remain; an explicit release approval has been made.

**Current truth:** none of those cumulative release claims is satisfied merely by this master plan. This document creates the acceptance map; implementation issues, measurements, CI, human playtests and release evidence must close each gap.

## 19. Evidence and primary production references

These sources support **production practices/platform requirements**, not claims that their companies' quality, sales or player scale will automatically transfer to this project:

1. Ubisoft, *How We Make Games: Creative Process* — production, alpha, beta, master and operations: https://www.ubisoft.com/en-us/company/how-we-make-games/creative-process
2. Unity 6.3, *Profiler introduction* — measure CPU/GPU, memory, audio and markers using the real target: https://docs.unity.com/en-us/engine/6000.3/manual/analysis/profiler/introduction
3. Unity 6.3, *Graphics performance and profiling* — profiling, rendering work, LOD and GPU budget: https://docs.unity.com/en-us/engine/6000.3/manual/analysis/graphics-performance-profiling
4. Xbox Accessibility Guidelines — practical design/test criteria, not legal certification: https://learn.microsoft.com/en-us/xbox/accessibility/guidelines
5. Steamworks *Coming Soon*: https://partner.steamgames.com/doc/store/coming_soon
6. Steamworks *Steam Playtest*: https://partner.steamgames.com/doc/features/playtest
7. Steamworks *Early Access*: https://partner.steamgames.com/doc/store/earlyaccess
8. Steamworks *Review Process*: https://partner.steamgames.com/doc/store/review_process
9. Steamworks *Release Process*: https://partner.steamgames.com/doc/store/releasing
10. Unity *2026 Gaming Report* — survey context regarding scope and development realities (descriptive, not prescriptive): https://unity.com/resources/gaming-report
11. Repository source and current status: [Control #32](https://github.com/Nippytime/rabron/issues/32), [evidence work #89](https://github.com/Nippytime/rabron/issues/89), [source PR #92](https://github.com/Nippytime/rabron/pull/92), [prototype #9](https://github.com/Nippytime/rabron/issues/9), [source #3](https://github.com/Nippytime/rabron/issues/3), [historical waterfall](../reconstruction/docs/full-game-waterfall.md), [player-scale research](../reconstruction/docs/player-scale-design-evidence.md), [machine ledger](../reconstruction/data/extraction_coverage.json).

---

### Plan-change protocol
Any change to platform, product identity, must-ship feature, live-service economy, security/rights posture or release quality target needs an Issue, tradeoff/risk record and acceptance review. Smaller scope refinements use focused PRs. Preserve earlier fact snapshots as historical records and annotate newer verified evidence. The team can change *how* it builds the game when testing supports a better choice; it cannot redefine missing evidence as success.
