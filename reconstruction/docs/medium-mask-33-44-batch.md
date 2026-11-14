# W1-T: source-verified original medium character-mask 33–44 UnityFS inventory

**Original-source scan:** https://github.com/Nippytime/rabron/actions/runs/43637568828

All ten exact original Git blob SHA-1/size pinned medium character-mask
sources (33–34, 36–39 and 41–44) were read-only sparse-checked-out from
the original pinned Unity Git tree. UnityFS type signatures and independent
SHA-256 of each original were verified. UnityPy **1.25.4** scanned
the source Unity object types, original serialized-file-scoped MonoBehaviour
identities and bounded numeric field scans (max **2,048 fields/depth32**)
in five two-source batches (max two concurrently). No game media was
exported or committed.

| Original bundle | Verified source bytes | MonoBehaviours parsed/total | Mesh | Texture2D | Original SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `character-mask-33_assets_all.bundle` | 1,385,457 | 0/0 | 0 | 3 | `2851ee220daa73569e9c8deacf74682d0064c8b792ebe2b1c8a9302dbaff610e` |
| `character-mask-34_assets_all.bundle` | 1,952,792 | 2/2 | 10 | 3 | `6c520039021bfbe58eb18d5799ce0f0af5b7e1e32f09a8caa9b7d68901fd3b23` |
| `character-mask-36_assets_all.bundle` | 2,223,752 | 0/0 | 0 | 5 | `16dccc374aeb848a7c5ca1ca76a4bdbdf246b85c5d51199f17d798c2ac2cc6e2` |
| `character-mask-37_assets_all.bundle` | 1,674,936 | 0/0 | 0 | 3 | `2ad70355e7f34c09e15f253629b65f75c08a0fda84751196148b38d19885d4c6` |
| `character-mask-38_assets_all.bundle` | 3,385,948 | 4/4 | 10 | 5 | `4ef9b9f86e2981482a5c8fe424240aca270f4fe9a1ba4b5d3597f59a05a2db20` |
| `character-mask-39_assets_all.bundle` | 3,518,919 | 0/0 | 0 | 6 | `7e30dd1291ecc8d571adbfc29be11dfaaa1879e656f9ff43181f9032ce754198` |
| `character-mask-41_assets_all.bundle` | 2,330,689 | 2/2 | 10 | 3 | `51dc1ce217cf364bd54e8ce4ec90596a365967df02c61fe5606866549718d8f3` |
| `character-mask-42_assets_all.bundle` | 2,103,509 | 0/0 | 0 | 4 | `d4356859671540b3f7b1bc98a4d42aa9d0f5d2d79168d43f03d16d92c92749d2` |
| `character-mask-43_assets_all.bundle` | 3,407,846 | 0/0 | 0 | 6 | `52c923145d6aed37ff6305015c6dadfd981ae5217ede2dcaf1b286646ca89fa0` |
| `character-mask-44_assets_all.bundle` | 4,329,612 | 6/6 | 10 | 9 | `305a51ce72bddcfe0203ab0f44afc86d962ea67c9ef50d33fea6a7c89adcf785` |
| **Total** | **26,313,460** | **14/14** | **40** | **47** | Ten original source digests |

Four originals (masks **34, 38, 41 and 44**) have parsed MonoBehaviours
(**2, 4, 2 and 6 respectively**) alongside meshes and materials.
Six are genuine texture-only sources with zero MonoBehaviours. Across
all ten sources there are **12 Material** objects, **zero unparsed
records**, **zero new numeric field/depth caps** and **zero** candidate
combat/economy/progression/timing field matches.

The ledger now documents **238/330** original UnityFS bundles and
**81,876** parsed MonoBehaviours. **92** original bundles remain unscanned:
**72** medium non-LFS and **20** LFS original sources. The existing
**42** historical bounded numeric-cap records remain unresolved.

Original copyrighted source media was not redistributed. Source-verified
serialized asset metadata is **not** authoritative gameplay logic.
Matching original GameAssembly.dll, IL2CPP method bodies, game server
authority, source media rights, Unity Editor/Play Mode and Windows EXE
runtime acceptance (#9) are still unverified.

**Merge gate:** on the latest measured-data PR head, a nonempty full
original ten-source binary recheck plus every previous source/numeric/
LFS/Python Actions workflow must complete successfully. Missing, queued,
skipped, running or failed gates do not count as success.
