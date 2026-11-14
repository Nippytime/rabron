# W1-K: source-verified original settlement and two large weapon UnityFS bundles

**Measured source provenance:** https://github.com/Nippytime/rabron/actions/runs/43630060068

Exactly three previously unscanned original non-LFS UnityFS sources, from
`reconstruction/data/large_settlement_weapon_source_targets.json`, were
sparse-checked out and verified against the pinned original Git tree.
The shared scanner checked the original byte length, Git SHA-1, UnityFS
signature and independently measured SHA-256; pinned UnityPy 1.25.4
inventoried original Unity object types, serialized-file-scoped MonoBehaviour
IDs and bounded client numeric fields with limits **2,048 fields / depth 32**.
No original game textures, scene media, executable code or sounds are exported.

| Original large source bundle | Verified bytes | Parsed/total MonoBehaviours | Field-capped records | Combat/timing keyword matches | Measured SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `location-settlement2-standalone_scenes_all.bundle` | 44,443,885 | 1,506 / 1,506 | 2 | 0 / 540 | `2c89e28f03f445e016f0459bd81f1ae17ae855fe6b3e95ae1b396d95c228ea6c` |
| `weapon-jp7_assets_all.bundle` | 41,683,128 | 53 / 53 | 0 | 132 / 0 | `fee08f2c4c2dd7c229df500576a04dbb24921e31e36dad2d9dd5f98747e12596` |
| `weapon-srreaper_assets_all.bundle` | 47,972,189 | 84 / 84 | 0 | 198 / 0 | `e0a42af5fb6b07a84969121d9252e5cead0301f262f7623d386e9f2da8771e18` |
| **Total** | **134,099,202** | **1,643 / 1,643** | **2** | **330 / 540** | Source hashes above |

Two MonoBehaviours in
`location-settlement2-standalone_scenes_all.bundle` are explicitly
**numeric field/depth-capped** within the declared scanning bounds.
Its 1,506 typetrees were parsed, but the bounded numeric inventory
is **partial**. The JP7 and SRReaper sources were fully scanned within
those numeric bounds, with zero new caps. There were **no unparsed
MonoBehaviour typetrees** in this three-source batch.

Additional source keyword matches: **214** economy, **0** progression.
These are path-matching client serialized field heuristics and are **not**
verified gameplay coefficients, authoritative construction/economy
values, weapon damage, recoil, ballistics, or multiplayer server rules.

## Source coverage and remaining blockers

- **167 / 330** original bundle paths documented by actual bounded scans.
- **81,823** parsed MonoBehaviours; this does not mean full Unity scene
  export, recovered IL2CPP source code or runtime acceptance.
- **163** original bundles lack a documented source scan: **140 medium
  non-LFS, 3 large non-LFS (two UI atlases and global Wwise), 20 pending
  LFS sources**.
- **37** numeric-cap records remain unresolved: 26 historical, 7 W1-F
  localization, 1 W1-H realm, 1 W1-I settlement additive scene and
  2 W1-K settlement2 scene records. Raw historical observed caps: 67,
  including 30 resolved by prior targeted numeric rescans.
- The exact measured Git IDs, SHA-256s, typed object counts, source sizes,
  limits, candidate counts and partiality are in
  `reconstruction/data/extraction_coverage.json`. Per-object scoped
  path IDs and truncation reasons remain source-run metadata artifacts.
- Future CI must execute nonempty full-original **rechecks** after the
  ledger commit. Missing or changed source identity, object counts or
  candidate counts must fail instead of being silently skipped.
- Matching original GameAssembly.dll, IL2CPP code, server gameplay
  authority and licensed original-media rights remain unavailable or
  unverified. Unity 6000.3 Editor import, Play Mode and Windows EXE
  acceptance have **not** been executed (issue #9). W1 and W2–W8
  waterfall acceptance are not complete.
