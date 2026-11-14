# W1-L: measured final large original UI and Wwise audio UnityFS inventory

**Source-verified run:** https://github.com/Nippytime/rabron/actions/runs/43630843839

These were the **last three previously unscanned large (20–64 MiB)
non-LFS original UnityFS bundles**, as defined by exact source names in
`reconstruction/data/final_large_media_source_targets.json`. They
were independently downloaded from the pinned Git tree in three
bounded one-source GitHub Actions jobs; each exact source byte length,
original Git blob SHA-1, UnityFS header and computed SHA-256 were checked.
Read-only pinned UnityPy 1.25.4 counted the Unity object kinds and,
where present, MonoBehaviour numeric fields at **2,048 fields/depth32**.
No original textures, sprite atlases, audio, binary media or executable
scripts were copied into the repository or the evidence artifacts.

| Original bundle | Source bytes verified | Parsed/total MonoBehaviours | Numeric caps | Verified Unity object types | Measured SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| `ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_all__fullspriteatlas_4k.spriteatlasv2.bundle` | 33,795,283 | 0 / 0 | 0 | AssetBundle: 1, SpriteAtlas: 1, Texture2D: 1 | `a9fd7f715211a12af9182f722dcaa073e3780107fdbbdad259b09d20c12dfc47` |
| `ui-spriteatlas_assets_bigimages.bundle` | 22,973,668 | 0 / 0 | 0 | AssetBundle: 1, Sprite: 15, Texture2D: 15 | `49796e7a90b2d3aa087579e825dca057cb4d8f8d3075321c89170e91b16419a9` |
| `wwisedata_windows_global_assets_all.bundle` | 22,088,300 | 1 / 1 | 1 | AssetBundle: 1, MonoBehaviour: 1 | `34b2695857cc96f6714c9f138c82cbef209b6616f4805cae413861b037bd85d8` |
| **Totals** | **78,857,251** | **1 / 1** | **1** | Per-source counts above | Per-source hashes above |

Both UI sprite atlas sources legitimately had **zero MonoBehaviours**;
the verified alternative object types were:
one `SpriteAtlas` and one `Texture2D` in the 4K UI source;
15 `Sprite` and 15 `Texture2D` in the big-images source,
plus an `AssetBundle` in each.

The global Wwise source contained **one parsed MonoBehaviour with one
explicitly numerically capped record**. Its bounded MonoBehaviour
numeric inventory is **partial**, despite a successfully parsed
typetree. No source in this batch reported unparsed MonoBehaviours.
All four candidate keyword categories (combat, economy, progression,
timing/world) had **zero** matches. The source scan did not decode
or establish rights for original Wwise audio playback or exports.

## Durable coverage and limits

- Source-documented original UnityFS paths: **170 of 330**.
- Parsed MonoBehaviours: **81,824**, not recovered game code.
- Original bundle paths still **unscanned: 160**: **140 medium non-LFS**
  and **20 LFS-pointer** sources. **No non-LFS large bundle remains
  unscanned** in the source inventory.
- Remaining unresolved numeric capped records: **38** (26 historical,
  7 localization, 1 W1-H realm, 1 W1-I settlement additive scene,
  2 W1-K settlement2 and 1 W1-L Wwise), of **68** raw observed caps
  including 30 previously resolved targeted scans.
- Exact source byte fingerprints, typed Unity object counts, numeric
  limits, partiality and field keyword totals are now in
  `reconstruction/data/extraction_coverage.json`; per-object IDs
  remain metadata-only GitHub Actions artifacts.
- The full three-source **recheck** must pass on the measured-ledger
  PR head, along with existing legacy source, numeric/LFS and
  regression workflows. No source with zero behaviors is falsely
  marked unverified, and the Wwise numeric cap is not discarded.
- Matching original GameAssembly.dll and IL2CPP method bodies,
  server-authoritative gameplay systems and rights to source media
  remain missing/unverified. Full Unity Editor import, Play Mode,
  Windows EXE and W1–W8 full game acceptance have **not** been run.
