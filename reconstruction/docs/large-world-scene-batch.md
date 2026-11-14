# W1-I: source-verified original large world scenes and weapon inventory

**Measured extraction and reconciliation:** https://github.com/Nippytime/rabron/actions/runs/43628460048

Three original large (20–64 MiB non-LFS) UnityFS bundles were selected
from the **unchanged Git tree** by explicit path manifest in
`reconstruction/data/large_source_targets.json`, then sparse-checked out
in three one-source jobs. The shared read-only UnityPy 1.25.4 scanner
validated exact original byte length, Git blob SHA-1, UnityFS header,
independently computed SHA-256, all Unity object type counts and bounded
2,048-numeric-field / depth-32 MonoBehaviour inventories. No game media
or binaries were exported to the repository.

| Source `.bundle` | Verified bytes | Parsed/total MonoBehaviours | Field-capped | Combat/economy candidate matches | Verified source SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `location-settlement-standalone_scenes_settlementadditive_standalone.bundle` | 28,081,566 | 495 / 495 | 1 | 0 / 217 | `f476a69d29dfe2f0943c04e15e43262c75392a45ae235a5ffcea3557db920fb0` |
| `space-global_scenes_all.bundle` | 27,095,840 | 603 / 603 | 0 | 3 / 0 | `c353550911b1e721fcc0823c2334155b7dbb182d7fc1a5417ebfa139b87f7959` |
| `weapon-apscalar_assets_all.bundle` | 32,240,826 | 53 / 53 | 0 | 132 / 0 | `85fd9c92c4a8dec9341d549f3b0594de5e0c4047200dc1b77925a7a61dec8e3d` |
| **Totals** | **87,418,232** | **1,151 / 1,151** | **1** | **135 / 217** | Measured SHA-256s above |

Progression keyword matches: **90**; timing/world: **864**.
All values are **client serialized-field-path heuristics**, not evidence of
source-authoritative combat, economy, construction, territory or server rules.

## Preserved partiality and cross-file Unity IDs

- One MonoBehaviour in `location-settlement-standalone_scenes_settlementadditive_standalone.bundle`
  reached the numeric **field_limit** (path ID `31213`).
  Its typetree was parsed, but the bounded numeric scan is **partial**.
- `space-global_scenes_all.bundle` contains **603** parsed MonoBehaviours
  across **five** distinct serialized file names. There were **110**
  groups of repeated local Unity path IDs across those files, despite
  **603 distinct (serialized_file, path_id) identities**. The former
  global-ID check correctly rejected this bundle in an initial CI run;
  the shared scanner/validator now preserves exact per-file names and
  rejects any duplicate **within** the same serialized file or missing
  file identity when local path IDs repeat. No object was deduplicated.
- `weapon-apscalar_assets_all.bundle` had 53/53 parsed typetrees and
  zero numeric field caps. No unparsed MonoBehaviour was reported in
  the three-source batch.
- Per-object path IDs, serialized file identities and numeric partial
  reasons are retained in the metadata-only Actions artifacts; the
  source size/hash, object-type counts, totals, field limits and candidate
  counts are committed in `reconstruction/data/extraction_coverage.json`.

## Current source recovery boundary

- Documented source paths: **161/330**; parsed MonoBehaviours:
  **79,934**.
- Without documented original source scans: **169** (140 medium non-LFS,
  9 large non-LFS, 20 pending LFS pointer originals).
- Raw numeric caps in historical ledger: **65**, of which 30 were
  previously resolved by targeted numeric rescans, leaving **35** known
  unresolved (26 historical, 7 W1-F localization, 1 W1-H realm,
  1 W1-I settlement).
- Subsequent CI must run nonempty exact-source rechecks across these
  same three originals, and fail if serialized-count or byte fingerprints
  drift. A passing source scan does not establish matching GameAssembly.dll,
  IL2CPP method bodies, original server authority or allowed use of
  copyrighted original game assets.
- **Not performed:** Unity 6000.3 Editor import, actual Play Mode runtime,
  packaged Windows EXE acceptance and full game implementation; separate
  issue #9 and waterfall gates remain open.
