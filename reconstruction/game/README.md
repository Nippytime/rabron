# ROB RUN — standalone gameplay foundation

This is the beginning of a **new, independently authored game implementation**,
not the original proprietary Unity C# source or a restored game scene.

## What works

A pure C# 8 / .NET Standard 2.1 gameplay state machine covering this sequence:

1. Scout a city heist, then put on a mask to become a criminal.
2. Begin the heist, record loot item IDs and optional alarm state, then escape.
3. Receive **externally supplied positive item sale quotes** and sell the
   inventory at a fence. The cash appears on a *counter*, not immediately in
   the player's balance.
4. Explicitly collect the counter cash as dirty cash.
5. Start laundering with an **externally supplied conversion offer and
   deadline**. The job only completes when the supplied time has elapsed.
6. Exit the city to clear criminal status; return as a civilian to open a
   bank account and deposit cleaned cash.
7. Only **after returning to the city as a civilian**, reset the completed
   heist cycle while preserving all remaining balances. Calling the core
   reset as a criminal or while still in the desert is rejected without
   changing money, alarms, role or phase. A civilian returning from a
   completed laundering cycle **cannot mask again** while still in the
   `Laundered` phase: first explicitly reset to `Idle`, then mask before or
   after scouting. This matches the existing Unity mask station and prevents
   direct core callers from re-entering criminal status mid-reset.

The provisional guard alarm is **single-shot** per active robbery.
An uncontrolled staff member may raise the first alert; repeated alerts or
new alerts after **controlled staff** are rejected without changing state.
Controlling staff after a previously raised alarm does not erase that alarm.
The live Unity guard already applies these conditions; they are original
prototype rules, not recovered reference-game NPC mechanics.

This implements a working rules **simulation**, with no 3D camera, UI,
animation or multiplayer networking yet.

## Local demo checkpoint contract

\`HeistSession.ExportSnapshot()\` and \`HeistSession.FromSnapshot()\` transfer
the full heist phase, role, loot IDs, collectible fence cash, guard/alarm
flags, dirty/clean money, bank balance and running laundering job. Restores
validate the save version, IDs, financial amounts, phase consistency and
timer/payout integrity before using any saved values. A criminal can never
persist or start in the **desert**: leaving the city clears criminal status,
and forged desert/criminal role combinations are rejected before recovery.
Legitimate civilian and police saves in the desert still restore normally.
An **unpayable laundering job** is rejected *before* reserving dirty cash: the
pending clean payout must fit the remaining 64-bit clean wallet capacity.
Save restoration also rejects a corrupted or legacy in-progress job whose
credit would overflow that wallet, instead of accepting an unfinishable timer.
A rejected start leaves the phase, dirty balance and current savings intact.

\`Core/HeistSessionSnapshot.cs\` is a pure C# serializable data carrier.
The core never touches JSON, Unity APIs or file storage. The Unity
prototype owns \`JsonUtility\` and local file operations in
\`../unity-prototype/Assets/Scripts/PrototypeSaveStore.cs\`. This file
format is an independently authored **local demo**, not original ROB RUN
account or server persistence.

## Build and run

The game logic uses only .NET Standard 2.1 framework APIs (no Unity types),
so it can be imported as C# scripts into a Unity 6000 project later. Tests
are a dependency-free console harness under .NET 10.

~~~bash
dotnet build reconstruction/game/Core/Game.Core.csproj --configuration Release
dotnet run --project reconstruction/game/Tests/Game.Tests.csproj --configuration Release
~~~

The GitHub Actions workflow runs these same commands on pushes and PRs.

## Provenance / uncertainty

Behavior evidence: \`reconstruction/docs/evidence.md\` (developer help center),
\`reconstruction/docs/location-bundle-audit.md\` and
\`reconstruction/docs/lfs-bundle-audit.md\` (actual client artifacts).

**Verified qualitative behavior:** masking activates criminal status within
the city; leaving the city clears it; fencing creates physically collectable
counter cash; money laundering is time-consuming; a civilian can bank clean
funds; the bank survives theft but not the seven-day wipe.

**NOT recovered or verified:** loot spawn weights, sale prices, weapon damage,
money laundering exchange rates, time limits, whether every loot must be sold
at once, uncollected-cash theft mechanics, precise NPC alarm conditions,
cash denomination types, role permissions, banking fees and interaction
requirements. The code's discrete phase transitions and the restriction that
clean output may not exceed dirty input are **provisional design safeguards**,
not evidence of exact parity.

The integration tests use tiny fixture values solely to assert transitions,
money conservation, and the absence of premature balance credit. No fixture
amount is an original ROB RUN payout, reward, fee, or duration.

## Next engineering steps

- Validate the existing `reconstruction/unity-prototype/` using a real
  Unity 6000.3 Editor smoke test, full Play Mode heist and Windows build.
- Implement scene markers for scouting, loot nodes, physical counter pick-up,
  police/surrender and house laundering.
- Store economy coefficients as data with explicit source provenance and
  test behavior against captured gameplay sessions.
- Replace local monetary authority with a server-authoritative session and
  persistence layer before multiplayer access.

Original game files under StreamingAssets/ are never modified or included
in this new core's build output.
