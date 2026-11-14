# W1-M: measured three original medium Wwise source inventories

**Real source Actions run:** https://github.com/Nippytime/rabron/actions/runs/43631572017

Exactly three previously unscanned original medium non-LFS Wwise
UnityFS bundles were checked against the pinned Git tree and their
original Git SHA-1, byte sizes, UnityFS signatures and independently
computed SHA-256s in three bounded read-only GitHub Actions jobs.
The pinned UnityPy 1.25.4 scanner retained Unity object types,
serialized-file-scoped path IDs, bounded numeric fields (2,048/depth32)
and truthful partiality metadata. No original audio, Wwise-bank
binaries or other proprietary media was exported.

| Original `.bundle` | Verified source bytes | Parsed / total MonoBehaviours | Numeric capped records | Original-source SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `wwisedata_windows_battle_localized_assets_all.bundle` | 14,696,031 | 2/2 | 2 | `f31d5bd4dc1cb489575f461b0ed85a573065363665a871a219b4310f6f6d4ea5` |
| `wwisedata_windows_gamestart_assets_all.bundle` | 10,517,479 | 2/2 | 1 | `31b6e9f84e81feb1e64d1dcf4a30e008e17351949b0ebf10c6f903be1e981ac2` |
| `wwisedata_windows_initbank_assets_all.bundle` | 2,140,229 | 1/1 | 1 | `ebb4156795693a22ae0641d68e3133c3c99b19629bb04bd05a96bae57d9a42e0` |
| **Total** | **27,353,739** | **5 / 5** | **4** | Per-source hashes above |

All five MonoBehaviours yielded parsable typetrees, but **four
numeric-field-capped records** were reported across these sources.
Every Wwise bundle is therefore marked **bounded numeric incomplete**.
None of the three reported unparsed MonoBehaviour records. Each source
also had an `AssetBundle` object. All four candidate numeric
keyword categories returned **zero matches**; this neither proves
presence nor absence of original audio gameplay logic.

## Remaining source and acceptance limitations

- Original UnityFS source paths documented: **173/330**.
- Parsed MonoBehaviours: **81,829**, not recovered code.
- Original paths still without documented source scan: **157**:
  **137 medium non-LFS** and **20 pending LFS** original bundles.
  All large non-LFS originals are documented.
- **42 unresolved capped numeric records**: 26 older, 7 W1-F
  localization, 1 W1-H realm, 1 W1-I settlement, 2 W1-K
  settlement2, 1 W1-L global Wwise and 4 W1-M audio banks.
  The raw ledger contains **72** cap observations, 30 of which
  were previously resolved by targeted numeric scans.
- The SHA-1/Git blob IDs, independent SHA-256s, source sizes,
  object types, candidate counts, declared scan limits and explicit
  partiality are stored in `reconstruction/data/extraction_coverage.json`.
  Per-object bounded field samples remain metadata-only Actions
  artifacts.
- After committing these records, W1-M CI must run a **nonempty
  full-original-source recheck**, plus all triggered W1-F through
  W1-L source checks and existing numeric/LFS and Python tests.
- Matching original GameAssembly.dll, IL2CPP method code, Wwise
  bank playback/redistribution rights, authoritative server game
  mechanics and actual Unity 6000.3 Editor/Play Mode/Windows EXE
  acceptance remain unavailable or unverified. W1 source gate and
  W2–W8 full game roadmap are not complete.
