# W1-P: eight remaining medium civilian body original UnityFS inventories

**Measured original-source run:** https://github.com/Nippytime/rabron/actions/runs/43634223903

Eight original medium non-LFS civilian character-body bundles were independently
sparse-checked-out and byte-verified using the pinned Git source tree and
original Git blob SHA-1 and byte sizes from
`reconstruction/data/medium_civilian_remaining_source_targets.json`.
The read-only UnityPy **1.25.4** scanner confirmed UnityFS signatures,
computed source SHA-256 hashes and recorded actual Unity object types and
bounded MonoBehaviour numeric evidence (**2,048 fields, maximum depth 32**).
All eight sources were processed in four batches of two, maximum two
concurrently. Original binary media was not included in artifacts.

| Original bundle | Verified bytes | Parsed/total MonoBehaviours | Mesh | Texture2D | Measured SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_30_type_1_paint_2.asset.bundle` | 7,780,131 | 1/1 | 0 | 3 | `409749643cb3d26cb17506e58328591b7af42e603227f1c06fc086c5e662b48e` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_31_type_1_paint_1.asset.bundle` | 9,131,096 | 1/1 | 5 | 3 | `ef99e1cd2ffbf58b0094b19b1730e40d0add71dbc11b67d6971abd28dda4e5e9` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_31_type_2_paint_1.asset.bundle` | 9,506,770 | 1/1 | 5 | 3 | `21cc0cfa5fa843ed9b7c07b0d81fcdf2607ccc2e9750e8a30b8e6d357edff1a7` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_33_type_2_paint_1.asset.bundle` | 8,922,946 | 1/1 | 5 | 3 | `e89228813c71cd95472ed86c3181eb754783b0f8820c4b7131a310118eb64be5` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_42_type_1_paint_1.asset.bundle` | 1,557,943 | 1/1 | 0 | 1 | `d68e91fcf80d97650d87bda7a85c1370beb592f1734f7eb6ae538d2d63a7f261` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_42_type_1_paint_2.asset.bundle` | 1,215,072 | 1/1 | 0 | 1 | `77d22c89dd4b12e37e19b6ba938283f0a6e77d16311f114caccae82f50d2fa54` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_42_type_1_paint_3.asset.bundle` | 1,354,334 | 1/1 | 0 | 1 | `755c0a4ad3e6ad734e37b556133627bc896b44a63b4694b70c7140180fc9634d` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_5_type_1_paint_1.asset.bundle` | 9,311,867 | 1/1 | 5 | 3 | `1ad2d23b8098394ff85fb480c43bc14a6cac7efdc9c61d1d5e39a534040b7ce4` |
| **Total** | **48,780,159** | **8/8** | **20** | **18** | Eight verified original hashes |

All eight originals contain one parsed MonoBehaviour, one Material, and one
AssetBundle object. The three body-42 variants legitimately have no Mesh
objects and one Texture2D each; body-30 paint-2 also has no Mesh and
contains three Texture2D objects. Four remaining sources each contain
five Mesh and three Texture2D objects. All eight had **zero unparsed
MonoBehaviours, zero numeric field/depth-capped records and zero
candidate fields** in the combat, economy, progression and
timing/world categories. These are bounded **client source metadata**
counts, *not* authoritative character customization, economy, combat,
police AI or progression mechanics.

## Coverage and verification boundaries

After recording this measured batch, the ledger documents **198/330** original
UnityFS bundle paths and **81,854** parsed MonoBehaviours. **132** original
bundles remain unscanned: **112** medium non-LFS and **20** LFS-pointer
sources. The existing **42 unresolved numeric caps** are unaffected.

This batch does not recover missing matching GameAssembly.dll, original IL2CPP
method bodies, server-authoritative game systems, reuse rights for proprietary
media, or Unity Editor/Play Mode/Windows EXE acceptance (issue #9).
No game mesh, image, model, audio or executable bytes are committed or
distributed; metadata-only Actions evidence preserves original scoped
serialized-file/path IDs.

**Merge gate:** require successful full **eight-source original-byte recheck**
on the latest PR head, in addition to all previous source/numeric/LFS/Python
Actions checks. Incomplete, absent or failed checks are not green.
