# W1-R: verified ten original medium character-mask 12–21 UnityFS bundles

**Original-source run:** https://github.com/Nippytime/rabron/actions/runs/43636004658

Ten exact `character-mask-12` through `character-mask-21` sources were sparse-checked-out
read-only from the pinned original Git tree, verified against original Git
blob SHA-1 and byte lengths in `reconstruction/data/medium_mask_12_21_source_targets.json`,
and independently SHA-256 hashed. Pinned UnityPy **1.25.4** scanned
UnityFS object types and bounded numeric MonoBehaviour fields
(**2,048-field maximum/depth32**) in five original-source batches
of two (maximum two concurrently). No original game media
was exported or committed.

| Original bundle | Source bytes | MonoBehaviours parsed/total | Texture2D | Original SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `character-mask-12_assets_all.bundle` | 1,783,058 | 0/0 | 3 | `84de8f4cb924f17b524ee2c99637447028fcbd38c5b3dfac520b85f836e2fc8e` |
| `character-mask-13_assets_all.bundle` | 1,778,615 | 0/0 | 3 | `e28fcdb0f84124ec6dbfb851285fa247cea7b5bf30c591ca8ba4932572cf5cba` |
| `character-mask-14_assets_all.bundle` | 1,505,267 | 0/0 | 3 | `b03f5819aa39ff08b54098c16d69ae013e6d29a4058c0f8593119311a4f3d323` |
| `character-mask-15_assets_all.bundle` | 2,302,774 | 0/0 | 5 | `56dc0c53daf6c93b2e634e6630579b46f7797c7c4a679b3b9784cd23bfda2263` |
| `character-mask-16_assets_all.bundle` | 3,787,811 | 0/0 | 6 | `502a3187fa42d5295c7f0832de3af407a10489ab1eb64291540e2c1e58bd8ac2` |
| `character-mask-17_assets_all.bundle` | 1,733,881 | 0/0 | 3 | `280f638d19b5f40b73175166608d2bad7561087591813262a6a803dba0ece09b` |
| `character-mask-18_assets_all.bundle` | 1,780,034 | 0/0 | 3 | `e0ba2c527167f4e67c23a74856a5094787a88d33c0512e2d978238c4d3b3db57` |
| `character-mask-19_assets_all.bundle` | 1,605,021 | 0/0 | 3 | `1c45a9644d4af221334321f43beee12bd8500a4bb8af984479bcc2e052c410ee` |
| `character-mask-20_assets_all.bundle` | 1,463,961 | 0/0 | 3 | `eacac7ad7625ee98d659c6963dab4b0e13955485b618c45a7dc021ffb101c577` |
| `character-mask-21_assets_all.bundle` | 1,861,513 | 0/0 | 3 | `f7a9dfcbe879b8972b4ca01ff6b94d4b620478a188f4d98fd5c2efa0b6f7c596` |
| **Total** | **19,601,935** | **0/0** | **35** | Ten verified source hashes |

Each original contains precisely one AssetBundle and several Texture2D
objects, with **zero actual MonoBehaviours, zero Mesh objects, zero
unparsed records, zero numeric field/depth caps and zero candidate
combat/economy/progression/timing fields**. These are genuine
serialized-file inventory zero counts, not failed extraction or
unverified numerical gameplay claims.

After this source pass the evidence ledger documents **218/330**
original UnityFS sources and **81,858** parsed MonoBehaviours.
**112** original bundle paths remain unscanned (**92** medium
non-LFS, **20** original LFS); **42** old numeric capped records
remain unresolved. No original authoritative combat or economy
coefficients, source IL2CPP methods, `GameAssembly.dll`, game server
authority, proprietary redistribution rights or actual
Unity Editor/Play Mode/EXE acceptance (#9) are established.

**Merge gate:** full nonempty latest-head ten-original source-byte
recheck plus all previous source, numeric, LFS and Python
GitHub Actions checks must complete successfully before merge.
