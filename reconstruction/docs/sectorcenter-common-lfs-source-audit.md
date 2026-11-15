# W1-AI — Original sector-center and environment-common LFS audit

**Initial original-byte run:** [GitHub Actions #43662347513](https://github.com/Nippytime/rabron/actions/runs/43662347513).
The [measured-ledger artifact](https://github.com/Nippytime/rabron/actions/runs/43662347513/artifacts/14140438364) reports
`documented_before=322`, `documented_after=324`, `new_documented=2`,
`source_reverified=0`, `tracked_bundles=330`, `unscanned_after=6`,
and zero unparseable attempts. Both actual original UnityFS workers and
strict same-run two-source reconciliation completed success.

| Original UnityFS bundle | SHA-256/LFS OID | Actual bytes | Objects | MonoBehaviours | Numeric result |
| --- | --- | ---: | ---: | ---: | --- |
| `location-sectorcenter-standalone_scenes_all.bundle` | `2d5fc983bb6f832e5ba331017180e6f0c86708e242bed4003815c93e7ab65e50` | 120,455,935 | 74,713 | 2,411/2,411 parsed | **2 capped fields**, incomplete numeric scan |
| `shared-environment-common_assets_all.bundle` | `a023695985095ae08f397ca8a46beb39a9091f06f46e75358ef7faad6e4f2d9c` | 142,691,728 | 2,421 | 5/5 parsed | **0 caps**, complete bounded numeric scan |

Pinned original Git blob SHA-1:
`906d8a339dfc85d6d70421d801daf82d65f7f158` (sector-center),
`d28a772caad8a0b2fa0d6be9d33e92e99c9ab30f` (environment-common).
Both source jobs validated Git LFS pointers, selectively downloaded the
exact original LFS object, checked original length, SHA-256 and UnityFS
header, and inventoried metadata using read-only pinned UnityPy 1.25.4
at 2,048 numeric fields/depth 32. No proprietary media exports.
Source artifacts:
[sector-center](https://github.com/Nippytime/rabron/actions/runs/43662347513/artifacts/14141050720) and
[environment-common](https://github.com/Nippytime/rabron/actions/runs/43662347513/artifacts/14140178434).

Sector-center typed Unity objects include 19,212 GameObject, 19,211
Transform, 9,843 MeshFilter and MeshRenderer each, 5,450 BoxCollider,
2,656 MeshCollider, 2,619 LODGroup, 2,285 Mesh and 2,411
MonoBehaviour. Candidate numeric keyword matches: combat **2**,
economy **228**, progression **12**, timing/world **1,862**.
**Two numeric field caps remain**; the sector-center record truthfully
sets `bounded_numeric_scan_complete=false`.

Environment-common includes 442 Texture2D, 395 Mesh, 370 GameObject
and Transform each, 296 MeshFilter and MeshRenderer each,
206 Material and five MonoBehaviours. Candidate matches: combat
**4**, timing/world **140**, economy/progression **0**. No caps.

Combined, these original sources add **2,416 parsed MonoBehaviours**
to the previous **125,947**: total **128,363**.
Numeric cap records rise **74 → 76**, with **46** outstanding after
prior targeted rescan recoveries. The separate W1-AH Wwise oversized
unparsed MonoBehaviour (**1**) remains unresolved. The branch
documents **324/330** original sources, **6** still unscanned.

These are bounded client Unity object counts and keyword matches,
**not original C#/IL2CPP logic, server-authoritative gameplay formulas,
complete numeric field extraction or media rights**. All records retain
`status=documented_scan_not_fully_verified`.

**Acceptance remains conditional:** recheck *both* exact original LFS
binaries on the new ledger head in `mode=recheck`; require
`source_reverified=2`, `new_documented=0`, `documented_after=324`,
a nonempty successful same-run reconciliation, all historical/Python
checks completed success, unchanged refs, squash merge into `dev`,
and successful postmerge `dev` Python CI before closing issue #89.
