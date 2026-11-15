# W1-AM exact original city-scene UnityFS LFS source inventory

**Original-source proof:** [W1-AM first actual binary scan and strict reconciliation #43675221667](https://github.com/Nippytime/rabron/actions/runs/43675221667) completed **3/3 nonempty jobs successfully**. Git LFS original pointer was independently verified, then **549,566,135 actual bytes** downloaded selectively and checked against the exact original SHA-256 and UnityFS magic. The scan used pinned UnityPy 1.25.4, 32 MiB block/read and 128 MiB cache limits, and a separately named 8 MiB city MonoBehaviour object budget; no third-party original media was exported.

| Original identity / measurement | Verified value |
| --- | --- |
| Original source | `StreamingAssets/aa/StandaloneWindows64/location-city-standalone_scenes_city_standalone.unity.bundle` |
| Git pointer blob SHA-1 | `c73e7b84edc6b4e73001923054ff3a29bd540393` |
| Full original binary and LFS SHA-256 | `5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f` |
| Exact downloaded bytes | **549,566,135** |
| Typed Unity object headers counted | **366,174** |
| Original MonoBehaviours parsed / present | **14,467 / 14,467** |
| Numeric-field cap records | **5** (2,048 fields/depth 32) |
| Explicitly unparsed MonoBehaviours | **0** |
| Bounded numeric scan complete | **No — five capped records** |
| Candidate fields in bounded parsed section | combat **195**, economy **133**, progression **144**, timing/world **8,201** |

High-level object inventory: GameObject **97,446**, Transform **97,437**, MeshFilter **47,281**, MeshRenderer **47,263**, BoxCollider **30,245**, LODGroup **17,036**, MonoBehaviour **14,467**, Mesh **6,487**, CapsuleCollider **3,201**, MeshCollider **1,627**, Texture2D **815**, ParticleSystem **656**, ParticleSystemRenderer **656**, Material **609**, Light **431**, SkinnedMeshRenderer **206**, and other serialized types. These are **client metadata classifications**, not reconstructed gameplay formulas.

**Strict first source reconciliation**: `documented_before=329`, `documented_after=330`, `new_documented=1`, `source_reverified=0`, `unscanned_after=0`, `tracked_bundles=330`, `unparseable_attempts=[]`. Original source artifact [#14145647082](https://github.com/Nippytime/rabron/actions/runs/43675221667/artifacts/14145647082) and measured ledger [#14146191881](https://github.com/Nippytime/rabron/actions/runs/43675221667/artifacts/14146191881) retain the evidence.

Proposed branch ledger source-path coverage is **330/330**, with **143,131** parsed MonoBehaviours and **355 numeric caps** (350 previously, 5 new). Previously unresolved field caps under existing targeted recovery accounting were 320; they become **325** with five new city caps. The prior two separately unparsed Wwise MonoBehaviours remain. This is **NOT semantic recovery completion**: five new city MonoBehaviour field caps, 274 earlier Wwise numeric caps, old Wwise oversized parsing, and original IL2CPP/server method bodies remain unresolved. Asset reuse/redistribution rights, Unity Editor/Play Mode and Windows EXE testing are not established.

**Latest-head verification still pending:** these measured records must be committed and then reverified with a fresh current-head full-original city `recheck` proving `source_reverified=1`, `new_documented=0`, `documented_after=330`, `unscanned_after=0`. Every current-head historical, source and Python job/workflow/check must complete success before merging into `dev`; only then validate postmerge `dev` Python CI, close #100 and update control #32.
