# W1-AG: verified original global-space and hub-scene Git LFS UnityFS source evidence

**Actual successful original-byte scan/reconcile:** https://github.com/Nippytime/rabron/actions/runs/43652173183

Two original Git-tracked LFS pointer SHA-1 blobs, original `oid sha256` and declared source sizes were checked before selective downloads. Both actual full original `UnityFS` binaries matched their OID SHA-256 and size; read-only pinned UnityPy **1.25.4** measured typed objects and serialized-file-scoped MonoBehaviours. Numeric inventory bounded at **2,048 fields/depth32**. No proprietary media payload was exported.

| Original source | Verified source bytes | Parsed/total MonoBehaviours | Numeric field caps | Original LFS SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `space-global_assets_all.bundle` | 120,234,780 | 37940/37940 | 0 | `b500b6d5f173eb1c2fcb0abeecef0f72e334dd39f784027cf676a774c036af6f` |
| `location-hub_standalone_scenes_all.bundle` | 119,040,551 | 784/784 | 2 | `3cc468e96fe0a97e8b78d84a3b74ac8d29a8c7613b8b2d44aa2c0c71da91feee` |
| **Total** | **239,275,331** | **38,724/38,724** | **2** | Original SHA-256/OIDs matched |

Measured original Unity objects include **1,731 Mesh**, **310 Texture2D**, **1,804 CanvasGroup**, **1,134 Sprite**, **24,275 GameObject** and **38,724 MonoBehaviour**. Bounded serialized client numeric keyword groups: **14,525 timing/world**, **33 economy**, **16 progression**, and **7 combat** fields. These are candidate client data only, not verified server authority, gameplay formulas or economics.

**Partiality must remain explicit:** The hub-scene source contains **2 numeric-field cap records**, and its `bounded_numeric_scan_complete` is **false**; global-space has 0 caps and `bounded_numeric_scan_complete=true`. Zero unparsed MonoBehaviours does **not** mean the entire numeric source is complete. Newly discovered caps increase the unresolved historic+new numeric cap backlog from **42 to 44**, rather than being discarded or treated resolved.

The ledger now records **320/330 original sources** and **125,947 parsed MonoBehaviours**; **10 original LFS source paths remain unscanned**. There are **74** cap observations across historical scans, including **44** unresolved distinct capped records (30 previously reverified), pending independent numeric follow-up. Matching original GameAssembly.dll/IL2CPP methods, authoritative server logic, media redistribution rights, Unity 6000.3 Editor/Play Mode/Windows EXE acceptance (#9) and W2–W8 full-game production are unverified.

**Merge gate:** Full nonempty exact two-original latest-head source-byte recheck and every historic source/numeric/LFS/Python workflow/job completed success, unchanged refs squash merge, successful post-merge dev Python CI before issue #85 close/control #32 update.
