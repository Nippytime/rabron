# W1-O: measured ten civilian body original UnityFS source inventories

**Original source run:** https://github.com/Nippytime/rabron/actions/runs/43633293481

Exactly ten original medium non-LFS civilian body customization
UnityFS bundles, selected by
`reconstruction/data/medium_player_body_source_targets.json`,
were sparse-checked-out and byte-verified against pinned Git tree
metadata in five read-only 2-source scan batches. The existing
UnityPy 1.25.4 scanner measured each original Git blob SHA-1, byte
length, UnityFS signature and independently computed SHA-256,
Unity object types and bounded MonoBehaviour numeric fields
(**2,048 fields/depth32**).

| Original bundle | Verified bytes | Parsed/total MonoBehaviours | Mesh objects | Texture2D objects | Measured source SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_12_type_1_paint_1.asset.bundle` | 9,834,628 | 1/1 | 5 | 3 | `c719f565d32d1c7583efbd2f5e602bccd24c62fdadb076b40e6ea8c6de456e3a` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_1.asset.bundle` | 3,762,350 | 1/1 | 0 | 2 | `8a4780ae201fd4ec167d73795eb40798b15b54dfec152a30175586f0e32319bc` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_2.asset.bundle` | 3,781,735 | 1/1 | 0 | 2 | `c30e0e64af6aff38ab768c7b8b5cd7fe22c2885a60422a284b6a561576bdfcb7` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_3.asset.bundle` | 3,698,361 | 1/1 | 0 | 2 | `422b732023d4ba58759e53870a5aa9322255483204e964beaef88d821ee39252` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_1.asset.bundle` | 7,083,002 | 1/1 | 0 | 3 | `e476d07bf86d7a9d88156c0613631bcd355422e12a6e87e18516590514bf42da` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_2.asset.bundle` | 7,593,958 | 1/1 | 0 | 3 | `8cd537dfe5bf1d7b1436661d6104306e5de348fbcf7b1f11bc6dfa768cc19c3c` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_3.asset.bundle` | 7,525,426 | 1/1 | 0 | 3 | `c61ae6245072e519e1cd1d13aa77667393b18d10fe45d3b222c4470571de5185` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_4.asset.bundle` | 7,652,010 | 1/1 | 0 | 3 | `709cd42f3ff6e43c6eff6bad3d7379e0b60e5ccf73b6ae7bfce06c9f8a2c5dd0` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_28_type_1_paint_1.asset.bundle` | 9,044,997 | 1/1 | 9 | 3 | `98843c086f86dd9b14c2c6317a85812882498fd9d01d88bef48a5ecf05b1a5d1` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_30_type_1_paint_1.asset.bundle` | 8,299,139 | 1/1 | 0 | 3 | `8ba4adda3444cfa455f7a0fee158db4eacbb6be802bae59b93a622b32572b536` |
| **Total** | **68,275,606** | **10/10** | **14** | **27** | Per-source fingerprints above |

All ten sources had **one parsed MonoBehaviour each**, one Material
and one AssetBundle. **Mesh counts differ per source**: the body-12
and body-28 sources held five and nine Mesh objects respectively,
while the remaining eight had no Mesh objects. The 27 Texture2D
objects are distributed as shown above. There were **zero unparsed
typetrees and zero new numeric field/depth-capped records**, with
**zero** keyword matches in the four recorded numeric categories.
These are actual verified client serialized metadata counts, **not
authoritative customization, progression, or combat formulas**.

No original copyrighted character meshes, images, materials,
models, sounds, executables or Unity media were exported into the
repository or metadata artifacts. Per-object serialized file/path
IDs remain metadata-only Actions scan evidence.

## Recovery boundary

- Original source-documented UnityFS bundles: **190/330**.
- Total MonoBehaviours parsed: **81,846**, which does not imply
  original IL2CPP source code or complete playable content.
- Still without documented original source inventory: **140**:
  **120 medium non-LFS** and **20 pending LFS original sources**.
  Eight further `characterbodiesviewdescription_body_` medium
  sources remain outside this batch.
- **42 unresolved numeric-cap records** remain, including 30
  older caps previously resolved among 72 raw observations.
  W1-O adds **none**.
- Following the measured source ledger commit, current-head
  CI must execute a nonempty **full ten-source recheck**
  along with all historic source, numeric/LFS and Python gates.
- Missing matching GameAssembly.dll and original IL2CPP method
  bodies, server authority, exact original game formulas and
  licensed media reuse rights remain unverified. Real Unity
  6000.3 Editor import, Play Mode and Windows EXE smoke have
  **not** run (issue #9). W1 evidence gate and W2–W8 roadmap
  remain incomplete.
