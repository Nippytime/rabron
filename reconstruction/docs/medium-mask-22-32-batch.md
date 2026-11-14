# W1-S: measured ten original medium character-mask 22–32 bundles

**Measured original source run:** https://github.com/Nippytime/rabron/actions/runs/43636832117

The ten exact original mask-22 through mask-32 sources (22–29 and 31–32)
were sparse-checked-out read-only and verified against pinned original Git
blob SHA-1 and byte lengths from
`reconstruction/data/medium_mask_22_32_source_targets.json`. A separate
SHA-256 digest was computed for each original, UnityFS was validated,
and pinned UnityPy **1.25.4** recorded actual Unity object types and
bounded MonoBehaviour numeric fields (**2,048 fields / maximum depth 32**).
All five two-source batches and strict reconciliation completed successfully.
No original game media was exported or committed.

| Original source | Verified bytes | Parsed/total MonoBehaviours | Mesh | Texture2D | Original SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-mask-22_assets_all.bundle` | 1,852,356 | 0/0 | 0 | 3 | `e0d4dd87c9787dba43db313efe6edceced1c05876cfdd19d5aba521963ec7ba9` |
| `character-mask-23_assets_all.bundle` | 1,533,802 | 0/0 | 0 | 3 | `ae44af30f542876fef080cd80bebacba1efba5de91fc14c10e9d8daf963a08f2` |
| `character-mask-24_assets_all.bundle` | 4,215,350 | 0/0 | 0 | 9 | `a30266df2be363601df0bb134fcb9c4f220275b77b2b79a652663897a96ce89f` |
| `character-mask-25_assets_all.bundle` | 3,335,032 | 0/0 | 0 | 6 | `36ef804b66ff47d99382bbae6a39ae55e8d97f6078acd691c8538a42c99a128b` |
| `character-mask-26_assets_all.bundle` | 6,047,197 | 0/0 | 0 | 12 | `a2aab3e1e997b7d333662650a2154ea2e686344cf8da4c8046f970d24336fa00` |
| `character-mask-27_assets_all.bundle` | 7,079,808 | 4/4 | 10 | 12 | `7ba68d4e637e10fe4f4eef51ee2fe1d281f40ce6fdc107372a39d8963cfa44dc` |
| `character-mask-28_assets_all.bundle` | 1,428,716 | 0/0 | 0 | 3 | `2607547b1000d953fa7b093ca63e53870d64225bcd997b5a37feabf6705752dc` |
| `character-mask-29_assets_all.bundle` | 1,543,116 | 0/0 | 0 | 3 | `645f85aa30cbc032e1fa2e117a478129c22dfd7ebc0278382abe9310a57d8083` |
| `character-mask-31_assets_all.bundle` | 1,791,881 | 0/0 | 0 | 3 | `68fd554f2cd10b2897d7a6b6b2d135d14c80fcdae85ff00e6b166ff0b90f1448` |
| `character-mask-32_assets_all.bundle` | 1,868,138 | 0/0 | 0 | 4 | `e7b39863c2aac170cd2e12a2da1bc5672ff82ad383ec8e03c51c356c0b2855ef` |
| **Total** | **30,695,396** | **4/4** | **10** | **58** | Ten verified per-source digests |

Nine original mask variants are genuinely texture-only with one
AssetBundle and several Texture2D objects and **zero** MonoBehaviours.
`character-mask-27_assets_all.bundle` instead has **4/4**
parsed MonoBehaviours, **10 Mesh**, **2 Material** and **12 Texture2D**.
All ten originals produced **zero unparsed records**, **zero new numeric
caps**, and **zero** candidate combat/economy/progression/timing numeric
fields. Genuine zero records are not scan failures.

After this measured batch, the ledger documents **228/330** originals and
**81,862** parsed MonoBehaviours; **102** original bundles remain unscanned
(**82** medium non-LFS, **20** pending LFS) and the existing
**42** unresolved historical numeric caps persist.

These are source-verified client serialized media inventories—not original
authoritative mask behavior, combat/economy/server formulas or IL2CPP method
bodies. Matching GameAssembly.dll, proprietary media reuse rights and actual
Unity 6000.3 Editor/Play Mode/Windows EXE acceptance (issue #9) have not
been established.

**Merge requirement:** a nonempty full latest-head ten-source recheck of
the actual original bytes and all previously required source/numeric/LFS/
Python Actions checks must complete successfully. Pending, missing, skipped
or failed gates do not count as success.
