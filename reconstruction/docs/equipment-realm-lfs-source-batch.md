# W1-AD: original equipment-VFX and realm-scene Git LFS UnityFS source evidence

**Actual original-byte LFS Actions run:** https://github.com/Nippytime/rabron/actions/runs/43650079085

Two exact original LFS pointer entries were read-only verified against Git pointer SHA-1, declared original SHA-256 OID and byte size. Authenticated Git LFS downloaded only these two sources, and the actual UnityFS signatures, SHA-256 and byte lengths matched both original pointers. Pinned **UnityPy 1.25.4** scanned original Unity object types and serialized-file-scoped MonoBehaviours with **2,048 numeric fields/depth32**. No proprietary media was exported.

| Original source | Actual verified bytes | MonoBehaviours parsed/total | Original LFS SHA-256 |
| --- | ---: | ---: | --- |
| `equipement_assets_vfx.bundle` | 55,350,015 | 98/98 | `396f23f4945428b72bb49ebe0cfdc1526ecbe178a2329c2afe7a4eb7022f0b82` |
| `space-realm_scenes_all.bundle` | 73,336,741 | 11/11 | `3b93cf7b33ef488ec4956f301fdbac7dfb170ceb7838e2ecc2ab235208a4320b` |
| **Total** | **128,686,756** | **109/109** | Two verified original SHA-256/OID identities |

Typed original object totals: **731 ParticleSystem**, **171 Mesh**, **201 Texture2D**, **270 Material**, **1,160 GameObject** and **109 MonoBehaviour**, zero unparsed records or new field caps. Bounded numeric metadata exposes **444 timing/world keyword candidate fields** (442 in equipment VFX, 2 in realm scenes). These are client serialized presentation/configuration candidates, **not authoritative world timings, damage, economy or server formulas**.

The ledger documents **314/330** original UnityFS sources and **82,377** parsed MonoBehaviours. **16** original LFS sources remain unscanned; **42** historic numeric caps remain unresolved. Matching original IL2CPP/GameAssembly.dll methods, server authority, media reuse rights and actual Unity 6000.3 Editor/Play Mode/Windows EXE acceptance (issue #9) are unverified.

**Merge gate:** Latest-head complete nonempty original two-LFS-source binary recheck and all historic source/numeric/LFS/Python workflows/jobs completed success, unchanged head/base before squash merge, post-merge dev CI success, then close #79 and update control issue #32.
