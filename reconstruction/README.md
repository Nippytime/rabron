# ROB RUN reconstruction workspace

The parent repository is a **packaged Unity IL2CPP player-data dump**, not the
original Unity source project. This workspace is for an independent, evidence-
driven recreation of its gameplay formula. It does not alter the raw game files.

## Progress

- Milestone 1: auditable metadata inventory, source-led mechanic ledger, and
  small **headless executable behavior specification** with tests.
- Not yet delivered: an interactive Unity scene, exact recovered balance tables,
  animation/physics parity, networking, or a playable ROB RUN replacement.

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

## Implementation sequence

1. Audit and evidence ledger (this milestone).
2. Extract machine-readable asset schemas and numerical balance from the
   ScriptableObject bundles / matching local IL2CPP binary where authorized.
3. Implement playable vertical slice in a fresh Unity project: scout -> mask ->
   heist -> flee -> sell -> launder -> reinvest.
4. Add vehicles, cargo, police roles, settlement ownership, base defenses,
   clan control and seven-day reset.
5. Add authoritative multiplayer, persistence, security and profiling.

Every numeric game rule should be tagged with its source (extracted, directly
observed, or proposed balance). Unknown is preferable to fabricated precision.
