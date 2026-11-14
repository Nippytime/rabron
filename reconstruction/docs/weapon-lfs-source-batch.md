# W1-AC: verified original weapon MC10 and PDW90 Git LFS UnityFS sources

**Successful original LFS binary run:** https://github.com/Nippytime/rabron/actions/runs/43649328171

Two exact, Git-tracked original LFS pointers were validated against original pointer SHA-1, declared SHA-256 OID and original byte size. GitHub Actions selectively downloaded **only** these two originals, verified actual UnityFS signatures, byte count and SHA-256 against their LFS OIDs, and used read-only UnityPy **1.25.4** with numeric limits **2,048 fields/depth32**. No proprietary models, textures or original media were exported.

| Original bundle | Verified bytes | MonoBehaviours parsed/total | Original LFS SHA-256 |
| --- | ---: | ---: | --- |
| `weapon-mc10_assets_all.bundle` | 54,256,657 | 78/78 | `945c1dcb401470df2e12ee5da672631b54e43a82b5ccd339daf17f12186f6b38` |
| `weapon-pdw90_assets_all.bundle` | 55,401,905 | 57/57 | `e47b0953477de5dab01f9ff73a36a5a8fccf28ceb0926a9aef1b310d252d33d8` |
| **Total** | **109,658,562** | **135/135** | Original SHA-256/OID matches |

Measured Unity object totals: **51 Mesh**, **69 Texture2D**, **13 Material**, **512 GameObject**, **15 BoxCollider**, **135 MonoBehaviour**, zero unparsed records and zero new numeric field caps. Bounded source metadata contains **330 combat keyword numeric-field matches** (198 MC10, 132 PDW90). These are **client serialized keyword candidates, not confirmed server-authoritative damage, recoil or ballistic formulas**.

The ledger now documents **312/330** original tracked UnityFS source bundles and **82,268** parsed MonoBehaviours; **18** original LFS-pointer source paths remain unscanned. **42 older numeric caps** remain unresolved. Matching original IL2CPP/GameAssembly.dll, server rules, media reuse rights, Unity 6000.3 Editor/Play Mode and Windows EXE acceptance (issue #9) remain unverified.

**Merge gate:** nonempty exact two-original LFS latest-head byte recheck and all historical source/numeric/LFS/Python workflow/jobs completed success, unchanged refs before squash merge, successful post-merge dev Python CI before closing issue #77 and updating control #32.
