# ROB RUN reconstruction workspace

The parent repository is a **packaged Unity IL2CPP player-data dump**, not the
original Unity source project. This workspace is for an independent, evidence-
driven recreation of its gameplay formula. It does not alter the raw game files.

## Progress

- Milestone 1: auditable metadata inventory, source-led mechanic ledger, and
  small **headless executable behavior specification** with tests.
- Working Unity 6.3 prototype **source** now exists under
  reconstruction/unity-prototype/ with procedural city/heist, input, cash
  pickup, guard, laundering, bank, local saves, and authored Editor/Play Mode
  acceptance scripts. **No Unity Editor or Windows EXE run is verified yet.**
- Not yet delivered: a full content-complete game, exact recovered economy/
  combat/alert coefficients, animation/physics parity, or multiplayer authority.
- **Full product scope and waterfall gates:**
  reconstruction/docs/full-game-waterfall.md. New systems, including opt-in
  community/viral loops, are explicitly marked PROPOSED rather than recovered.

## Run the tests

From the repository root, with Python 3.11 or newer:

~~~bash
python -m unittest discover -s reconstruction/tests -v
~~~

No third-party Python dependencies are required.

## Audit the original build

~~~bash
python reconstruction/tools/audit_build.py --root . --output /tmp/rob-run-manifest.json
~~~

This scans the raw file tree and parses the managed assembly list, startup list,
and Addressables linker type names. The audit is **read-only**: it doesn't execute
game code, unpack bundles or change any extracted asset. It does not claim to
recover IL2CPP method bodies or economic coefficients.

A shallow/sparse CI checkout of this directory is sufficient for unit tests,
but it is **not** sufficient for a full-binary inventory of the parent repo.

## Evidence-first extraction queue

The full original build inventory includes **330 tracked Unity bundles**.
Only nine prior MonoBehaviour bundle passes are source-documented; their
combined 7,787 parsed objects still include 56 historic per-object numeric
field-limit truncations. Even zero cap counts do not establish server formulas
or full nested-field coverage.

List all tracked bundles without downloading binaries, cross-check known
SHA-256 evidence and produce a prioritized, explicitly incomplete backlog:

~~~bash
python reconstruction/tools/plan_bundle_scans.py \
  --ref HEAD --min-tracked 330 \
  --output /tmp/bundle-scan-backlog.json
~~~

The GitHub Actions reconstruction-test workflow generates the same backlog
artifact after source tests. It is an inventory, **not** a claim that every
bundle was decoded. Historical scan evidence is recorded at
reconstruction/data/extraction_coverage.json. Depth-limited numeric scans now
report partial extraction rather than silently omitting nested fields.

## Current reference model

reconstruction/rules.py covers:

- Civilian-to-Criminal transition when masked inside the city; clearing the
  criminal role on exit
- Loss outcomes for city Civilian/Criminal/Police deaths, desert deaths,
  surrender, and accepted bribes
- Seven-day reset categories and confirmed persistent fields, using externally
  supplied conversion values rather than invented formulas

The developer's help center confirms the qualitative rules, not exact balance.
See reconstruction/docs/evidence.md for full source URLs, caveats, binary
references and unresolved cases.

## Delivery sequence

Use the detailed stage gates and complete mechanic inventory in
reconstruction/docs/full-game-waterfall.md. In short: W0 requirements ->
W1 exhaustive evidence inventory and priority rescans -> W2 reviewed
architecture/data contracts -> W3 complete offline gameplay -> W4
multiplayer server authority -> W5 content-complete environments ->
W6 social/replay/challenge/weekly loops -> W7 real Unity and release
validation -> W8 data-informed tuning and maintenance.

One focused issue, work branch and PR into dev per increment. Source CI is
mandatory now; real Unity Editor, gameplay, network and Windows verification
must run before a release can be claimed complete.

Every numeric game rule should be tagged with its source (extracted, directly
observed, or proposed balance). Unknown is preferable to fabricated precision.
