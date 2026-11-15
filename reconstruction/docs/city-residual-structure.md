# W1-AR — Original city residual numeric-cap structure diagnostic

**Source of truth:** [first-original W1-AR Actions run #43682928889](https://github.com/Nippytime/rabron/actions/runs/43682928889) (all **3/3 nonempty jobs completed success**: plan, inspect, reconcile). Original city source Git LFS path: `StreamingAssets/aa/StandaloneWindows64/location-city-standalone_scenes_city_standalone.unity.bundle`, exactly **549,566,135 original bytes**, SHA-256 `5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f`; original pointer Git blob `c73e7b84edc6b4e73001923054ff3a29bd540393`.

The measured `city-residual-structure-measured` Actions artifact **14149531336** includes the metadata-only `city-residual-structure.json` (**4,755 bytes**, SHA-256 `aecf8a6f32b292ba4114aaf0d4126d0a2d007ee4eb7e4f2499565ee7730b857c`, Git blob `aff0e9f96838f4ad13b0a17ebb1e3dfdb00d46f9`). The Git blob is byte-identical to the independently downloaded Actions artifact. This document describes **measured original client serialized structure only**, never numeric values, formulas, code, media or redistributed original assets.

## Three source-scoped, still-numeric-capped objects

| Exact serialized file | Path ID | Original object bytes | Measured top-level structure | Numeric outcome |
| --- | ---: | ---: | --- | --- |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344196` | 523,360 | `<Renderers>k__BackingField`: 41,623 renderer references; `<HidingObjectRenderers>k__BackingField`: 1,986 references; empty room-related lists | **Still capped** |
| Same serialized file | `344248` | 507,228 | `<MeshRenderers>k__BackingField`: 42,266 mesh-renderer references | **Still capped** |
| `CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets` | `7968` | 673,360 | `Nodes`: 16,810 water quadtree node records, `RootNodeIds`: 225 entries | **Still capped** |

All three parsed within the unchanged **8 MiB per-MonoBehaviour** bound, and original source-wide totals were verified: **366,174 Unity object headers, 14,467 MonoBehaviours**. Every reported first-element member name is metadata, not a recovered value. Object structure shows why the earlier 16,384-field numeric traversal cap was reached: large renderer-reference arrays and water quadtree nodes. This **does not resolve** numeric field caps and does not establish any numeric gameplay mechanics or original server formulas.

**Selection conclusion:** further indiscriminate expansion of these scene-reference/quadtree arrays is not presently justified as an efficient way to recover core economy/combat/AI parameters. Preserve those three historical caps as explicit unresolved original evidence, and focus on provenance-relevant client configuration or separately acquired authoritative code if available. Do not delete or renumber them to improve completeness metrics.

**Accounting after this source diagnosis:** no new source paths and no numeric cap resolution: **330/330 original source-file paths inventoried**, **143,131 parsed MonoBehaviours**, **355 historical numeric field-cap records / 323 targeted unresolved**, and **two original oversized Wwise MonoBehaviours remain unparsed**. This is not W1/E1 numeric completeness. Parent [#3](https://github.com/Nippytime/rabron/issues/3) stays open; [Unity Editor, Play Mode and Windows EXE validation #9](https://github.com/Nippytime/rabron/issues/9) and full game production gates remain incomplete.

**Integration rule:** first-original read-only measurement and source reconciliation succeeded; the committed metadata is a proposed work-branch artifact until a fresh **exact-current-head `mode=recheck`** proves deterministic source agreement, all nonempty current-head Actions and checks pass, and PR is merged to `dev` with postmerge verification. Do not infer successful CI or integration from this document alone.
