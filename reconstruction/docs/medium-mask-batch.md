# W1-Q: measured ten original medium character-mask UnityFS bundle inventories

**Measured original-source run:** https://github.com/Nippytime/rabron/actions/runs/43635238378

Ten original medium non-LFS `character-mask-*` sources were read-only
sparse-checked-out and checked against the exact Git SHA-1/byte sizes
in `reconstruction/data/medium_mask_source_targets.json`, the pinned
original Git tree and independent SHA-256 calculations. The existing
UnityPy **1.25.4** scanner measured their UnityFS signature and Unity
object-type inventories, with bounded MonoBehaviour numeric scans
(**2,048 fields; maximum depth 32**) in five two-source batches
(max two concurrently). No game media was exported.

| Original bundle | Verified bytes | Parsed/total MonoBehaviours | Mesh | Texture2D | Original SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-mask-10_assets_all.bundle` | 4,080,875 | 4/4 | 8 | 6 | `46196a2c9b79e8729fe9e794a690326e313bfa4858365543981b8a5072d05d17` |
| `character-mask-11_assets_all.bundle` | 1,790,923 | 0/0 | 0 | 3 | `807af99842f8cff940d9d54868decf5efe077aecbdce8a068f0599bfa023efce` |
| `character-mask-1_assets_all.bundle` | 8,283,863 | 0/0 | 0 | 18 | `c3eaeb52052473bb4b9d31a7d4da165afabcad6a975e46947fc62dfee9a35a32` |
| `character-mask-2_assets_all.bundle` | 5,208,353 | 0/0 | 0 | 15 | `ef7bb01cbd86647e3e569635641444db16f7d03653a1cf7d867692df5d79204f` |
| `character-mask-3_assets_all.bundle` | 6,543,295 | 0/0 | 0 | 16 | `d61bceaff7b8b1d9dd5cdbbd53a76e11d20f407262146789a66c9d41fd77760b` |
| `character-mask-4_assets_all.bundle` | 1,735,902 | 0/0 | 0 | 3 | `587afbc311b74d7199ebef8186fd6791f89cc4ed910f4dd40c921b621fd1f63a` |
| `character-mask-5_assets_all.bundle` | 2,844,216 | 0/0 | 0 | 6 | `8ead65dda03be2ca7ab73a9c0623517333eecf9de77d33178a02b01be422ee04` |
| `character-mask-6_assets_all.bundle` | 7,912,556 | 0/0 | 0 | 15 | `b0ee24147e326b48ec8a1153bec3d25d87e3afbb1589ee2b0fe13bc4eb3a86df` |
| `character-mask-7_assets_all.bundle` | 1,652,361 | 0/0 | 0 | 3 | `97a6abb8ff3befc5220bec15f2a624a087aa39f7c917b312fac0dbb12bd1ee8c` |
| `character-mask-9_assets_all.bundle` | 6,463,144 | 0/0 | 0 | 12 | `0ce84c45ed6a40a2d21db9ce8e2a8eaf3258902c54940603326ca690665a1b62` |
| **Total** | **46,515,488** | **4/4** | **8** | **97** | Ten verified source SHA-256s |

Nine of ten original mask sources contain no MonoBehaviour and
only verified `AssetBundle`/`Texture2D` object types; this is a
**genuine recorded zero**, not an extraction error or evidence
of missing data. The tenth (`character-mask-10_assets_all.bundle`)
has **4/4** parsed MonoBehaviours, **8 Mesh**, **6 Material**
and **6 Texture2D** objects. All ten originals had **zero unparsed
MonoBehaviour records**, **zero numeric caps**, and **zero**
candidate numeric fields in combat, economy, progression, and
timing/world categories. The counts establish client serialized
asset metadata only, **not authoritative robbery mask or gameplay
mechanics**.

## Coverage and remaining limitations

The ledger now documents **208/330** originals, **81,858** parsed
MonoBehaviours and **122** unscanned original bundles
(**102** medium non-LFS plus **20** LFS). The **42** historic
unresolved numeric field-capped source records remain unresolved.

No original mesh, model, texture, sound or executable was
committed; Actions artifacts contain only metadata and preserve
serialized-file-scoped object IDs for any MonoBehaviour records.
The matching original `GameAssembly.dll`, IL2CPP method bodies,
server-authoritative gameplay, media redistribution rights and
actual Unity Editor/Play Mode/Windows EXE validation (#9) are
not established.

**Merge gate:** the latest PR head must execute a nonempty **full
ten-source original-byte recheck**, plus all historic
source/numeric/LFS/Python Actions checks. Missing/skipped/pending/
red checks do not pass.
