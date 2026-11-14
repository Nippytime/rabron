# W1-N: verified original police body customization UnityFS inventory

**Measured source run:** https://github.com/Nippytime/rabron/actions/runs/43632465318

Exactly seven previously unscanned medium non-LFS police body
customization bundles from
`reconstruction/data/medium_police_body_source_targets.json` were
read from original Git objects in four bounded 2/2/2/1 source
GitHub Actions batches. Each source's original Git SHA-1 object ID,
byte length, UnityFS signature, independently computed SHA-256 and
Unity object inventory were validated. The shared pinned UnityPy
1.25.4 scanner retained serialized-file-scoped MonoBehaviour identities,
with declared 2,048 numeric fields/depth 32 bounds.

| Original source bundle | Verified bytes | Parsed/total MonoBehaviours | Meshes | Textures | Measured SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_1_manpolicebody.asset.bundle` | 8,126,199 | 1/1 | 5 | 3 | `d7beddfeb959153dc93400c1aeaf2813734b986c9615bb363266ed446fcc3d99` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_1_womanpolicebody.asset.bundle` | 9,011,397 | 1/1 | 5 | 3 | `66e91451a23a5d7a40c3293f315cf453527681b14a1d8acfe0a56008c598eaf0` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_2_manpolicebody.asset.bundle` | 8,894,809 | 1/1 | 5 | 3 | `2ae00d9abb0d65789afcced1ade533599cf489e206a5caf045c500e9010fb74d` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_2_womanpolicebody.asset.bundle` | 9,563,512 | 1/1 | 5 | 3 | `4eefd4d35b642f0accd5a5e3255e1b6a4c621a049eb27f8ef87f41a4ed71271a` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_3_manpolicebody.asset.bundle` | 9,969,196 | 1/1 | 5 | 3 | `c860292a707737fc858f7ce4decbec2105191a17c57b7d6d657dc0e301fee664` |
| `character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_3_womanpolicebody.asset.bundle` | 8,264,205 | 1/1 | 5 | 3 | `e907c72b344327523d003fcbe12fdb7dddf1e2a821a01a4d46629dc38e023f41` |
| `character-separeted_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_0_womanpolicebody.asset.bundle` | 8,681,637 | 1/1 | 5 | 3 | `a7c99f60a975f8f0603381802342e362db23bc8e7fa72df6ebaa9315f975c949` |
| **Total** | **62,510,955** | **7/7** | **35** | **21** | Per-source hashes above |

Each original contains exactly **one** parsed MonoBehaviour, **five**
Unity Mesh objects, **three** Texture2D objects, **one** Material
and **one** AssetBundle object. All seven had **zero unparsed**
MonoBehaviours and **zero numeric field/depth-capped records**.
All recorded numeric keyword categories (combat, economy, progression,
timing/world) were zero. The already documented small
`0_manpolicebody` original is not included in these new scans.

**Only metadata was retained.** No original police character meshes,
textures, materials, models, audiovisual files or executable assets
were exported into the repository. This source inventory does not
establish police AI, law-enforcement behavior, combat formulas,
server authority, original visual fidelity or media reuse rights.

## Updated source recovery boundary

- **180/330** tracked original UnityFS sources have source-verified,
  bounded inventories in `reconstruction/data/extraction_coverage.json`.
- **81,836** MonoBehaviours parsed; this is client serialized metadata,
  not reconstructed source code.
- **150** original paths remain unscanned: **130 medium non-LFS**,
  **20 LFS-pointer original paths**. No unscanned large non-LFS original
  source remains.
- **42** numeric cap records remain unresolved (72 raw observations,
  including 30 previously resolved with targeted historic scans).
  W1-N adds **no new caps**.
- These seven source identities, exact source SHA fingerprints, typed
  counts, caps, limits and keyword counts are committed in the machine
  ledger; per-object path IDs remain metadata-only CI artifacts.
  The seven originals must be reverified on the measured-ledger PR head.
- Matching original GameAssembly.dll, IL2CPP methods, original server
  authority and licensed original-media rights remain missing or
  unverified. Unity 6000.3 Editor import, Play Mode and Windows EXE
  manual acceptance have **not** been run (issue #9). The full W1
  evidence gate and W2–W8 waterfall remain incomplete.
