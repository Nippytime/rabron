# W1-AE: two original RC556 and TAG12K weapon LFS UnityFS source scans

**Successful original LFS binary run:** https://github.com/Nippytime/rabron/actions/runs/43650766303

Two original Git-tracked LFS source pointers were verified against original Git SHA-1 blob hashes, SHA-256 LFS OIDs and declared byte lengths before selective LFS download. The downloaded original bytes matched the exact UnityFS signatures, source lengths and OID SHA-256s. Pinned **UnityPy 1.25.4** read-only scans counted actual Unity object types, serialized-file-scoped MonoBehaviours and bounded numeric fields (2,048 fields/depth32). No original proprietary media was exported.

| Original source | Verified original bytes | MonoBehaviours parsed/total | Original SHA-256 / LFS OID |
| --- | ---: | ---: | --- |
| `weapon-rc556_assets_all.bundle` | 69,142,769 | 132/132 | `b03dc0972f2727aca8f442d66fd1f4f7a1511bd2064a4f085bf3fae59b7f1d53` |
| `weapon-tag12k_assets_all.bundle` | 58,972,603 | 57/57 | `ad2678f11e396cfb1e86e637737a4305048f335a5c10551e515db274c39fbe6b` |
| **Total** | **128,115,372** | **189/189** | Both original SHA-256 identities match |

Actual original typed object totals: **68 Mesh**, **75 Texture2D**, **13 Material**, **710 GameObject**, **189 MonoBehaviour**, zero unparsed records and zero new numeric field caps. The extractor found **396 combat** and **36 timing/world-related** numeric keyword matches, which are **client serialized candidate data only**, not proven authoritative weapon damage/recoil/spread or server gameplay formulas.

After this evidence commit, the coverage ledger documents **316/330 original UnityFS bundles** and **82,566 parsed MonoBehaviours**. **14 original LFS-pointer sources** remain unscanned and **42 historical numeric field caps** remain unresolved. The missing matching original GameAssembly.dll/IL2CPP implementation, server authority, media redistribution rights and Unity 6000.3 Editor/Play Mode/Windows EXE acceptance (#9) remain unverified.

**Gate:** Nonempty complete two-original latest-head source-byte recheck and all prior source/numeric/LFS/Python workflow/jobs completed successful; head/base unchanged at squash merge, verify post-merge `dev` Python CI, then close focused issue #81 and update control #32.
