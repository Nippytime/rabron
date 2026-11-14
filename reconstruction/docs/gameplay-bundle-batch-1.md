# W1-B — first six previously unscanned gameplay-related bundles

**Observed, not proposed.** Real GitHub Actions matrix run:
https://github.com/Nippytime/rabron/actions/runs/43584959275

Source is the uploaded Unity 6000.3.18f1 Windows client data under
StreamingAssets/aa/StandaloneWindows64/. Individual files were checked out
by sparse checkout; their SHA-256 values were measured from the original
UnityFS bytes. No original art, audio, meshes or game executable were
committed to authored reconstruction files.

## Measured extraction results

Tool: reconstruction/tools/extract_unity_bundle.py, UnityPy 1.25.4;
numeric per-MonoBehaviour maximum **8,192 fields**, maximum traversal
depth **32**. All six jobs completed successfully, and all inspected
MonoBehaviours parsed. No scanned MonoBehaviour record was reported
truncated at these limits.

| Bundle (omit .bundle) | MonoBehaviours parsed / total | Economy keyword hits | Combat keyword hits | Timing/world keyword hits | SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| vehicle-cars_assets_all | 78/78 | 0 | 0 | 28 | 119d9aa6abef7adcc2823284dbc236fc953d0e35dc4a1a423aff7e336e503540 |
| equipement_assets_usableitem | 163/163 | 0 | 0 | 140 | cb89ea19ccc682aa47673384c16473a8c572c502a556c9c40f9ad47e4a22c08f |
| shared-environment-plot_assets_all | 3/3 | 0 | 3 | 105 | e4d428a426175fd318afc4ee1797985fb5f2cade21a80b142c256a89a1d35ad3 |
| vehicles-helicopters_assets_all | 132/132 | 0 | 0 | 48 | 6ca29e596bfb0bffd534bb02795b3abc7ede16848e6f5d5e411b44653415d984 |
| weapon-vulture50_assets_all | 34/34 | 0 | 88 | 12 | 576c2da1b7f987bffad5737c50c5b5e5b9195c3d673eee3416c84af897746377 |
| location-settlement-standalone_scenes_settlement_standalone | 910/910 | 0 | 0 | 11 | 8bdcfda70d8e69618e76f282d4c289ac0d406fad8d2cc3f774668c155e1c78db |
| **TOTAL** | **1,320 / 1,320** | **0** | **91** | **344** | Per-bundle checksums above |

The categories are **heuristic matches on field paths**, not confirmations
that the values are actual damage, movement speed, construction price,
fuel, crash tolerance, probabilities or a network/server rule. For
example, "combat" text in a plot or weapon prefab could be a damage VFX,
UI, or animation parameter. The scanner's "complete_numeric_extraction:
true" applies ONLY to serialized MonoBehaviour numerics within these
explicit per-object limits, not all objects in the asset or all game data.

### Useful scene/type observations

- Vehicle-cars: 478 GameObjects, 340 MeshRenderers, 78 MonoBehaviours;
  source exists for a rough vehicle prefab/rig hierarchy and collision
  metadata. No validated driving formula.
- Equipment usable item: 47 GameObjects, 163 MonoBehaviours, 19 Mesh
  objects; content metadata may help build independently-authored item
  archetypes. No proven authoritative item pricing/effects.
- Plot environment: 146 GameObjects, 123 MeshRenderers, just three
  MonoBehaviours; most information is prefab/mesh rather than numeric
  gameplay config. Do not mistake the 105 timing/world matches for a
  105-coefficient construction ruleset.
- Helicopters: 824 GameObjects, 584 MeshRenderers, 132 MonoBehaviours;
  indicative of structural content, not recovered flight aerodynamics.
- Weapon vulture50: 94 GameObjects, 34 MonoBehaviours; 88 "combat"
  keyword matches are **candidates** only. No authoritative weapon
  damage/recoil/muzzle speed inferred from this.
- Settlement standalone: 2,494 GameObjects, 2,217 BoxColliders, 395
  MeshColliders, 910 MonoBehaviours, NavMeshSettings/Occlusion structures;
  promising for blockout/collision *reference* without copying protected
  scene assets. This scan does not export actual geometry.

### Evidence handling and next work

- New machine-readable records with exact SHA-256, per-bundle object
  counts and heuristic category counts are appended to
  reconstruction/data/extraction_coverage.json.
- Six separate Actions artifacts, named with each bundle, contain raw
  *numeric-only* JSON and a summarized subset. They are short-lived
  research artifacts; do not commit copied proprietary media.
- Coverage becomes **15/330 tracked bundles** with documented
  MonoBehaviour passes: the new six have no reported per-record truncation
  at the chosen limits, the older nine still include **56** reported
  cap occurrences. **313 bundles have no documented pass** in the
  current ledger; **two** known NPC/tutorial sources still require
  actual LFS bytes for scanning.
- Next waterfall step: targeted scans of high-priority uninspected
  locations/NPCs/items/cargo/police and the 56 older capped records;
  build MonoScript/field identity crosswalks; classify which values are
  visual/prefab/client configuration. Obtain matching GameAssembly.dll
  through authorized means if possible, and collect observed behavior
  for absent server formulas.
- All original game economics, damage, notoriety/police AI, taxes,
  car physics and server persistence remain **unverified**. No new
  gameplay coefficient has been incorporated into the prototype.
