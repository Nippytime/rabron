# W1-AF: verified original KL545 weapon and character LFS source scans

**Successful original Git LFS UnityFS binary run:** https://github.com/Nippytime/rabron/actions/runs/43651416997

Both original Git-tracked LFS pointer SHA-1 hashes, SHA-256 OIDs and declared sizes were verified before a selective download of exactly these sources. Actual UnityFS signatures, SHA-256 digests and byte sizes matched the original OIDs after download. Read-only pinned **UnityPy 1.25.4** scanned original object types and serialized-file-scoped MonoBehaviours with bounded numeric metadata (2,048 fields/depth32), without exporting proprietary media.

| Original source | Actual verified original bytes | MonoBehaviours parsed/total | Original LFS SHA-256 |
| --- | ---: | ---: | --- |
| `weapon-kl545_assets_all.bundle` | 105,697,435 | 221/221 | `b8d9643f6333f07ab662371d5d64a00cf961b0e602d6a8018ca33393621ec3db` |
| `character_assets_.bundle` | 97,160,534 | 4436/4436 | `0d6ac130fa1761c2058d3f790b887b0275bdbc08c6576fbd16fccf4a33f94ba1` |
| **Total** | **202,857,969** | **4,657/4,657** | Both SHA-256 / OID identities verified |

The original sources contain **330 Mesh**, **99 Texture2D**, **31 Material**, **2,563 AnimationClip**, **24,539 GameObject** and **4,657 MonoBehaviour** objects. Numeric inventory contains **532 combat** and **5,595 timing/world** keyword matches, which are client serialized candidates, **not verified damage/weapon recoil, authoritative animation timing, or server-side formulas**. There are zero unparsed records and zero new numeric field cap records.

The evidence ledger now documents **318/330** original UnityFS bundles and **87,223** parsed MonoBehaviours. **12** original LFS-pointer sources remain unscanned; **42** historic numeric caps remain unresolved. Matching GameAssembly.dll/IL2CPP code, authoritative server systems, media reuse rights, Unity 6000.3 Editor/Play Mode and Windows EXE acceptance (#9) remain unverified.

**Hard merge gate:** exact nonempty two-original latest-head binary recheck and every historical source/numeric/LFS/Python workflow/job completed success, unchanged head/base squash merge, successful post-merge dev Python CI before focused issue #83 closure/control update.
